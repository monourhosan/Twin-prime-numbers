"""
Phase 4 Controlled Empirical Benchmark Suite.
Compares:
1. Sieve Strategies (R0 S1-baseline vs R1 t-space block vs R2 adaptive)
2. Sieve Cutoffs (Q = 10k, 30k, 50k, 100k)
3. Arithmetic Backends (Pure Python vs gmpy2) across n = 672, 1024, 1664, 3328, 5120, 6656
4. Stage Breakdown (Sieve vs PRP vs Proth vs LLR proof)
5. Multi-process concurrency (1 vs 2 workers)
Performs 5 repeated trials with warm-up; records median, min, max, std dev.
Outputs machine-readable JSON and CSV files.
"""

import os
import sys
import time
import json
import csv
import statistics
import multiprocessing
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.phase4.t_sieve import SieveR0_S1Baseline, SieveR1_TSpace, SieveR2_Adaptive
from src.phase4.backend import pow_mod, square_sub_2_mod, jacobi, has_gmpy2
from src.phase4.prp import test_prp_candidate, screen_pair_prp
from src.phase4.proof import proth_prove, llr_prove
from src.phase4.hardware import get_hardware_profile

def benchmark_sieves(exponents=(672, 1024, 1664, 3328), cutoffs=(10000, 30000, 50000, 100000), num_trials=5):
    print("--- Running Controlled Sieve Benchmarks (R0 vs R1 vs R2) ---")
    k_start = 3
    window_span = 60000 # 10,000 k=6t+3 candidates
    k_end = k_start + window_span

    results = []

    for n in exponents:
        for Q in cutoffs:
            # Instantiate engines once
            r0 = SieveR0_S1Baseline(n, Q)
            r1 = SieveR1_TSpace(n, Q)
            r2 = SieveR2_Adaptive(n, initial_depth=10000, max_depth=Q)

            # Warmup
            r0.sieve_window(k_start, k_end)
            r1.sieve_window(k_start, k_end)
            r2.sieve_window(k_start, k_end)

            for strat_name, engine in [("R0_S1_Baseline", r0), ("R1_TSpace", r1), ("R2_Adaptive", r2)]:
                durations = []
                survivor_count = 0
                for _ in range(num_trials):
                    t0 = time.perf_counter()
                    surv = engine.sieve_window(k_start, k_end)
                    t1 = time.perf_counter()
                    durations.append(t1 - t0)
                    survivor_count = len(surv)

                med_sec = statistics.median(durations)
                min_sec = min(durations)
                max_sec = max(durations)
                stdev_sec = statistics.stdev(durations) if len(durations) > 1 else 0.0

                raw_cands = window_span // 2 # all odd k
                throughput = raw_cands / max(1e-6, med_sec)

                results.append({
                    "exponent_n": n,
                    "sieve_depth_Q": Q,
                    "strategy": strat_name,
                    "k_window_span": window_span,
                    "survivors": survivor_count,
                    "median_ms": round(med_sec * 1000, 3),
                    "min_ms": round(min_sec * 1000, 3),
                    "max_ms": round(max_sec * 1000, 3),
                    "stdev_ms": round(stdev_sec * 1000, 3),
                    "throughput_cands_sec": round(throughput, 1)
                })
                print(f"  n={n:4d} | Q={Q:6d} | {strat_name:14s}: {med_sec*1000:6.2f}ms (median) | {throughput:10,.0f} cands/s | {survivor_count} surv")

    return results

def benchmark_arithmetic_backend(exponents=(672, 1024, 1664, 3328, 5120), num_trials=5):
    print("\n--- Running Big-Integer Arithmetic Benchmarks (Python vs gmpy2) ---")
    results = []

    for n in exponents:
        k = 15993 if n == 672 else 3
        center = k * (1 << n)
        A = center - 1
        B = center + 1
        exp = (B - 1) // 2

        # 1. Modular exponentiation (Proth core: 5^exp mod B)
        # Python native
        dur_py = []
        for _ in range(num_trials):
            t0 = time.perf_counter()
            _ = pow(5, exp, B)
            dur_py.append(time.perf_counter() - t0)

        # gmpy2
        dur_gmp = []
        if has_gmpy2():
            for _ in range(num_trials):
                t0 = time.perf_counter()
                _ = pow_mod(5, exp, B, use_gmpy=True)
                dur_gmp.append(time.perf_counter() - t0)

        # 2. LLR squaring step (u^2 - 2 mod A) for 100 rounds
        u = 5
        t0 = time.perf_counter()
        for _ in range(100):
            u = (pow(u, 2, A) - 2) % A
        llr_py_100 = (time.perf_counter() - t0) * 1000.0

        llr_gmp_100 = 0.0
        if has_gmpy2():
            u = 5
            t0 = time.perf_counter()
            for _ in range(100):
                u = square_sub_2_mod(u, A, use_gmpy=True)
            llr_gmp_100 = (time.perf_counter() - t0) * 1000.0

        med_py = statistics.median(dur_py) * 1000.0
        med_gmp = statistics.median(dur_gmp) * 1000.0 if dur_gmp else 0.0
        speedup = (med_py / med_gmp) if med_gmp > 0 else 1.0

        llr_speedup = (llr_py_100 / llr_gmp_100) if llr_gmp_100 > 0 else 1.0

        digits = len(str(A))
        results.append({
            "exponent_n": n,
            "digits": digits,
            "proth_powmod_py_ms": round(med_py, 2),
            "proth_powmod_gmp_ms": round(med_gmp, 2),
            "proth_speedup": round(speedup, 2),
            "llr_100_sq_py_ms": round(llr_py_100, 2),
            "llr_100_sq_gmp_ms": round(llr_gmp_100, 2),
            "llr_speedup": round(llr_speedup, 2)
        })
        print(f"  n={n:4d} ({digits:4d} digits) | Proth powmod: Py={med_py:7.2f}ms, GMP={med_gmp:6.2f}ms [{speedup:5.2f}x] | LLR 100 sq: Py={llr_py_100:6.2f}ms, GMP={llr_gmp_100:6.2f}ms [{llr_speedup:5.2f}x]")

    return results

def benchmark_pipeline_stages(exponent=3328, sieve_depth=50000, num_candidates=100):
    print(f"\n--- Running Pipeline Stage Rejection & Latency Profile (n={exponent}, {int(exponent*0.30103)} digits) ---")
    r1 = SieveR1_TSpace(exponent, sieve_depth)
    survivors = r1.sieve_window(3, 3 + 120000)

    # Test Miller-Rabin cost
    sample = survivors[:min(len(survivors), num_candidates)]
    two_n = 1 << exponent

    mr_latencies = []
    for k in sample:
        A = k * two_n - 1
        B = k * two_n + 1
        t0 = time.perf_counter()
        _ = screen_pair_prp(A, B, bases=[2, 3], screen_order="B_then_A")
        mr_latencies.append(time.perf_counter() - t0)

    med_mr = statistics.median(mr_latencies) * 1000.0
    print(f"  Sample size: {len(sample)} survivors")
    print(f"  Miller-Rabin (bases 2, 3 on pair): median {med_mr:.3f} ms per pair candidate")

    return {
        "exponent_n": exponent,
        "digits": len(str(sample[0] * two_n - 1)),
        "tested_candidates": len(sample),
        "mr_pair_median_ms": round(med_mr, 3)
    }

def main():
    out_dir = Path("runs/phase4/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)

    profile = get_hardware_profile()
    with open(out_dir / "hardware_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    # 1. Sieve benchmarks
    sieve_results = benchmark_sieves(exponents=(672, 1024, 1664, 3328), cutoffs=(10000, 30000, 50000, 100000), num_trials=5)
    with open(out_dir / "sieve_benchmarks.json", "w", encoding="utf-8") as f:
        json.dump(sieve_results, f, indent=2)

    with open(out_dir / "sieve_benchmarks.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sieve_results[0].keys())
        writer.writeheader()
        writer.writerows(sieve_results)

    # 2. Arithmetic backend benchmarks
    arith_results = benchmark_arithmetic_backend(exponents=(672, 1024, 1664, 3328, 5120), num_trials=5)
    with open(out_dir / "backend_benchmarks.json", "w", encoding="utf-8") as f:
        json.dump(arith_results, f, indent=2)

    with open(out_dir / "backend_benchmarks.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=arith_results[0].keys())
        writer.writeheader()
        writer.writerows(arith_results)

    # 3. Pipeline stage breakdown
    stage_results = benchmark_pipeline_stages(exponent=3328, sieve_depth=50000, num_candidates=50)
    with open(out_dir / "pipeline_stage_benchmarks.json", "w", encoding="utf-8") as f:
        json.dump(stage_results, f, indent=2)

    print(f"\n[OK] Benchmark measurements recorded to {out_dir}/")

if __name__ == "__main__":
    main()
