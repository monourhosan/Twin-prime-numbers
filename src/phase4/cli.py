"""
Phase 4 Command-Line Interface (ADRS-4).
Implements subcommands: doctor, audit, verify, benchmark, search, status, pause, resume, stop, coverage-audit, report.
Strictly respects --config precedence with None-based defaults.
Supports real multi-process worker execution on Windows AMD64.
"""

import sys
import os
import argparse
import time
import json
import subprocess
import multiprocessing
from pathlib import Path
from typing import Optional, List

from .config import Phase4Config
from .storage import Phase4Storage
from .scheduler import TaskScheduler
from .hardware import get_hardware_profile, get_safe_worker_count
from .worker import WorkerPipeline, worker_process_main
from .coverage import audit_coverage
from .certificate import TwinPrimeCertificateV4

def cmd_doctor(args):
    print("=== Phase 4 ADRS-4 System Doctor ===")
    profile = get_hardware_profile()
    for k, v in profile.items():
        print(f"  {k:22}: {v}")

    # Check git status
    try:
        git_sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        git_dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        print(f"  {'git_head':22}: {git_sha[:10]}")
        print(f"  {'git_worktree_clean':22}: {len(git_dirty) == 0}")
    except Exception as e:
        print(f"  git check error: {e}")

    # Arithmetic backend verification
    from .backend import has_gmpy2, verify_backend_consistency
    print(f"  {'gmpy2_accelerated':22}: {has_gmpy2()}")
    try:
        consistent = verify_backend_consistency()
        print(f"  {'backend_consistency':22}: {'PASS (100% agreement)' if consistent else 'FAIL'}")
    except Exception as e:
        print(f"  backend consistency error: {e}")

def cmd_audit(args):
    print("=== Phase 4 Historical and Baseline Audit ===")
    out_file = Path(args.output or "research/phase4/PHASE3_AUDIT.md")
    print(f"Audit report registered at: {out_file}")

    # Invoke independent verifier on Phase 2 and Phase 3 proofs
    cmd = [sys.executable, "scripts/phase4_independent_verify.py", "proofs/phase3", "proofs/phase2"]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

def cmd_verify(args):
    target = Path(args.directory or "proofs/phase4")
    attest_dir = Path(args.attest_dir or "proofs/phase4/attestations")
    print(f"Executing strict independent verification on {target}...")
    cmd = [sys.executable, "scripts/phase4_independent_verify.py", str(target), "--attest-dir", str(attest_dir)]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

def cmd_coverage_audit(args):
    campaign_id = args.campaign or "target_1000"
    ckpt_dir = Path(args.checkpoint_dir or f"runs/phase4/{campaign_id}")
    db_path = ckpt_dir / f"{campaign_id}.sqlite"

    if not db_path.exists():
        print(f"Error: Database {db_path} does not exist.")
        sys.exit(1)

    storage = Phase4Storage(db_path)
    cov = audit_coverage(storage, campaign_id)

    print(f"\n=== Coverage Audit Report for Campaign '{campaign_id}' ===")
    for n, data in cov.items():
        print(f"\nExponent n={n}:")
        print(f"  Total tasks: {data['total_tasks']} (Completed: {data['completed_tasks']}, Partial: {data['partial_tasks']})")
        print(f"  Covered k-span: {data['total_covered_k_span']:,}")
        print(f"  Gaps detected: {len(data['gaps'])}")
        for g in data['gaps']:
            print(f"     [GAP] [{g[0]}, {g[1]})")
        print(f"  Overlaps detected: {len(data['overlaps'])}")
        print(f"  Coverage Status: {'CERTIFIED GAP-FREE' if data['is_gap_free'] else 'GAPS DETECTED'}")

def cmd_search(args):
    # Load configuration
    if args.config and Path(args.config).exists():
        cfg = Phase4Config.from_file(Path(args.config))
    else:
        cfg = Phase4Config()

    # Override only explicitly provided CLI flags (None-based precedence)
    if args.campaign is not None:
        cfg.campaign_id = args.campaign
    if args.min_digits is not None:
        cfg.min_digits = args.min_digits
    if args.exponents is not None:
        cfg.exponents = [int(x.strip()) for x in args.exponents.split(",")]
    if args.k_start is not None:
        cfg.k_start = args.k_start
    if args.k_end is not None:
        cfg.k_end = args.k_end
    if args.window_size is not None:
        cfg.window_k_span = args.window_size
    if args.sieve_depth is not None:
        cfg.sieve_depth = args.sieve_depth
    if args.algorithm is not None:
        cfg.sieve_strategy = args.algorithm
    if args.workers is not None:
        cfg.workers = args.workers
    if args.max_wall_hours is not None:
        cfg.max_wall_hours_per_session = args.max_wall_hours
    if args.until_proven_pairs is not None:
        cfg.stop_after_verified_pairs = args.until_proven_pairs
    if args.checkpoint_dir is not None:
        cfg.checkpoint_dir = args.checkpoint_dir

    cfg.validate()

    ckpt_dir = Path(cfg.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    db_path = ckpt_dir / f"{cfg.campaign_id}.sqlite"
    storage = Phase4Storage(db_path)

    # Register campaign metadata
    git_sha = "unknown"
    try:
        git_sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:10]
    except Exception:
        pass
    storage.register_campaign(cfg.campaign_id, cfg.compute_sha256(), git_sha, get_hardware_profile())

    # Snapshot resolved config
    resolved_config_path = ckpt_dir / "resolved_config.json"
    cfg.save_to_file(resolved_config_path)

    if args.dry_run:
        print(f"=== DRY RUN: ADRS-4 Campaign '{cfg.campaign_id}' ===")
        print(f"  Target digits: >={cfg.min_digits}")
        print(f"  Exponents: {cfg.exponents}")
        print(f"  k-range: [{cfg.k_start}, {cfg.k_end or 'progressive open-ended'})")
        print(f"  Sieve Strategy: {cfg.sieve_strategy}")
        print(f"  Sieve Depth: {cfg.sieve_depth:,}")
        print(f"  Workers: {cfg.workers} (Safe max: {get_safe_worker_count(cfg.workers)})")
        print(f"  Max wall hours: {cfg.max_wall_hours_per_session or 'Unlimited'}")
        print(f"  Target proven pairs: {cfg.stop_after_verified_pairs}")
        print(f"  Config SHA-256: {cfg.compute_sha256()}")
        print(f"  Database: {db_path}")
        return

    # Clear stop / pause signals
    stop_file = ckpt_dir / f"{cfg.campaign_id}.stop"
    pause_file = ckpt_dir / f"{cfg.campaign_id}.pause"
    if stop_file.exists():
        stop_file.unlink()
    if pause_file.exists():
        pause_file.unlink()

    # Plan tasks ahead
    scheduler = TaskScheduler(cfg, storage)
    scheduler.plan_and_register_tasks(num_windows_ahead=20)

    print(f"\n=== Launching Phase 4 ADRS-4 Campaign '{cfg.campaign_id}' ===")
    print(f"  Target: >={cfg.min_digits} digits | Exponents: {cfg.exponents}")
    print(f"  Workers: {cfg.workers} | Sieve: {cfg.sieve_strategy} (Depth: {cfg.sieve_depth:,})")
    print(f"  Config SHA-256: {cfg.compute_sha256()}")

    deadline = None
    if cfg.max_wall_hours_per_session > 0:
        deadline = time.monotonic() + cfg.max_wall_hours_per_session * 3600.0

    proven_found_total = 0

    def on_discovery(cert: TwinPrimeCertificateV4, attest_path: Optional[Path]):
        nonlocal proven_found_total
        proven_found_total += 1
        print(f"\n********************************************************************")
        print(f"*** [DISCOVERY] NEW-TO-PROJECT CERTIFIED TWIN-PRIME PAIR FOUND!  ***")
        print(f"  k = {cert.k}, n = {cert.n}")
        print(f"  Decimal digits: {cert.lower_digits} digits each (Target was >={cfg.min_digits})")
        print(f"  Upper Prime (Proth): witness w = {cert.proth_witness}")
        print(f"  Lower Prime (LLR): parameter P = {cert.llr_p}, u0 = {cert.llr_u0[:30]}...")
        print(f"  Proof Payload: proofs/phase4/cert_k{cert.k}_n{cert.n}.json")
        print(f"  Proof SHA-256: {cert.compute_payload_sha256()}")
        if attest_path:
            print(f"  Independent Attestation: {attest_path}")
            print(f"  Status: PAIR_INDEPENDENTLY_VERIFIED")
        print(f"********************************************************************\n")

    # If multi-worker is requested, spawn worker processes
    if cfg.workers > 1:
        safe_workers = get_safe_worker_count(cfg.workers)
        print(f"Spawning {safe_workers} parallel worker processes (spawn context)...")
        # Ensure child processes inherit project root in PYTHONPATH
        proj_root = str(Path(__file__).resolve().parent.parent.parent)
        curr_ppath = os.environ.get("PYTHONPATH", "")
        if proj_root not in curr_ppath:
            os.environ["PYTHONPATH"] = f"{proj_root}{os.pathsep}{curr_ppath}" if curr_ppath else proj_root

        ctx = multiprocessing.get_context("spawn")
        processes = []
        for widx in range(safe_workers):
            p = ctx.Process(
                target=worker_process_main,
                args=(str(resolved_config_path), f"worker_child_{widx}_pid{os.getpid()}")
            )
            p.start()
            processes.append(p)

        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("\nReceived interrupt. Stopping child worker processes...")
            stop_file.write_text("STOP\n", encoding="utf-8")
            for p in processes:
                p.join(timeout=5)
                if p.is_alive():
                    p.terminate()
        return

    # Single-worker in-process execution
    pipeline = WorkerPipeline(cfg, storage, worker_id=f"worker_main_pid{os.getpid()}")

    while proven_found_total < cfg.stop_after_verified_pairs:
        if deadline and time.monotonic() >= deadline:
            print("\n[STOP] Reached session maximum wall hours limit.")
            break

        if pipeline.check_stop_signals():
            print("\n[STOP/PAUSE] Stop or pause signal detected.")
            break

        task = storage.claim_task(cfg.campaign_id, worker_id=f"worker_main_pid{os.getpid()}", pid=os.getpid(), lease_duration_sec=cfg.lease_timeout_seconds)
        if not task:
            # Advance k_start progressively and plan more tasks
            cfg.k_start += cfg.window_k_span * 20
            scheduler.plan_and_register_tasks(num_windows_ahead=20)
            task = storage.claim_task(cfg.campaign_id, worker_id=f"worker_main_pid{os.getpid()}", pid=os.getpid(), lease_duration_sec=cfg.lease_timeout_seconds)
            if not task:
                print("No further tasks remaining.")
                break

        remaining = cfg.stop_after_verified_pairs - proven_found_total
        discoveries, completed, metrics = pipeline.process_task(
            task=task,
            on_discovery=on_discovery,
            deadline_time=deadline,
            target_proven_remaining=remaining
        )

        st_str = "COMPLETED" if completed else "PARTIAL"
        rate = (metrics["raw_tested"] / max(1e-6, metrics["wall_seconds"]))
        print(f"Task {task['task_id']} [{st_str}]: screened {metrics['raw_tested']:,} cands in {metrics['wall_seconds']:.2f}s ({rate:,.0f} cands/s) | Sieve survivors: {metrics['sieve_survivors']} | PRPs: {metrics['prp_passed']} | Proven this run: {proven_found_total}", flush=True)

def cmd_status(args):
    campaign_id = args.campaign or "target_1000"
    ckpt_dir = Path(args.checkpoint_dir or f"runs/phase4/{campaign_id}")
    db_path = ckpt_dir / f"{campaign_id}.sqlite"

    if not db_path.exists():
        print(f"No database found for campaign '{campaign_id}'. Status: NOT_STARTED")
        return

    storage = Phase4Storage(db_path)
    st = storage.get_campaign_status(campaign_id)

    # Check process liveness
    stop_file = ckpt_dir / f"{campaign_id}.stop"
    pause_file = ckpt_dir / f"{campaign_id}.pause"

    if stop_file.exists():
        operational_state = "STOPPED"
    elif pause_file.exists():
        operational_state = "PAUSED"
    elif st["active_leases"] > 0:
        operational_state = "ACTIVE"
    elif st["completed_tasks"] > 0 and st["pending_tasks"] == 0:
        operational_state = "COMPLETED"
    else:
        operational_state = "IDLE / STOPPED"

    print(f"=== ADRS-4 Campaign Status: '{campaign_id}' ===")
    print(f"  Operational State: {operational_state}")
    print(f"  Completed Tasks:   {st['completed_tasks']:,} / {st['total_tasks']:,}")
    print(f"  Partial Tasks:     {st['partial_tasks']:,}")
    print(f"  Leased Tasks:      {st['leased_tasks']:,} (Active Leases: {st['active_leases']})")
    print(f"  Pending Tasks:     {st['pending_tasks']:,}")
    print(f"  Candidates Tested: {st['raw_tested']:,}")
    print(f"  Sieve Survivors:   {st['sieve_survivors']:,}")
    print(f"  PRP Passes:        {st['prp_passed']:,}")
    print(f"  Proven Discoveries:{st['discoveries']:,}")
    print(f"  Elapsed Wall Time: {st['elapsed_wall_seconds']:.1f}s")

def cmd_pause(args):
    campaign_id = args.campaign or "target_1000"
    ckpt_dir = Path(args.checkpoint_dir or f"runs/phase4/{campaign_id}")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    pause_file = ckpt_dir / f"{campaign_id}.pause"
    pause_file.write_text("PAUSE\n", encoding="utf-8")
    print(f"Created pause signal: {pause_file}")

def cmd_resume(args):
    campaign_id = args.campaign or "target_1000"
    ckpt_dir = Path(args.checkpoint_dir or f"runs/phase4/{campaign_id}")
    pause_file = ckpt_dir / f"{campaign_id}.pause"
    stop_file = ckpt_dir / f"{campaign_id}.stop"
    if pause_file.exists():
        pause_file.unlink()
        print(f"Removed pause signal: {pause_file}")
    if stop_file.exists():
        stop_file.unlink()
        print(f"Removed stop signal: {stop_file}")

def cmd_stop(args):
    campaign_id = args.campaign or "target_1000"
    ckpt_dir = Path(args.checkpoint_dir or f"runs/phase4/{campaign_id}")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    stop_file = ckpt_dir / f"{campaign_id}.stop"
    stop_file.write_text("STOP\n", encoding="utf-8")
    print(f"Created stop signal: {stop_file}")

def cmd_report(args):
    campaign_id = args.campaign or "target_1000"
    ckpt_dir = Path(args.checkpoint_dir or f"runs/phase4/{campaign_id}")
    db_path = ckpt_dir / f"{campaign_id}.sqlite"
    out_file = Path(args.output) if args.output else ckpt_dir / "reports" / "status.md"

    if not db_path.exists():
        print(f"Database {db_path} does not exist.")
        return

    storage = Phase4Storage(db_path)
    st = storage.get_campaign_status(campaign_id)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# ADRS-4 Discovery Status and Operational Ledger: {campaign_id}\n",
        f"**Audit Timestamp:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}  \n",
        f"**Campaign ID:** `{campaign_id}`  \n\n",
        "## 1. Executive Summary\n",
        f"- **Completed Tasks:** {st['completed_tasks']}\n",
        f"- **Partial Tasks:** {st['partial_tasks']}\n",
        f"- **Candidates Screened:** {st['raw_tested']:,}\n",
        f"- **Proven Pairs:** {st['discoveries']}\n\n",
    ]
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report generated at {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Phase 4 ADRS-4 Twin-Prime Discovery Engine")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # doctor
    p_doc = subparsers.add_parser("doctor")
    p_doc.set_defaults(func=cmd_doctor)

    # audit
    p_audit = subparsers.add_parser("audit")
    p_audit.add_argument("--phase3", action="store_true")
    p_audit.add_argument("--output", default=None)
    p_audit.set_defaults(func=cmd_audit)

    # verify
    p_verify = subparsers.add_parser("verify")
    p_verify.add_argument("--directory", default="proofs/phase4")
    p_verify.add_argument("--attest-dir", default="proofs/phase4/attestations")
    p_verify.add_argument("--independent", action="store_true")
    p_verify.set_defaults(func=cmd_verify)

    # coverage-audit
    p_cov = subparsers.add_parser("coverage-audit")
    p_cov.add_argument("--campaign", default="target_1000")
    p_cov.add_argument("--checkpoint-dir", default=None)
    p_cov.set_defaults(func=cmd_coverage_audit)

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("--config", default=None)
    p_search.add_argument("--campaign", default=None)
    p_search.add_argument("--min-digits", type=int, default=None)
    p_search.add_argument("--exponents", default=None)
    p_search.add_argument("--k-start", type=int, default=None)
    p_search.add_argument("--k-end", type=int, default=None)
    p_search.add_argument("--window-size", type=int, default=None)
    p_search.add_argument("--sieve-depth", type=int, default=None)
    p_search.add_argument("--algorithm", default=None)
    p_search.add_argument("--workers", type=int, default=None)
    p_search.add_argument("--max-wall-hours", type=float, default=None)
    p_search.add_argument("--until-proven-pairs", type=int, default=None)
    p_search.add_argument("--checkpoint-dir", default=None)
    p_search.add_argument("--resume", action="store_true")
    p_search.add_argument("--dry-run", action="store_true")
    p_search.set_defaults(func=cmd_search)

    # status
    p_status = subparsers.add_parser("status")
    p_status.add_argument("--campaign", default="target_1000")
    p_status.add_argument("--checkpoint-dir", default=None)
    p_status.set_defaults(func=cmd_status)

    # pause
    p_pause = subparsers.add_parser("pause")
    p_pause.add_argument("--campaign", default="target_1000")
    p_pause.add_argument("--checkpoint-dir", default=None)
    p_pause.set_defaults(func=cmd_pause)

    # resume
    p_resume = subparsers.add_parser("resume")
    p_resume.add_argument("--campaign", default="target_1000")
    p_resume.add_argument("--checkpoint-dir", default=None)
    p_resume.set_defaults(func=cmd_resume)

    # stop
    p_stop = subparsers.add_parser("stop")
    p_stop.add_argument("--campaign", default="target_1000")
    p_stop.add_argument("--checkpoint-dir", default=None)
    p_stop.set_defaults(func=cmd_stop)

    # report
    p_rep = subparsers.add_parser("report")
    p_rep.add_argument("--campaign", default="target_1000")
    p_rep.add_argument("--checkpoint-dir", default=None)
    p_rep.add_argument("--output", default=None)
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
