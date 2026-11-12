"""
Comprehensive Empirical Benchmark Harness for Phase 3 (HDRSS).
Directly compares:
- S0: Phase 2 Baseline (Scalar Window Sieve)
- S1: Phase 3 Strategy S1 (Vectorized Segmented Bitset Sieve)
- S2: Phase 3 Strategy S2 (Hybrid Strided + Sparse Modular Sieve)
Across multiple exponents n in {672, 1024, 1664} and sieve depths.
"""

import sys
import time
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.phase2.window_sieve import WindowSieve as S0Sieve
from src.phase3.segmented_sieve import SegmentedSieveS1 as S1Sieve
from src.phase3.hybrid_sieve import HybridSieveS2 as S2Sieve

def run_benchmarks():
    print("=================================================================")
    print("=== Phase 3 HDRSS Computational Sieve & Engine Benchmark Suite ===")
    print("=================================================================\n")

    out_dir = ROOT / "runs" / "phase3" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)

    exponents = [672, 1024, 1664]
    depths = [10_000, 50_000, 100_000]
    k_window = 100_000
    k_start = 3

    records = []

    for n in exponents:
        digits = int(n * 0.30103)
        print(f"\n--- Exponent n={n} (~{digits} decimal digits) | Window: [k={k_start}, {k_start + k_window}) ---")

        for Q in depths:
            # 1. Strategy S0 (Phase 2 Baseline)
            t0 = time.monotonic()
            s0 = S0Sieve(n=n, sieve_depth=Q)
            surv0 = s0.sieve_window(k_start, k_start + k_window)
            t_s0 = max(1e-6, time.monotonic() - t0)

            # 2. Strategy S1 (Vectorized Segmented Bitset)
            t0 = time.monotonic()
            s1 = S1Sieve(n=n, sieve_depth=Q)
            surv1 = s1.sieve_window(k_start, k_start + k_window)
            t_s1 = max(1e-6, time.monotonic() - t0)

            # 3. Strategy S2 (Hybrid Strided + Sparse)
            t0 = time.monotonic()
            s2 = S2Sieve(n=n, sieve_depth=Q, stride_cutoff=min(10_000, Q))
            surv2 = s2.sieve_window(k_start, k_start + k_window)
            t_s2 = max(1e-6, time.monotonic() - t0)

            # Verification of mathematical equivalence
            assert sorted(surv1) == sorted(surv2), f"S1 and S2 survivor sets must be identical for n={n}, Q={Q}"

            speedup_s1 = t_s0 / t_s1
            speedup_s2 = t_s0 / t_s2
            raw_cands = k_window // 2
            rate_s2 = raw_cands / t_s2

            print(f"  Cutoff Q={Q:>6}: S0={t_s0*1000:6.1f}ms | S1={t_s1*1000:6.1f}ms ({speedup_s1:4.1f}x) | S2={t_s2*1000:6.1f}ms ({speedup_s2:4.1f}x) | Survivors={len(surv2):>4} ({rate_s2:,.0f} k/s)")

            records.append({
                "n": n,
                "target_digits": digits,
                "sieve_depth": Q,
                "k_window": k_window,
                "survivors": len(surv2),
                "t_s0_ms": round(t_s0 * 1000, 2),
                "t_s1_ms": round(t_s1 * 1000, 2),
                "t_s2_ms": round(t_s2 * 1000, 2),
                "speedup_s1": round(speedup_s1, 2),
                "speedup_s2": round(speedup_s2, 2),
                "throughput_s2_cands_sec": round(rate_s2, 1)
            })

    # Save JSON
    json_path = out_dir / "benchmark_comparison.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # Save CSV
    csv_path = out_dir / "benchmark_comparison.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "digits", "sieve_depth", "window", "survivors", "t_s0_ms", "t_s1_ms", "t_s2_ms", "speedup_s1", "speedup_s2", "throughput_s2"])
        for r in records:
            writer.writerow([r["n"], r["target_digits"], r["sieve_depth"], r["k_window"], r["survivors"], r["t_s0_ms"], r["t_s1_ms"], r["t_s2_ms"], r["speedup_s1"], r["speedup_s2"], r["throughput_s2_cands_sec"]])

    print(f"\n[OK] Benchmark JSON written to {json_path}")
    print(f"[OK] Benchmark CSV written to {csv_path}")
    return records

if __name__ == "__main__":
    run_benchmarks()
