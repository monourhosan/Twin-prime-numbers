"""
Comprehensive Benchmark Suite for Phase 8 ADES-8.
Executes:
1. Kernel Comparison: Variant A (HDC-7 1D) vs Variant B (CPU Ref 2D) vs Variant C (ADES-8 Recurrence 2D)
2. Primorial Multiplier Parameter Exploration (R = 13, 31, 47, 97)
3. Tile Sieve Scaling: Height (H = 4, 8, 16, 32) and Depth (S = 20k, 50k, 100k, 250k)
4. End-to-End Pipeline Latency: Sieving, Fermat-A, Fermat-B, Miller-Rabin, Proth, LLR
Outputs raw CSV to research/phase8/benchmarks_raw.csv and formats research/phase8/BENCHMARK_REPORT.md
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time
import csv
import statistics
import math
from typing import List, Dict, Any, Tuple

from src.phase8.math import (
    get_primorial_multiplier,
    get_small_primes,
    solve_modular_roots,
    compute_candidate_pair,
    exact_digit_t_bounds
)
from src.phase8.sieve_2d import ADES8TwoDimSieve
from src.phase8.screening import CandidateScreener
from src.phase8.prover import ADES8Prover


def run_kernel_benchmarks(reps: int = 3) -> List[Dict[str, Any]]:
    """Runs kernel microbenchmarks comparing Variant A, B, and C."""
    print("=" * 60)
    print("Executing Kernel Comparison: Variant A vs B vs C")
    print("=" * 60)

    n_start = 5000
    n_height = 16
    t_start = 20000
    t_width = 10000
    sieve_limit = 50000
    R = 13
    total_candidates = n_height * t_width

    sieve = ADES8TwoDimSieve(R=R, sieve_limit=sieve_limit)

    results = []

    # 1. Variant A: HDC-7 1D Baseline (row by row)
    times_A = []
    surv_A_count = 0
    for r in range(reps):
        t0 = time.perf_counter()
        survivors_A = []
        for row in range(n_height):
            surv_row, _ = sieve.sieve_row_baseline_1d(n_start + row, t_start, t_width)
            survivors_A.extend(surv_row)
        elapsed = time.perf_counter() - t0
        times_A.append(elapsed)
        surv_A_count = len(survivors_A)

    med_A = statistics.median(times_A)
    rate_A = total_candidates / med_A
    print(f"Variant A (HDC-7 1D Baseline):  {med_A*1000:.2f} ms ({rate_A:,.0f} cand/s) | Survivors: {surv_A_count}")
    results.append({
        "category": "kernel_comparison",
        "variant": "Variant A (HDC-7 1D Baseline)",
        "median_sec": med_A,
        "throughput_cand_per_sec": rate_A,
        "survivors": surv_A_count,
        "notes": "Independent 1D modular roots"
    })

    # 2. Variant B: CPU Reference 2D (no recurrence)
    times_B = []
    surv_B_count = 0
    for r in range(reps):
        t0 = time.perf_counter()
        surv_B, _ = sieve.sieve_tile_reference_2d(n_start, n_height, t_start, t_width)
        elapsed = time.perf_counter() - t0
        times_B.append(elapsed)
        surv_B_count = len(surv_B)

    med_B = statistics.median(times_B)
    rate_B = total_candidates / med_B
    print(f"Variant B (CPU Reference 2D):   {med_B*1000:.2f} ms ({rate_B:,.0f} cand/s) | Survivors: {surv_B_count}")
    results.append({
        "category": "kernel_comparison",
        "variant": "Variant B (CPU Reference 2D)",
        "median_sec": med_B,
        "throughput_cand_per_sec": rate_B,
        "survivors": surv_B_count,
        "notes": "Direct 2D modular roots"
    })

    # 3. Variant C: ADES-8 Optimized 2D (Recurrence)
    times_C = []
    surv_C_count = 0
    for r in range(reps):
        t0 = time.perf_counter()
        surv_C, m_c = sieve.sieve_tile_recurrence(n_start, n_height, t_start, t_width)
        elapsed = time.perf_counter() - t0
        times_C.append(elapsed)
        surv_C_count = len(surv_C)

    med_C = statistics.median(times_C)
    rate_C = total_candidates / med_C
    print(f"Variant C (ADES-8 Recurrence):  {med_C*1000:.2f} ms ({rate_C:,.0f} cand/s) | Survivors: {surv_C_count}")
    results.append({
        "category": "kernel_comparison",
        "variant": "Variant C (ADES-8 Recurrence 2D)",
        "median_sec": med_C,
        "throughput_cand_per_sec": rate_C,
        "survivors": surv_C_count,
        "notes": "O(1) modular root recurrence across rows"
    })

    assert surv_A_count == surv_B_count == surv_C_count, "Survivor count mismatch across variants!"
    speedup = med_B / med_C
    print(f"-> Speedup Variant C vs Variant B: {speedup:.2f}x")
    return results


def run_param_benchmarks() -> List[Dict[str, Any]]:
    """Benchmarks primorial cutoffs R = 13, 31, 47, 97."""
    print("-" * 60)
    print("Executing Primorial Multiplier Scaling (R = 13, 31, 47, 97)")
    print("-" * 60)

    results = []
    n_start = 5000
    n_height = 8
    t_start = 10000
    t_width = 10000
    total_candidates = n_height * t_width

    for R in (13, 31, 47, 97):
        M = get_primorial_multiplier(R)
        sieve = ADES8TwoDimSieve(R=R, sieve_limit=50000)
        t0 = time.perf_counter()
        surv, meta = sieve.sieve_tile_recurrence(n_start, n_height, t_start, t_width)
        elapsed = time.perf_counter() - t0
        rate = total_candidates / elapsed

        # Compute G(R)
        primes_gain = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        G = 1.0
        for p in primes_gain:
            if 5 <= p <= R:
                G *= (p / (p - 2))

        print(f"R = {R:2d} | M bits: {M.bit_length():4d} | G(R): {G:.4f} | Sieve Time: {elapsed*1000:.2f} ms | Survivors: {len(surv)}")
        results.append({
            "category": "primorial_scaling",
            "R": R,
            "M_bits": M.bit_length(),
            "G_R": G,
            "elapsed_sec": elapsed,
            "throughput_cand_per_sec": rate,
            "survivors": len(surv)
        })

    return results


def run_scaling_benchmarks() -> List[Dict[str, Any]]:
    """Benchmarks tile height scaling and sieve limit scaling."""
    print("-" * 60)
    print("Executing Sieve Scaling: Height H and Depth S")
    print("-" * 60)

    results = []
    # 1. Height scaling H in [4, 8, 16, 32]
    sieve = ADES8TwoDimSieve(R=13, sieve_limit=50000)
    t_width = 10000
    for H in (4, 8, 16, 32):
        t0 = time.perf_counter()
        surv, _ = sieve.sieve_tile_recurrence(5000, H, 20000, t_width)
        elapsed = time.perf_counter() - t0
        cands = H * t_width
        rate = cands / elapsed
        print(f"Tile Height H = {H:2d} (Cands: {cands:6d}) | Time: {elapsed*1000:.2f} ms | Throughput: {rate:,.0f} cands/s")
        results.append({
            "category": "height_scaling",
            "H": H,
            "candidates": cands,
            "elapsed_sec": elapsed,
            "throughput": rate
        })

    # 2. Depth scaling S in [20k, 50k, 100k, 250k]
    for S in (20000, 50000, 100000, 250000):
        s = ADES8TwoDimSieve(R=13, sieve_limit=S)
        t0 = time.perf_counter()
        surv, _ = s.sieve_tile_recurrence(5000, 8, 20000, 10000)
        elapsed = time.perf_counter() - t0
        cands = 8 * 10000
        rate = cands / elapsed
        surv_frac = len(surv) / cands
        print(f"Sieve Limit S = {S:6d} | Time: {elapsed*1000:.2f} ms | Survivors: {len(surv)} ({surv_frac*100:.2f}%)")
        results.append({
            "category": "depth_scaling",
            "S": S,
            "elapsed_sec": elapsed,
            "survivors": len(surv),
            "survivor_fraction": surv_frac
        })

    return results


def run_pipeline_benchmarks() -> List[Dict[str, Any]]:
    """Measures latency of each pipeline stage on 1,515-digit candidate."""
    print("-" * 60)
    print("Executing End-to-End Pipeline Stage Latencies (D = 1,515 digits)")
    print("-" * 60)

    results = []
    screener = CandidateScreener(mr_rounds=25)
    prover = ADES8Prover()

    M = get_primorial_multiplier(13)
    n = 5000
    t = 25000
    k, C, A, Bprime = compute_candidate_pair(M, t, n)

    # Stage 1: Fermat Base-2 (Composite candidate)
    t0 = time.perf_counter()
    reps = 100
    for _ in range(reps):
        screener.test_fermat_base2(A)
    f_time = (time.perf_counter() - t0) / reps
    print(f"1. Fast Base-2 Fermat Test (per candidate): {f_time*1000:.3f} ms ({1/f_time:.1f} tests/s)")
    results.append({"category": "stage_latency", "stage": "fermat_base2", "per_op_sec": f_time})

    # Stage 2: Miller-Rabin 25 rounds
    t0 = time.perf_counter()
    reps_mr = 20
    for _ in range(reps_mr):
        screener.test_miller_rabin(A, rounds=25)
    mr_time = (time.perf_counter() - t0) / reps_mr
    print(f"2. Miller-Rabin 25 Rounds:                  {mr_time*1000:.3f} ms ({1/mr_time:.1f} tests/s)")
    results.append({"category": "stage_latency", "stage": "miller_rabin_25", "per_op_sec": mr_time})

    # Stage 3: Proth Proof exponentiation
    t0 = time.perf_counter()
    # Exp = (B - 1) // 2
    ok_p, w, msg, p_time = prover.prove_proth_upper(k, n, Bprime)
    print(f"3. Proth Proof Exponentiation (B'=k*2^n+1): {p_time*1000:.3f} ms")
    results.append({"category": "stage_latency", "stage": "proth_proof", "per_op_sec": p_time})

    # Stage 4: LLR Squaring Round Latency
    # 5,000 squarings on 1515-digit integer
    import gmpy2
    u_mpz = gmpy2.mpz(15)
    A_mpz = gmpy2.mpz(A)
    t0 = time.perf_counter()
    for _ in range(1000):
        u_mpz = (gmpy2.square(u_mpz) - 2) % A_mpz
    llr_1k_time = time.perf_counter() - t0
    llr_total_est = (llr_1k_time / 1000) * (n - 2)
    print(f"4. LLR Recurrence ({n-2} squarings estimated): {llr_total_est:.3f} s ({llr_1k_time*1000:.2f} ms per 1,000 rounds)")
    results.append({"category": "stage_latency", "stage": "llr_proof_full", "per_op_sec": llr_total_est})

    return results


def main():
    os.makedirs("research/phase8", exist_ok=True)
    csv_path = "research/phase8/benchmarks_raw.csv"

    all_data = []
    kernel_data = run_kernel_benchmarks()
    param_data = run_param_benchmarks()
    scaling_data = run_scaling_benchmarks()
    pipe_data = run_pipeline_benchmarks()

    all_data.extend(kernel_data)
    all_data.extend(param_data)
    all_data.extend(scaling_data)
    all_data.extend(pipe_data)

    # Write raw CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "variant", "R", "H", "S", "M_bits", "G_R", "stage", "median_sec", "elapsed_sec", "per_op_sec", "throughput_cand_per_sec", "throughput", "candidates", "survivors", "survivor_fraction", "notes"])
        writer.writeheader()
        for row in all_data:
            writer.writerow(row)

    print("=" * 60)
    print(f"Benchmarks completed successfully! Raw data written to {csv_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
