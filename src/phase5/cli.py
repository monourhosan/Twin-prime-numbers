"""
Phase 5 CLI Interface.
Provides subcommands:
- audit: Inspects environment, hardware, test suite, and historical proof repository.
- discover: Executes SCCA candidate search and generates deterministic Schema 5.0 certificates.
- benchmark: Measures candidate generation, sieving, PRP screening, and proof throughput.
- status: Displays campaign ledger status, lease states, and bandit performance.
- verify: Runs independent first-principles verification on certificates.
"""

import sys
import os
import time
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from .candidates import SmoothCenterFamily, TwinPairCandidate
from .crt_walker import SegmentedSCCAFilter, CRTWheel
from .primality import prp_test, prove_pocklington_upper, prove_morrison_lower, PrimalityStatus
from .certificate import TwinPrimeCertificateV5
from .storage import Phase5Storage
from .scheduler import MultiFamilyScheduler, SCCAProfile, SchedulingPolicy

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

    # 2. Historical Proof Inventory
    print("\nAuditing Historical Proof Certificates:")
    repo_root = Path(args.repo)
    proof_dirs = [
        ("Phase 1", repo_root / "proofs" / "phase1"),
        ("Phase 2", repo_root / "proofs" / "phase2"),
        ("Phase 3", repo_root / "proofs" / "phase3"),
        ("Phase 4", repo_root / "proofs" / "phase4"),
        ("Phase 5", repo_root / "proofs" / "phase5"),
    ]
    
    max_digits = 0
    max_pair_info = ""
    total_certs = 0
    
    for phase_label, pdir in proof_dirs:
        if pdir.exists():
            certs = list(pdir.glob("cert_*.json")) + list(pdir.glob("imported_cert_*.json"))
            for cf in certs:
                total_certs += 1
                try:
                    with open(cf, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    digits = d.get("digits_lower") or d.get("pair", {}).get("lower_digits") or 0
                    if digits > max_digits:
                        max_digits = digits
                        max_pair_info = f"{cf.name} ({digits} digits)"
                    print(f"  [{phase_label}] {cf.name}: {digits} digits")
                except Exception as e:
                    print(f"  [{phase_label}] {cf.name}: Failed to read ({e})")
                    
    print(f"\nTotal historical certificates audited: {total_certs}")
    print(f"Current Repository Maximum: {max_digits} digits ({max_pair_info})")
    print("Novelty Requirement: Discovery must be absent from all historical records above.")
    print("Stretch Goal Target: >= 1,510 digits.")
    print("=" * 60)

def execute_discovery_search(
    storage: Phase5Storage,
    profile: SCCAProfile,
    t_start: int,
    t_end: int,
    output_dir: Path,
    max_finds: int = 1,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """Executes SCCA search over t in [t_start, t_end)."""
    fam = profile.family
    sieve_limit = profile.sieve_limit
    
    if verbose:
        print(f"\n[Worker] Starting work unit on {fam.family_id}: t in [{t_start}, {t_end}), sieve_limit={sieve_limit}")
        print(f"  F = {fam.F} ({fam.F.bit_length()} bits, {len(str(fam.F))} digits)")
        print(f"  F_odd = {fam.F_odd}")
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
    discoveries = []
    
    git_commit = get_git_commit()
    
    for t_val in survivors:
        cand = fam.candidate(t_val)
        
        # Check size condition
        size_ok, size_err = cand.satisfies_size_condition()
        if not size_ok:
            continue
            
        # Check algebraic properties
        alg_ok, alg_err = cand.validate_algebraic()
        if not alg_ok:
            continue

        # Stage 1: Dual PRP screening
        if not prp_test(cand.A):
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "COMPOSITE_A", cand.canonical_hash())
            continue
            
        if not prp_test(cand.B):
            storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "COMPOSITE_B", cand.canonical_hash())
            continue
            
        dual_prp_count += 1
        storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "PRP_BOTH", cand.canonical_hash())
        
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

        # Both PROVEN!
        proven_count += 1
        storage.record_candidate(fam.family_id, t_val, cand.A, cand.B, cand.digits_A, "PROVEN_BOTH", cand.canonical_hash())
        
        if verbose:
            print(f"  *** [PROVEN TWIN PAIR FOUND!] ***")
            print(f"    A = {cand.A} (Morrison proved with P={param_P})")
            print(f"    B = {cand.B} (Pocklington proved with a={witness_a})")
            print(f"    Digits: {cand.digits_A} / {cand.digits_B}")

        # Check project deduplication
        is_known = storage.is_known_discovery(cand.canonical_hash())
        novelty_status = "ALREADY_IN_PROJECT" if is_known else "NEW_TO_REPO_ONLY"

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
            novelty_status=novelty_status
        )
        cert_path = cert.save(output_dir)
        cert_data = cert.to_dict()
        
        # Record discovery
        storage.record_discovery(
            family_id=fam.family_id,
            t=t_val,
            digits=cand.digits_A,
            A=cand.A,
            B=cand.B,
            cert_path=str(cert_path),
            sha256=cert_data["sha256"],
            novelty_status=novelty_status
        )
        
        # Run immediate independent verification subprocess
        verifier_script = Path(__file__).resolve().parent.parent.parent / "scripts" / "phase5_independent_verify.py"
        if verifier_script.exists():
            v_res = subprocess.run([sys.executable, str(verifier_script), str(cert_path)], capture_output=True, text=True)
            if v_res.returncode == 0:
                print(f"    Independent verification: PASS ({cert_path.name})")
            else:
                print(f"    Independent verification: FAIL ({v_res.stderr})")

        discoveries.append({
            "candidate": cand,
            "cert_path": cert_path,
            "sha256": cert_data["sha256"],
            "novelty_status": novelty_status
        })

        if len(discoveries) >= max_finds:
            break

    elapsed = time.time() - t0
    storage.update_bandit_stats(fam.family_id, elapsed, len(survivors), dual_prp_count, proven_count)
    return discoveries

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
        seed=cfg.get("seed", 42)
    )

    max_work_units = cfg.get("max_work_units", 5)
    max_total_discoveries = cfg.get("max_discoveries", 1)
    
    print(f"Running Phase 5 Discovery Campaign: policy={policy.value}, max_units={max_work_units}")
    total_found = 0

    for u_idx in range(max_work_units):
        wu = scheduler.dispense_work_unit()
        print(f"\n--- Work Unit {u_idx + 1}/{max_work_units} ({wu['work_unit_id']}) ---")
        print(f"Rationale: {wu['rationale']}")
        
        finds = execute_discovery_search(
            storage=storage,
            profile=wu["profile"],
            t_start=wu["t_start"],
            t_end=wu["t_end"],
            output_dir=output_dir,
            max_finds=max_total_discoveries - total_found,
            verbose=True
        )
        total_found += len(finds)
        storage.complete_work_unit(wu["work_unit_id"], survivors=0, dual_prp=0, proven=len(finds))

        if total_found >= max_total_discoveries:
            print(f"\nTarget discovery count reached: {total_found} certified pair(s). Stopping campaign.")
            break

def run_benchmark(args):
    print("=" * 60)
    print("PHASE 5 SCCA CONTROLLED BENCHMARK")
    print("=" * 60)
    
    # Compare Method S1 (CRT Class Walker vs Segment Filter)
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
    
    # 2. Primality Proving Speed at various digit bands
    print("\n2. Primality Proving Benchmark (Pocklington + Morrison):")
    for digits, f_exp in [(20, {2: 1, 3: 20, 5: 10}), (50, {2: 1, 3: 50, 5: 25}), (100, {2: 1, 3: 100, 5: 50})]:
        test_fam = SmoothCenterFamily(f_exp, family_id=f"f_{digits}d")
        # Measure 1 Pocklington + 1 Morrison
        cand = test_fam.candidate(3)
        t0 = time.time()
        # Matrix pow
        _ = prove_pocklington_upper(cand.B, test_fam.F_odd, test_fam.odd_prime_factors)
        _ = prove_morrison_lower(cand.A, test_fam.F_odd, test_fam.odd_prime_factors)
        t_proof = time.time() - t0
        print(f"  Digit Band ~{cand.digits_A}d: Proof time = {t_proof*1000:.2f} ms")

    print("\nBenchmark completed successfully.")
    print("=" * 60)

def run_status(args):
    db_path = Path("runs/phase5/phase5_search.db")
    if not db_path.exists():
        print(f"No database found at {db_path}")
        return
    storage = Phase5Storage(db_path)
    with storage._get_connection() as conn:
        wus = conn.execute("SELECT status, count(*) as cnt FROM work_units GROUP BY status").fetchall()
        cands = conn.execute("SELECT status, count(*) as cnt FROM candidates GROUP BY status").fetchall()
        discs = conn.execute("SELECT * FROM discoveries").fetchall()
        b_stats = conn.execute("SELECT * FROM bandit_stats").fetchall()

    print("=" * 60)
    print("PHASE 5 CAMPAIGN STATUS")
    print("=" * 60)
    print("Work Units:")
    for w in wus:
        print(f"  {w['status']}: {w['cnt']}")
    print("\nCandidates:")
    for c in cands:
        print(f"  {c['status']}: {c['cnt']}")
    print(f"\nDiscoveries: {len(discs)}")
    for d in discs:
        print(f"  Discovery: family={d['family_id']}, t={d['t']}, digits={d['digits']}, status={d['novelty_status']}")
        print(f"    SHA-256: {d['sha256']}")
        print(f"    Cert: {d['cert_path']}")
    print("\nBandit Performance:")
    for b in b_stats:
        print(f"  Family {b['family_id']}: pulls={b['pulls']}, time={b['total_time']:.2f}s, dual_prp={b['dual_prp']}, proven={b['proven']}, reward={b['last_reward']:.4f}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Phase 5 SCCA Twin Prime Search Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # audit
    p_audit = subparsers.add_parser("audit")
    p_audit.add_argument("--repo", default=".", help="Repository root path")

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

    # verify
    p_ver = subparsers.add_parser("verify")
    p_ver.add_argument("target", help="Certificate path or directory")

    args = parser.parse_args()
    if args.command == "audit":
        run_audit(args)
    elif args.command == "discover":
        run_discover(args)
    elif args.command == "benchmark":
        run_benchmark(args)
    elif args.command == "status":
        run_status(args)
    elif args.command == "verify":
        v_script = Path(__file__).resolve().parent.parent.parent / "scripts" / "phase5_independent_verify.py"
        subprocess.run([sys.executable, str(v_script), args.target])

if __name__ == "__main__":
    main()
