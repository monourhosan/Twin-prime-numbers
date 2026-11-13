"""
Command-Line Interface for Phase 6 GITCSS Engine.
Supports operations: audit, benchmark, search, status, pause, verify, coverage.
"""

import sys
import os
import json
import argparse
import platform
from pathlib import Path
from datetime import datetime, timezone

from src.phase6.independent_verify import verify_file
from src.phase6.campaign import GITCSSCampaign
from src.phase6.models import IntervalMapping

def cmd_audit(args):
    """Audits system environment, hardware, dependencies, and historical inventory."""
    print("=== Phase 6 Environment & Historical Inventory Audit ===")
    print(f"OS / Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {sys.version}")
    try:
        import gmpy2
        print(f"gmpy2: {gmpy2.__version__} (GMP backend: {gmpy2.mp_version()})")
    except ImportError:
        print("gmpy2: NOT installed")
    try:
        import sympy
        print(f"sympy: {sympy.__version__}")
    except ImportError:
        print("sympy: NOT installed")
        
    cpu_count = os.cpu_count()
    print(f"Available CPU logical cores: {cpu_count}")

    inv_file = Path("research/phase5_audit/historical_inventory.json")
    if inv_file.exists():
        with open(inv_file, "r", encoding="utf-8") as f:
            inv = json.load(f)
        print(f"Authoritative Historical Inventory: {len(inv)} certified pairs loaded.")
    else:
        print("WARNING: Historical inventory not found at research/phase5_audit/historical_inventory.json")

    # Audit proof certificates
    proof_dirs = {
        "Phase 1": list(Path("proofs").glob("cert_*.json")),
        "Phase 2": list(Path("proofs/phase2").glob("*.json")) if Path("proofs/phase2").exists() else [],
        "Phase 3": list(Path("proofs/phase3").glob("*.json")) if Path("proofs/phase3").exists() else [],
        "Phase 4": list(Path("proofs/phase4").glob("*.json")) if Path("proofs/phase4").exists() else [],
        "Phase 5": list(Path("proofs/phase5").glob("*.json")) if Path("proofs/phase5").exists() else [],
        "Phase 6": list(Path("proofs/phase6/certificates").glob("*.json")) if Path("proofs/phase6/certificates").exists() else [],
    }
    total_certs = sum(len(c) for c in proof_dirs.values())
    print(f"\nProof Certificates Inventory ({total_certs} total files):")
    for phase, certs in proof_dirs.items():
        print(f"  - {phase}: {len(certs)} certificate(s)")

    print("\nAudit completed successfully. Status: OK")
    sys.exit(0)

def cmd_benchmark(args):
    """Executes controlled benchmark suite."""
    print("=== Launching Phase 6 Controlled Benchmarks ===")
    from scripts.phase6_benchmarks import run_benchmarks
    run_benchmarks()
    sys.exit(0)

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

def cmd_search(args):
    """Executes a bounded discovery search campaign."""
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
    sys.exit(0)

def cmd_status(args):
    """Shows status of active/completed campaigns, candidates, and coverage."""
    print("=== Phase 6 GITCSS Campaign Status ===")
    campaigns_dir = Path("runs/phase6/campaigns")
    if not campaigns_dir.exists():
        print("No campaigns directory found.")
        sys.exit(0)
        
    runs = sorted(list(campaigns_dir.iterdir()), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        print("No campaign runs recorded.")
        sys.exit(0)
        
    target_runs = runs[:5] if not args.run_id else [campaigns_dir / args.run_id]
    for r in target_runs:
        if not r.exists():
            print(f"Run directory not found: {r}")
            continue
        print(f"\nRun: {r.name}")
        report_file = r / "final_report.md"
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip().startswith("- **")]
            for l in lines:
                print(f"  {l}")
        else:
            print("  (Run in progress or incomplete)")
            
    # Check candidate ledger
    cand_file = Path("data/phase6_candidates.jsonl")
    if cand_file.exists():
        with open(cand_file, "r", encoding="utf-8") as f:
            total_cands = sum(1 for _ in f)
        print(f"\nTotal Candidates in Ledger: {total_cands:,}")
    sys.exit(0)

def cmd_pause(args):
    """Signals a running campaign to halt safely at the next segment checkpoint."""
    print("=== Signaling Pause to Phase 6 Campaign ===")
    if args.run_id:
        target_dir = Path("runs/phase6/campaigns") / args.run_id
        if not target_dir.exists():
            print(f"ERROR: Specified run directory does not exist: {target_dir}")
            sys.exit(1)
        pause_file = target_dir / ".pause"
    else:
        pause_file = Path("runs/phase6/.pause")
        pause_file.parent.mkdir(parents=True, exist_ok=True)
        
    pause_file.write_text(f"PAUSE requested at {datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8")
    print(f"Pause signal written to: {pause_file}")
    print("The active campaign will complete its current segment, record coverage, save the checkpoint, and exit gracefully.")
    sys.exit(0)

def cmd_coverage(args):
    """Audits coverage manifest for gaps and integrity."""
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"No coverage manifest found at {manifest_path}")
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    segments = data.get("segments", [])
    print(f"Auditing {len(segments)} completed segments in manifest {manifest_path}...")
    
    # Check disjoint and contiguous
    has_gaps = False
    for i in range(len(segments) - 1):
        s1 = segments[i]
        s2 = segments[i + 1]
        if int(s1["m_end"]) != int(s2["m_start"]):
            print(f"GAP OR OVERLAP DETECTED between segment {s1['segment_id']} (ends {s1['m_end']}) and segment {s2['segment_id']} (starts {s2['m_start']})!")
            has_gaps = True
            
    if not has_gaps:
        print("COVERAGE AUDIT PASS: All recorded segments are strictly contiguous with zero gaps or overlaps.")
        sys.exit(0)
    else:
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Phase 6 GITCSS Engine CLI")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # audit
    p_audit = subparsers.add_parser("audit", help="Run baseline environment and historical audit")
    p_audit.set_defaults(func=cmd_audit)

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run controlled benchmark suite")
    p_bench.set_defaults(func=cmd_benchmark)

    # search / discover
    for sc in ["search", "discover"]:
        p_search = subparsers.add_parser(sc, help="Run general-integer discovery search campaign")
        p_search.add_argument("--config", required=True, help="Path to campaign configuration JSON")
        p_search.add_argument("--run-id", default=None, help="Optional run identifier")
        p_search.add_argument("--resume", action="store_true", default=True, help="Resume from last checkpoint")
        p_search.add_argument("--max-segments", type=int, default=None, help="Maximum segments to process")
        p_search.add_argument("--no-stop", action="store_true", default=False, help="Do not stop on first discovery")
        p_search.set_defaults(func=cmd_search)

    # status
    p_status = subparsers.add_parser("status", help="Show active and completed campaign status")
    p_status.add_argument("--run-id", default=None, help="Optional specific run identifier")
    p_status.set_defaults(func=cmd_status)

    # pause
    p_pause = subparsers.add_parser("pause", help="Signal campaign to pause safely at checkpoint")
    p_pause.add_argument("--run-id", default=None, help="Optional specific run identifier")
    p_pause.set_defaults(func=cmd_pause)

    # verify
    p_verify = subparsers.add_parser("verify", help="Independently verify certificates")
    p_verify.add_argument("target", help="Path to certificate JSON file or directory")
    p_verify.set_defaults(func=cmd_verify)

    # coverage / coverage-audit
    for sc in ["coverage", "coverage-audit"]:
        p_cov = subparsers.add_parser(sc, help="Audit coverage manifest for gaps and integrity")
        p_cov.add_argument("--manifest", default="data/phase6_coverage_manifest.json", help="Path to manifest JSON")
        p_cov.set_defaults(func=cmd_coverage)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
        
    args.func(args)

if __name__ == "__main__":
    main()
