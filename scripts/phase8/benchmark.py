"""
PAQCS Performance Benchmark Suite (Phase 8).
Measures anchor construction, sieve throughput, PRP screening, and prover speeds.
"""
import time
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from src.phase8.paqcs_anchor import PrimorialAnchor
from src.phase8.paqcs_sieve import prepare_sieve_plan, SegmentedPAQCSSieve
from src.phase8.paqcs_screening import screen_candidate_single


def run_benchmark():
    print("=" * 60)
    print("PAQCS Performance Benchmark Suite (Phase 8)")
    print("=" * 60)

    # 1. Anchor benchmark
    t0 = time.perf_counter()
    anchor = PrimorialAnchor(y=1780)
    t_anchor = time.perf_counter() - t0
    print(f"Anchor S_1780 construction: {t_anchor*1000:.2f} ms ({anchor.digits} digits, {len(anchor.primes)} primes)")

    # 2. Sieve plan benchmark
    t0 = time.perf_counter()
    plan = prepare_sieve_plan(anchor.S_y, anchor.y, Q_bound=200000, h=3)
    t_plan = time.perf_counter() - t0
    print(f"Sieve plan preparation (Q=200k): {t_plan*1000:.2f} ms ({len(plan)} primes)")

    # 3. Sieve execution benchmark
    t_min = anchor.compute_min_t(target_digits=1511, h=3)
    sieve = SegmentedPAQCSSieve(plan)
    N_cand = 50000
    t0 = time.perf_counter()
    survivors = sieve.sieve_segment(t_min, t_min + 2 * (N_cand - 1))
    t_sieve = time.perf_counter() - t0
    rate = N_cand / t_sieve
    print(f"Sieve execution ({N_cand} candidates): {t_sieve*1000:.2f} ms ({rate:.1f} cand/s)")
    print(f"Survivors: {len(survivors)} ({len(survivors)/N_cand*100:.2f}%)")

    # 4. Screening throughput benchmark
    sample = survivors[:200]
    t0 = time.perf_counter()
    for s_t in sample:
        screen_candidate_single(anchor.S_y, s_t, h=3)
    t_screen = time.perf_counter() - t0
    screen_rate = len(sample) / t_screen
    print(f"Screening throughput (single-core): {screen_rate:.1f} cand/s ({t_screen/len(sample)*1000:.2f} ms/cand)")
    print(f"Estimated 6-core throughput: {screen_rate * 6:.1f} cand/s")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
