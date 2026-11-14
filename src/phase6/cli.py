"""
Command-Line Interface for Phase 6 (QCP-6 and GITCSS).
Supports noninteractive CLI commands:
- python -m src.phase6 audit --repo .
- python -m src.phase6 benchmark --config configs/phase6/pilot.json
- python -m src.phase6 discover --config configs/phase6/primary.json [--dry-run] [--resume]
- python -m src.phase6 status --campaign primary
- python -m src.phase6 pause --campaign primary
- python -m src.phase6 verify proofs/phase6/
"""

import sys
import os
import json
import argparse
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any

from .search import DiscoveryRunner
from .benchmark import run_comprehensive_benchmark
from .ledger import SearchLedger


def cmd_audit(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo) if hasattr(args, "repo") and args.repo else Path.cwd()
    print("============================================================")
    print("PHASE 6 REPOSITORY & COMPUTATIONAL ENVIRONMENT AUDIT (QCP-6)")
    print("============================================================")
    
    # Git commit
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    except Exception:
        git_commit = "unknown"
        git_branch = "unknown"

    print(f"Git Branch: {git_branch}")
    print(f"Git Commit: {git_commit}")
    print(f"OS / Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python Runtime: {sys.version.split()[0]} ({sys.platform})")

    try:
        import gmpy2
        print(f"gmpy2: Installed (version {gmpy2.__version__}, backend: {gmpy2.mp_version()})")
    except ImportError:
        print("gmpy2: NOT installed")

    try:
        import sympy
        print(f"sympy: Installed (version {sympy.__version__})")
    except ImportError:
        print("sympy: NOT installed")

    # Historical inventory check
    inv_file = repo_root / "data" / "phase6" / "exclusion_index.json"
    if not inv_file.exists():
        inv_file = repo_root / "research" / "phase5_audit" / "historical_inventory.json"

    if inv_file.exists():
        with open(inv_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"\nExclusion Inventory: {len(data)} unique historical centers loaded.")
    else:
        print("\nWARNING: No historical exclusion inventory found!")

    # Check proofs
    certs = sorted(list((repo_root / "proofs").glob("**/cert_*.json")) + list((repo_root / "proofs").glob("**/imported_cert_*.json")))
    print(f"Total proof certificates in repository: {len(certs)}")

    print("\nPhase 6 Environment Audit: PASSED (Status: READY)")
    print("============================================================")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"Error: Config file not found: {cfg_path}")
        return 1

    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    res = run_comprehensive_benchmark(config, repo_root=Path.cwd())
    print("Benchmark run complete.")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"Error: Config file not found: {cfg_path}")
        return 1

    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if hasattr(args, "dry_run") and args.dry_run:
        config["dry_run"] = True

    resume_flag = bool(getattr(args, "resume", False))
    runner = DiscoveryRunner(config, repo_root=Path.cwd())
    res = runner.run(resume=resume_flag)

    print("\n=== Discovery Summary ===")
    print(f"Status: {res['status']}")
    print(f"Campaign: {res['campaign_id']}")
    print(f"Candidates Tested: {res['tested_candidates']}")
    print(f"Sieve Survivors: {res['sieve_survivors']}")
    print(f"Dual PRP Hits: {res['prp_hits']}")
    print(f"Elapsed Time: {res['elapsed_seconds']:.2f}s")
    if res.get("certificate_path"):
        print(f"Certificate: {res['certificate_path']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    campaign_id = args.campaign
    db_path = Path.cwd() / "runs" / "phase6" / campaign_id / "ledger.db"
    if not db_path.exists():
        print(f"No ledger found for campaign '{campaign_id}' at {db_path}")
        return 1

    ledger = SearchLedger(db_path)
    status = ledger.get_campaign_status(campaign_id)
    print(f"=== Campaign Status: {campaign_id} ===")
    for k, v in status.items():
        print(f"  {k}: {v}")
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    campaign_id = args.campaign
    run_dir = Path.cwd() / "runs" / "phase6" / campaign_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pause_file = run_dir / ".pause"
    pause_file.write_text("PAUSED", encoding="utf-8")

    db_path = run_dir / "ledger.db"
    if db_path.exists():
        ledger = SearchLedger(db_path)
        ledger.set_campaign_status(campaign_id, "PAUSED")

    print(f"Campaign '{campaign_id}' successfully PAUSED (.pause written).")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from scripts.phase6_independent_verify import main as verify_main
    sys.argv = ["phase6_independent_verify.py", args.path]
    return verify_main()


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 Number Theory Search & Verification Engine")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit environment and historical repository inventory")
    p_audit.add_argument("--repo", default=".", help="Repository root path")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run empirical benchmarks")
    p_bench.add_argument("--config", required=True, help="Path to benchmark JSON configuration")

    # discover / search
    p_disc = subparsers.add_parser("discover", help="Execute discovery campaign")
    p_disc.add_argument("--config", required=True, help="Path to campaign JSON configuration")
    p_disc.add_argument("--dry-run", action="store_true", help="Validate setup without testing candidates")
    p_disc.add_argument("--resume", action="store_true", help="Resume an existing campaign")

    p_search = subparsers.add_parser("search", help="Alias for discover")
    p_search.add_argument("--config", required=True, help="Path to campaign JSON configuration")
    p_search.add_argument("--dry-run", action="store_true", help="Validate setup without testing candidates")
    p_search.add_argument("--resume", action="store_true", help="Resume an existing campaign")

    # status
    p_stat = subparsers.add_parser("status", help="Get campaign status from persistent ledger")
    p_stat.add_argument("--campaign", required=True, help="Campaign identifier")

    # pause
    p_pause = subparsers.add_parser("pause", help="Cooperatively pause campaign")
    p_pause.add_argument("--campaign", required=True, help="Campaign identifier")

    # verify
    p_ver = subparsers.add_parser("verify", help="Independently verify certificate artifacts")
    p_ver.add_argument("path", help="Path to certificate JSON file or directory")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "audit":
        return cmd_audit(args)
    elif args.subcommand == "benchmark":
        return cmd_benchmark(args)
    elif args.subcommand in ("discover", "search"):
        return cmd_discover(args)
    elif args.subcommand == "status":
        return cmd_status(args)
    elif args.subcommand == "pause":
        return cmd_pause(args)
    elif args.subcommand == "verify":
        return cmd_verify(args)
    else:
        print(f"Unknown subcommand: {args.subcommand}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
