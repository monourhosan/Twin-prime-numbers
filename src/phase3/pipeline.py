"""
Phase 3 Pipeline Orchestrator (HDRSS).
Executes candidate windows with exact stage timings, strict proof ordering,
task continuation tracking (PARTIAL / COMPLETED), and graceful stop detection.
"""

import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from .config import Phase3Config
from .candidate_generator import Phase3Wheel
from .segmented_sieve import SegmentedSieveS1
from .hybrid_sieve import HybridSieveS2
from .prp import screen_pair_prp, PRPStatus
from .proof import proth_prove, llr_prove, ProofStatus
from .certificate import TwinPrimeCertificateV3
from .metrics import WindowMetrics
from .storage import Phase3Storage

class SearchPipeline:
    def __init__(self, config: Phase3Config, storage: Phase3Storage, worker_id: str = "worker_1"):
        self.config = config
        self.storage = storage
        self.worker_id = worker_id

        # Instantiate sieves on demand per exponent
        self._s1_cache: Dict[int, SegmentedSieveS1] = {}
        self._s2_cache: Dict[int, HybridSieveS2] = {}
        self._wheel_cache: Dict[int, Phase3Wheel] = {}

    def get_sieve(self, n: int):
        algo = self.config.algorithm.lower()
        if algo in ("s2", "hybrid_sparse"):
            if n not in self._s2_cache:
                self._s2_cache[n] = HybridSieveS2(
                    n=n,
                    sieve_depth=self.config.sieve_depth,
                    stride_cutoff=self.config.stride_cutoff
                )
            return self._s2_cache[n]
        else: # Default is S1: Vectorized Segmented Sieve (Fastest measured)
            if n not in self._s1_cache:
                self._s1_cache[n] = SegmentedSieveS1(n, self.config.sieve_depth)
            return self._s1_cache[n]

    def check_stop_signals(self) -> bool:
        """Checks for external graceful stop / pause file requests."""
        stop_file = Path(self.config.checkpoint_dir) / f"{self.config.campaign_id}.stop"
        pause_file = Path(self.config.checkpoint_dir) / f"{self.config.campaign_id}.pause"
        return stop_file.exists() or pause_file.exists()

    def process_task(
        self,
        task: Dict[str, Any],
        on_discovery: Optional[Callable[[TwinPrimeCertificateV3], None]] = None,
        deadline_time: Optional[float] = None,
        target_proven_remaining: Optional[int] = None,
    ) -> Tuple[List[TwinPrimeCertificateV3], bool, WindowMetrics]:
        """
        Executes search for a work unit task.
        Returns: (discoveries, is_fully_completed, metrics).
        If stopped early (by limit, deadline, or stop file), marks is_fully_completed=False.
        """
        task_id = task["task_id"]
        n = task["n"]
        k_start = task["next_unprocessed_k"]
        k_end = task["k_end"]

        metrics = WindowMetrics()
        t_start_wall = time.monotonic()
        t_start_cpu = time.process_time()

        raw_candidates_count = (k_end - k_start) // 2
        metrics.raw_odd_k = max(0, raw_candidates_count)

        # 1. Sieving
        t0 = time.monotonic()
        sieve = self.get_sieve(n)
        survivors = sieve.sieve_window(k_start, k_end)
        metrics.sieve_ms = (time.monotonic() - t0) * 1000.0
        metrics.sieve_survivors = len(survivors)

        discovered: List[TwinPrimeCertificateV3] = []
        is_completed = True
        next_unprocessed_k = k_end
        two_n = 1 << n

        # 2. Iterate through survivors
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

            # Enforce theorem precondition k < 2^n
            if k >= two_n:
                continue

            A = k * two_n - 1
            B = k * two_n + 1

            # Exact digit checking
            digits_A = len(str(A))
            digits_B = len(str(B))
            if digits_A < self.config.min_digits or digits_B < self.config.min_digits:
                continue

            # Stage 2: PRP screening (Miller-Rabin)
            t_prp = time.monotonic()
            status_A, status_B = screen_pair_prp(A, B, bases=self.config.prp_bases)
            metrics.prp_ms += (time.monotonic() - t_prp) * 1000.0

            if status_B != PRPStatus.PROBABLE_PRIME or status_A != PRPStatus.PROBABLE_PRIME:
                continue

            metrics.prp_pair_pass += 1

            # Stage 3: Rigorous deterministic primality proving
            t_proof = time.monotonic()
            # Proth on B
            p_status, w, p_msg = proth_prove(k, n, B, witness_candidates=self.config.proth_witness_pool)
            if p_status != ProofStatus.PROVEN:
                metrics.proof_ms += (time.monotonic() - t_proof) * 1000.0
                continue
            metrics.proth_proven += 1

            # LLR on A
            l_status, p_param, u0, l_msg = llr_prove(k, n, A, parameter_candidates=self.config.llr_parameter_pool)
            metrics.proof_ms += (time.monotonic() - t_proof) * 1000.0
            if l_status != ProofStatus.PROVEN:
                continue
            metrics.llr_proven += 1

            # Both proven! Build certificate
            t_io = time.monotonic()
            cert = TwinPrimeCertificateV3(
                k=k,
                n=n,
                proth_witness=w,
                llr_parameter_p=p_param,
                llr_u0=u0,
                campaign_id=self.config.campaign_id,
                task_id=task_id,
                settings_sha256=self.config.compute_sha256(),
            )
            discovered.append(cert)
            metrics.pair_verified += 1
            metrics.io_ms += (time.monotonic() - t_io) * 1000.0

            if on_discovery:
                on_discovery(cert)

            # Check if target proven pairs reached
            if target_proven_remaining and len(discovered) >= target_proven_remaining:
                # Early stop: this window is partial unless this was the last survivor
                if idx < len(survivors) - 1:
                    is_completed = False
                    next_unprocessed_k = survivors[idx + 1]
                break

        # Compute elapsed timings
        metrics.wall_seconds = time.monotonic() - t_start_wall
        metrics.process_cpu_seconds = time.process_time() - t_start_cpu

        # If not completed, accurately record only actually covered candidate range
        if not is_completed:
            metrics.raw_odd_k = max(0, (next_unprocessed_k - k_start) // 2)

        # Update storage
        stats_delta = {
            "raw_tested": metrics.raw_odd_k,
            "wheel_survivors": metrics.sieve_survivors, # filtered candidates
            "sieve_survivors": metrics.sieve_survivors,
            "prp_survivors": metrics.prp_pair_pass,
            "proven_pairs": len(discovered),
            "elapsed_seconds": metrics.wall_seconds,
        }
        self.storage.update_task_progress(
            task_id=task_id,
            next_k=next_unprocessed_k,
            is_completed=is_completed,
            stats_delta=stats_delta
        )
        self.storage.update_heartbeat(self.config.campaign_id, self.worker_id, task_id)

        return discovered, is_completed, metrics
