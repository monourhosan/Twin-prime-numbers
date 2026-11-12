"""
Phase 4 Worker Pipeline and Multiprocessing Execution Engine.
Compatible with Windows spawn, manages atomic leases, stage metrics,
automatic checkpointing, and graceful pause/stop signal detection.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple

from .config import Phase4Config
from .storage import Phase4Storage
from .t_sieve import SieveR0_S1Baseline, SieveR1_TSpace, SieveR2_Adaptive
from .prp import screen_pair_prp, PRPStatus
from .proof import proth_prove, llr_prove, ProofStatus
from .certificate import TwinPrimeCertificateV4

class WorkerPipeline:
    def __init__(self, config: Phase4Config, storage: Phase4Storage, worker_id: str):
        self.config = config
        self.storage = storage
        self.worker_id = worker_id
        self.pid = os.getpid()

        self._sieve_cache: Dict[int, Any] = {}

    def get_sieve_engine(self, n: int):
        if n not in self._sieve_cache:
            strat = self.config.sieve_strategy.lower()
            if strat == "r0_s1_baseline":
                self._sieve_cache[n] = SieveR0_S1Baseline(n, self.config.sieve_depth)
            elif strat == "r2_adaptive":
                self._sieve_cache[n] = SieveR2_Adaptive(n, initial_depth=10_000, max_depth=self.config.sieve_depth)
            else: # Default is R1 (t-space block sieve)
                self._sieve_cache[n] = SieveR1_TSpace(n, self.config.sieve_depth)
        return self._sieve_cache[n]

    def check_stop_signals(self) -> bool:
        ckpt_dir = Path(self.config.checkpoint_dir)
        stop_file = ckpt_dir / f"{self.config.campaign_id}.stop"
        pause_file = ckpt_dir / f"{self.config.campaign_id}.pause"
        return stop_file.exists() or pause_file.exists()

    def process_task(
        self,
        task: Dict[str, Any],
        on_discovery: Optional[Callable[[TwinPrimeCertificateV4, Optional[Path]], None]] = None,
        deadline_time: Optional[float] = None,
        target_proven_remaining: Optional[int] = None
    ) -> Tuple[List[TwinPrimeCertificateV4], bool, Dict[str, Any]]:
        task_id = task["task_id"]
        lease_token = task["lease_token"]
        n = task["n"]
        k_start = task["next_unprocessed_k"]
        k_end = task["k_end"]

        t_wall_start = time.monotonic()
        t_cpu_start = time.process_time()

        # Step 1: Sieving
        sieve = self.get_sieve_engine(n)
        survivors = sieve.sieve_window(k_start, k_end)

        # Heartbeat lease
        self.storage.heartbeat_lease(lease_token, self.config.lease_timeout_seconds)

        discoveries = []
        is_completed = True
        next_unprocessed_k = k_end
        two_n = 1 << n

        prp_screened = 0
        prp_passed = 0
        proth_proven_count = 0
        llr_proven_count = 0

        proofs_dir = Path(self.config.proofs_dir)
        proofs_dir.mkdir(parents=True, exist_ok=True)
        attest_dir = proofs_dir / "attestations"

        last_hb = time.monotonic()

        # Step 2: Iterate survivors
        for idx, k in enumerate(survivors):
            # Check stop conditions
            if deadline_time and time.monotonic() >= deadline_time:
                is_completed = False
                next_unprocessed_k = k
                break

            if self.check_stop_signals():
                is_completed = False
                next_unprocessed_k = k
                break

            # Periodic heartbeat during heavy computation
            if time.monotonic() - last_hb >= 15.0:
                self.storage.heartbeat_lease(lease_token, self.config.lease_timeout_seconds)
                last_hb = time.monotonic()

            if k >= two_n:
                continue

            A = k * two_n - 1
            B = k * two_n + 1

            # Exact digit check
            digits_A = len(str(A))
            digits_B = len(str(B))
            if digits_A < self.config.min_digits or digits_B < self.config.min_digits:
                continue

            # Stage 2: PRP screening (Miller-Rabin)
            prp_screened += 1
            st_A, st_B, _ = screen_pair_prp(A, B, bases=self.config.prp_bases, screen_order="B_then_A")

            if st_A == PRPStatus.PROBABLE_PRIME and st_B == PRPStatus.PROBABLE_PRIME:
                prp_passed += 1

                # Stage 3: Upper Proof (Proth's Theorem)
                st_proth, witness, msg_p = proth_prove(k, n, B, witness_pool=self.config.proth_witness_pool, use_gmpy=self.config.use_gmpy2)
                if st_proth == ProofStatus.PROVEN_PRIME and witness is not None:
                    proth_proven_count += 1

                    # Stage 4: Lower Proof (LLR Theorem)
                    st_llr, param_p, u0, msg_l = llr_prove(k, n, A, parameter_pool=self.config.llr_parameter_pool, use_gmpy=self.config.use_gmpy2)
                    if st_llr == ProofStatus.PROVEN_PRIME and param_p is not None and u0 is not None:
                        llr_proven_count += 1

                        # Generate certificate payload
                        cert = TwinPrimeCertificateV4(
                            k=k,
                            n=n,
                            proth_witness=witness,
                            llr_p=param_p,
                            llr_u0=u0,
                            campaign_id=self.config.campaign_id,
                            task_id=task_id,
                            config_sha256=self.config.compute_sha256()
                        )
                        payload_path = proofs_dir / f"cert_k{k}_n{n}.json"
                        payload_sha = cert.save_payload_file(payload_path)

                        # Independent verification subprocess
                        attest_path = None
                        if self.config.require_independent_verification:
                            verify_cmd = [
                                sys.executable, "scripts/phase4_independent_verify.py",
                                str(payload_path), "--attest-dir", str(attest_dir)
                            ]
                            v_res = subprocess.run(verify_cmd, capture_output=True, text=True)
                            if v_res.returncode == 0:
                                expected_attest = attest_dir / f"attest_{payload_sha[:16]}.json"
                                if expected_attest.exists():
                                    attest_path = expected_attest
                                    cert.claim_level = "PAIR_INDEPENDENTLY_VERIFIED"

                        self.storage.record_discovery(
                            payload_sha256=payload_sha,
                            campaign_id=self.config.campaign_id,
                            task_id=task_id,
                            k=k,
                            n=n,
                            digits=cert.lower_digits,
                            proth_witness=witness,
                            llr_p=param_p,
                            payload_path=str(payload_path),
                            independent_status="VERIFIED" if attest_path else "UNVERIFIED",
                            attestation_path=str(attest_path) if attest_path else None
                        )

                        discoveries.append(cert)
                        if on_discovery:
                            on_discovery(cert, attest_path)

                        if target_proven_remaining and len(discoveries) >= target_proven_remaining:
                            if idx < len(survivors) - 1:
                                is_completed = False
                                next_unprocessed_k = survivors[idx + 1]
                            break

        wall_sec = time.monotonic() - t_wall_start
        cpu_sec = time.process_time() - t_cpu_start

        # Compute accurate candidate counts
        raw_candidates = (k_end - k_start) // 2 if is_completed else max(0, (next_unprocessed_k - k_start) // 2)

        stage_metrics = {
            "raw_tested": raw_candidates,
            "wheel_survivors": len(survivors) if is_completed else idx,
            "sieve_survivors": len(survivors) if is_completed else idx,
            "prp_screened": prp_screened,
            "prp_passed": prp_passed,
            "proth_proven": proth_proven_count,
            "llr_proven": llr_proven_count,
            "wall_seconds": wall_sec,
            "cpu_seconds": cpu_sec
        }

        # Commit to durable storage
        self.storage.commit_task_progress(
            task_id=task_id,
            lease_token=lease_token,
            worker_id=self.worker_id,
            next_k=next_unprocessed_k,
            is_completed=is_completed,
            metrics_dict=stage_metrics
        )

        return discoveries, is_completed, stage_metrics

def worker_process_main(config_path: str, worker_id: str):
    """Entry point for spawned child worker processes."""
    cfg = Phase4Config.from_file(Path(config_path))
    ckpt_dir = Path(cfg.checkpoint_dir)
    db_path = ckpt_dir / f"{cfg.campaign_id}.sqlite"
    storage = Phase4Storage(db_path)
    pipeline = WorkerPipeline(cfg, storage, worker_id)

    while True:
        if pipeline.check_stop_signals():
            break

        task = storage.claim_task(cfg.campaign_id, worker_id=worker_id, pid=os.getpid(), lease_duration_sec=cfg.lease_timeout_seconds)
        if not task:
            break

        discoveries, completed, metrics = pipeline.process_task(task)
        if not completed:
            break
