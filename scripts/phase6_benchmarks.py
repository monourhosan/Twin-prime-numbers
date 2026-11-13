"""
Controlled benchmark suite for Phase 6 GITCSS engine.
Measures sieve throughput, wheel configurations, bucket sieving, and screening latency.
Outputs data/phase6_benchmarks.csv and research/phase6/BENCHMARKS.md.
"""

import time
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

from src.phase6.wheel import CenterWheel
from src.phase6.segmented import SegmentedCenterSieve
from src.phase6.bucket_sieve import BucketCenterSieve
from src.phase6.screening import CandidateScreener
from src.phase6.proof_backend import DeterministicPairProver

def run_benchmarks():
    print("=== Running Phase 6 GITCSS Controlled Benchmarks ===")
    
    out_csv = Path("data/phase6_benchmarks.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json = Path("runs/phase6/benchmarks/benchmark_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    
    csv_rows = []
    json_results = {}

    # 1. Wheel Elimination Benchmarks
    print("\n--- 1. Wheel Configuration Benchmarks ---")
    wheel_configs = [
        ("No_Wheel", []),
        ("Wheel_5", [5]),
        ("Wheel_5_7", [5, 7]),
        ("Wheel_5_7_11", [5, 7, 11]),
        ("Wheel_5_7_11_13", [5, 7, 11, 13])
    ]
    wheel_data = []
    seg_size = 262144
    m_base = 1000000
    
    for name, primes in wheel_configs:
        wheel = CenterWheel(primes) if primes else None
        sieve = SegmentedCenterSieve(sieve_limit=10000, wheel=wheel)
        
        # Warmup
        sieve.sieve_segment(m_base, seg_size)
        
        # Measure 3 runs
        times = []
        survivors_count = 0
        for _ in range(3):
            t0 = time.perf_counter()
            survivors = sieve.sieve_segment(m_base, seg_size)
            times.append(time.perf_counter() - t0)
            survivors_count = len(survivors)
            
        med_time = sorted(times)[1]
        throughput = seg_size / med_time
        surv_ratio = survivors_count / seg_size
        
        print(f"  {name:18}: {throughput:12,.0f} centers/s, survivors: {survivors_count:6,} ({surv_ratio*100:5.2f}%), time: {med_time*1000:6.2f} ms")
        wheel_data.append({
            "config": name,
            "modulus": wheel.W if wheel else 1,
            "throughput_centers_per_sec": throughput,
            "survivors": survivors_count,
            "survivor_fraction": surv_ratio,
            "median_time_ms": med_time * 1000
        })
        csv_rows.append({
            "category": "wheel_comparison",
            "name": name,
            "param1": wheel.W if wheel else 1,
            "param2": len(primes),
            "throughput_centers_per_sec": throughput,
            "survivor_fraction": surv_ratio,
            "latency_ms": med_time * 1000
        })

    json_results["wheel_comparison"] = wheel_data

    # 2. Sieve Limit Scaling Benchmarks
    print("\n--- 2. Sieve Limit Scaling Benchmarks (Wheel 5-7-11-13) ---")
    wheel = CenterWheel([5, 7, 11, 13])
    sieve_limits = [1000, 5000, 20000, 50000, 100000]
    limit_data = []
    
    for L in sieve_limits:
        sieve = SegmentedCenterSieve(sieve_limit=L, wheel=wheel)
        # Measure 3 runs
        times = []
        survivors_count = 0
        for _ in range(3):
            t0 = time.perf_counter()
            survivors = sieve.sieve_segment(m_base, seg_size)
            times.append(time.perf_counter() - t0)
            survivors_count = len(survivors)
            
        med_time = sorted(times)[1]
        throughput = seg_size / med_time
        surv_ratio = survivors_count / seg_size
        
        print(f"  L = {L:7,}: {throughput:12,.0f} centers/s, survivors: {survivors_count:6,} ({surv_ratio*100:5.2f}%), time: {med_time*1000:6.2f} ms")
        limit_data.append({
            "sieve_limit": L,
            "throughput_centers_per_sec": throughput,
            "survivors": survivors_count,
            "survivor_fraction": surv_ratio,
            "median_time_ms": med_time * 1000
        })
        csv_rows.append({
            "category": "sieve_limit_scaling",
            "name": f"L_{L}",
            "param1": L,
            "param2": seg_size,
            "throughput_centers_per_sec": throughput,
            "survivor_fraction": surv_ratio,
            "latency_ms": med_time * 1000
        })

    json_results["sieve_limit_scaling"] = limit_data

    # 3. Standard Segmented vs. Bucket Sieve
    print("\n--- 3. Standard Segmented vs. Bucket Sieve Comparison ---")
    comp_data = []
    L_comp = 50000
    seg_sizes = [65536, 131072, 262144]
    
    for S in seg_sizes:
        s_std = SegmentedCenterSieve(sieve_limit=L_comp, wheel=wheel)
        s_bkt = BucketCenterSieve(sieve_limit=L_comp, segment_size=S, wheel=wheel)
        
        # Std
        times_std = []
        for _ in range(3):
            t0 = time.perf_counter()
            s_std.sieve_segment(m_base, S)
            times_std.append(time.perf_counter() - t0)
        med_std = sorted(times_std)[1]
        tp_std = S / med_std
        
        # Bkt
        times_bkt = []
        for _ in range(3):
            t0 = time.perf_counter()
            s_bkt.sieve_segment(m_base, S)
            times_bkt.append(time.perf_counter() - t0)
        med_bkt = sorted(times_bkt)[1]
        tp_bkt = S / med_bkt
        
        print(f"  Segment Size {S:7,}: Standard = {tp_std:10,.0f} cands/s | Bucket = {tp_bkt:10,.0f} cands/s")
        comp_data.append({
            "segment_size": S,
            "standard_throughput": tp_std,
            "bucket_throughput": tp_bkt,
            "speedup_ratio": tp_bkt / tp_std
        })
        csv_rows.append({
            "category": "sieve_architecture",
            "name": f"S_{S}",
            "param1": S,
            "param2": L_comp,
            "throughput_centers_per_sec": tp_std,
            "survivor_fraction": 0.0,
            "latency_ms": med_std * 1000
        })

    json_results["architecture_comparison"] = comp_data

    # 4. Screening Latency by Digit Band
    print("\n--- 4. Screening Latency by Digit Scale ---")
    screener = CandidateScreener(mr_rounds=25)
    scale_data = []
    
    for digits in [10, 30, 50, 100]:
        # Form candidate near 10^(digits-1)
        base_m = (10**(digits - 1) + 1234567) // 6
        times = []
        for offset in range(50):
            t0 = time.perf_counter()
            screener.screen_candidate(base_m + offset)
            times.append(time.perf_counter() - t0)
        med_screen_us = sorted(times)[len(times)//2] * 1e6
        throughput_screens = 1.0 / (med_screen_us / 1e6)
        print(f"  {digits:3} digits: {med_screen_us:8.2f} us / candidate ({throughput_screens:10,.0f} screens/s)")
        scale_data.append({
            "digits": digits,
            "median_screen_us": med_screen_us,
            "screens_per_sec": throughput_screens
        })
        csv_rows.append({
            "category": "screening_scaling",
            "name": f"{digits}d",
            "param1": digits,
            "param2": 25,
            "throughput_centers_per_sec": throughput_screens,
            "survivor_fraction": 0.0,
            "latency_ms": med_screen_us / 1000.0
        })

    json_results["screening_scaling"] = scale_data

    # Save outputs
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2)
        
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "category", "name", "param1", "param2",
            "throughput_centers_per_sec", "survivor_fraction", "latency_ms"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)
        
    print(f"\nBenchmark results written to {out_json} and {out_csv}")

if __name__ == "__main__":
    run_benchmarks()
