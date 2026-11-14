"""
Phase 5 CLI Interface.
Provides subcommands:
- audit: Inspects environment, hardware, test suite, and historical proof repository with independent verification.
- discover: Executes SCCA candidate search and generates deterministic Schema 5.0 certificates with strict fail-closed verification gating.
- benchmark: Measures candidate generation, sieving, PRP screening, and proof throughput.
- status: Displays campaign ledger status, lease states, and bandit performance across configurable database paths.
- verify: Runs independent first-principles verification on certificates and propagates exit code.
"""

import sys
import os
import time
import json
import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .candidates import SmoothCenterFamily, TwinPairCandidate
from .crt_walker import SegmentedSCCAFilter, CRTWheel
from .primality import prp_test, prove_pocklington_upper, prove_morrison_lower, PrimalityStatus
from .certificate import TwinPrimeCertificateV5
from .storage import Phase5Storage
from .scheduler import MultiFamilyScheduler, SCCAProfile, SchedulingPolicy
from .campaign import SCCA1510Campaign

def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3)
        return res.stdout.strip() if res.returncode == 0 else "unknown"
    except Exception:
        return "unknown"

def run_audit(args):
    print("=" * 60)
    print("PHASE 5 SCCA BASELINE & REPOSITORY AUDIT")
    print("=" * 60)
    
    # 1. Environment info
    commit = get_git_commit()
    print(f"Git Commit: {commit}")
    print(f"Python: {sys.version.split()[0]} ({sys.platform})")
    
    try:
        import gmpy2
        print(f"gmpy2: Installed (version {gmpy2.version()})")
    except ImportError:
        print("gmpy2: Not installed (using pure Python fallback)")
        
    try:
        import sympy
        print(f"sympy: Installed (version {sympy.__version__})")
    except ImportError:
        print("sympy: Not installed")

    # 2. Historical Proof Inventory & Independent Verification
    print("\nAuditing Historical Proof Certificates:")
    repo_root = Path(args.repo).resolve()
    proof_dirs = [
        ("Phase 1", repo_root / "proofs", False, "scripts/verify_certificate.py"),
        ("Phase 2", repo_root / "proofs" / "phase2", True, "scripts/phase2_verify.py"),
        ("Phase 3", repo_root / "proofs" / "phase3", True, "scripts/phase3_independent_verify.py"),
        ("Phase 4", repo_root / "proofs" / "phase4", True, "scripts/phase4_independent_verify.py"),
        ("Phase 5", repo_root / "proofs" / "phase5", True, "scripts/phase5_independent_verify.py"),
        ("Phase 6", repo_root / "proofs" / "phase6" / "certificates", True, "src/phase6/independent_verify.py"),
    ]
    
    max_digits = 0
    max_pair_info = ""
    total_certs = 0
    verified_certs = 0
    failed_certs = 0
    audit_records = []
    
    # Separate audit attestation output directory to keep historical proofs pristine
    audit_attest_dir = repo_root / "research" / "phase5_integrity" / "attestations"
    audit_attest_dir.mkdir(parents=True, exist_ok=True)

    for phase_label, pdir, is_sub, verifier_rel in proof_dirs:
        if pdir.exists():
            if is_sub:
                certs = sorted(list(pdir.glob("cert_*.json")) + list(pdir.glob("imported_cert_*.json")))
            else:
                certs = sorted([p for p in pdir.glob("cert_*.json") if p.parent == pdir])
            
            verifier_path = repo_root / verifier_rel
            
            for cf in certs:
                total_certs += 1
                cf_bytes = cf.read_bytes()
                cf_sha256 = hashlib.sha256(cf_bytes).hexdigest()
                digits = 0
                pair_id = None
                pair_valid = False
                issues = []
                proof_status = "NOT_RUN"
                return_code = None

                try:
                    d = json.load(open(cf, "r", encoding="utf-8"))
                    # Extract pair integers
                    A, B = None, None
                    if "pair" in d and "lower_prime_A" in d["pair"] and "upper_prime_B" in d["pair"]:
                        A = int(d["pair"]["lower_prime_A"])
                        B = int(d["pair"]["upper_prime_B"])
                    elif "pair" in d and "lower_decimal" in d["pair"] and "upper_decimal" in d["pair"]:
                        A = int(d["pair"]["lower_decimal"])
                        B = int(d["pair"]["upper_decimal"])
                    elif "pair" in d and "p_minus" in d["pair"] and "p_plus" in d["pair"]:
                        A = int(d["pair"]["p_minus"])
                        B = int(d["pair"]["p_plus"])
                    elif "lower_decimal" in d and "upper_decimal" in d:
                        A = int(d["lower_decimal"])
                        B = int(d["upper_decimal"])
                    elif "p_minus" in d and "p_plus" in d:
                        A = int(d["p_minus"])
                        B = int(d["p_plus"])
                    elif "parameters" in d and "t" in d["parameters"] and "exponents" in d["parameters"]:
                        exp = {int(k): int(v) for k, v in d["parameters"]["exponents"].items()}
                        F = 1
                        for pr, e in exp.items():
                            F *= (pr ** e)
                        C = F * int(d["parameters"]["t"])
                        A = C - 1
                        B = C + 1
                    elif "k" in d and "n" in d:
                        C = int(d["k"]) * (1 << int(d["n"]))
                        A = C - 1
                        B = C + 1

                    if A is not None and B is not None:
                        digits = len(str(A))
                        pair_valid = (B - A == 2) and (A > 2) and (A % 2 == 1) and (B % 2 == 1)
                        pair_key = f"twin-pair-v1:{min(A, B)}:{max(A, B)}"
                        pair_id = hashlib.sha256(pair_key.encode("utf-8")).hexdigest()
                    else:
                        issues.append("Could not extract exact (A, B) pair integers")

                    if digits > max_digits:
                        max_digits = digits
                        max_pair_info = f"{cf.name} ({digits} digits)"

                    # Run format-specific independent verifier
                    if verifier_path.exists():
                        cmd = [sys.executable, str(verifier_path), str(cf)]
                        if phase_label == "Phase 5":
                            cmd.extend(["--attestation-dir", str(audit_attest_dir)])
                        
                        v_res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        return_code = v_res.returncode
                        if return_code == 0:
                            proof_status = "VERIFIED"
                            verified_certs += 1
                        else:
                            proof_status = "FAILED"
                            failed_certs += 1
                            issues.append(f"Verifier returned code {return_code}: {v_res.stderr.strip() or v_res.stdout.strip()}")
                    else:
                        proof_status = "UNSUPPORTED_FORMAT"
                        issues.append(f"Independent verifier script missing: {verifier_path}")

                    print(f"  [{phase_label}] {cf.name}: {digits} digits -> {proof_status}")

                except Exception as e:
                    proof_status = "MALFORMED"
                    failed_certs += 1
                    issues.append(f"Exception during inspection: {e}")
                    print(f"  [{phase_label}] {cf.name}: MALFORMED ({e})")

                audit_records.append({
                    "audit_version": "phase5-integrity-v1",
                    "repo_commit": commit,
                    "phase": phase_label,
                    "certificate_path": str(cf.relative_to(repo_root)).replace("\\", "/"),
                    "certificate_file_sha256": cf_sha256,
                    "pair_id": pair_id,
                    "pair_relation_valid": pair_valid,
                    "digits": digits,
                    "proof_verification": proof_status,
                    "verification_tool": str(verifier_rel),
                    "verification_return_code": return_code,
                    "issues": issues
                })

    print(f"\nTotal historical certificates audited: {total_certs}")
    print(f"  Verified: {verified_certs} | Failed / Malformed: {failed_certs}")
    print(f"Current Repository Maximum: {max_digits} digits ({max_pair_info})")
    print("=" * 60)

    # Write report if requested
    if getattr(args, "report", None):
        rep_path = Path(args.report)
        rep_path.parent.mkdir(parents=True, exist_ok=True)
        with open(rep_path, "w", encoding="utf-8") as f:
            json.dump({
                "audit_version": "phase5-integrity-v1",
                "repo_commit": commit,
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "summary": {
                    "total_certificates": total_certs,
                    "verified": verified_certs,
                    "failed": failed_certs,
                    "max_digits": max_digits
                },
                "artifacts": audit_records
            }, f, indent=2)
        print(f"Saved machine-readable audit report to: {rep_path}")

    if getattr(args, "strict", False) and failed_certs > 0:
        print(f"ERROR: Strict audit failed with {failed_certs} unverified/failed certificate(s).")
        sys.exit(1)

def execute_discovery_search(
    storage: Phase5Storage,
    profile: SCCAProfile,
    t_start: int,
    t_end: int,
    output_dir: Path,
    historical_inventory_path: Optional[Path] = None,
    max_finds: int = 1,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Executes SCCA search over t in [t_start, t_end) with strict fail-closed verification gating.
    Returns dict containing:
      - 'discoveries': List of verified and accepted discovery dicts.
      - 'metrics': Typed per-work-unit counters (survivors, dual_prp, proven, verified, failed_v).
    """
    fam = profile.family
    sieve_limit = profile.sieve_limit
    
    if verbose:
        print(f"\n[Worker] Starting work unit on {fam.family_id}: t in [{t_start}, {t_end}), sieve_limit={sieve_limit}")
        print(f"  F = {fam.F} ({fam.F.bit_length()} bits, {len(str(fam.F))} digits)")
        print(f"  Prime factors: {fam.prime_factors}")

    t0 = time.time()
    
    # 1. Segmented Modular Filter (Method S1)
    sieve_filter = SegmentedSCCAFilter(fam, sieve_limit=sieve_limit)
    survivors = sieve_filter.sieve_segment(t_start, t_end)
    t_sieve = time.time() - t0
    
    if verbose:
        print(f"  Sieve complete in {t_sieve*1000:.2f} ms: {len(survivors)} / {t_end - t_start} survived ({len(survivors)/(t_end - t_start)*100:.2f}%)")

    dual_prp_count = 0
    proven_count = 0
    verified_count = 0
    failed_v_count = 0
    discoveries = []
    
    git_commit = get_git_commit()
    
    for t_val in survivors:
        cand = fam.candidate(t_val)
        pair_id = storage.canonical_pair_id(cand.A, cand.B)
        
        # Check size condition
        size_ok, size_err = cand.satisfies_size_condition()
        if not size_ok:
            continue
            
        # Check algebraic properties
        alg_ok, alg_err = cand.validate_algebraic()
        if not alg_ok:
            continue

        # Novelty check BEFORE persisting candidate or running proofs
        novelty_check = storage.check_novelty(
            cand.A, cand.B,
            historical_inventory_path=historical_inventory_path
        )
        if novelty_check in ("INVALID_PAIR", "DUPLICATE_IN_CURRENT_RUN"):
            continue

        # Stage 1: Dual PRP screening
        if not prp_test(cand.A):
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "COMPOSITE_A", pair_id)
            continue
            
        if not prp_test(cand.B):
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "COMPOSITE_B", pair_id)
            continue
            
        dual_prp_count += 1
        storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "PRP_BOTH", pair_id)
        
        if verbose:
            print(f"  [DUAL PRP HIT] t={t_val}: A={cand.A}, B={cand.B} ({cand.digits_A} digits)")

        # Stage 2: Pocklington deterministic proof on B
        pock_status, witness_a, pock_proof, pock_err = prove_pocklington_upper(cand.B, fam.F_odd, fam.odd_prime_factors)
        if pock_status != PrimalityStatus.PROVEN_PRIME:
            if verbose:
                print(f"    Pocklington proof on B failed: {pock_err}")
            continue

        # Stage 3: Morrison deterministic proof on A
        morr_status, param_P, morr_proof, morr_err = prove_morrison_lower(cand.A, fam.F_odd, fam.odd_prime_factors)
        if morr_status != PrimalityStatus.PROVEN_PRIME:
            if verbose:
                print(f"    Morrison proof on A failed: {morr_err}")
            continue

        # Both PROVEN at generation tier
        proven_count += 1
        storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "PROOF_GENERATED", pair_id)
        
        if verbose:
            print(f"  *** [PROVEN TWIN PAIR GENERATED] ***")
            print(f"    A = {cand.A} (Morrison proved with P={param_P})")
            print(f"    B = {cand.B} (Pocklington proved with a={witness_a})")
            print(f"    Digits: {cand.digits_A} / {cand.digits_B}")
            print(f"    Novelty: {novelty_check}")

        # Search provenance
        provenance = {
            "git_commit": git_commit,
            "algorithm": "SCCA_Method_S1_S2",
            "family_id": fam.family_id,
            "t": t_val,
            "sieve_limit": sieve_limit,
            "elapsed_sec": time.time() - t0
        }

        # Build and save Schema 5.0 Certificate
        cert = TwinPrimeCertificateV5(
            candidate=cand,
            lower_proof=morr_proof,
            upper_proof=pock_proof,
            search_provenance=provenance,
            status="PROVEN_BOTH",
            novelty_status=novelty_check
        )
        cert_path = cert.save(output_dir)
        cert_data = cert.to_dict()
        cert_sha256 = cert_data["sha256"]
        
        # --------------------------------------------------------------------
        # FAIL-CLOSED INDEPENDENT VERIFICATION ACCEPTANCE GATE (P0-A)
        # --------------------------------------------------------------------
        verifier_script = Path(__file__).resolve().parent.parent.parent / "scripts" / "phase5_independent_verify.py"
        verification_passed = False
        attestation_file = None
        
        if not verifier_script.exists():
            print(f"    CRITICAL: Verifier script missing at {verifier_script}. Acceptance BLOCKED.")
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "VERIFICATION_UNAVAILABLE", pair_id)
            failed_v_count += 1
        else:
            try:
                v_res = subprocess.run(
                    [sys.executable, str(verifier_script), str(cert_path)],
                    capture_output=True,
                    text=True,
                    timeout=60.0
                )
                if v_res.returncode == 0:
                    # Validate that attestation artifact exists and is a valid PASS
                    expected_att = cert_path.parent / "attestations" / f"attest_{cert_sha256[:16]}.json"
                    if expected_att.exists():
                        with open(expected_att, "r", encoding="utf-8") as af:
                            att_data = json.load(af)
                        if (
                            att_data.get("result") == "PASS" and
                            att_data.get("target_sha256") == cert_sha256 and
                            att_data.get("target_certificate") == cert_path.name
                        ):
                            verification_passed = True
                            attestation_file = expected_att
                            if verbose:
                                print(f"    Independent verification: PASS ({cert_path.name})")
                        else:
                            print(f"    Independent verification attestation mismatch or not PASS in {expected_att}")
                    else:
                        print(f"    Independent verification attestation file not found at {expected_att}")
                else:
                    print(f"    Independent verification FAIL (code {v_res.returncode}): {v_res.stderr.strip() or v_res.stdout.strip()}")
            except subprocess.TimeoutExpired:
                print(f"    Independent verification TIMED OUT after 60s for {cert_path.name}")
            except Exception as e:
                print(f"    Independent verification EXCEPTION: {e}")

        if verification_passed:
            verified_count += 1
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "VERIFIED_BOTH", pair_id)
            storage.record_discovery(
                family_id=fam.family_id,
                t=t_val,
                digits=cand.digits_A,
                A=cand.A,
                B=cand.B,
                cert_path=str(cert_path),
                sha256=cert_sha256,
                novelty_status=novelty_check,
                pair_id=pair_id
            )
            discoveries.append({
                "candidate": cand,
                "cert_path": cert_path,
                "sha256": cert_sha256,
                "novelty_status": novelty_check,
                "pair_id": pair_id,
                "attestation_path": str(attestation_file)
            })
        else:
            failed_v_count += 1
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "VERIFICATION_FAILED", pair_id)
            print(f"    Discovery REJECTED: Candidate {fam.family_id}_t{t_val} failed independent verification.")

        if len(discoveries) >= max_finds:
            break

    elapsed = time.time() - t0
    storage.update_bandit_stats(
        fam.family_id,
        elapsed,
        len(survivors),
        dual_prp_count,
        verified_count,
        batch_size=(t_end - t_start)
    )
    return {
        "discoveries": discoveries,
        "metrics": {
            "survivors": len(survivors),
            "dual_prp": dual_prp_count,
            "proven": proven_count,
            "verified": verified_count,
            "failed_verification": failed_v_count
        }
    }

def run_discover(args):
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    db_path = Path(cfg.get("db_path", "runs/phase5/phase5_search.db"))
    output_dir = Path(cfg.get("proofs_dir", "proofs/phase5"))
    storage = Phase5Storage(db_path)

    # Path to authoritative historical inventory
    hist_inv_path = Path(cfg.get("historical_inventory", "research/phase5_integrity/HISTORICAL_CERTIFICATE_INVENTORY.json"))
    if not hist_inv_path.exists():
        # Fallback to older audit inventory if present
        alt_path = Path("research/phase5_audit/historical_inventory.json")
        if alt_path.exists():
            hist_inv_path = alt_path

    profiles = []
    for f_cfg in cfg.get("families", []):
        prof = SCCAProfile(
            family_id=f_cfg["family_id"],
            exponents={int(p): int(e) for p, e in f_cfg["exponents"].items()},
            t_batch_size=f_cfg.get("t_batch_size", 1000),
            sieve_limit=f_cfg.get("sieve_limit", 50000),
            priority=f_cfg.get("priority", 1)
        )
        profiles.append(prof)

    policy_str = cfg.get("policy", "BANDIT_UCB1")
    policy = SchedulingPolicy(policy_str) if policy_str in SchedulingPolicy.__members__ else SchedulingPolicy.BANDIT_UCB1

    scheduler = MultiFamilyScheduler(
        storage=storage,
        profiles=profiles,
        policy=policy,
        seed=cfg.get("seed", 42),
        resume=args.resume
    )

    max_work_units = cfg.get("max_work_units", 5)
    max_total_discoveries = cfg.get("max_discoveries", 1)
    
    print(f"Running Phase 5 Discovery Campaign: policy={policy.value}, resume={args.resume}, max_units={max_work_units}")
    total_found = 0

    for u_idx in range(max_work_units):
        wu = scheduler.dispense_work_unit()
        print(f"\n--- Work Unit {u_idx + 1}/{max_work_units} ({wu['work_unit_id']}) ---")
        print(f"Rationale: {wu['rationale']}")
        
        search_res = execute_discovery_search(
            storage=storage,
            profile=wu["profile"],
            t_start=wu["t_start"],
            t_end=wu["t_end"],
            output_dir=output_dir,
            historical_inventory_path=hist_inv_path,
            max_finds=max_total_discoveries - total_found,
            verbose=True
        )
        finds = search_res["discoveries"]
        metrics = search_res["metrics"]
        total_found += len(finds)
        
        # Persist MEASURED metrics rather than fabricated zeros (P1-F)
        storage.complete_work_unit(
            wu["work_unit_id"],
            survivors=metrics["survivors"],
            dual_prp=metrics["dual_prp"],
            proven=len(finds)
        )

        if total_found >= max_total_discoveries:
            print(f"\nTarget discovery count reached: {total_found} verified pair(s). Stopping campaign.")
            break

def run_benchmark(args):
    print("=" * 60)
    print("PHASE 5 SCCA CONTROLLED BENCHMARK")
    print("=" * 60)
    
    fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="bench_fam")
    t_start = 1
    t_end = 20000
    sieve_limit = 50000
    
    print(f"\n1. Sieve Throughput Comparison (Interval length: {t_end - t_start}):")
    # A. Segmented filter
    t0 = time.time()
    seg_filter = SegmentedSCCAFilter(fam, sieve_limit=sieve_limit)
    surv_seg = seg_filter.sieve_segment(t_start, t_end)
    t_seg = time.time() - t0
    rate_seg = (t_end - t_start) / max(t_seg, 0.0001)
    print(f"  Method S1 Segment Filter: {t_seg*1000:.2f} ms ({rate_seg:,.0f} cands/s), survivors: {len(surv_seg)}")

    # B. CRT Wheel Walker
    t0 = time.time()
    wheel = CRTWheel(fam, wheel_primes=[11, 13, 17])
    surv_wheel = list(wheel.walk_classes(t_start, t_end))
    t_wheel = time.time() - t0
    rate_wheel = (t_end - t_start) / max(t_wheel, 0.0001)
    print(f"  Method S1 CRT Wheel Walker: {t_wheel*1000:.2f} ms ({rate_wheel:,.0f} cands/s), survivors: {len(surv_wheel)}")
    
    print("\n2. Primality Proving Speed at various digit bands:")
    for digits, f_exp in [(20, {2: 1, 3: 20, 5: 10}), (50, {2: 1, 3: 50, 5: 25}), (100, {2: 1, 3: 100, 5: 50})]:
        test_fam = SmoothCenterFamily(f_exp, family_id=f"f_{digits}d")
        cand = test_fam.candidate(3)
        t0 = time.time()
        _ = prove_pocklington_upper(cand.B, test_fam.F_odd, test_fam.odd_prime_factors)
        _ = prove_morrison_lower(cand.A, test_fam.F_odd, test_fam.odd_prime_factors)
        t_proof = time.time() - t0
        print(f"  Digit Band ~{cand.digits_A}d: Proof time = {t_proof*1000:.2f} ms")

    print("\nBenchmark completed successfully.")
    print("=" * 60)

def run_status(args):
    # Resolve DB path with precedence: --db, --config, then default (P1-D)
    db_path = None
    if getattr(args, "db", None):
        db_path = Path(args.db)
    elif getattr(args, "config", None):
        cfg_path = Path(args.config)
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if "db_path" in cfg:
                    db_path = Path(cfg["db_path"])
            except Exception:
                pass
    
    if db_path is None:
        db_path = Path("runs/phase5/phase5_search.db")

    print("=" * 60)
    print("PHASE 5 CAMPAIGN STATUS")
    print("=" * 60)
    print(f"Database Path: {db_path.resolve()}")

    if not db_path.exists():
        print(f"No database found at {db_path}. (Not initialized)")
        print("=" * 60)
        return

    storage = Phase5Storage(db_path)
    with storage._get_connection() as conn:
        wus = conn.execute("SELECT status, count(*) as cnt FROM work_units GROUP BY status").fetchall()
        cands = conn.execute("SELECT status, count(*) as cnt FROM candidates GROUP BY status").fetchall()
        discs = conn.execute("SELECT * FROM discoveries").fetchall()
        b_stats = conn.execute("SELECT * FROM bandit_stats").fetchall()

    print("\nWork Units:")
    for w in wus:
        print(f"  {w['status']}: {w['cnt']}")
    print("\nCandidates:")
    for c in cands:
        print(f"  {c['status']}: {c['cnt']}")
    print(f"\nDiscoveries: {len(discs)}")
    for d in discs:
        print(f"  Discovery: family={d['family_id']}, t={d['t']}, digits={d['digits']}, status={d['novelty_status']}")
        print(f"    SHA-256: {d['sha256']}")
        print(f"    Pair ID: {d['pair_id'] if 'pair_id' in d.keys() else 'N/A'}")
        print(f"    Cert: {d['cert_path']}")
    print("\nBandit Performance:")
    for b in b_stats:
        mean_r = b["mean_reward"] if "mean_reward" in b.keys() else 0.0
        print(f"  Family {b['family_id']}: pulls={b['pulls']}, time={b['total_time']:.2f}s, dual_prp={b['dual_prp']}, proven={b['proven']}, mean_reward={mean_r:.4f}")
    print("=" * 60)

def run_campaign(args):
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    max_units = args.max_units or cfg.get("max_work_units", 10)
    campaign = SCCA1510Campaign(
        config=cfg,
        run_id=args.run_id,
        resume=args.resume
    )
    campaign.run_bounded_search(
        max_work_units=max_units,
        stop_on_discovery=not args.no_stop
    )

def main():
    parser = argparse.ArgumentParser(description="Phase 5 SCCA Twin Prime Search Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # campaign
    p_camp = subparsers.add_parser("campaign")
    p_camp.add_argument("--config", required=True, help="Path to JSON campaign configuration")
    p_camp.add_argument("--max-units", type=int, default=None, help="Maximum work units to process")
    p_camp.add_argument("--run-id", default=None, help="Explicit run ID (for resume or specific tag)")
    p_camp.add_argument("--resume", action="store_true", help="Resume run from last checkpoint")
    p_camp.add_argument("--no-stop", action="store_true", help="Continue searching even after first discovery")

    # audit
    p_audit = subparsers.add_parser("audit")
    p_audit.add_argument("--repo", default=".", help="Repository root path")
    p_audit.add_argument("--strict", action="store_true", help="Exit with code 1 if any certificate fails verification")
    p_audit.add_argument("--report", default=None, help="Optional output path for machine-readable JSON report")

    # discover
    p_disc = subparsers.add_parser("discover")
    p_disc.add_argument("--config", required=True, help="Path to JSON configuration")
    p_disc.add_argument("--resume", action="store_true", help="Resume from previous checkpoints")

    # benchmark
    p_bench = subparsers.add_parser("benchmark")
    p_bench.add_argument("--config", default=None, help="Optional config path")

    # status
    p_stat = subparsers.add_parser("status")
    p_stat.add_argument("--campaign", default="discovery", help="Campaign name")
    p_stat.add_argument("--config", default=None, help="Campaign config JSON path")
    p_stat.add_argument("--db", default=None, help="Direct database path")

    # verify
    p_ver = subparsers.add_parser("verify")
    p_ver.add_argument("target", help="Certificate path or directory")
    p_ver.add_argument("--attestation-dir", default=None, help="Directory to write attestations")
    p_ver.add_argument("--overwrite", action="store_true", help="Overwrite existing attestations")

    args = parser.parse_args()
    if args.command == "campaign":
        run_campaign(args)
    elif args.command == "audit":
        run_audit(args)
    elif args.command == "discover":
        run_discover(args)
    elif args.command == "benchmark":
        run_benchmark(args)
    elif args.command == "status":
        run_status(args)
    elif args.command == "verify":
        v_script = Path(__file__).resolve().parent.parent.parent / "scripts" / "phase5_independent_verify.py"
        cmd = [sys.executable, str(v_script), args.target]
        if args.attestation_dir:
            cmd.extend(["--attestation-dir", str(args.attestation_dir)])
        if args.overwrite:
            cmd.append("--overwrite")
        res = subprocess.run(cmd)
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()
