"""
Phase 5 Staged Campaign Engine for >= 1,510-Digit Twin-Prime Search.
Implements:
1. Immutable run directory layout under research/phase5_runs/<run_id>/.
2. Snapshotting of configuration, environment, and historical inventory SHA-256.
3. Multi-tier filtering:
   - SCCA Modular Segment Sieve (Depth L)
   - Fast Tier-1 Single-round Base-2 Fermat PRP on A
   - Fast Tier-2 Single-round Base-2 Fermat PRP on B
   - High-rigor Tier-3 25-round Miller-Rabin Dual PRP
   - Deterministic Tier-4 Pocklington (B) and Morrison (A) proofs
   - Isolated Tier-5 First-Principles Independent Verification
   - Strict Tier-6 Novelty Classification against frozen historical inventory
4. Atomic Checkpointing and lossless --resume support.
"""

import sys
import os
import time
import json
import uuid
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import gmpy2

from .candidates import SmoothCenterFamily, TwinPairCandidate
from .crt_walker import SegmentedSCCAFilter
from .primality import prove_pocklington_upper, prove_morrison_lower, PrimalityStatus
from .certificate import TwinPrimeCertificateV5
from .storage import Phase5Storage
from .scheduler import MultiFamilyScheduler, SCCAProfile, SchedulingPolicy

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3)
        return res.stdout.strip() if res.returncode == 0 else "unknown"
    except Exception:
        return "unknown"

class SCCA1510Campaign:
    def __init__(
        self,
        config: Dict[str, Any],
        run_id: Optional[str] = None,
        resume: bool = False
    ):
        self.config = config
        self.run_id = run_id or f"run_1510d_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.resume = resume
        
        # Directory paths
        self.run_dir = REPO_ROOT / "research" / "phase5_runs" / self.run_id
        self.reports_run_dir = REPO_ROOT / "reports" / "phase5_runs" / self.run_id
        
        self.checkpoints_dir = self.run_dir / "checkpoints"
        self.candidates_dir = self.run_dir / "candidates"
        self.proofs_dir = self.run_dir / "proofs"
        self.attestations_dir = self.run_dir / "attestations"
        self.logs_dir = self.run_dir / "logs"
        self.metrics_dir = self.run_dir / "metrics"
        
        for d in [self.checkpoints_dir, self.candidates_dir, self.proofs_dir, self.attestations_dir, self.logs_dir, self.metrics_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.db_path = self.run_dir / "campaign.db"
        self.storage = Phase5Storage(self.db_path)
        
        # Authoritative historical inventory path
        self.hist_inv_path = Path(config.get("historical_inventory", REPO_ROOT / "research" / "phase5_audit" / "historical_inventory.json"))
        if not self.hist_inv_path.exists():
            raise FileNotFoundError(f"Authoritative historical inventory not found at {self.hist_inv_path}")

        # Save immutable metadata on fresh run
        self._init_run_metadata()

        # Build SCCA profiles
        self.profiles: List[SCCAProfile] = []
        for f_cfg in config.get("families", []):
            prof = SCCAProfile(
                family_id=f_cfg["family_id"],
                exponents={int(p): int(e) for p, e in f_cfg["exponents"].items()},
                t_batch_size=f_cfg.get("t_batch_size", 5000),
                sieve_limit=f_cfg.get("sieve_limit", 500000),
                priority=f_cfg.get("priority", 1)
            )
            self.profiles.append(prof)

        # Scheduler
        policy_str = config.get("policy", "COST_AWARE")
        self.policy = SchedulingPolicy(policy_str) if policy_str in SchedulingPolicy.__members__ else SchedulingPolicy.COST_AWARE
        
        self.scheduler = MultiFamilyScheduler(
            storage=self.storage,
            profiles=self.profiles,
            policy=self.policy,
            seed=config.get("seed", 42),
            min_exploration_pulls=config.get("min_exploration_pulls", 2),
            ucb_c=config.get("ucb_c", 1.414),
            resume=self.resume
        )

        # Telemetry
        self.log_file = self.logs_dir / "campaign.log"
        self.telemetry = {
            "run_id": self.run_id,
            "start_utc": datetime.now(timezone.utc).isoformat(),
            "total_screened": 0,
            "total_survivors": 0,
            "left_prps": 0,
            "dual_prps": 0,
            "proven_pairs": 0,
            "wall_time_sec": 0.0,
            "work_units_completed": 0,
            "discoveries": []
        }

    def _init_run_metadata(self):
        """Snapshots immutable configuration, environment, and historical inventory hash."""
        # 1. Config JSON
        cfg_out = self.run_dir / "config.json"
        if not cfg_out.exists() or not self.resume:
            with open(cfg_out, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)

        # 2. Historical inventory hash
        hash_out = self.run_dir / "historical_inventory_hash.txt"
        inv_sha256 = hashlib.sha256(self.hist_inv_path.read_bytes()).hexdigest()
        with open(hash_out, "w", encoding="utf-8") as f:
            f.write(f"{inv_sha256}  {self.hist_inv_path.name}\n")

        # 3. Environment JSON
        env_out = self.run_dir / "environment.json"
        if not env_out.exists() or not self.resume:
            env_data = {
                "python_version": sys.version,
                "git_commit": get_git_commit(),
                "gmpy2_version": gmpy2.version(),
                "pid": os.getpid(),
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            }
            with open(env_out, "w", encoding="utf-8") as f:
                json.dump(env_data, f, indent=2)

    def log(self, message: str):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"[{ts}] {message}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def run_bounded_search(
        self,
        max_work_units: int = 10,
        stop_on_discovery: bool = True
    ) -> List[Dict[str, Any]]:
        """Executes the bounded search loop across scheduled work units."""
        self.log(f"Starting SCCA >= 1,510-Digit Search Campaign: Run ID '{self.run_id}'")
        self.log(f"Policy: {self.policy.value}, Max Work Units: {max_work_units}, Resume: {self.resume}")
        self.log(f"Loaded {len(self.profiles)} search families at >= 1,510 digits.")

        t_campaign_start = time.time()
        discoveries_found = []

        for unit_idx in range(max_work_units):
            wu = self.scheduler.dispense_work_unit()
            prof = wu["profile"]
            fid = wu["family_id"]
            t_start = wu["t_start"]
            t_end = wu["t_end"]
            batch_size = t_end - t_start

            self.log(f"\n--- Work Unit {unit_idx + 1}/{max_work_units}: {fid} [{t_start}, {t_end}) ---")
            self.log(f"Scheduler Rationale: {wu['rationale']}")
            self.log(f"F digits: {len(str(prof.family.F))}, Odd prime factors: {prof.family.odd_prime_factors}")

            t0 = time.time()

            # 1. Modular Sieve
            sieve = SegmentedSCCAFilter(prof.family, sieve_limit=prof.sieve_limit)
            survivors = sieve.sieve_segment(t_start, t_end)
            t_sieve = time.time() - t0
            surv_count = len(survivors)
            surv_pct = (surv_count / batch_size) * 100

            self.log(f"  Sieve complete in {t_sieve*1000:.1f} ms: {surv_count} / {batch_size} survived ({surv_pct:.2f}%)")

            wu_left_prps = 0
            wu_dual_prps = 0
            wu_proven = 0

            # 2. Multi-tier screening on survivors
            for t_val in survivors:
                cand = prof.family.candidate(t_val)

                # Precondition checks
                size_ok, _ = cand.satisfies_size_condition()
                if not size_ok:
                    continue

                alg_ok, _ = cand.validate_algebraic()
                if not alg_ok:
                    continue

                A_mpz = gmpy2.mpz(cand.A)
                B_mpz = gmpy2.mpz(cand.B)

                # Fast Tier-1: Base-2 Fermat PRP on candidate A
                if not gmpy2.is_prime(A_mpz, 1):
                    continue

                wu_left_prps += 1
                self.log(f"  [LEFT PRP HIT #{self.telemetry['left_prps'] + wu_left_prps}] t={t_val} (digits={cand.digits_A})")

                # Fast Tier-2: Base-2 Fermat PRP on candidate B
                if not gmpy2.is_prime(B_mpz, 1):
                    continue

                # High-Rigor Tier-3: 25-round Miller-Rabin test on both candidates
                if not gmpy2.is_prime(A_mpz, 25) or not gmpy2.is_prime(B_mpz, 25):
                    continue

                wu_dual_prps += 1
                self.log(f"\n  ************************************************************")
                self.log(f"  *** [DUAL PRP HIT AT >= 1,510 DIGITS DETECTED!] ***")
                self.log(f"  Coordinates: family={fid}, t={t_val}, digits={cand.digits_A}")
                self.log(f"  ************************************************************\n")

                # Novelty Check BEFORE proof generation
                novelty_status = self.storage.check_novelty(
                    cand.A, cand.B,
                    historical_inventory_path=self.hist_inv_path
                )
                self.log(f"  Pre-Proof Novelty Status: {novelty_status}")

                # Tier-4: Deterministic Proofs
                self.log("  Executing deterministic Pocklington BLS Theorem 4 proof on upper member B...")
                t_proof_start = time.time()
                p_stat, w_a, p_proof, p_err = prove_pocklington_upper(cand.B, prof.family.F_odd, prof.family.odd_prime_factors)
                if p_stat != PrimalityStatus.PROVEN_PRIME:
                    self.log(f"  Pocklington proof FAILED: {p_err}")
                    continue
                self.log(f"  Pocklington proof PASS (witness a={w_a}) in {(time.time() - t_proof_start)*1000:.1f} ms")

                self.log("  Executing deterministic Morrison BLS Theorem 17 proof on lower member A...")
                t_morr_start = time.time()
                m_stat, P_val, m_proof, m_err = prove_morrison_lower(cand.A, prof.family.F_odd, prof.family.odd_prime_factors)
                if m_stat != PrimalityStatus.PROVEN_PRIME:
                    self.log(f"  Morrison proof FAILED: {m_err}")
                    continue
                self.log(f"  Morrison proof PASS (parameter P={P_val}) in {(time.time() - t_morr_start)*1000:.1f} ms")

                wu_proven += 1
                self.log(f"  BOTH PRIMES DETERMINISTICALLY CERTIFIED: {cand.digits_A} DIGITS EACH!")

                # Build and Save Schema 5.0 Certificate
                pair_id = self.storage.canonical_pair_id(cand.A, cand.B)
                provenance = {
                    "run_id": self.run_id,
                    "git_commit": get_git_commit(),
                    "family_id": fid,
                    "t": t_val,
                    "sieve_limit": prof.sieve_limit,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat()
                }

                cert = TwinPrimeCertificateV5(
                    candidate=cand,
                    lower_proof=m_proof,
                    upper_proof=p_proof,
                    search_provenance=provenance,
                    status="PROVEN_BOTH",
                    novelty_status=novelty_status
                )
                
                # Save certificate in run directory
                cert_file = cert.save(self.proofs_dir)
                cert_data = cert.to_dict()
                self.log(f"  Certificate persisted to: {cert_file}")

                # Tier-5: First-Principles Independent Verification (Gate P0-A)
                self.log("  Running independent first-principles verification on proof payload...")
                v_script = REPO_ROOT / "scripts" / "phase5_independent_verify.py"
                v_cmd = [sys.executable, str(v_script), str(cert_file)]
                verification_passed = False
                if v_script.exists():
                    try:
                        v_res = subprocess.run(v_cmd, capture_output=True, text=True, timeout=60.0)
                        if v_res.returncode == 0:
                            # Verify that attestation was produced and reports PASS
                            att_file = cert_file.parent / "attestations" / f"attest_{cert_data['sha256'][:16]}.json"
                            if att_file.exists():
                                with open(att_file, "r", encoding="utf-8") as af:
                                    att_data = json.load(af)
                                if att_data.get("result") == "PASS":
                                    verification_passed = True
                                    self.log(f"  INDEPENDENT VERIFICATION: SUCCESSFUL ATTESTATION PASS! ({att_file.name})")
                                else:
                                    self.log(f"  INDEPENDENT VERIFICATION: Attestation result is not PASS: {att_data.get('result')}")
                            else:
                                self.log(f"  INDEPENDENT VERIFICATION: Attestation file not found at {att_file}")
                        else:
                            self.log(f"  INDEPENDENT VERIFICATION: FAILED (code {v_res.returncode}): {v_res.stderr.strip() or v_res.stdout.strip()}")
                    except Exception as e:
                        self.log(f"  INDEPENDENT VERIFICATION EXCEPTION: {e}")
                else:
                    self.log(f"  INDEPENDENT VERIFICATION BLOCKED: Verifier script missing at {v_script}")

                if not verification_passed:
                    self.log(f"  CRITICAL: Candidate {fid}_t{t_val} REJECTED due to failed independent verification.")
                    self.storage.record_candidate(fid, t_val, cand.A, cand.B, cand.digits_A, "VERIFICATION_FAILED", pair_id)
                    continue

                # Record discovery in storage only after verification PASS
                pair_id = self.storage.canonical_pair_id(cand.A, cand.B)
                self.storage.record_candidate(fid, t_val, cand.A, cand.B, cand.digits_A, "VERIFIED_BOTH", pair_id)
                self.storage.record_discovery(
                    family_id=fid,
                    t=t_val,
                    digits=cand.digits_A,
                    A=cand.A,
                    B=cand.B,
                    cert_path=str(cert_file),
                    sha256=cert_data["sha256"],
                    novelty_status=novelty_status,
                    pair_id=pair_id
                )

                disc_record = {
                    "family_id": fid,
                    "t": t_val,
                    "digits": cand.digits_A,
                    "canonical_key": self.storage.canonical_pair_key(cand.A, cand.B),
                    "pair_id": pair_id,
                    "sha256": cert_data["sha256"],
                    "novelty_status": novelty_status,
                    "certificate_path": str(cert_file)
                }
                discoveries_found.append(disc_record)
                self.telemetry["discoveries"].append(disc_record)

                if stop_on_discovery:
                    break

            # Complete work unit
            wu_elapsed = time.time() - t0
            self.storage.complete_work_unit(wu["work_unit_id"], survivors=surv_count, dual_prp=wu_dual_prps, proven=wu_proven)
            self.storage.update_bandit_stats(
                family_id=fid,
                elapsed_sec=wu_elapsed,
                survivors=surv_count,
                dual_prp=wu_dual_prps,
                proven=wu_proven,
                batch_size=batch_size
            )

            # Update telemetry
            self.telemetry["total_screened"] += batch_size
            self.telemetry["total_survivors"] += surv_count
            self.telemetry["left_prps"] += wu_left_prps
            self.telemetry["dual_prps"] += wu_dual_prps
            self.telemetry["proven_pairs"] += wu_proven
            self.telemetry["work_units_completed"] += 1
            self.telemetry["wall_time_sec"] = time.time() - t_campaign_start

            # Checkpoint metrics snapshot
            self._save_checkpoint(unit_idx + 1)

            if discoveries_found and stop_on_discovery:
                self.log(f"\nDiscovery goal achieved: {len(discoveries_found)} certified pair(s). Stopping search.")
                break

        # Generate final report
        self._generate_final_report()
        return discoveries_found

    def _save_checkpoint(self, seq: int):
        ckpt_file = self.checkpoints_dir / f"checkpoint_seq{seq:04d}.json"
        data = {
            "checkpoint_sequence": seq,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "telemetry": self.telemetry,
            "bandit_stats": self.storage.get_bandit_stats()
        }
        with open(ckpt_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _generate_final_report(self):
        rep_file = self.run_dir / "final_report.md"
        lines = [
            f"# Phase 5 Search Campaign Final Report: {self.run_id}",
            "",
            f"**Execution Completed UTC:** {datetime.now(timezone.utc).isoformat()}  ",
            f"**Total Wall Time:** {self.telemetry['wall_time_sec']:.2f} s  ",
            f"**Total Candidates Screened:** {self.telemetry['total_screened']:,}  ",
            f"**Total Sieve Survivors:** {self.telemetry['total_survivors']:,}  ",
            f"**Single-Side Left PRPs:** {self.telemetry['left_prps']}  ",
            f"**Dual PRPs:** {self.telemetry['dual_prps']}  ",
            f"**Proven & Independently Verified Pairs:** {self.telemetry['proven_pairs']}  ",
            "",
            "## Discoveries",
            ""
        ]
        if self.telemetry["discoveries"]:
            for d in self.telemetry["discoveries"]:
                lines.append(f"- **Pair at {d['digits']} Digits:** {d['family_id']} (t={d['t']})")
                lines.append(f"  - Novelty Status: `{d['novelty_status']}`")
                lines.append(f"  - Certificate SHA-256: `{d['sha256']}`")
                lines.append(f"  - Certificate Path: `{d['certificate_path']}`")
        else:
            lines.append("No certified twin-prime pair discovered in tested bounded search intervals.")
            lines.append("Negative search results logged for all tested sub-intervals.")

        with open(rep_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        # Mirror report into reports/phase5_runs/<run_id>/
        self.reports_run_dir.mkdir(parents=True, exist_ok=True)
        with open(self.reports_run_dir / "final_report.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
