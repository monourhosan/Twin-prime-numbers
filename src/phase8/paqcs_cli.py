"""
PAQCS Command-Line Interface (Phase 8).
Usage:
  python -m src.phase8.paqcs_cli anchor [--y 1780] [--digits 1511]
  python -m src.phase8.paqcs_cli search --config configs/phase8/paqcs_primary_1511d.json
  python -m src.phase8.paqcs_cli verify proofs/phase8/certificates/cert_paqcs_1511d_*.json
  python -m src.phase8.paqcs_cli benchmark [--candidates 50000]
"""

import argparse
import json
import sys
from pathlib import Path

from .paqcs_anchor import PrimorialAnchor
from .paqcs_campaign import PAQCSCampaign
from scripts.phase8_paqcs_independent_verify import verify_paqcs_certificate


def cmd_anchor(args):
    anchor = PrimorialAnchor(y=args.y)
    t_min = anchor.compute_min_t(target_digits=args.digits, h=args.h)
    print("=" * 60)
    print(f"PAQCS Primorial Anchor (y = {args.y})")
    print("=" * 60)
    print(f"Prime factors count: {len(anchor.primes)} ({anchor.primes[0]} .. {anchor.primes[-1]})")
    print(f"S_y decimal digits:  {anchor.digits}")
    print(f"Factors SHA-256:     {anchor.factors_sha256}")
    print(f"Target digits:       {args.digits} (h = {args.h})")
    print(f"Minimum odd t:       {t_min}")
    print("=" * 60)


def cmd_search(args):
    if not args.config:
        print("Error: --config required for search")
        sys.exit(1)
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    campaign = PAQCSCampaign(cfg)
    discoveries = campaign.execute()
    if discoveries:
        print(f"\nSUCCESS: Discovered {len(discoveries)} certified twin prime pair(s)!")
        for disc in discoveries:
            print(f"  t={disc['t']}, digits={disc['digits']}, cert={disc['certificate']}")
    else:
        print("\nCampaign completed: no dual-PRP found in specified candidate range.")


def cmd_verify(args):
    target = Path(args.path)
    attest_dir = Path("proofs/phase8/attestations")
    if target.is_file():
        files = [target]
    else:
        files = sorted(target.glob("cert_paqcs_*.json"))

    if not files:
        print(f"No PAQCS certificates found at {target}")
        sys.exit(1)

    all_ok = True
    for fp in files:
        print(f"Auditing: {fp.name}")
        ok, logs, _ = verify_paqcs_certificate(fp, attest_dir=attest_dir)
        for l in logs:
            print(f"  + {l}")
        if ok:
            print(f"  [PASS] {fp.name} unconditionally verified!\n")
        else:
            print(f"  [FAIL] {fp.name} rejected!\n")
            all_ok = False
    sys.exit(0 if all_ok else 2)


def main():
    parser = argparse.ArgumentParser(description="PAQCS Primorial-Anchored Quadratic-Cofactor Search CLI")
    subparsers = parser.add_subparsers(dest="command")

    # anchor
    p_anchor = subparsers.add_parser("anchor", help="Inspect primorial anchor")
    p_anchor.add_argument("--y", type=int, default=1780, help="Primorial bound y (default: 1780)")
    p_anchor.add_argument("--digits", type=int, default=1511, help="Target digits (default: 1511)")
    p_anchor.add_argument("--h", type=int, default=3, help="Offset h (default: 3)")

    # search
    p_search = subparsers.add_parser("search", help="Run PAQCS search campaign")
    p_search.add_argument("--config", type=str, required=True, help="Path to JSON campaign configuration")

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify PAQCS certificate")
    p_verify.add_argument("path", type=str, help="Path to certificate file or directory")

    args = parser.parse_args()
    if args.command == "anchor":
        cmd_anchor(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "verify":
        cmd_verify(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
