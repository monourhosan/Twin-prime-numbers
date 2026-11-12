"""
Experiment Orchestrator for CATS.
Runs bounded searches, structured sweeps across digit scales,
ablation comparisons, and produces data/benchmarks.csv, data/candidates.jsonl,
and data/coverage_manifest.json.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
import platform
from datetime import datetime, timezone

from src.cats.sieve import BoundedTwinSieve, StructuredTwinSieve
from src.cats.primality import is_prime_u64, is_probable_prime, proth_prove, llr_prove
from src.cats.adaptive import estimate_optimal_sieve_depth
from src.cats.certificate import TwinPrimeCertificate

DATA_DIR = Path("data")
PROOFS_DIR = Path("proofs")
CONFIGS_DIR = Path("configs")

def get_system_specs():
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count_logical": os.cpu_count(),
    }

def run_experiments():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

    candidates_file = DATA_DIR / "candidates.jsonl"
    benchmarks_file = DATA_DIR / "benchmarks.csv"
    manifest_file = DATA_DIR / "coverage_manifest.json"

    # Reset candidates file
    with open(candidates_file, "w", encoding="utf-8") as f:
        pass

    benchmark_rows = [
        "experiment_id,mode,parameter,search_range,sieve_depth,sieve_time_sec,total_time_sec,survivors,verified_twins,largest_lower_prime"
    ]

    manifest = {
        "metadata": {
            "title": "CATS Twin-Prime Research Coverage Manifest",
            "primary_auditor": "Monour Hosan Saif",
            "contributors": "Gemini and ChatGPT",
            "execution_date_utc": datetime.now(timezone.utc).isoformat(),
            "system_specifications": get_system_specs(),
            "engine": "CATS (NumPy/SymPy Python 3.12)",
        },
        "completed_searches": []
    }

    # -------------------------------------------------------------
    # 1. Bounded Exhaustive Searches
    # -------------------------------------------------------------
    print("\n=======================================================")
    print("STAGE 1: BOUNDED EXHAUSTIVE SEARCH EXPERIMENTS")
    print("=======================================================")
    bounded_targets = [100_000, 1_000_000, 5_000_000, 10_000_000]

    for bound in bounded_targets:
        print(f"\n--- Exhaustive Bounded Search in [2, {bound:,}] ---")
        t0 = time.time()
        sieve_depth = int(bound**0.5)
        sieve = BoundedTwinSieve(2, bound, sieve_depth, use_dual_sieve=True)
        candidates, stats = sieve.run_sieve()
        t_sieve = time.time() - t0

        t_test = time.time()
        verified_twins = [p for p in candidates if is_prime_u64(p[0]) and is_prime_u64(p[1])]
        t_total = time.time() - t0

        largest_pair = verified_twins[-1] if verified_twins else (None, None)
        print(f"Survivors: {stats.survivors:,}/{stats.total_candidates:,} (sieve: {t_sieve:.4f}s)")
        print(f"Verified twin pairs: {len(verified_twins):,} (total: {t_total:.4f}s)")
        print(f"Largest pair certified in [2, {bound:,}]: {largest_pair}")

        benchmark_rows.append(
            f"BND-{bound},bounded,{bound},[2-{bound}],{sieve_depth},{t_sieve:.4f},{t_total:.4f},{stats.survivors},{len(verified_twins)},{largest_pair[0]}"
        )

        # Log candidate records to candidates.jsonl
        with open(candidates_file, "a", encoding="utf-8") as f:
            entry = {
                "experiment": f"bounded_{bound}",
                "interval": [2, bound],
                "verified_twins_count": len(verified_twins),
                "largest_twin_pair": largest_pair,
                "status": "EXHAUSTIVELY_CERTIFIED",
            }
            f.write(json.dumps(entry) + "\n")

        manifest["completed_searches"].append({
            "type": "bounded_exhaustive",
            "interval": [2, bound],
            "sieve_depth": sieve_depth,
            "runtime_seconds": round(t_total, 4),
            "total_twins_found": len(verified_twins),
            "largest_pair_certified": largest_pair,
            "status": "COMPLETE_AND_PROVEN"
        })

    # -------------------------------------------------------------
    # 2. Structured Search Sweeps (k * 2^n +/- 1)
    # -------------------------------------------------------------
    print("\n=======================================================")
    print("STAGE 2: STRUCTURED SEARCH SWEEPS ACROSS DIGIT SCALES")
    print("=======================================================")
    structured_targets = [
        # (n, k_max, target_digits_approx)
        (30, 10_000, 14),
        (50, 10_000, 20),
        (100, 10_000, 35),
        (250, 5_000, 80),
        (500, 2_000, 155),
        (1000, 1_000, 305),
        (2000, 500, 606),
    ]

    all_proven_certs = []

    for n, k_max, approx_digits in structured_targets:
        print(f"\n--- Structured Search: k * 2^{n} +/- 1 (k in [1, {k_max}], ~{approx_digits} digits) ---")
        opt_q = estimate_optimal_sieve_depth(n, k_max)
        t0 = time.time()
        sieve = StructuredTwinSieve(n, 1, k_max, opt_q, use_dual_sieve=True)
        survivors, stats = sieve.run_sieve()
        t_sieve = time.time() - t0

        two_pow_n = 1 << n
        proven_pairs = []
        largest_lower = None

        for k in survivors:
            center = k * two_pow_n
            p_plus = center + 1
            if not is_probable_prime(p_plus, [2]):
                continue
            is_proth, proth_w = proth_prove(k, n, p_plus)
            if is_proth:
                p_minus = center - 1
                is_llr, llr_p, _ = llr_prove(k, n, p_minus)
                if is_llr:
                    digits = len(str(p_plus))
                    cert = TwinPrimeCertificate(
                        pair_type=f"Structured: k * 2^{n} +/- 1",
                        p_minus_str=str(p_minus),
                        p_plus_str=str(p_plus),
                        digits=digits,
                        k=k,
                        n=n,
                        proth_witness=proth_w,
                        llr_witness=llr_p,
                        is_proven=True
                    )
                    cert_filename = PROOFS_DIR / f"cert_k{k}_n{n}.json"
                    cert.save_to_file(cert_filename)
                    proven_pairs.append((k, digits, cert))
                    all_proven_certs.append(cert)
                    largest_lower = str(p_minus)

        t_total = time.time() - t0
        print(f"Survivors: {stats.survivors:,}/{stats.total_candidates:,} (sieve: {t_sieve:.4f}s)")
        print(f"Proven Twin Prime Pairs: {len(proven_pairs)} (total time: {t_total:.4f}s)")
        for k, d, cert in proven_pairs:
            print(f"  -> PROVEN: {k} * 2^{n} +/- 1 ({d} digits)")

        benchmark_rows.append(
            f"STR-n{n},structured,n={n},k_max={k_max},{opt_q},{t_sieve:.4f},{t_total:.4f},{stats.survivors},{len(proven_pairs)},{largest_lower[:20] if largest_lower else 'None'}"
        )

        with open(candidates_file, "a", encoding="utf-8") as f:
            for k, d, cert in proven_pairs:
                f.write(json.dumps(cert.to_dict()) + "\n")

        manifest["completed_searches"].append({
            "type": "structured_heuristic",
            "formula": f"k * 2^{n} +/- 1",
            "n": n,
            "k_range": [1, k_max],
            "sieve_depth": opt_q,
            "runtime_seconds": round(t_total, 4),
            "proven_pairs_count": len(proven_pairs),
            "certificates_generated": [c.certificate_id for _, _, c in proven_pairs],
            "status": "COMPLETE_AND_PROVEN"
        })

    # -------------------------------------------------------------
    # 3. Controlled Ablation Study
    # -------------------------------------------------------------
    print("\n=======================================================")
    print("STAGE 3: CONTROLLED ABLATION STUDY")
    print("=======================================================")
    ablation_n = 200
    ablation_k_max = 20_000
    two_pow_n = 1 << ablation_n

    # Config 1: Baseline
    print("Running Configuration 1: Baseline (Static Q=5000, Single-residue)...")
    t0 = time.time()
    s1 = StructuredTwinSieve(ablation_n, 1, ablation_k_max, 5_000, use_dual_sieve=False)
    surv1, stat1 = s1.run_sieve()
    t_s1 = time.time() - t0
    c1 = 0
    for k in surv1:
        c = k * two_pow_n
        if is_probable_prime(c + 1, [2, 3]) and is_probable_prime(c - 1, [2, 3]):
            c1 += 1
    t_tot1 = time.time() - t0

    # Config 2: + Dual-Residue Sieve
    print("Running Configuration 2: + Dual-Residue Sieve...")
    t0 = time.time()
    s2 = StructuredTwinSieve(ablation_n, 1, ablation_k_max, 5_000, use_dual_sieve=True)
    surv2, stat2 = s2.run_sieve()
    t_s2 = time.time() - t0
    c2 = 0
    for k in surv2:
        c = k * two_pow_n
        if is_probable_prime(c + 1, [2, 3]) and is_probable_prime(c - 1, [2, 3]):
            c2 += 1
    t_tot2 = time.time() - t0

    # Config 3: + Adaptive Sieve Depth
    opt_q_abl = estimate_optimal_sieve_depth(ablation_n, ablation_k_max)
    print(f"Running Configuration 3: + Adaptive Sieve Depth (Q*={opt_q_abl})...")
    t0 = time.time()
    s3 = StructuredTwinSieve(ablation_n, 1, ablation_k_max, opt_q_abl, use_dual_sieve=True)
    surv3, stat3 = s3.run_sieve()
    t_s3 = time.time() - t0
    c3 = 0
    for k in surv3:
        c = k * two_pow_n
        if is_probable_prime(c + 1, [2, 3]) and is_probable_prime(c - 1, [2, 3]):
            c3 += 1
    t_tot3 = time.time() - t0

    # Config 4: Full CATS (+ Certificate-Cost-Aware Pipeline)
    print("Running Configuration 4: Full CATS (DR-Sieve + ASD + CCAP with proofs)...")
    t0 = time.time()
    s4 = StructuredTwinSieve(ablation_n, 1, ablation_k_max, opt_q_abl, use_dual_sieve=True)
    surv4, stat4 = s4.run_sieve()
    t_s4 = time.time() - t0
    c4 = 0
    for k in surv4:
        c = k * two_pow_n
        p_plus = c + 1
        if not is_probable_prime(p_plus, [2]):
            continue
        is_pr, _ = proth_prove(k, ablation_n, p_plus)
        if is_pr:
            is_ll, _, _ = llr_prove(k, ablation_n, c - 1)
            if is_ll:
                c4 += 1
    t_tot4 = time.time() - t0

    ablation_data = [
        {"config": "Baseline (Static Q=5k, Single Sieve)", "sieve_time": t_s1, "total_time": t_tot1, "survivors": stat1.survivors, "speedup": 1.0},
        {"config": "+ Dual-Residue Sieve (DR-Sieve)", "sieve_time": t_s2, "total_time": t_tot2, "survivors": stat2.survivors, "speedup": round(t_tot1 / max(1e-6, t_tot2), 2)},
        {"config": "+ Adaptive Sieve Depth (ASD)", "sieve_time": t_s3, "total_time": t_tot3, "survivors": stat3.survivors, "speedup": round(t_tot1 / max(1e-6, t_tot3), 2)},
        {"config": "Full CATS (+ CCAP Verified Proofs)", "sieve_time": t_s4, "total_time": t_tot4, "survivors": stat4.survivors, "speedup": round(t_tot1 / max(1e-6, t_tot4), 2)},
    ]

    manifest["ablation_study"] = {
        "parameters": {"n": ablation_n, "k_max": ablation_k_max},
        "results": ablation_data
    }

    # Save benchmarks
    with open(benchmarks_file, "w", encoding="utf-8") as f:
        f.write("\n".join(benchmark_rows) + "\n")
    print(f"\n[OK] Benchmarks saved to {benchmarks_file}")

    # Save manifest
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Coverage manifest saved to {manifest_file}")
    print(f"[OK] Total proven certificates generated in proofs/: {len(list(PROOFS_DIR.glob('*.json')))}")

if __name__ == "__main__":
    run_experiments()
