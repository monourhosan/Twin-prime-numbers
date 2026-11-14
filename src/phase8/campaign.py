"""
Durable Campaign Manager and Ledger for Phase 8 ADES-8.
Manages:
- Tile grid iteration and scheduling
- Two-tier execution: 2D sieving -> Staged Screening -> Deterministic Proof
- Atomic checkpointing and persistent JSONL ledgers
- Stop-on-first-hit record certification
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from src.phase8.math import get_primorial_multiplier, compute_candidate_pair
from src.phase8.sieve_2d import ADES8TwoDimSieve
from src.phase8.screening import CandidateScreener
from src.phase8.prover import ADES8Prover, compute_canonical_sha256


class ADES8CampaignManager:
    """
    Orchestrates resilient, resumable 2D twin prime search campaigns.
    """
    def __init__(
        self,
        config: Dict[str, Any],
        campaign_dir: str = "data/phase8",
        proof_dir: str = "proofs/phase8/certificates"
    ):
        self.config = config
        self.campaign_dir = campaign_dir
        self.proof_dir = proof_dir

        os.makedirs(self.campaign_dir, exist_ok=True)
        os.makedirs(self.proof_dir, exist_ok=True)

        self.R = config.get("R_primorial", 13)
        self.M = get_primorial_multiplier(self.R)
        self.sieve_limit = config.get("sieve_limit", 100000)
        self.digit_band = config.get("digit_band", 1515)

        self.n_start = config.get("n_start", 5000)
        self.n_height = config.get("n_height", 16)
        self.t_start = config.get("t_start", 20000)
        self.t_width = config.get("t_width", 50000)
        self.max_tiles = config.get("max_tiles", 100)
        self.timeout_sec = config.get("timeout_sec", 3600.0)

        self.sieve = ADES8TwoDimSieve(R=self.R, sieve_limit=self.sieve_limit)
        self.screener = CandidateScreener(mr_rounds=config.get("mr_rounds", 25))
        self.prover = ADES8Prover()

        self.ledger_tiles_path = os.path.join(self.campaign_dir, "tiles_completed.jsonl")
        self.ledger_prps_path = os.path.join(self.campaign_dir, "prp_candidates.jsonl")
        self.checkpoint_path = os.path.join(self.campaign_dir, "campaign_checkpoint.json")

    def get_completed_tiles(self) -> set:
        """Loads completed tile keys from ledger."""
        completed = set()
        if os.path.exists(self.ledger_tiles_path):
            with open(self.ledger_tiles_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            completed.add(record["tile_id"])
                        except Exception:
                            pass
        return completed

    def run_campaign(self) -> Dict[str, Any]:
        """
        Executes campaign across tiles until a fresh pair is proven,
        max_tiles reached, or timeout expires.
        """
        t_campaign_start = time.perf_counter()
        completed_tiles = self.get_completed_tiles()

        total_sieved_candidates = 0
        total_survivors = 0
        total_fermat_tested = 0
        total_dual_prps = 0
        certified_certificate: Optional[Dict[str, Any]] = None

        tile_idx = 0
        current_t = self.t_start

        while tile_idx < self.max_tiles:
            # Check elapsed time
            elapsed = time.perf_counter() - t_campaign_start
            if elapsed >= self.timeout_sec:
                break

            tile_id = f"tile_n{self.n_start}_{self.n_start + self.n_height - 1}_t{current_t}_{current_t + self.t_width - 1}"

            if tile_id in completed_tiles:
                current_t += self.t_width
                tile_idx += 1
                continue

            # Sieve this 2D tile
            t_tile_start = time.perf_counter()
            survivors, sieve_metrics = self.sieve.sieve_tile_recurrence(
                n_start=self.n_start,
                n_height=self.n_height,
                t_start=current_t,
                t_width=self.t_width,
                digit_band=self.digit_band
            )

            num_tile_survivors = len(survivors)
            total_survivors += num_tile_survivors
            total_sieved_candidates += (self.n_height * self.t_width)

            # Screen survivors
            tile_prps: List[Dict[str, Any]] = []
            for n_val, t_val in survivors:
                total_fermat_tested += 1
                is_prp, status, screen_meta = self.screener.screen_survivor(self.M, t_val, n_val)
                if is_prp:
                    total_dual_prps += 1
                    prp_record = {
                        "utc": datetime.now(timezone.utc).isoformat(),
                        "tile_id": tile_id,
                        "n": n_val,
                        "t": t_val,
                        "k": screen_meta["k"],
                        "digits": screen_meta["digits"],
                        "status": "DUAL_PRP_CONFIRMED"
                    }
                    tile_prps.append(prp_record)

                    # Persist PRP immediately
                    with open(self.ledger_prps_path, "a", encoding="utf-8") as f_prp:
                        f_prp.write(json.dumps(prp_record) + "\n")

                    # Attempt deterministic proof!
                    proven_cert = self.prover.prove_pair(
                        R_primorial=self.R,
                        M=self.M,
                        t=t_val,
                        n=n_val,
                        campaign_id=self.config.get("campaign_id", "ades8_record_campaign"),
                        search_provenance={
                            "utc_certified": datetime.now(timezone.utc).isoformat(),
                            "tile_id": tile_id,
                            "sieve_depth": self.sieve_limit,
                            "screener": "CandidateScreener_mr25"
                        }
                    )

                    if proven_cert is not None:
                        # Success! Save certificate
                        cert_filename = f"cert_ades8_{proven_cert['pair']['digits']}d_R{self.R}_n{n_val}_t{t_val}.json"
                        cert_path = os.path.join(self.proof_dir, cert_filename)
                        with open(cert_path, "w", encoding="utf-8") as f_cert:
                            json.dump(proven_cert, f_cert, indent=2)

                        certified_certificate = proven_cert
                        break

            # Ledger completed tile
            tile_elapsed = time.perf_counter() - t_tile_start
            tile_record = {
                "utc": datetime.now(timezone.utc).isoformat(),
                "tile_id": tile_id,
                "n_start": self.n_start,
                "n_height": self.n_height,
                "t_start": current_t,
                "t_width": self.t_width,
                "survivors": num_tile_survivors,
                "prps_found": len(tile_prps),
                "elapsed_sec": tile_elapsed
            }
            with open(self.ledger_tiles_path, "a", encoding="utf-8") as f_tile:
                f_tile.write(json.dumps(tile_record) + "\n")

            # Checkpoint
            checkpoint_data = {
                "utc": datetime.now(timezone.utc).isoformat(),
                "last_tile_id": tile_id,
                "next_t": current_t + self.t_width,
                "tiles_completed": tile_idx + 1,
                "total_sieved_candidates": total_sieved_candidates,
                "total_survivors": total_survivors,
                "total_fermat_tested": total_fermat_tested,
                "total_dual_prps": total_dual_prps,
                "has_certified_hit": certified_certificate is not None
            }
            with open(self.checkpoint_path, "w", encoding="utf-8") as f_chk:
                json.dump(checkpoint_data, f_chk, indent=2)

            if certified_certificate is not None:
                # Stop on first certified hit
                break

            current_t += self.t_width
            tile_idx += 1

        total_campaign_elapsed = time.perf_counter() - t_campaign_start

        return {
            "status": "SUCCESS_RECORD_PROVEN" if certified_certificate else "COMPLETED_NO_RECORD",
            "tiles_processed": tile_idx + (1 if certified_certificate else 0),
            "total_candidates_sieved": total_sieved_candidates,
            "total_survivors": total_survivors,
            "total_fermat_tested": total_fermat_tested,
            "total_dual_prps": total_dual_prps,
            "certified_pair": certified_certificate,
            "campaign_elapsed_sec": total_campaign_elapsed
        }
