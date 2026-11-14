"""
Phase 6: Search Pipeline and Live Campaign Runner (Method Q and Method R).
Executes high-throughput segmented sieving, multi-tier screening, atomic checkpointing,
and immediate unconditional certification upon PRP discovery.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .families import MethodQFamily, MethodRFamily
from .sieve import QSieveSegment, QSieveReference, QSieveEvent, RSieveSegment
from .screening import CandidateScreener
from .proof import MethodQProofEngine, compute_canonical_sha256
from .ledger import SearchLedger


def load_exclusion_index(repo_root: Path) -> set:
    """Loads all known canonical integer centers from data/phase6/exclusion_index.json."""
    idx_path = repo_root / "data" / "phase6" / "exclusion_index.json"
    if not idx_path.exists():
        return set()
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(entry["center_decimal"]) for entry in data}
    except Exception:
        return set()


class DiscoveryRunner:
    """
    Orchestrates the live search campaign.
    """

    def __init__(self, config: Dict[str, Any], repo_root: Optional[Path] = None):
        self.config = config
        self.repo_root = repo_root or Path.cwd()
        self.campaign_id = config.get("campaign_id", "primary")
        self.method = config.get("method", "method_q")
        self.stop_on_first = config.get("stop_on_first_certified", True)
        self.time_budget = config.get("wall_clock_seconds", 600.0)
        self.dry_run = config.get("dry_run", False)

        # Run directory and ledger
        self.run_dir = self.repo_root / "runs" / "phase6" / self.campaign_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = SearchLedger(self.run_dir / "ledger.db")

        # Load exclusion index
        self.exclusion_index = load_exclusion_index(self.repo_root)

        # Config hash
        config_canonical = json.dumps(config, sort_keys=True)
        self.config_hash = hashlib.sha256(config_canonical.encode("utf-8")).hexdigest()

        # Initialize family
        self._init_family()

    def _init_family(self) -> None:
        if self.method == "method_q":
            seed = self.config.get("seed", 2026111401)
            target_digits = self.config.get("target_pair_digits", 100)
            h = self.config.get("h", 3)
            # Check if explicit S factors provided
            if "S_factors" in self.config:
                factors = {int(k): int(v) for k, v in self.config["S_factors"].items()}
                self.family = MethodQFamily(S_factors=factors, h=h, seed=seed)
            else:
                t_bits = self.config.get("t_bits", 20)
                self.family = MethodQFamily.generate_fresh(target_pair_digits=target_digits, seed=seed, h=h, t_bits=t_bits)
        else:
            seed = self.config.get("seed", 2026111402)
            target_digits = self.config.get("target_pair_digits", 100)
            if "C0" in self.config:
                self.family = MethodRFamily(C0=int(self.config["C0"]), seed=seed)
            else:
                self.family = MethodRFamily.generate_fresh(target_digits=target_digits, seed=seed)

    def is_paused(self) -> bool:
        pause_file = self.run_dir / ".pause"
        if pause_file.exists():
            return True
        st = self.ledger.get_campaign_status(self.campaign_id)
        return st.get("status") == "PAUSED"

    def run(self, resume: bool = False) -> Dict[str, Any]:
        t_start = time.time()
        print(f"=== Starting Phase 6 Discovery Run [{self.campaign_id}] ===")
        print(f"Method: {self.method}")
        print(f"Target digits: {self.config.get('target_pair_digits')}")

        if self.method == "method_q":
            print(f"Anchor S digits: {len(str(self.family.S))}")
            print(f"S factors: {list(self.family.S_factors.keys())}")
            print(f"h: {self.family.h}")

        j_min = self.config.get("j_min", 0)
        j_max = self.config.get("j_max", 100000)
        block_size = self.config.get("block_size", 25000)
        sieve_limit = self.config.get("sieve_limit", 100000)
        screening_order = self.config.get("screening_order", "A_first")

        # Partition into work units
        work_units = []
        cur_j = j_min
        while cur_j < j_max:
            end_j = min(cur_j + block_size, j_max)
            work_units.append((cur_j, end_j))
            cur_j = end_j

        self.ledger.init_campaign(self.campaign_id, self.config, work_units, self.config_hash)

        if self.dry_run:
            print("DRY-RUN mode enabled. Setup validated. No candidates will be tested.")
            return {
                "status": "DRY_RUN_COMPLETED",
                "campaign_id": self.campaign_id,
                "work_units_count": len(work_units),
                "config_hash": self.config_hash,
                "tested_candidates": 0,
                "sieve_survivors": 0,
                "prp_hits": 0,
                "elapsed_seconds": time.time() - t_start
            }

        # Initialize engines
        if self.method == "method_q":
            backend = self.config.get("sieve_backend", "q_segment")
            if backend == "q_event":
                sieve_engine = QSieveEvent(self.family, sieve_limit=sieve_limit, segment_size=block_size)
            elif backend == "q_reference":
                sieve_engine = QSieveReference(self.family, sieve_limit=sieve_limit)
            else:
                sieve_engine = QSieveSegment(self.family, sieve_limit=sieve_limit)
        else:
            sieve_engine = RSieveSegment(self.family, sieve_limit=sieve_limit)

        screener = CandidateScreener(mr_rounds=self.config.get("mr_rounds", 25))
        prover = MethodQProofEngine()

        total_tested = 0
        total_survivors = 0
        total_prp = 0
        discovered_cert: Optional[Dict[str, Any]] = None
        discovered_path: Optional[Path] = None

        while True:
            # Check elapsed time
            elapsed = time.time() - t_start
            if elapsed >= self.time_budget:
                print(f"Wall-clock budget reached ({elapsed:.1f}s >= {self.time_budget}s). Checkpointing...")
                break

            # Check pause
            if self.is_paused():
                print("Campaign is PAUSED. Halting work.")
                break

            # Lease next work unit
            lease = self.ledger.lease_next_unit(self.campaign_id)
            if not lease:
                print("All work units completed.")
                break
            unit_id, u_start, u_end = lease
            u_len = u_end - u_start

            # Sieve segment
            if hasattr(sieve_engine, "sieve_segment"):
                survivors = sieve_engine.sieve_segment(u_start, u_len)
            else:
                survivors = sieve_engine.sieve_window(u_start, u_end)

            u_tested = u_len
            u_survivors = len(survivors)
            u_prps = 0

            # Screen survivors
            for j in survivors:
                if self.method == "method_q":
                    t_val = 2 * j + 1
                    A, B, C = self.family.evaluate(t_val)
                else:
                    t_val = j
                    A, B, C = self.family.evaluate(j)

                # Novelty check against repository exclusion index
                if C in self.exclusion_index:
                    print(f"Candidate center {C} matches repository historical inventory! Skipping duplicate.")
                    self.ledger.record_candidate(self.campaign_id, t_val, str(A), str(B), str(C), len(str(A)), "EXCLUDED_DUPLICATE")
                    continue

                # Multi-tier screening
                dual_prp, is_A, is_B, reason = screener.screen_pair(A, B, order=screening_order)
                if dual_prp:
                    u_prps += 1
                    total_prp += 1
                    print(f"\n[DUAL PRP HIT!] t={t_val}, digits={len(str(A))}")
                    print(f"  A: {str(A)[:30]}...{str(A)[-10:]}")
                    print(f"  B: {str(B)[:30]}...{str(B)[-10:]}")
                    self.ledger.record_candidate(self.campaign_id, t_val, str(A), str(B), str(C), len(str(A)), "PRP_BOTH")

                    # Attempt unconditional primality proof
                    if self.method == "method_q":
                        print("  Executing unconditional dual BLS primality proof...")
                        t_proof_0 = time.time()
                        ok_proof, cert, err = prover.prove_twin_pair(
                            self.family,
                            t_val,
                            campaign_id=self.campaign_id,
                            discovery_seed=self.config.get("seed")
                        )
                        proof_elapsed = time.time() - t_proof_0
                        if ok_proof and cert:
                            print(f"  PROOF SUCCESSFUL in {proof_elapsed:.3f}s!")
                            cert_dir = self.repo_root / "proofs" / "phase6" / "certificates"
                            cert_dir.mkdir(parents=True, exist_ok=True)
                            cert_id = f"cert_qcp6_{len(str(A))}d_t{t_val}"
                            cert_file = cert_dir / f"{cert_id}.json"
                            with open(cert_file, "w", encoding="utf-8") as f:
                                json.dump(cert, f, indent=2)

                            self.ledger.record_candidate(self.campaign_id, t_val, str(A), str(B), str(C), len(str(A)), "PROVEN")
                            self.ledger.mark_pair_found(self.campaign_id)
                            discovered_cert = cert
                            discovered_path = cert_file
                            print(f"  Proof artifact saved: {cert_file.as_posix()}")

                            if self.stop_on_first:
                                self.ledger.complete_unit(unit_id, u_tested, u_survivors, u_prps)
                                total_tested += u_tested
                                total_survivors += u_survivors
                                return {
                                    "status": "CERTIFIED_FRESH_PAIR",
                                    "campaign_id": self.campaign_id,
                                    "certificate_path": str(cert_file),
                                    "certificate": cert,
                                    "tested_candidates": total_tested,
                                    "sieve_survivors": total_survivors,
                                    "prp_hits": total_prp,
                                    "elapsed_seconds": time.time() - t_start
                                }
                        else:
                            print(f"  Proof FAILED: {err}")
                    else:
                        print("  Method R candidate discovered (PRP only: ECPP proof blocked in Windows environment).")

            self.ledger.complete_unit(unit_id, u_tested, u_survivors, u_prps)
            total_tested += u_tested
            total_survivors += u_survivors

        elapsed_total = time.time() - t_start
        status_str = "CERTIFIED_FRESH_PAIR" if discovered_cert else ("PRP_ONLY_PENDING_PROOF" if total_prp > 0 else "NO_HIT_WITHIN_BUDGET")

        return {
            "status": status_str,
            "campaign_id": self.campaign_id,
            "certificate_path": str(discovered_path) if discovered_path else None,
            "certificate": discovered_cert,
            "tested_candidates": total_tested,
            "sieve_survivors": total_survivors,
            "prp_hits": total_prp,
            "elapsed_seconds": elapsed_total
        }
