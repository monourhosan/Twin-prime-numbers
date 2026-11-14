"""
Campaign execution engine for Phase 6 general-integer twin-prime discovery.
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.phase6.models import IntervalMapping, CandidatePair
from src.phase6.primes import generate_primes_up_to
from src.phase6.wheel import CenterWheel
from src.phase6.segmented import SegmentedCenterSieve
from src.phase6.bucket_sieve import BucketCenterSieve
from src.phase6.screening import CandidateScreener
from src.phase6.proof_backend import DeterministicPairProver
from src.phase6.certificate_manifest import build_certificate_payload, save_certificate
from src.phase6.independent_verify import verify_file
from src.phase6.coverage import CoverageManager

class GITCSSCampaign:
    """Orchestrates bounded general-integer twin-prime campaigns."""
    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None, resume: bool = True):
        self.config = config
        self.campaign_id = config.get("campaign_id", "gitcss_campaign")
        self.run_id = run_id or f"run_{self.campaign_id}_{int(time.time())}"
        self.resume = resume
        
        self.run_dir = Path("runs/phase6/campaigns") / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Exact interval mapping
        p_min = int(self.config["p_min"])
        p_max = int(self.config["p_max"])
        self.interval = IntervalMapping.from_p_range(p_min, p_max)
        
        self.sieve_limit = int(self.config.get("sieve_limit", 100000))
        self.segment_size = int(self.config.get("segment_size", 262144))
        wheel_primes = self.config.get("wheel_primes", [5, 7, 11, 13])
        self.wheel = CenterWheel(wheel_primes)
        
        use_bucket = self.config.get("use_bucket_sieve", False)
        if use_bucket:
            self.sieve = BucketCenterSieve(self.sieve_limit, self.segment_size, self.wheel)
        else:
            self.sieve = SegmentedCenterSieve(self.sieve_limit, self.wheel)
            
        self.screener = CandidateScreener(mr_rounds=self.config.get("mr_rounds", 25))
        self.prover = DeterministicPairProver()
        
        self.db_path = self.run_dir / "campaign.db"
        self.coverage = CoverageManager(self.db_path)
        
        # Load historical inventory for novelty checks
        inv_path = Path(self.config.get("historical_inventory", "research/phase5_audit/historical_inventory.json"))
        self.historical_keys = set()
        if inv_path.exists():
            with open(inv_path, "r", encoding="utf-8") as f:
                inv = json.load(f)
                for item in inv:
                    self.historical_keys.add(item.get("canonical_key"))
                    
        self.candidates_jsonl = Path("data/phase6_candidates.jsonl")
        self.candidates_jsonl.parent.mkdir(parents=True, exist_ok=True)
        
        self.telemetry = {
            "campaign_id": self.campaign_id,
            "run_id": self.run_id,
            "m_min": self.interval.m_min,
            "m_max": self.interval.m_max,
            "segments_completed": 0,
            "centers_sieved": 0,
            "sieve_survivors": 0,
            "left_prps": 0,
            "dual_prps": 0,
            "proven_pairs": 0,
            "wall_time_seconds": 0.0
        }

    def _log(self, msg: str):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{ts}] {msg}", flush=True)

    def run_bounded_search(
        self,
        max_segments: Optional[int] = None,
        stop_on_discovery: bool = True
    ) -> List[Dict[str, Any]]:
        """Executes the search across mapped center segments."""
        start_time = time.perf_counter()
        self._log(f"Starting GITCSS Campaign '{self.campaign_id}' (Run: {self.run_id})")
        self._log(f"p-range: [{self.interval.p_min}, {self.interval.p_max}]")
        self._log(f"m-range: [{self.interval.m_min}, {self.interval.m_max}] (total {self.interval.total_m_candidates} centers)")
        self._log(f"Sieve limit: {self.sieve_limit}, Segment size: {self.segment_size}, Wheel: {self.wheel.primes}")

        # Resumption
        m_curr = self.interval.m_min
        if self.resume:
            max_done = self.coverage.get_max_completed_m()
            if max_done >= m_curr:
                m_curr = max_done
                self._log(f"Resuming campaign from completed checkpoint: m = {m_curr}")

        discoveries = []
        segments_done = 0
        seg_idx = 0

        while m_curr <= self.interval.m_max:
            # Check pause requests
            pause_file = self.run_dir / ".pause"
            global_pause = Path("runs/phase6/.pause")
            if pause_file.exists() or global_pause.exists():
                self._log("Pause request signal detected. Saving checkpoint and halting safely.")
                if pause_file.exists():
                    try:
                        pause_file.unlink()
                    except Exception:
                        pass
                break

            # Check time budget
            time_budget = self.config.get("time_budget_seconds")
            if time_budget and (time.perf_counter() - start_time) >= time_budget:
                self._log(f"Time budget limit ({time_budget}s) reached. Halting gracefully.")
                break

            if max_segments is not None and segments_done >= max_segments:
                self._log(f"Reached max segment limit ({max_segments}). Halting.")
                break

            seg_start = m_curr
            seg_end = min(seg_start + self.segment_size, self.interval.m_max + 1)
            actual_size = seg_end - seg_start
            
            t0 = time.perf_counter()
            # Sieve segment
            survivors = self.sieve.sieve_segment(seg_start, actual_size)
            sieve_sec = time.perf_counter() - t0
            
            self.telemetry["centers_sieved"] += actual_size
            self.telemetry["sieve_survivors"] += len(survivors)
            
            dual_prp_in_seg = 0
            proven_in_seg = 0
            
            # Screen survivors
            for m_val in survivors:
                res = self.screener.screen_candidate(m_val)
                
                # Append candidate to ledger
                with open(self.candidates_jsonl, "a", encoding="utf-8") as f:
                    entry = {
                        "run_id": self.run_id,
                        "m": str(m_val),
                        "A": str(res.candidate.A),
                        "B": str(res.candidate.B),
                        "digits": res.candidate.digits,
                        "stage_passed": res.stage_passed,
                        "is_dual_prp": res.is_dual_prp,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    f.write(json.dumps(entry) + "\n")
                    
                if res.is_left_prp:
                    self.telemetry["left_prps"] += 1
                    
                if res.is_dual_prp:
                    self.telemetry["dual_prps"] += 1
                    dual_prp_in_seg += 1
                    self._log(f"*** [DUAL PRP HIT DETECTED!] m={m_val}, digits={res.candidate.digits} ***")
                    
                    # Novelty check
                    canonical_key = f"{res.candidate.A}:{res.candidate.B}"
                    if canonical_key in self.historical_keys:
                        self._log(f"Candidate {canonical_key} already exists in historical inventory! Skipping proof.")
                        continue
                        
                    self._log(f"Executing deterministic primality proof on m={m_val}...")
                    proof = self.prover.prove_pair(m_val)
                    if proof is not None:
                        self._log("DETERMINISTIC PROOF SUCCESS! Both primes certified.")
                        cert_payload = build_certificate_payload(m_val, proof, self.campaign_id)
                        cert_path = save_certificate(cert_payload)
                        self._log(f"Certificate saved to: {cert_path}")
                        
                        # Verify independently
                        ok = verify_file(cert_path)
                        if ok:
                            self._log("INDEPENDENT ATTESTATION VERIFIED!")
                            self.telemetry["proven_pairs"] += 1
                            proven_in_seg += 1
                            discoveries.append({
                                "m": m_val,
                                "A": res.candidate.A,
                                "B": res.candidate.B,
                                "digits": res.candidate.digits,
                                "certificate_path": str(cert_path)
                            })
                            if stop_on_discovery:
                                self._log("Stop on discovery enabled. Concluding campaign.")
                                break
                    else:
                        self._log(f"Proof generation timed out or unfactored for m={m_val}.")

            elapsed_seg = time.perf_counter() - t0
            self.coverage.record_completed_segment(
                segment_id=seg_idx,
                m_start=seg_start,
                m_end=seg_end,
                survivors=len(survivors),
                dual_prps=dual_prp_in_seg,
                proven=proven_in_seg,
                elapsed_sec=elapsed_seg,
                timestamp_utc=datetime.now(timezone.utc).isoformat()
            )

            segments_done += 1
            self.telemetry["segments_completed"] += 1
            seg_idx += 1
            m_curr = seg_end
            
            if discoveries and stop_on_discovery:
                break

        total_wall = time.perf_counter() - start_time
        self.telemetry["wall_time_seconds"] = total_wall
        self._write_final_report(discoveries)
        return discoveries

    def _write_final_report(self, discoveries: List[Dict[str, Any]]):
        """Generates comprehensive final report in run directory."""
        report_file = self.run_dir / "final_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# GITCSS Campaign Final Execution Report\n\n")
            f.write(f"**Campaign ID:** `{self.campaign_id}`  \n")
            f.write(f"**Run ID:** `{self.run_id}`  \n")
            f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}  \n\n")
            f.write(f"## Telemetry Summary\n\n")
            f.write(f"- **Centers Searched:** {self.telemetry['centers_sieved']:,}\n")
            f.write(f"- **Sieve Survivors:** {self.telemetry['sieve_survivors']:,}\n")
            f.write(f"- **Left PRPs:** {self.telemetry['left_prps']}\n")
            f.write(f"- **Dual PRPs:** {self.telemetry['dual_prps']}\n")
            f.write(f"- **Proven Pairs:** {self.telemetry['proven_pairs']}\n")
            f.write(f"- **Wall Time:** {self.telemetry['wall_time_seconds']:.2f} s\n\n")
            f.write(f"## Discovery Status\n\n")
            if discoveries:
                f.write(f"**Status:** `DISCOVERY_CERTIFIED_AND_ATTESTED`\n\n")
                for d in discoveries:
                    f.write(f"- Lower prime A: `{d['A']}`\n")
                    f.write(f"- Upper prime B: `{d['B']}`\n")
                    f.write(f"- Digits: {d['digits']}\n")
                    f.write(f"- Certificate: `{d['certificate_path']}`\n\n")
            else:
                f.write(f"**Status:** `NO_NEW_PAIR_FOUND_IN_TESTED_RANGE`\n\n")
                f.write(f"Completed finite range: m in [{self.interval.m_min}, {self.coverage.get_max_completed_m()}]\n")
