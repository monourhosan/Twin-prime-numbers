"""
CLI operations for Phase 7 High-Density Certificate-Aware Search (HDC-7).
Subcommands:
- plan: Inspect parameter boundaries, digit scaling, and expected yield.
- benchmark: Run comparative benchmark across primorial bounds B and screening orders.
- search: Execute resumable discovery campaign.
- verify: Execute strict standalone independent verification.
- status: Display campaign progress and ledger state.
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List

from src.phase7.math import (
    get_primorial_multiplier,
    exact_digit_t_bounds,
    compute_candidate_pair
)
from src.phase7.sieve import CompactTSieve
from src.phase7.screening import HDCScreener
from src.phase7.prover import HDCProver
from src.phase7.campaign import HDCCampaign
from scripts.phase7_independent_verify import verify_certificate_v7


def cmd_plan(args: argparse.Namespace) -> None:
    """Computes exact digit bounds, index ranges, and theoretical density."""
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    D = cfg.get("min_digits", 1510)
    B = cfg.get("B_primorial", 13)
    n = cfg["exponent"]
    MB = get_primorial_multiplier(B)

    k_min, k_max, t_min, t_max = exact_digit_t_bounds(D, MB, n)
    span = max(0, t_max - t_min + 1)

    print("=" * 60)
    print(f"HDC-7 CAMPAIGN PLAN: {cfg.get('campaign_id')}")
    print("=" * 60)
    print(f"Target digits per member: {D}")
    print(f"Primorial bound B:        {B}")
    print(f"Multiplier M_B:           {MB} ({MB.bit_length()} bits)")
    print(f"Exponent n:               {n} (2^n has {len(str(1 << n))} digits)")
    print(f"Valid k interval:         [{k_min}, {k_max}]")
    print(f"Valid compact t interval: [{t_min}, {t_max}]")
    print(f"Total eligible centers:   {span}")
    print(f"k < 2^n condition:        {k_max < (1 << n)}")

    if span > 0:
        _, C_low, A_low, B_low = compute_candidate_pair(MB, t_min, n)
        _, C_high, A_high, B_high = compute_candidate_pair(MB, t_max, n)
        print(f"Boundary digits at t_min: len(A)={len(str(A_low))}, len(B)={len(str(B_low))}")
        print(f"Boundary digits at t_max: len(A)={len(str(A_high))}, len(B)={len(str(B_high))}")
    print("=" * 60)


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Runs controlled empirical benchmarks across primorial cutoffs B."""
    print("=" * 60)
    print("HDC-7 EMPIRICAL BENCHMARKS")
    print("=" * 60)

    D = args.digits
    test_bounds = [3, 13, 31, 47]
    sieve_depth = args.sieve_depth
    test_span = args.span

    results = []
    for B in test_bounds:
        MB = get_primorial_multiplier(B)
        # Select optimal n for D digits so that t interval contains test_span centers
        target_k = 10000 * MB
        target_2n = (10**(D - 1)) // target_k
        n = int(math_log2(target_2n))
        k_min, k_max, t_min, t_max = exact_digit_t_bounds(D, MB, n)

        if t_min > t_max:
            continue

        actual_span = min(test_span, t_max - t_min + 1)
        t_end = t_min + actual_span

        # 1. Sieve benchmark
        sieve = CompactTSieve(MB, n, sieve_depth=sieve_depth)
        t0 = time.perf_counter()
        survivors, tele = sieve.sieve_segment(t_min, t_end)
        sieve_time = time.perf_counter() - t0

        # 2. Screening benchmark (test first 20 survivors)
        sample_survivors = survivors[:min(20, len(survivors))]
        screener_a = HDCScreener(order="A_first")
        t0 = time.perf_counter()
        a_first_dual = 0
        for t_val in sample_survivors:
            _, _, is_d, _ = screener_a.screen_pair(MB, t_val, n)
            if is_d:
                a_first_dual += 1
        a_screen_time = time.perf_counter() - t0

        row = {
            "B": B,
            "M_B": str(MB),
            "n": n,
            "centers_sieved": actual_span,
            "survivors": len(survivors),
            "survival_rate": len(survivors) / actual_span if actual_span > 0 else 0,
            "sieve_time_sec": sieve_time,
            "sieve_rate_cps": actual_span / sieve_time if sieve_time > 0 else 0,
            "sample_screened": len(sample_survivors),
            "screen_time_sec": a_screen_time,
            "screen_ms_per_candidate": (a_screen_time / len(sample_survivors) * 1000) if sample_survivors else 0
        }
        results.append(row)
        print(f"B={B:<2} | n={n} | Span={actual_span:<6} | Survivors={len(survivors):<5} ({row['survival_rate']*100:.2f}%) | Sieve={row['sieve_rate_cps']:.0f} c/s | Screen={row['screen_ms_per_candidate']:.2f} ms/cand")

    out_file = Path("research/phase7/benchmark_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nBenchmark results saved to: {out_file}")


def math_log2(x: int) -> float:
    import math
    return x.bit_length() - 1 + math.log2(x / (1 << (x.bit_length() - 1)))


def cmd_search(args: argparse.Namespace) -> None:
    """Executes campaign search."""
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    campaign = HDCCampaign(cfg)
    max_seconds = args.max_seconds
    max_centers = args.max_centers

    print("=" * 60)
    print(f"STARTING HDC-7 SEARCH: {campaign.campaign_id}")
    print(f"Digits: {campaign.target_digits} | B: {campaign.B_cut} | Exponent n: {campaign.n}")
    print(f"Cursor t: {campaign.cursor} -> t_max: {campaign.t_max}")
    print("=" * 60)

    res = campaign.run(max_wall_seconds=max_seconds, max_centers=max_centers)
    print("\n" + "=" * 60)
    print("CAMPAIGN EXECUTION RESULT:")
    print("=" * 60)
    print(f"Status:               {res.get('status')}")
    print(f"Raw centers checked:  {res.get('raw_centers_checked')}")
    print(f"Sieve survivors:      {res.get('sieve_survivors', campaign.sieve_survivors)}")
    print(f"Left PRPs (A):        {campaign.left_prps}")
    print(f"Right PRPs (B'):      {campaign.right_prps}")
    print(f"Dual PRPs:            {campaign.dual_prps}")
    print(f"Certified pairs:      {res.get('certified_pairs')}")
    print(f"Elapsed time (sec):   {res.get('elapsed_seconds', 0.0):.2f}")

    if res.get("status") == "DISCOVERY_SUCCESS":
        print(f"\n[DISCOVERY SUCCESS] Fresh certified twin-prime pair produced!")
        print(f"Certificate: {res.get('certificate_path')}")
    print("=" * 60)


def cmd_verify(args: argparse.Namespace) -> None:
    """Verifies certificates."""
    target = Path(args.target)
    attest_dir = Path(args.attest_dir) if args.attest_dir else None

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("cert_*.json"))
    else:
        print(f"Path not found: {target}")
        sys.exit(1)

    for fp in files:
        print(f"Verifying: {fp.name}...")
        ok, logs, att = verify_certificate_v7(fp, attest_dir)
        for l in logs:
            print(f"  + {l}")
        if ok:
            print(f"  [PASS] {fp.name} unconditionally verified!\n")
        else:
            print(f"  [FAIL] {fp.name} rejected!\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="HDC-7 Primorial-Constrained Twin Prime Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # plan
    p_plan = subparsers.add_parser("plan", help="Inspect parameter boundaries and plan")
    p_plan.add_argument("--config", required=True, help="Path to config JSON")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run benchmark suite")
    p_bench.add_argument("--digits", type=int, default=1510, help="Target digits (default: 1510)")
    p_bench.add_argument("--span", type=int, default=5000, help="Number of centers per benchmark")
    p_bench.add_argument("--sieve-depth", type=int, default=50000, help="Sieve prime limit")

    # search
    p_search = subparsers.add_parser("search", help="Execute discovery campaign")
    p_search.add_argument("--config", required=True, help="Path to config JSON")
    p_search.add_argument("--max-seconds", type=float, default=None, help="Wall-clock limit in seconds")
    p_search.add_argument("--max-centers", type=int, default=None, help="Maximum centers to search")

    # verify
    p_ver = subparsers.add_parser("verify", help="Run independent verification")
    p_ver.add_argument("--target", required=True, help="Certificate file or directory")
    p_ver.add_argument("--attest-dir", default="proofs/phase7/attestations", help="Attestation directory")

    args = parser.parse_args()
    if args.command == "plan":
        cmd_plan(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "verify":
        cmd_verify(args)


if __name__ == "__main__":
    main()
