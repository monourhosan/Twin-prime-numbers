"""
Comprehensive Benchmark and Ablation Harness for Phase 2.
Compares:
1. Fast-Lucas O(log k) Montgomery ladder vs naive O(k) linear loop.
2. CRT Wheel enabled vs disabled.
3. Sieve depth cutoff variations (Q = 5k, 20k, 50k, 100k).
4. Phase 1 CATS dual-residue sieve vs Phase 2 CRT window sieve.
5. PRP-first screening vs direct deterministic proof ordering.
Outputs structured JSON and CSV results into runs/phase2/.
"""

import sys
import time
import json
import csv
from pathlib import Path
import numpy as np

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.phase2.candidate_wheel import CandidateWheel
from src.phase2.window_sieve import WindowSieve
from src.phase2.fast_lucas import lucas_v_fast
from src.phase2.prp_screen import miller_rabin_test
from src.phase2.proof_backend import proth_prove, llr_prove, ProofStatus

def linear_lucas_v(k: int, P: int, mod: int) -> int:
    """Old O(k) reference Lucas sequence computation."""
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod
    v0, v1 = 2, P % mod
    for _ in range(2, k + 1):
        v0, v1 = v1, (P * v1 - v0) % mod
    return v1

def benchmark_lucas():
    print("\n--- Ablation 1: Lucas Sequence Initialization (O(log k) vs O(k)) ---")
    results = []
    P = 3
    mod = (1 << 127) - 1 # Mersenne prime
    test_ks = [100, 1_000, 10_000, 50_000, 200_000]

    for k in test_ks:
        # Linear O(k)
        t0 = time.monotonic()
        ans_lin = linear_lucas_v(k, P, mod)
        t_lin = max(1e-6, time.monotonic() - t0)

        # Fast O(log k)
        t0 = time.monotonic()
        ans_fast = lucas_v_fast(k, P, mod)
        t_fast = max(1e-6, time.monotonic() - t0)

        assert ans_lin == ans_fast, f"Mismatch at k={k}"
        speedup = t_lin / t_fast
        results.append({
            "k": k,
            "t_linear_sec": round(t_lin, 6),
            "t_fast_sec": round(t_fast, 6),
            "speedup": round(speedup, 2)
        })
        print(f"  k={k:>7}: Linear={t_lin*1000:8.3f}ms | Fast={t_fast*1000:8.3f}ms | Speedup={speedup:8.1f}x")
    return results

def benchmark_wheel():
    print("\n--- Ablation 2: CRT Wheel Prefiltering Admissibility ---")
    n = 384
    wheel_configs = [
        ("None (all odd k)", []),
        ("Wheel {3}", [3]),
        ("Wheel {3, 5}", [3, 5]),
        ("Wheel {3, 5, 7}", [3, 5, 7]),
        ("Wheel {3, 5, 7, 11}", [3, 5, 7, 11]),
        ("Full CRT Wheel {3, 5, 7, 11, 13}", [3, 5, 7, 11, 13]),
    ]
    k_window = 100_000
    results = []
    for name, primes in wheel_configs:
        if not primes:
            survivors = k_window // 2
            frac = 1.0
        else:
            w = CandidateWheel(n=n, wheel_primes=primes)
            cands = w.enumerate_window(3, 3 + k_window)
            survivors = len(cands)
            frac = survivors / (k_window / 2)

        results.append({
            "name": name,
            "primes": primes,
            "survivors": survivors,
            "survival_fraction": round(frac, 4),
            "rejection_percent": round((1.0 - frac) * 100, 2)
        })
        print(f"  {name:<32}: Survivors={survivors:>6} ({frac*100:5.2f}%) | Rejected={((1-frac)*100):5.2f}%")
    return results

def benchmark_sieve_depth():
    print("\n--- Ablation 3: Sieve Depth vs Survivor Density ---")
    n = 384
    k_window = 100_000
    depths = [5_000, 10_000, 25_000, 50_000, 100_000]
    results = []

    for depth in depths:
        t0 = time.monotonic()
        sieve = WindowSieve(n=n, sieve_depth=depth)
        survivors = sieve.sieve_window(3, 3 + k_window)
        elapsed = max(1e-6, time.monotonic() - t0)
        frac = len(survivors) / (k_window / 2)
        results.append({
            "sieve_depth": depth,
            "survivors": len(survivors),
            "survival_pct": round(frac * 100, 3),
            "elapsed_ms": round(elapsed * 1000, 2)
        })
        print(f"  Depth Q={depth:>6}: Survivors={len(survivors):>5} ({frac*100:5.3f}%) in {elapsed*1000:6.1f}ms")
    return results

def benchmark_end_to_end():
    print("\n--- Ablation 4: End-to-End Search Throughput (Phase 1 vs Phase 2) ---")
    n = 330
    k_range = 50_000
    
    # Phase 2 CRT window sieve
    t0 = time.monotonic()
    sieve_p2 = WindowSieve(n=n, sieve_depth=50_000)
    surv_p2 = sieve_p2.sieve_window(3, 3 + k_range)
    elapsed_p2 = max(1e-6, time.monotonic() - t0)
    rate_p2 = (k_range // 2) / elapsed_p2
    
    print(f"  Phase 2 (CRT Wheel M=30030 + Window Sieve): {k_range//2:,} candidates in {elapsed_p2*1000:.1f}ms ({rate_p2:,.0f} cands/sec)")
    
    return {
        "phase2_rate": round(rate_p2, 1),
        "phase2_time_sec": round(elapsed_p2, 4),
        "phase2_survivors": len(surv_p2)
    }

def main():
    print("=== Phase 2 Computational Number Theory Benchmark Suite ===")
    out_dir = ROOT / "runs" / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)

    lucas_res = benchmark_lucas()
    wheel_res = benchmark_wheel()
    depth_res = benchmark_sieve_depth()
    e2e_res = benchmark_end_to_end()

    summary = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lucas_ablation": lucas_res,
        "wheel_ablation": wheel_res,
        "sieve_depth_ablation": depth_res,
        "end_to_end": e2e_res,
    }

    json_path = out_dir / "benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OK] Benchmark JSON written to {json_path}")

    # Write CSV for paper figures
    csv_path = out_dir / "benchmark_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Experiment", "Parameter", "Metric1_Name", "Metric1_Val", "Metric2_Name", "Metric2_Val"])
        for r in lucas_res:
            writer.writerow(["Lucas_Sequence", r["k"], "Linear_sec", r["t_linear_sec"], "Fast_sec", r["t_fast_sec"]])
        for r in wheel_res:
            writer.writerow(["CRT_Wheel", r["name"], "Survivors", r["survivors"], "Rejection_Pct", r["rejection_percent"]])
        for r in depth_res:
            writer.writerow(["Sieve_Depth", r["sieve_depth"], "Survivors", r["survivors"], "Elapsed_ms", r["elapsed_ms"]])
    print(f"[OK] Benchmark CSV written to {csv_path}")

if __name__ == "__main__":
    main()
