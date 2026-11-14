"""
Phase 7 HDC-7 Campaign Manager and Resumable Search Engine.
Manages candidate generation, compact t-space sieving, staged screening,
deterministic proofs, crash recovery, and durable state ledgering.
"""

import os
import sys
import time
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

from src.phase7.math import (
    get_primorial_multiplier,
    exact_digit_t_bounds,
    compute_candidate_pair
)
from src.phase7.sieve import CompactTSieve
from src.phase7.screening import HDCScreener
from src.phase7.prover import HDCProver
from scripts.phase7_independent_verify import verify_certificate_v7


class HDCCampaign:
    """
    Executes and coordinates an HDC-7 discovery campaign.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.campaign_id = config.get("campaign_id", "hdc7_discovery_1510d")
        self.target_digits = config.get("min_digits", 1510)
        self.B_cut = config.get("B_primorial", 13)
        self.MB = get_primorial_multiplier(self.B_cut)
        self.n = config["exponent"]
        self.sieve_depth = config.get("sieve_depth", 50000)
        self.batch_size = config.get("batch_size", 5000)
        self.order = config.get("screening_order", "A_first")
        self.checkpoint_sec = config.get("checkpoint_seconds", 15.0)
        self.stop_after_verified = config.get("stop_after_verified_pairs", 1)

        # Paths
        self.proofs_dir = Path(config.get("proofs_dir", "proofs/phase7/certificates"))
        self.attest_dir = Path(config.get("attestations_dir", "proofs/phase7/attestations"))
        self.runs_dir = Path(config.get("checkpoint_dir", "data/phase7"))
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
        self.attest_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_file = self.runs_dir / f"{self.campaign_id}_checkpoint.json"

        # Bounds
        k_min, k_max, t_min, t_max = exact_digit_t_bounds(self.target_digits, self.MB, self.n)
        self.k_min = k_min
        self.k_max = k_max
        self.t_min = config.get("t_start", t_min)
        self.t_max = min(config.get("t_end", t_max), t_max)

        # Components
        self.sieve = CompactTSieve(self.MB, self.n, sieve_depth=self.sieve_depth)
        self.screener = HDCScreener(order=self.order)
        self.prover = HDCProver()

        # Telemetry
        self.cursor = self.t_min
        self.raw_centers_checked = 0
        self.sieve_survivors = 0
        self.left_prps = 0
        self.right_prps = 0
        self.dual_prps = 0
        self.certified_pairs = 0
        self.last_checkpoint_time = time.perf_counter()
        self.start_wall_time = time.perf_counter()
        self.history: List[Dict[str, Any]] = []

        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Loads state from durable checkpoint if present."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("campaign_id") == self.campaign_id:
                    self.cursor = data.get("cursor_t", self.t_min)
                    self.raw_centers_checked = data.get("raw_centers_checked", 0)
                    self.sieve_survivors = data.get("sieve_survivors", 0)
                    self.left_prps = data.get("left_prps", 0)
                    self.right_prps = data.get("right_prps", 0)
                    self.dual_prps = data.get("dual_prps", 0)
                    self.certified_pairs = data.get("certified_pairs", 0)
            except Exception:
                pass

    def save_checkpoint(self, status: str = "IN_PROGRESS") -> None:
        """Writes atomic checkpoint to disk."""
        now_utc = datetime.now(timezone.utc).isoformat()
        elapsed = time.perf_counter() - self.start_wall_time
        state = {
            "campaign_id": self.campaign_id,
            "status": status,
            "utc_checkpoint": now_utc,
            "cursor_t": self.cursor,
            "t_min": self.t_min,
            "t_max": self.t_max,
            "exponent_n": self.n,
            "B_primorial": self.B_cut,
            "M_B": str(self.MB),
            "target_digits": self.target_digits,
            "raw_centers_checked": self.raw_centers_checked,
            "sieve_survivors": self.sieve_survivors,
            "left_prps": self.left_prps,
            "right_prps": self.right_prps,
            "dual_prps": self.dual_prps,
            "certified_pairs": self.certified_pairs,
            "elapsed_seconds": elapsed,
            "sieve_depth": self.sieve_depth,
            "screening_order": self.order
        }
        tmp_file = self.checkpoint_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp_file.replace(self.checkpoint_file)
        self.last_checkpoint_time = time.perf_counter()

    def run(self, max_wall_seconds: Optional[float] = None, max_centers: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes campaign search loop.
        """
        t0 = time.perf_counter()
        target_centers = max_centers or (self.t_max - self.cursor + 1)

        while self.cursor <= self.t_max:
            if max_wall_seconds and (time.perf_counter() - t0) >= max_wall_seconds:
                self.save_checkpoint("PAUSED_WALL_LIMIT")
                break
            if self.raw_centers_checked >= target_centers:
                self.save_checkpoint("PAUSED_CENTER_LIMIT")
                break
            if self.certified_pairs >= self.stop_after_verified:
                self.save_checkpoint("COMPLETED_TARGET_DISCOVERED")
                break

            # 1. Determine batch segment [batch_start, batch_end)
            batch_start = self.cursor
            batch_end = min(self.cursor + self.batch_size, self.t_max + 1)
            span = batch_end - batch_start
            if span <= 0:
                break

            # 2. Sieve segment in compact t-space
            survivors, tele = self.sieve.sieve_segment(batch_start, batch_end)
            self.sieve_survivors += len(survivors)

            # 3. Screen survivors
            for t_idx in survivors:
                is_a, is_b, is_dual, scr_tele = self.screener.screen_pair(self.MB, t_idx, self.n)
                if is_a:
                    self.left_prps += 1
                if is_b:
                    self.right_prps += 1

                if is_dual:
                    self.dual_prps += 1
                    # Candidate pair is dual PRP! Proceed immediately to deterministic proof!
                    cert = self.prover.prove_pair(
                        self.B_cut, self.MB, t_idx, self.n,
                        search_provenance={
                            "campaign_id": self.campaign_id,
                            "utc_found": datetime.now(timezone.utc).isoformat(),
                            "host_environment": "Phase 7 HDC Engine"
                        }
                    )
                    if cert is not None:
                        # Save certificate
                        cert_name = f"cert_hdc7_{self.target_digits}d_B{self.B_cut}_n{self.n}_t{t_idx}.json"
                        cert_path = self.proofs_dir / cert_name
                        with open(cert_path, "w", encoding="utf-8") as f:
                            json.dump(cert, f, indent=2)

                        # Run strict standalone independent verifier
                        ok, logs, att = verify_certificate_v7(cert_path, self.attest_dir)
                        if ok:
                            self.certified_pairs += 1
                            self.cursor = t_idx + 1
                            self.raw_centers_checked += (t_idx - batch_start + 1)
                            self.save_checkpoint("COMPLETED_TARGET_DISCOVERED")
                            return {
                                "status": "DISCOVERY_SUCCESS",
                                "certified_pairs": self.certified_pairs,
                                "certificate_path": str(cert_path),
                                "certificate": cert,
                                "attestation": att,
                                "raw_centers_checked": self.raw_centers_checked,
                                "dual_prps": self.dual_prps,
                                "elapsed_seconds": time.perf_counter() - t0
                            }

                # Periodic checkpoint
                if (time.perf_counter() - self.last_checkpoint_time) >= self.checkpoint_sec:
                    self.save_checkpoint("IN_PROGRESS")

            self.cursor = batch_end
            self.raw_centers_checked += span

            if (time.perf_counter() - self.last_checkpoint_time) >= self.checkpoint_sec:
                self.save_checkpoint("IN_PROGRESS")

        final_status = "COMPLETED" if self.cursor > self.t_max else "PAUSED"
        self.save_checkpoint(final_status)
        return {
            "status": final_status,
            "certified_pairs": self.certified_pairs,
            "raw_centers_checked": self.raw_centers_checked,
            "sieve_survivors": self.sieve_survivors,
            "left_prps": self.left_prps,
            "right_prps": self.right_prps,
            "dual_prps": self.dual_prps,
            "elapsed_seconds": time.perf_counter() - t0
        }
