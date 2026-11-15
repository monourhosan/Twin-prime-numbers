"""
Phase 9 Resumable Search Campaign Orchestrator.
Coordinates GPU sieving (MX250), CPU screening, and Dual-BLS certification.
Implements:
- Atomic JSON checkpoints
- Crash-safe resumption
- Thermal telemetry monitoring (80°C soft throttle, 85°C pause)
- Structured JSONL logging
- Automatic certification and attestation upon discovery
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import gmpy2

from .anchor import PrimorialAnchor, is_small_prime_deterministic
from .cpu_sieve import prepare_sieve_plan, SievePrimePlan, CPUSieve
from .gpu_sieve import GPUSieveMX250
from .screening import screen_candidate_t, CandidateStatus
from .prover import PACCM9Prover
from scripts.phase9_independent_verify import verify_paccm9_certificate

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_gpu_temperature() -> Optional[float]:
    """Queries current NVIDIA GPU temperature via nvidia-smi."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            return float(res.stdout.strip().splitlines()[0])
    except Exception:
        pass
    return None


class CampaignOrchestrator:
    """
    Manages a segmented, checkpointed Phase 9 twin-prime discovery campaign.
    """

    def __init__(
        self,
        campaign_id: str,
        anchor_y: int,
        t_start: int,
        t_end: int,
        sieve_depth: int = 100000,
        batch_size: int = 5000,
        use_gpu: bool = True,
        cross_check_cpu: bool = False,
        stop_on_first_discovery: bool = True,
        data_dir: Optional[Path] = None
    ):
        self.campaign_id = campaign_id
        self.anchor_y = anchor_y
        self.t_start = t_start if t_start % 2 == 1 else t_start + 1
        self.t_end = t_end
        self.sieve_depth = sieve_depth
        self.batch_size = batch_size
        self.use_gpu = use_gpu
        self.cross_check_cpu = cross_check_cpu
        self.stop_on_first_discovery = stop_on_first_discovery

        self.data_dir = data_dir or (REPO_ROOT / "data" / "phase9")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.proofs_cert_dir = REPO_ROOT / "proofs" / "phase9" / "certificates"
        self.proofs_cert_dir.mkdir(parents=True, exist_ok=True)
        self.proofs_att_dir = REPO_ROOT / "proofs" / "phase9" / "attestations"
        self.proofs_att_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = self.data_dir / f"{self.campaign_id}_checkpoint.json"
        self.candidates_file = self.data_dir / f"{self.campaign_id}_candidates.jsonl"
        self.discoveries_file = self.data_dir / f"{self.campaign_id}_discoveries.jsonl"

        # Initialize anchor and prover
        self.anchor = PrimorialAnchor(y=self.anchor_y)
        self.prover = PACCM9Prover(self.anchor)

        # Telemetry metrics
        self.sieve_candidates_total = 0
        self.sieve_survivors_total = 0
        self.single_prp_count = 0
        self.dual_prp_count = 0
        self.proven_pairs_count = 0
        self.proven_pairs: List[Dict[str, Any]] = []

        # Current progress pointer
        self.current_t = self.t_start

        # Prepare sieve plan
        print(f"Preparing sieve plan for anchor y={self.anchor_y} up to Q={self.sieve_depth}...")
        t0_plan = time.perf_counter()
        self.plan = prepare_sieve_plan(self.anchor.S_y, self.anchor.y, self.sieve_depth)
        t1_plan = time.perf_counter()
        print(f"Sieve plan prepared: {len(self.plan)} primes in {t1_plan - t0_plan:.2f}s")

        # Initialize sieve engine
        if self.use_gpu:
            try:
                self.sieve_engine = GPUSieveMX250(self.plan, cross_check_cpu=self.cross_check_cpu)
                if not self.sieve_engine.gpu_ready:
                    print("GPU initialization failed; falling back to CPU sieve.")
                    self.sieve_engine = CPUSieve(self.plan)
                    self.use_gpu = False
                else:
                    print("GPU Sieve Engine successfully initialized on NVIDIA GeForce MX250!")
            except Exception as e:
                print(f"GPU exception: {e}; using CPU fallback.")
                self.sieve_engine = CPUSieve(self.plan)
                self.use_gpu = False
        else:
            self.sieve_engine = CPUSieve(self.plan)

        # Load checkpoint if exists
        self._load_checkpoint()

    def _load_checkpoint(self):
        if self.checkpoint_file.is_file():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.current_t = int(data.get("current_t", self.t_start))
                if self.current_t % 2 == 0:
                    self.current_t += 1
                self.sieve_candidates_total = int(data.get("sieve_candidates_total", 0))
                self.sieve_survivors_total = int(data.get("sieve_survivors_total", 0))
                self.single_prp_count = int(data.get("single_prp_count", 0))
                self.dual_prp_count = int(data.get("dual_prp_count", 0))
                self.proven_pairs_count = int(data.get("proven_pairs_count", 0))
                self.proven_pairs = data.get("proven_pairs", [])
                print(f"Resumed from checkpoint: current_t={self.current_t}, proven_pairs={self.proven_pairs_count}")
            except Exception as e:
                print(f"Warning: Failed to load checkpoint ({e}); starting fresh.")

    def _save_checkpoint(self):
        ckpt_data = {
            "campaign_id": self.campaign_id,
            "anchor_y": self.anchor_y,
            "t_start": self.t_start,
            "t_end": self.t_end,
            "current_t": self.current_t,
            "sieve_depth": self.sieve_depth,
            "use_gpu": self.use_gpu,
            "sieve_candidates_total": self.sieve_candidates_total,
            "sieve_survivors_total": self.sieve_survivors_total,
            "single_prp_count": self.single_prp_count,
            "dual_prp_count": self.dual_prp_count,
            "proven_pairs_count": self.proven_pairs_count,
            "proven_pairs": self.proven_pairs,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        tmp_file = self.checkpoint_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(ckpt_data, f, indent=2)
        tmp_file.replace(self.checkpoint_file)

    def run(self) -> Dict[str, Any]:
        """
        Executes the campaign from current_t up to t_end.
        """
        t_global_start = time.perf_counter()
        print(f"Starting campaign '{self.campaign_id}': t in [{self.current_t}, {self.t_end}], anchor y={self.anchor_y}")

        while self.current_t <= self.t_end:
            # Thermal telemetry check
            gpu_temp = get_gpu_temperature()
            if gpu_temp is not None:
                if gpu_temp >= 85.0:
                    print(f"SAFETY GUARDRAIL: GPU temp {gpu_temp}°C >= 85°C! Pausing campaign.")
                    self._save_checkpoint()
                    break
                elif gpu_temp >= 80.0:
                    print(f"Thermal warning: GPU temp {gpu_temp}°C >= 80°C. Throttling 2 seconds...")
                    time.sleep(2.0)

            # Determine batch range
            b_start = self.current_t
            b_end = min(self.t_end, b_start + 2 * self.batch_size)
            if b_end % 2 == 0:
                b_end -= 1

            n_in_batch = (b_end - b_start) // 2 + 1
            self.sieve_candidates_total += n_in_batch

            t0_batch = time.perf_counter()
            # 1. Sieve window
            survivors = self.sieve_engine.sieve_segment(b_start, b_end)
            self.sieve_survivors_total += len(survivors)

            # 2. Filter for prime multipliers t among survivors
            prime_survivors = [t for t in survivors if is_small_prime_deterministic(t)]

            # 3. CPU screening
            for t_cand in prime_survivors:
                status, pair_tuple = screen_candidate_t(self.anchor.S_y, t_cand, require_prime_t=True)
                if status == CandidateStatus.SINGLE_PRP:
                    self.single_prp_count += 1
                elif status == CandidateStatus.DUAL_PRP:
                    self.dual_prp_count += 1
                    assert pair_tuple is not None
                    C, A, B = pair_tuple
                    digits_A = len(str(A))
                    print(f"\n>>> DUAL-PRP CANDIDATE DISCOVERED! t={t_cand}, digits={digits_A} <<<")

                    # Log candidate
                    cand_record = {
                        "t": t_cand,
                        "digits": digits_A,
                        "status": "DUAL_PRP",
                        "timestamp_utc": datetime.now(timezone.utc).isoformat()
                    }
                    with open(self.candidates_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(cand_record) + "\n")

                    # Attempt deterministic certification
                    print("Executing deterministic Dual-BLS primality certification...")
                    t0_proof = time.perf_counter()
                    cert = self.prover.prove_pair(t_cand, campaign_id=self.campaign_id)
                    t1_proof = time.perf_counter()

                    if cert is not None:
                        cert_path = self.proofs_cert_dir / f"cert_paccm9_{digits_A}d_t{t_cand}.json"
                        with open(cert_path, "w", encoding="utf-8") as f:
                            json.dump(cert, f, indent=2)
                        print(f"Certificate generated and saved: {cert_path.name} in {t1_proof - t0_proof:.2f}s")

                        # Immediately run independent verifier
                        ok, v_logs, att = verify_paccm9_certificate(cert_path, attestation_dir=self.proofs_att_dir)
                        if ok:
                            print(f"[VERIFIED] {cert_path.name} unconditionally verified by independent verifier!")
                            self.proven_pairs_count += 1
                            pair_info = {
                                "t": t_cand,
                                "digits": digits_A,
                                "A": str(A),
                                "B": str(B),
                                "certificate_path": str(cert_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                                "sha256": cert["sha256"],
                                "proof_time_sec": t1_proof - t0_proof
                            }
                            self.proven_pairs.append(pair_info)
                            with open(self.discoveries_file, "a", encoding="utf-8") as f:
                                f.write(json.dumps(pair_info) + "\n")

                            if self.stop_on_first_discovery:
                                self.current_t = b_end + 2
                                self._save_checkpoint()
                                print(f"Primary discovery target reached! Stopping campaign as requested.")
                                return self.get_summary()

            # Advance current_t
            self.current_t = b_end + 2
            self._save_checkpoint()

            t1_batch = time.perf_counter()
            elapsed_batch = t1_batch - t0_batch
            throughput = n_in_batch / elapsed_batch if elapsed_batch > 0 else 0
            print(
                f"Batch [{b_start}, {b_end}]: {len(survivors)}/{n_in_batch} survivors ({len(prime_survivors)} prime), "
                f"PRPs (single={self.single_prp_count}, dual={self.dual_prp_count}), "
                f"speed={throughput:.0f} cand/s, temp={gpu_temp}°C"
            )

        if hasattr(self.sieve_engine, 'close'):
            self.sieve_engine.close()

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "anchor_y": self.anchor_y,
            "t_start": self.t_start,
            "t_end": self.t_end,
            "current_t": self.current_t,
            "sieve_depth": self.sieve_depth,
            "use_gpu": self.use_gpu,
            "sieve_candidates_total": self.sieve_candidates_total,
            "sieve_survivors_total": self.sieve_survivors_total,
            "single_prp_count": self.single_prp_count,
            "dual_prp_count": self.dual_prp_count,
            "proven_pairs_count": self.proven_pairs_count,
            "proven_pairs": self.proven_pairs
        }
