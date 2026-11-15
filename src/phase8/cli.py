"""
Command Line Interface for Phase 8 ADES-8.
Provides subcommands:
- plan: Displays theoretical density, exact bounds, and candidate counts
- search: Runs discovery campaign over 2D tiles
- verify: Verifies a Phase 8 certificate
- status: Displays campaign progress and ledgered results
"""

import sys
import os
import json
import argparse
import math

from src.phase8.math import (
    get_primorial_multiplier,
    exact_digit_t_bounds,
    compute_candidate_pair
)
from src.phase8.campaign import ADES8CampaignManager


def cmd_plan(args):
    """Computes exact digit bounds, primorial multiplier, and theoretical yield."""
    D = args.digit_band
    R = args.R
    M = get_primorial_multiplier(R)
    print("=" * 60)
    print(f"ADES-8 Search Plan: Target D = {D} decimal digits")
    print("=" * 60)
    print(f"Primorial cutoff R = {R}, M_R = {M}")

    # Hardy-Littlewood constant and primorial gain G(R)
    C2 = 0.6601618158468696
    primes_gain = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    G = 1.0
    for p in primes_gain:
        if 5 <= p <= R:
            G *= (p / (p - 2))
    
    lnX = D * math.log(10)
    rho = 12 * C2 * G / (lnX ** 2)

    print(f"Primorial relative gain G({R}) = {G:.6f}")
    print(f"ln(10^{D}) = {lnX:.2f}")
    print(f"Predicted twin prime density rho ~ {rho:.8e}")
    print(f"Expected candidates per twin prime: ~{1/rho:,.0f}")
    print("-" * 60)
    print("Exponent Row Breakdown:")

    total_valid_candidates = 0
    for n in range(args.n_start, args.n_start + args.n_height):
        k_min, k_max, t_min, t_max = exact_digit_t_bounds(D, M, n)
        if t_min <= t_max:
            count = t_max - t_min + 1
            total_valid_candidates += count
            print(f"  n = {n}: t in [{t_min}, {t_max}] ({count:,} candidates, k_max < 2^{n})")
        else:
            print(f"  n = {n}: [EMPTY - out of digit range]")

    print("-" * 60)
    print(f"Total valid candidates in {args.n_height}-row block: {total_valid_candidates:,}")
    expected_pairs = total_valid_candidates * rho
    p_hit = 1.0 - math.exp(-expected_pairs)
    print(f"Expected twin pairs in block: {expected_pairs:.4f}")
    print(f"Poisson P(at least 1 pair) in block: {p_hit * 100:.2f}%")
    print("=" * 60)


def cmd_search(args):
    """Executes search campaign from config file."""
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    print(f"Launching ADES-8 Campaign: {config.get('campaign_id', 'unnamed')}")
    print(f"  Digit Band: {config.get('digit_band', 1515)} digits")
    print(f"  Exponents: [{config.get('n_start', 5000)}, {config.get('n_start', 5000) + config.get('n_height', 16) - 1}]")
    print(f"  Sieve Depth S: {config.get('sieve_limit', 100000):,}")
    print(f"  Tile Width: {config.get('t_width', 50000):,}")
    print(f"  Max Tiles: {config.get('max_tiles', 100)}")

    manager = ADES8CampaignManager(config)
    result = manager.run_campaign()

    print("=" * 60)
    print(f"Campaign Result: {result['status']}")
    print(f"  Tiles Processed: {result['tiles_processed']}")
    print(f"  Candidates Sieved: {result['total_candidates_sieved']:,}")
    print(f"  Sieve Survivors: {result['total_survivors']:,}")
    print(f"  Fermat Tested: {result['total_fermat_tested']:,}")
    print(f"  Dual PRPs Discovered: {result['total_dual_prps']}")
    print(f"  Elapsed Time: {result['campaign_elapsed_sec']:.2f} s")
    if result["certified_pair"]:
        pair = result["certified_pair"]["pair"]
        print(f"  CERTIFIED FRESH RECORD PAIR DISCOVERED!")
        print(f"    Digits: {pair['digits']}")
        print(f"    Center C mod 6: {int(pair['center_decimal']) % 6}")
        print(f"    SHA-256: {result['certified_pair']['sha256']}")
    print("=" * 60)


def cmd_status(args):
    """Prints status of current campaign."""
    campaign_dir = args.campaign_dir
    chk_path = os.path.join(campaign_dir, "campaign_checkpoint.json")
    if os.path.exists(chk_path):
        with open(chk_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("ADES-8 Campaign Status:")
        for k, v in data.items():
            print(f"  {k}: {v}")
    else:
        print(f"No checkpoint found in {campaign_dir}")


def main():
    parser = argparse.ArgumentParser(description="ADES-8 Two-Dimensional Twin Prime Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # plan
    p_plan = subparsers.add_parser("plan", help="Compute search parameters and yield model")
    p_plan.add_argument("--digit-band", type=int, default=1515, help="Target decimal digits")
    p_plan.add_argument("--R", type=int, default=13, help="Primorial prime cutoff")
    p_plan.add_argument("--n-start", type=int, default=5000, help="Base exponent")
    p_plan.add_argument("--n-height", type=int, default=16, help="Tile height (rows)")

    # search
    p_search = subparsers.add_parser("search", help="Execute 2D search campaign")
    p_search.add_argument("--config", type=str, required=True, help="Path to JSON config")

    # status
    p_status = subparsers.add_parser("status", help="Check campaign status")
    p_status.add_argument("--campaign-dir", type=str, default="data/phase8", help="Campaign data directory")

    args = parser.parse_args()
    if args.command == "plan":
        cmd_plan(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
