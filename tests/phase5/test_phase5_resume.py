"""
Unit Tests for Phase 5 Durable Storage, Checkpoint Resumption, and Crash Recovery.
"""

import time
import pytest
from pathlib import Path
from src.phase5.storage import Phase5Storage

@pytest.fixture
def temp_storage(tmp_path):
    db_path = tmp_path / "test_storage.db"
    return Phase5Storage(db_path)

def test_work_unit_registration(temp_storage):
    cfg = {"family_id": "fam1", "exponents": {"2": 1, "3": 1}}
    ok1 = temp_storage.register_work_unit("wu1", "fam1", cfg, 1, 100, 5000)
    assert ok1 is True

    # Duplicate registration should be ignored
    ok2 = temp_storage.register_work_unit("wu1", "fam1", cfg, 1, 100, 5000)
    assert ok2 is False

def test_work_unit_atomic_leasing(temp_storage):
    cfg = {"family_id": "fam1", "exponents": {"2": 1, "3": 1}}
    temp_storage.register_work_unit("wu1", "fam1", cfg, 1, 100, 5000)

    # First worker acquires lease
    leased = temp_storage.lease_work_unit("worker_1", lease_duration_sec=10.0)
    assert leased is not None
    assert leased["work_unit_id"] == "wu1"

    # Second worker should get None (no work available)
    none_work = temp_storage.lease_work_unit("worker_2", lease_duration_sec=10.0)
    assert none_work is None

def test_crash_recovery_expired_lease_reclaim(temp_storage):
    cfg = {"family_id": "fam1", "exponents": {"2": 1, "3": 1}}
    temp_storage.register_work_unit("wu_crash", "fam1", cfg, 1, 100, 5000)

    # Worker 1 leases with very short lease (0.01 sec) and "crashes"
    _ = temp_storage.lease_work_unit("crashed_worker", lease_duration_sec=0.01)
    time.sleep(0.05) # Let lease expire

    # Worker 2 attempts to lease -> should reclaim expired lease!
    reclaimed = temp_storage.lease_work_unit("recovery_worker", lease_duration_sec=10.0)
    assert reclaimed is not None
    assert reclaimed["work_unit_id"] == "wu_crash"

def test_deduplication_ledger(temp_storage):
    hash_val = "test_canonical_hash_12345"
    assert temp_storage.is_known_discovery(hash_val) is False

    temp_storage.record_candidate("fam1", 10, 100, 102, 3, "PROVEN_BOTH", hash_val)
    assert temp_storage.is_known_discovery(hash_val) is True

def test_bandit_stats_accumulation(temp_storage):
    temp_storage.update_bandit_stats("fam1", elapsed_sec=1.0, survivors=50, dual_prp=2, proven=1)
    stats = temp_storage.get_bandit_stats()
    assert "fam1" in stats
    assert stats["fam1"]["pulls"] == 1
    assert stats["fam1"]["proven"] == 1

    temp_storage.update_bandit_stats("fam1", elapsed_sec=2.0, survivors=30, dual_prp=1, proven=0)
    stats2 = temp_storage.get_bandit_stats()
    assert stats2["fam1"]["pulls"] == 2
    assert stats2["fam1"]["total_time"] == 3.0
    assert stats2["fam1"]["survivors"] == 80
