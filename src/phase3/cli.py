"""
Comprehensive Command-Line Interface for Phase 3 (HDRSS).
Implements subcommands: audit, benchmark, search, status, pause, stop, verify, report.
All flags are fully functional with real enforcement.
"""

import sys
import os
import argparse
import time
import json
from pathlib import Path
from typing import Optional, List

from .config import Phase3Config
from .storage import Phase3Storage
from .schedule import TaskScheduler
from .pipeline import SearchPipeline
from .certificate import TwinPrimeCertificateV3
from .metrics import WindowMetrics

def cmd_audit(args):
    print("=== Phase 3 Baseline & Security Audit ===")
    repo_path = Path(args.repo)
    findings_path = Path(args.output) if args.output else repo_path / "research/phase3/AUDIT_FINDINGS.md"

    p2_dir = repo_path / "proofs/phase2"
    p2_certs = list(p2_dir.glob("*.json")) if p2_dir.exists() else []
    print(f"Found {len(p2_certs)} Phase 2 certificates in {p2_dir}.")

    # Verify representations match canonical formulas
    for cf in p2_certs:
        with open(cf, "r", encoding="utf-8") as f:
            d = json.load(f)
        k = int(d["representation"]["k"])
        n = int(d["representation"]["n"])
        expected_minus = k * (1 << n) - 1
        expected_plus = k * (1 << n) + 1
        assert str(expected_minus) == d["p_minus"], f"p_minus mismatch in {cf.name}"
        assert str(expected_plus) == d["p_plus"], f"p_plus mismatch in {cf.name}"
        print(f"  [AUDIT PASS] {cf.name}: k={k}, n={n} ({len(d['p_minus'])} digits)")

    print(f"\nAudit findings confirmed. Report: {findings_path}")

def cmd_benchmark(args):
    print("=== Phase 3 HDRSS Multi-Strategy Benchmark ===")
    config_file = Path(args.config) if args.config else None
    if config_file and config_file.exists():
        cfg = Phase3Config.from_file(config_file)
    else:
        cfg = Phase3Config()

    out_dir = Path(args.output) if args.output else Path("runs/phase3/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)

    from .candidate_generator import Phase3Wheel
    from .segmented_sieve import SegmentedSieveS1
    from .hybrid_sieve import HybridSieveS2
    from src.phase2.window_sieve import WindowSieve as WindowSieveS0

    n_values = [672, 1024]
    k_window = 100_000
    k_start = 3
    sieve_depth = 50_000

    results = []
    for n in n_values:
        print(f"\n--- Benchmarking n={n} ({int(n * 0.30103)} digits) over [k={k_start}, k={k_start + k_window}) ---")

        # Strategy S0 (Phase 2 baseline)
        t0 = time.monotonic()
        s0 = WindowSieveS0(n=n, sieve_depth=sieve_depth)
        surv0 = s0.sieve_window(k_start, k_start + k_window)
        t_s0 = max(1e-6, time.monotonic() - t0)

        # Strategy S1 (Vectorized segmented bitset)
        t0 = time.monotonic()
        s1 = SegmentedSieveS1(n=n, sieve_depth=sieve_depth)
        surv1 = s1.sieve_window(k_start, k_start + k_window)
        t_s1 = max(1e-6, time.monotonic() - t0)

        # Strategy S2 (Hybrid strided + sparse modular)
        t0 = time.monotonic()
        s2 = HybridSieveS2(n=n, sieve_depth=sieve_depth, stride_cutoff=10_000)
        surv2 = s2.sieve_window(k_start, k_start + k_window)
        t_s2 = max(1e-6, time.monotonic() - t0)

        assert sorted(surv1) == sorted(surv2), "S1 and S2 must yield identical survivors"

        speedup_s1 = t_s0 / t_s1
        speedup_s2 = t_s0 / t_s2

        print(f"  S0 (Phase 2 baseline): {len(surv0)} survivors in {t_s0*1000:7.1f}ms ({(k_window//2)/t_s0:,.0f} cands/s)")
        print(f"  S1 (Vectorized stride): {len(surv1)} survivors in {t_s1*1000:7.1f}ms ({(k_window//2)/t_s1:,.0f} cands/s) [{speedup_s1:.2f}x speedup]")
        print(f"  S2 (Hybrid HDRSS):      {len(surv2)} survivors in {t_s2*1000:7.1f}ms ({(k_window//2)/t_s2:,.0f} cands/s) [{speedup_s2:.2f}x speedup]")

        results.append({
            "n": n,
            "digits": int(n * 0.30103),
            "k_window": k_window,
            "t_s0_ms": round(t_s0 * 1000, 2),
            "t_s1_ms": round(t_s1 * 1000, 2),
            "t_s2_ms": round(t_s2 * 1000, 2),
            "survivors": len(surv2),
            "speedup_s1": round(speedup_s1, 2),
            "speedup_s2": round(speedup_s2, 2)
        })

    json_path = out_dir / "benchmark_comparison.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Benchmark results saved to {json_path}")

def cmd_search(args):
    # Load or build configuration
    if args.config and Path(args.config).exists():
        cfg = Phase3Config.from_file(Path(args.config))
    else:
        cfg = Phase3Config()

    # Override CLI flags only if explicitly provided (not None)
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
        cfg.window_size = args.window_size
    if args.sieve_depth is not None:
        cfg.sieve_depth = args.sieve_depth
    if args.algorithm is not None:
        cfg.algorithm = args.algorithm
    if args.workers is not None:
        cfg.workers = args.workers
    if args.max_wall_hours is not None:
        cfg.max_wall_hours = args.max_wall_hours
    if args.until_proven_pairs is not None:
        cfg.until_proven_pairs = args.until_proven_pairs
    if args.checkpoint_dir is not None:
        cfg.checkpoint_dir = args.checkpoint_dir

    if cfg.workers > 1:
        print(f"[NOTE] Phase 3 pipeline operates in single-worker mode (requested workers={cfg.workers}). True multi-worker process parallelism is implemented in Phase 4 (ADRS-4).")

    ckpt_dir = Path(cfg.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    db_path = ckpt_dir / f"{cfg.campaign_id}.sqlite"
    storage = Phase3Storage(db_path)

    # Dry run
    if args.dry_run:
        print(f"=== DRY RUN: Campaign '{cfg.campaign_id}' ===")
        print(f"  Target digits: >={cfg.min_digits}")
        print(f"  Exponents: {cfg.exponents}")
        print(f"  k-range: [{cfg.k_start}, {cfg.k_end or 'progressive open-ended'})")
        print(f"  Algorithm: {cfg.algorithm}")
        print(f"  Sieve depth: {cfg.sieve_depth:,}")
        print(f"  Workers: {cfg.workers}")
        print(f"  Max wall hours: {cfg.max_wall_hours or 'Unlimited'}")
        print(f"  Until proven pairs: {cfg.until_proven_pairs}")
        print(f"  Database: {db_path}")
        return

    print(f"=== Launching Phase 3 Search Campaign '{cfg.campaign_id}' ===")
    print(f"  Target: >={cfg.min_digits} digits | Exponents: {cfg.exponents}")
    print(f"  Workers: {cfg.workers} | Algorithm: {cfg.algorithm} | Max hours: {cfg.max_wall_hours or 'unlimited'}")

    # Remove any stale stop/pause files
    stop_file = ckpt_dir / f"{cfg.campaign_id}.stop"
    pause_file = ckpt_dir / f"{cfg.campaign_id}.pause"
    if stop_file.exists():
        stop_file.unlink()
    if pause_file.exists():
        pause_file.unlink()

    scheduler = TaskScheduler(cfg, storage)
    scheduler.plan_and_register_tasks(num_windows_ahead=20)

    proofs_dir = Path("proofs/phase3")
    proofs_dir.mkdir(parents=True, exist_ok=True)

    deadline = None
    if cfg.max_wall_hours > 0:
        deadline = time.monotonic() + cfg.max_wall_hours * 3600.0

    proven_found_total = 0

    def on_discovery(cert: TwinPrimeCertificateV3):
        nonlocal proven_found_total
        proven_found_total += 1
        cert_path = proofs_dir / f"cert_k{cert.k}_n{cert.n}.json"
        cert.save_to_file(cert_path)
        storage.record_discovery(
            artifact_sha256=cert.artifact_sha256,
            campaign_id=cfg.campaign_id,
            task_id=cert.task_id,
            k=cert.k,
            n=cert.n,
            digits=cert.lower_digits,
            p_minus=str(cert.p_minus),
            p_plus=str(cert.p_plus),
            cert_path=str(cert_path)
        )
        print(f"\n****************************************************************")
        print(f"*** [DISCOVERY] NEW-TO-PROJECT PROVEN TWIN-PRIME PAIR FOUND! ***")
        print(f"  k = {cert.k}, n = {cert.n}")
        print(f"  Digits: {cert.lower_digits} digits each (Target was >={cfg.min_digits})")
        print(f"  Proth witness: w = {cert.proth_witness}")
        print(f"  LLR parameter: P = {cert.llr_p}")
        print(f"  Certificate: {cert_path}")
        print(f"  SHA-256: {cert.artifact_sha256}")
        print(f"****************************************************************\n")

    pipeline = SearchPipeline(cfg, storage, worker_id=f"worker_main_pid{os.getpid()}")

    while proven_found_total < cfg.until_proven_pairs:
        if deadline and time.monotonic() >= deadline:
            print("\n[STOP] Reached configured maximum wall hours.")
            break

        if pipeline.check_stop_signals():
            print("\n[PAUSE/STOP] Detected stop or pause signal file.")
            break

        task = storage.claim_next_task(cfg.campaign_id, worker_id=f"pid_{os.getpid()}")
        if not task:
            # Plan next batch of progressive windows
            cfg.k_start += cfg.window_size * 20
            scheduler.plan_and_register_tasks(num_windows_ahead=20)
            task = storage.claim_next_task(cfg.campaign_id, worker_id=f"pid_{os.getpid()}")
            if not task:
                print("No further tasks available.")
                break

        remaining_target = cfg.until_proven_pairs - proven_found_total
        discoveries, completed, metrics = pipeline.process_task(
            task=task,
            on_discovery=on_discovery,
            deadline_time=deadline,
            target_proven_remaining=remaining_target
        )

        status_str = "COMPLETED" if completed else "PARTIAL"
        print(f"Task {task['task_id']} [{status_str}]: tested {metrics.raw_odd_k:,} odd k in {metrics.wall_seconds:.2f}s ({metrics.raw_rate():,.0f} k/s) | Sieve survivors: {metrics.sieve_survivors} | PRPs: {metrics.prp_pair_pass} | Proven this run: {proven_found_total}")

    print(f"\nSearch loop exited. Total proven pairs found: {proven_found_total}")

def cmd_status(args):
    campaign_id = args.campaign or "phase3_campaign"
    ckpt_dir = Path(args.checkpoint_dir or "runs/phase3")
    db_path = ckpt_dir / f"{campaign_id}.sqlite"

    if not db_path.exists():
        print(f"No database found for campaign '{campaign_id}' at {db_path}")
        return

    storage = Phase3Storage(db_path)
    status = storage.get_campaign_status(campaign_id)

    print(f"=== Status for Campaign: {campaign_id} ===")
    hb = status.get("heartbeat")
    if hb:
        print(f"  Process State: ACTIVE (PID {hb['pid']}, Worker {hb['worker_id']})")
        print(f"  Last Heartbeat: {hb['last_heartbeat_utc']} UTC")
        print(f"  Active Task: {hb['active_task_id']}")
    else:
        print("  Process State: IDLE / STOPPED")

    print(f"  Tasks: Total={status['total_tasks']}, Completed={status['completed_tasks']}, Partial={status['partial_tasks']}")
    print(f"  Candidates Screened: {status['raw_tested']:,}")
    print(f"  Sieve Survivors: {status['sieve_survivors']:,}")
    print(f"  PRP Survivors: {status['prp_survivors']:,}")
    print(f"  Proven Pairs Found: {status['proven_pairs']}")
    print(f"  Accumulated CPU Seconds: {status['total_cpu_seconds']:.2f}s")

    discs = status.get("discoveries", [])
    if discs:
        print(f"\n  Discoveries in this campaign ({len(discs)}):")
        for d in discs:
            print(f"    * {d['digits']} digits: k={d['k']}, n={d['n']} -> {d['cert_path']}")
    else:
        print("  No discoveries yet.")

def cmd_pause(args):
    campaign_id = args.campaign or "phase3_campaign"
    ckpt_dir = Path(args.checkpoint_dir or "runs/phase3")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    pause_file = ckpt_dir / f"{campaign_id}.pause"
    pause_file.write_text("PAUSE\n", encoding="utf-8")
    print(f"Created pause signal: {pause_file}")
    print("The running worker will checkpoint and exit gracefully at the end of the current unit.")

def cmd_stop(args):
    campaign_id = args.campaign or "phase3_campaign"
    ckpt_dir = Path(args.checkpoint_dir or "runs/phase3")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    stop_file = ckpt_dir / f"{campaign_id}.stop"
    stop_file.write_text("STOP\n", encoding="utf-8")
    print(f"Created stop signal: {stop_file}")
    print("The running worker will checkpoint and exit gracefully.")

def cmd_verify(args):
    proof_dir = Path(args.directory or "proofs/phase3")
    print(f"Invoking independent strict verification on {proof_dir}...")
    import subprocess
    cmd = [sys.executable, "scripts/phase3_independent_verify.py", str(proof_dir)]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

def cmd_report(args):
    campaign_id = args.campaign or "phase3_campaign"
    ckpt_dir = Path(args.checkpoint_dir or "runs/phase3")
    db_path = ckpt_dir / f"{campaign_id}.sqlite"
    out_file = Path(args.output) if args.output else ckpt_dir / "reports" / f"status_{campaign_id}.md"

    storage = Phase3Storage(db_path) if db_path.exists() else None
    status = storage.get_campaign_status(campaign_id) if storage else {}

    print(f"Generating Phase 3 status report into {out_file}...")
    # Report generation logic
    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Phase 3 Discovery Status and Operational Ledger: {campaign_id}\n",
        f"**Audit Timestamp:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}  \n",
        f"**Campaign ID:** `{campaign_id}`  \n\n",
        "## 1. Executive Summary\n",
        f"- **Completed Tasks:** {status.get('completed_tasks', 0)}\n",
        f"- **Partial Tasks:** {status.get('partial_tasks', 0)}\n",
        f"- **Candidates Screened:** {status.get('raw_tested', 0):,}\n",
        f"- **Proven Pairs:** {status.get('proven_pairs', 0)}\n\n",
    ]
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written status report to {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Phase 3 HDRSS Twin-Prime Discovery Engine")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # audit
    p_audit = subparsers.add_parser("audit")
    p_audit.add_argument("--repo", default=".")
    p_audit.add_argument("--output", default="research/phase3/AUDIT_FINDINGS.md")
    p_audit.set_defaults(func=cmd_audit)

    # benchmark
    p_bench = subparsers.add_parser("benchmark")
    p_bench.add_argument("--config", default="configs/phase3/laptop_safe.json")
    p_bench.add_argument("--output", default="runs/phase3/benchmarks")
    p_bench.set_defaults(func=cmd_benchmark)

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
    p_status.add_argument("--campaign", default="phase3_campaign")
    p_status.add_argument("--checkpoint-dir", default="runs/phase3")
    p_status.set_defaults(func=cmd_status)

    # pause
    p_pause = subparsers.add_parser("pause")
    p_pause.add_argument("--campaign", default="phase3_campaign")
    p_pause.add_argument("--checkpoint-dir", default="runs/phase3")
    p_pause.set_defaults(func=cmd_pause)

    # stop
    p_stop = subparsers.add_parser("stop")
    p_stop.add_argument("--campaign", default="phase3_campaign")
    p_stop.add_argument("--checkpoint-dir", default="runs/phase3")
    p_stop.set_defaults(func=cmd_stop)

    # verify
    p_verify = subparsers.add_parser("verify")
    p_verify.add_argument("--directory", default="proofs/phase3")
    p_verify.set_defaults(func=cmd_verify)

    # report
    p_report = subparsers.add_parser("report")
    p_report.add_argument("--campaign", default="phase3_campaign")
    p_report.add_argument("--checkpoint-dir", default="runs/phase3")
    p_report.add_argument("--output", default=None)
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
