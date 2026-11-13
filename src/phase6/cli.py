"""
Command-Line Interface for Phase 6 GITCSS Engine.
"""

import sys
import os
import json
import argparse
from pathlib import Path

from src.phase6.independent_verify import verify_file
from src.phase6.campaign import GITCSSCampaign
from src.phase6.models import IntervalMapping

def cmd_audit(args):
    """Audits system environment and historical inventory."""
    print("=== Phase 6 Environment & Historical Inventory Audit ===")
    inv_file = Path("research/phase5_audit/historical_inventory.json")
    if inv_file.exists():
        with open(inv_file, "r", encoding="utf-8") as f:
            inv = json.load(f)
        print(f"Authoritative Historical Inventory: {len(inv)} certified pairs loaded.")
    else:
        print("WARNING: Historical inventory not found at research/phase5_audit/historical_inventory.json")
    print("Python version:", sys.version)
    print("Audit completed successfully.")

def cmd_verify(args):
    """Independently verifies certificate or directory of certificates."""
    target = Path(args.target)
    if not target.exists():
        print(f"ERROR: Target path does not exist: {target}")
        sys.exit(1)
        
    all_ok = True
    if target.is_dir():
        cert_files = sorted(list(target.glob("cert_*.json")))
        if not cert_files:
            print(f"No certificate files matching cert_*.json found in {target}")
            sys.exit(0)
        for cf in cert_files:
            if not verify_file(cf):
                all_ok = False
    else:
        all_ok = verify_file(target)
        
    sys.exit(0 if all_ok else 1)

def cmd_discover(args):
    """Executes a bounded discovery campaign."""
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"ERROR: Configuration file not found: {cfg_path}")
        sys.exit(1)
        
    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    campaign = GITCSSCampaign(config=config, run_id=args.run_id, resume=args.resume)
    discoveries = campaign.run_bounded_search(
        max_segments=args.max_segments,
        stop_on_discovery=not args.no_stop
    )
    if discoveries:
        print(f"\nSUCCESS: Discovered {len(discoveries)} new certified twin-prime pair(s)!")
    else:
        print("\nCampaign finished: No new twin-prime pair discovered in tested range.")

def cmd_coverage_audit(args):
    """Audits coverage manifest for gaps and integrity."""
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"No coverage manifest found at {manifest_path}")
        return
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    segments = data.get("segments", [])
    print(f"Auditing {len(segments)} completed segments in manifest...")
    
    # Check disjoint and contiguous
    for i in range(len(segments) - 1):
        s1 = segments[i]
        s2 = segments[i + 1]
        if int(s1["m_end"]) != int(s2["m_start"]):
            print(f"GAP OR OVERLAP DETECTED between segment {s1['segment_id']} (ends {s1['m_end']}) and segment {s2['segment_id']} (starts {s2['m_start']})!")
            return
            
    print("COVERAGE AUDIT PASS: All recorded segments are strictly contiguous with zero gaps or overlaps.")

def main():
    parser = argparse.ArgumentParser(description="Phase 6 GITCSS Engine CLI")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # audit
    p_audit = subparsers.add_parser("audit", help="Run baseline environment and historical audit")
    p_audit.set_defaults(func=cmd_audit)

    # verify
    p_verify = subparsers.add_parser("verify", help="Independently verify certificates")
    p_verify.add_argument("target", help="Path to certificate JSON file or directory")
    p_verify.set_defaults(func=cmd_verify)

    # discover
    p_disc = subparsers.add_parser("discover", help="Run general-integer discovery campaign")
    p_disc.add_argument("--config", required=True, help="Path to campaign configuration JSON")
    p_disc.add_argument("--run-id", default=None, help="Optional run identifier")
    p_disc.add_argument("--resume", action="store_true", default=True, help="Resume from last checkpoint")
    p_disc.add_argument("--max-segments", type=int, default=None, help="Maximum segments to process")
    p_disc.add_argument("--no-stop", action="store_true", default=False, help="Do not stop on first discovery")
    p_disc.set_defaults(func=cmd_discover)

    # coverage-audit
    p_cov = subparsers.add_parser("coverage-audit", help="Audit coverage manifest for gaps")
    p_cov.add_argument("--manifest", default="data/phase6_coverage_manifest.json", help="Path to manifest JSON")
    p_cov.set_defaults(func=cmd_coverage_audit)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
        
    args.func(args)

if __name__ == "__main__":
    main()
