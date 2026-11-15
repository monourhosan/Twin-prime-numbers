"""
Phase 9 Command-Line Interface.
Supports:
- search: Execute or resume PACCM-9 discovery campaign
- benchmark: Run comparative CPU vs GPU vs Hybrid benchmark
- verify: Run independent certificate verification
"""

import sys
import argparse
import json
import time
from pathlib import Path

from .anchor import PrimorialAnchor
from .campaign import CampaignOrchestrator
from scripts.phase9_independent_verify import verify_paccm9_certificate


def cmd_search(args):
    orchestrator = CampaignOrchestrator(
        campaign_id=args.campaign_id,
        anchor_y=args.anchor_y,
        t_start=args.t_start,
        t_end=args.t_end,
        sieve_depth=args.sieve_depth,
        batch_size=args.batch_size,
        use_gpu=not args.no_gpu,
        cross_check_cpu=args.cross_check,
        stop_on_first_discovery=args.stop_on_first
    )
    summary = orchestrator.run()
    print("\n=== CAMPAIGN EXECUTION SUMMARY ===")
    print(json.dumps(summary, indent=2))


def cmd_verify(args):
    cert_path = Path(args.cert_file).resolve()
    print(f"Auditing certificate: {cert_path.name}...")
    ok, logs, att = verify_paccm9_certificate(cert_path)
    for line in logs:
        print(f"  + {line}")
    if ok:
        print(f"  [PASS] {cert_path.name} unconditionally verified!")
        sys.exit(0)
    else:
        print(f"  [FAIL] Verification rejected for {cert_path.name}!")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Phase 9 PACCM-9 Twin Prime Discovery Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search command
    p_search = subparsers.add_parser("search", help="Run or resume search campaign")
    p_search.add_argument("--campaign-id", type=str, default="phase9_primary_search")
    p_search.add_argument("--anchor-y", type=int, default=283, help="Primorial anchor limit (default: 283 for ~355d)")
    p_search.add_argument("--t-start", type=int, default=1)
    p_search.add_argument("--t-end", type=int, default=50000)
    p_search.add_argument("--sieve-depth", type=int, default=100000)
    p_search.add_argument("--batch-size", type=int, default=5000)
    p_search.add_argument("--no-gpu", action="store_true", help="Disable NVIDIA GPU acceleration")
    p_search.add_argument("--cross-check", action="store_true", help="Cross-check GPU against CPU bitset")
    p_search.add_argument("--stop-on-first", action=argparse.BooleanOptionalAction, default=True, help="Stop upon first certified pair (or --no-stop-on-first to complete interval)")

    # Verify command
    p_verify = subparsers.add_parser("verify", help="Verify certificate")
    p_verify.add_argument("cert_file", type=str, help="Path to certificate JSON")

    args = parser.parse_args()
    if args.command == "search":
        cmd_search(args)
    elif args.command == "verify":
        cmd_verify(args)


if __name__ == "__main__":
    main()
