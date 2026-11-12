"""
Phase 4 Storage, Concurrency, and Crash Recovery Tests.
"""

import pytest
import tempfile
from pathlib import Path
from src.phase4.storage import Phase4Storage
from src.phase4.coverage import audit_coverage

def test_atomic_lease_and_heartbeat():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Path(tmp_dir) / "test_lease.sqlite"
        storage = Phase4Storage(db)
        storage.register_tasks_batch([("task_1", "camp1", 3328, 3, 10003)])

        # Claim task
        task = storage.claim_task("camp1", "worker_1", pid=1001, lease_duration_sec=60.0)
        assert task is not None
        assert task["task_id"] == "task_1"
        assert task["lease_token"].startswith("lease_")

        # Second worker cannot claim active lease
        task2 = storage.claim_task("camp1", "worker_2", pid=1002, lease_duration_sec=60.0)
        assert task2 is None

        # Heartbeat extension succeeds
        assert storage.heartbeat_lease(task["lease_token"], 120.0)

def test_expired_lease_automatic_reclaiming():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Path(tmp_dir) / "test_reclaim.sqlite"
        storage = Phase4Storage(db)
        storage.register_tasks_batch([("task_crash", "camp_rec", 3328, 3, 10003)])

        # Worker 1 acquires task with negative duration (immediately expired)
        task = storage.claim_task("camp_rec", "worker_dead", pid=999, lease_duration_sec=-1.0)
        assert task is not None

        # Worker 2 claims next task -> expired task is automatically reclaimed!
        task_reclaimed = storage.claim_task("camp_rec", "worker_alive", pid=1000, lease_duration_sec=60.0)
        assert task_reclaimed is not None
        assert task_reclaimed["task_id"] == "task_crash"

def test_fencing_token_rejects_stale_commit():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Path(tmp_dir) / "test_fencing.sqlite"
        storage = Phase4Storage(db)
        storage.register_tasks_batch([("task_f", "camp_f", 3328, 3, 10003)])

        # Task claimed by worker 1 with expired lease
        t1 = storage.claim_task("camp_f", "worker_1", pid=111, lease_duration_sec=-1.0)
        assert t1 is not None

        # Worker 2 reclaims task
        t2 = storage.claim_task("camp_f", "worker_2", pid=222, lease_duration_sec=60.0)
        assert t2 is not None

        # Worker 1 attempts to commit with stale lease_token -> rejected!
        metrics = {"raw_tested": 1000, "wheel_survivors": 100, "sieve_survivors": 50}
        success = storage.commit_task_progress(
            task_id="task_f",
            lease_token=t1["lease_token"],
            worker_id="worker_1",
            next_k=5003,
            is_completed=False,
            metrics_dict=metrics
        )
        assert not success, "Stale lease token must be rejected by fencing validation"

        # Worker 2 commits with valid lease_token -> succeeds!
        success2 = storage.commit_task_progress(
            task_id="task_f",
            lease_token=t2["lease_token"],
            worker_id="worker_2",
            next_k=10003,
            is_completed=True,
            metrics_dict=metrics
        )
        assert success2

def test_coverage_gap_audit():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Path(tmp_dir) / "test_cov.sqlite"
        storage = Phase4Storage(db)
        # Register contiguous tasks
        storage.register_tasks_batch([
            ("t1", "camp_cov", 3328, 3, 10003),
            ("t2", "camp_cov", 3328, 10003, 20003)
        ])

        cov = audit_coverage(storage, "camp_cov")
        assert 3328 in cov
        assert cov[3328]["is_gap_free"]
        assert len(cov[3328]["gaps"]) == 0
