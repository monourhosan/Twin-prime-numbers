"""
Reproducible Phase 5 Multi-Family Scheduler Experiment.
Compares:
1. Round-Robin (ROUND_ROBIN)
2. UCB1 with cumulative mean (BANDIT_UCB1)
3. Cost-Aware Bandit (COST_AWARE)
Across three mathematically distinct SCCA families on a fixed compute budget.
Generates raw machine-readable telemetry JSON and markdown summary.
"""

import sys
import os
import time
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.phase5.storage import Phase5Storage
from src.phase5.scheduler import MultiFamilyScheduler, SCCAProfile, SchedulingPolicy
from src.phase5.cli import execute_discovery_search

def run_scheduler_benchmark(
    policy: SchedulingPolicy,
    profiles: List[SCCAProfile],
    total_allocations: int,
    db_path: Path,
    proofs_dir: Path,
    hist_inv_path: Path
) -> Dict[str, Any]:
    """Runs a fixed budget of work units under the given scheduling policy."""
    if db_path.exists():
        db_path.unlink()
    if proofs_dir.exists():
        shutil.rmtree(proofs_dir)
    proofs_dir.mkdir(parents=True, exist_ok=True)

    storage = Phase5Storage(db_path)
    scheduler = MultiFamilyScheduler(
        storage=storage,
        profiles=profiles,
        policy=policy,
        seed=42,
        min_exploration_pulls=2,
        ucb_c=1.414,
        resume=False
    )

    t_start_total = time.time()
    unit_logs = []

    for u_idx in range(total_allocations):
        wu = scheduler.dispense_work_unit()
        prof = wu["profile"]
        fid = wu["family_id"]
        t_start = wu["t_start"]
        t_end = wu["t_end"]
        
        t0 = time.time()
        finds = execute_discovery_search(
            storage=storage,
            profile=prof,
            t_start=t_start,
            t_end=t_end,
            output_dir=proofs_dir,
            historical_inventory_path=hist_inv_path,
            max_finds=10,
            verbose=False
        )
        elapsed = time.time() - t0
        storage.complete_work_unit(wu["work_unit_id"], survivors=0, dual_prp=0, proven=len(finds))

        b_stats = storage.get_bandit_stats().get(fid, {})
        unit_logs.append({
            "allocation_index": u_idx + 1,
            "family_id": fid,
            "t_range": [t_start, t_end],
            "batch_size": t_end - t_start,
            "elapsed_sec": elapsed,
            "proven_count": len(finds),
            "rationale": wu["rationale"],
            "cumulative_pulls": b_stats.get("pulls", 0),
            "cumulative_reward": b_stats.get("cumulative_reward", 0.0),
            "mean_reward": b_stats.get("mean_reward", 0.0),
            "total_family_time": b_stats.get("total_time", 0.0)
        })

    total_wall_time = time.time() - t_start_total
    final_stats = storage.get_bandit_stats()

    total_screened = sum(u["batch_size"] for u in unit_logs)
    total_proven = sum(u["proven_count"] for u in unit_logs)

    return {
        "policy": policy.value,
        "total_allocations": total_allocations,
        "total_wall_time_sec": total_wall_time,
        "total_screened_candidates": total_screened,
        "total_proven_pairs": total_proven,
        "candidates_per_sec": total_screened / max(total_wall_time, 0.001),
        "family_summary": final_stats,
        "allocations": unit_logs
    }

def main():
    print("=" * 60)
    print("STAGE D: SCCA MULTI-FAMILY & SCHEDULER EXPERIMENT")
    print("=" * 60)

    # Define 3 distinct families
    # 1. Dense power of 3: base {2, 3, 5}
    fam1 = SCCAProfile(
        family_id="fam_scca_p3_dense",
        exponents={2: 1, 3: 40, 5: 10},
        t_batch_size=500,
        sieve_limit=50000,
        priority=1
    )
    # 2. Balanced multibase: base {2, 3, 5, 7, 11}
    fam2 = SCCAProfile(
        family_id="fam_scca_balanced_multibase",
        exponents={2: 3, 3: 20, 5: 10, 7: 6, 11: 3},
        t_batch_size=500,
        sieve_limit=50000,
        priority=2
    )
    # 3. Sparse highbase: base {2, 3, 7, 13, 17} (skips 5)
    fam3 = SCCAProfile(
        family_id="fam_scca_sparse_highbase",
        exponents={2: 2, 3: 25, 7: 10, 13: 5, 17: 3},
        t_batch_size=500,
        sieve_limit=50000,
        priority=3
    )

    profiles = [fam1, fam2, fam3]
    for p in profiles:
        print(f"Family {p.family_id}:")
        print(f"  F digits: {len(str(p.family.F))}, bits: {p.family.F.bit_length()}")
        print(f"  Odd factors: {p.family.odd_prime_factors}")

    hist_inv_path = REPO_ROOT / "research" / "phase5_audit" / "historical_inventory.json"
    bench_dir = REPO_ROOT / "research" / "phase5_benchmarks"
    raw_dir = bench_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    policies = [
        SchedulingPolicy.ROUND_ROBIN,
        SchedulingPolicy.BANDIT_UCB1,
        SchedulingPolicy.COST_AWARE
    ]

    results = {}
    allocations_budget = 12 # 12 allocations each (4 per family in round robin)

    for pol in policies:
        print(f"\nRunning benchmark for policy: {pol.value} (Budget = {allocations_budget} allocations)...")
        db_path = REPO_ROOT / "runs" / "phase5" / f"bench_{pol.value.lower()}.db"
        proofs_dir = REPO_ROOT / "runs" / "phase5" / f"proofs_{pol.value.lower()}"
        res = run_scheduler_benchmark(pol, profiles, allocations_budget, db_path, proofs_dir, hist_inv_path)
        results[pol.value] = res
        print(f"  Completed {allocations_budget} allocations in {res['total_wall_time_sec']:.2f}s ({res['candidates_per_sec']:,.0f} cands/s)")

    out_json = raw_dir / "scheduler_comparison.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Mirror into reports/phase5_benchmarks/raw
    reports_raw = REPO_ROOT / "reports" / "phase5_benchmarks" / "raw"
    reports_raw.mkdir(parents=True, exist_ok=True)
    with open(reports_raw / "scheduler_comparison.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved raw benchmark data to: {out_json}")

if __name__ == "__main__":
    main()
