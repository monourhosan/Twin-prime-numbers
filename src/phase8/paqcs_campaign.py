"""
PAQCS Campaign Execution Engine (Phase 8).
Orchestrates segmented sieving, parallel multiprocessing PRP screening,
dual-BLS proving, checkpointing, and independent attestation generation.
"""

import concurrent.futures
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .paqcs_anchor import PrimorialAnchor
from .paqcs_math import construct_pair
from .paqcs_sieve import prepare_sieve_plan, SegmentedPAQCSSieve
from .paqcs_screening import screen_batch_worker
from .paqcs_prover import PAQCSProver
from scripts.phase8_paqcs_independent_verify import verify_paqcs_certificate


class PAQCSCampaign:
    """
    Manages end-to-end execution of a PAQCS twin prime search campaign.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        run_dir: Optional[Path] = None
    ):
        self.config = config
        self.campaign_id = config.get("campaign_id", "paqcs_run")
        self.target_digits = config.get("target_digits", 1511)
        self.y_anchor = config.get("y_anchor", 1780)
        self.h = config.get("h", 3)
        self.Q_bound = config.get("Q_bound", 200000)
        self.block_size = config.get("block_size", 50000)
        self.max_candidates = config.get("max_candidates", 200000)
        self.workers = config.get("workers", 4)
        self.stop_on_first_discovery = config.get("stop_on_first_discovery", True)

        if run_dir:
            self.run_dir = run_dir
        else:
            ts = int(time.time())
            self.run_dir = Path(f"research/phase8_runs/{self.campaign_id}_{ts}")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_path = self.run_dir / "checkpoint.json"
        self.ledger_path = self.run_dir / "candidate_ledger.jsonl"
        self.log_path = self.run_dir / "campaign.log"

        # Initialize Anchor
        self.anchor = PrimorialAnchor(y=self.y_anchor)
        self.t_min = config.get("t_start")
        if self.t_min is None:
            self.t_min = self.anchor.compute_min_t(target_digits=self.target_digits, h=self.h)

        self.current_t = self.t_min
        self.candidates_searched = 0
        self.sieve_survivors_count = 0
        self.single_prp_count = 0
        self.dual_prp_count = 0
        self.discoveries: List[Dict[str, Any]] = []

        # Load checkpoint if exists
        if self.checkpoint_path.exists():
            self._load_checkpoint()

    def _log(self, msg: str):
        ts = datetime.now(timezone.utc).isoformat()
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _save_checkpoint(self):
        ckpt = {
            "campaign_id": self.campaign_id,
            "target_digits": self.target_digits,
            "y_anchor": self.y_anchor,
            "h": self.h,
            "Q_bound": self.Q_bound,
            "current_t": self.current_t,
            "t_min": self.t_min,
            "candidates_searched": self.candidates_searched,
            "sieve_survivors_count": self.sieve_survivors_count,
            "single_prp_count": self.single_prp_count,
            "dual_prp_count": self.dual_prp_count,
            "discoveries_count": len(self.discoveries),
            "utc_checkpoint": datetime.now(timezone.utc).isoformat()
        }
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(ckpt, f, indent=2)

    def _load_checkpoint(self):
        with open(self.checkpoint_path, "r", encoding="utf-8") as f:
            ckpt = json.load(f)
        self.current_t = ckpt.get("current_t", self.t_min)
        self.candidates_searched = ckpt.get("candidates_searched", 0)
        self.sieve_survivors_count = ckpt.get("sieve_survivors_count", 0)
        self.single_prp_count = ckpt.get("single_prp_count", 0)
        self.dual_prp_count = ckpt.get("dual_prp_count", 0)
        self._log(f"Resumed from checkpoint at current_t={self.current_t}, searched={self.candidates_searched}")

    def execute(self) -> List[Dict[str, Any]]:
        self._log(f"Starting PAQCS Campaign: {self.campaign_id}")
        self._log(f"Target digits: {self.target_digits}, Anchor y: {self.y_anchor} (S_y digits: {self.anchor.digits})")
        self._log(f"t_min: {self.t_min}, h: {self.h}, Q: {self.Q_bound}, Workers: {self.workers}")

        # Prepare sieve plan
        t0_plan = time.perf_counter()
        self._log("Preparing sieve prime plan...")
        plan = prepare_sieve_plan(self.anchor.S_y, self.anchor.y, self.Q_bound, h=self.h)
        self._log(f"Sieve plan ready: {len(plan)} primes in ({self.anchor.y}, {self.Q_bound}] ({time.perf_counter() - t0_plan:.2f}s)")

        sieve_engine = SegmentedPAQCSSieve(plan)
        prover = PAQCSProver(self.anchor)

        cert_dir = Path("proofs/phase8/certificates")
        attest_dir = Path("proofs/phase8/attestations")
        cert_dir.mkdir(parents=True, exist_ok=True)
        attest_dir.mkdir(parents=True, exist_ok=True)

        total_target_candidates = self.max_candidates

        while self.candidates_searched < total_target_candidates:
            block_cand_count = min(self.block_size, total_target_candidates - self.candidates_searched)
            t_block_start = self.current_t
            t_block_end = t_block_start + 2 * (block_cand_count - 1)

            t0_block = time.perf_counter()
            # 1. Segmented Sieve
            survivors = sieve_engine.sieve_segment(t_block_start, t_block_end)
            t_sieve = time.perf_counter() - t0_block
            self.sieve_survivors_count += len(survivors)
            surv_rate = (len(survivors) / block_cand_count) * 100

            self._log(
                f"Block [{t_block_start} .. {t_block_end}]: {block_cand_count} candidates, "
                f"{len(survivors)} survivors ({surv_rate:.2f}%) in {t_sieve*1000:.1f}ms"
            )

            # 2. Parallel Screening
            t0_screen = time.perf_counter()
            chunk_size = max(1, len(survivors) // (self.workers * 4) + 1)
            chunks = [survivors[i : i + chunk_size] for i in range(0, len(survivors), chunk_size)]
            worker_args = [(self.anchor.S_y, chunk, self.h) for chunk in chunks]

            block_duals = []
            block_singles = []

            if self.workers > 1 and len(chunks) > 1:
                with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers) as executor:
                    for chunk_res in executor.map(screen_batch_worker, worker_args):
                        for t_cand, is_single, is_dual in chunk_res:
                            if is_single:
                                block_singles.append(t_cand)
                                self.single_prp_count += 1
                            if is_dual:
                                block_duals.append(t_cand)
                                self.dual_prp_count += 1
            else:
                for arg in worker_args:
                    chunk_res = screen_batch_worker(arg)
                    for t_cand, is_single, is_dual in chunk_res:
                        if is_single:
                            block_singles.append(t_cand)
                            self.single_prp_count += 1
                        if is_dual:
                            block_duals.append(t_cand)
                            self.dual_prp_count += 1

            t_screen = time.perf_counter() - t0_screen
            screen_rate = len(survivors) / max(0.001, t_screen)
            self._log(
                f"  Screened {len(survivors)} survivors in {t_screen:.2f}s ({screen_rate:.1f} cand/s). "
                f"Singles: {len(block_singles)}, Duals: {len(block_duals)}"
            )

            # Record to candidate ledger
            with open(self.ledger_path, "a", encoding="utf-8") as f_ledger:
                for s_t in block_singles:
                    rec = {
                        "t": s_t,
                        "type": "DUAL_PRP" if s_t in block_duals else "SINGLE_PRP_LOWER",
                        "utc": datetime.now(timezone.utc).isoformat()
                    }
                    f_ledger.write(json.dumps(rec) + "\n")

            # 3. Prove any dual PRPs found
            for dual_t in block_duals:
                self._log(f"*** PROVING DUAL PRP at t={dual_t} ***")
                ok, cert, err = prover.prove_twin_pair(
                    dual_t,
                    h=self.h,
                    campaign_id=self.campaign_id
                )
                if ok and cert:
                    digits = cert["pair"]["digits"]
                    cert_file = cert_dir / f"cert_paqcs_{digits}d_t{dual_t}.json"
                    with open(cert_file, "w", encoding="utf-8") as f_cert:
                        json.dump(cert, f_cert, indent=2)
                    self._log(f"Saved certificate: {cert_file}")

                    # Run strict independent verifier immediately
                    v_ok, v_logs, att = verify_paqcs_certificate(cert_file, attest_dir)
                    for vl in v_logs:
                        self._log(f"  [Verifier] {vl}")
                    if v_ok:
                        self._log(f"*** VERIFICATION SUCCESS: {cert_file.name} UNCONDITIONALLY CERTIFIED! ***")
                        self.discoveries.append({
                            "t": dual_t,
                            "digits": digits,
                            "certificate": str(cert_file),
                            "sha256": cert["sha256"]
                        })
                    else:
                        self._log(f"*** VERIFICATION FAILED: {cert_file.name} rejected! ***")
                else:
                    self._log(f"Proof failed for t={dual_t}: {err}")

            self.candidates_searched += block_cand_count
            self.current_t = t_block_end + 2
            self._save_checkpoint()

            if block_duals and self.stop_on_first_discovery:
                self._log("Stopping on first confirmed discovery as requested.")
                break

        self._log(
            f"Campaign finished. Total searched: {self.candidates_searched}, "
            f"Survivors: {self.sieve_survivors_count}, Single PRPs: {self.single_prp_count}, "
            f"Dual PRPs: {self.dual_prp_count}, Discoveries: {len(self.discoveries)}"
        )
        return self.discoveries
