"""Tier 3 Integration Suite 6: Checkpoint & Resume Engine (F12) x Staged Campaigns (F14).

Validates the pairwise interaction between:
1. Checkpoint & Resume Engine (atomic JSON writes, schema validation, state persistence).
2. Staged Discovery Campaigns (bounded work units, stage transitions, crash recovery, zero redundant work).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import validate_checkpoint_schema


class MockCampaignRunner:
    """Simulates the production campaign runner for testing checkpoint/resume interactions."""

    def __init__(self, run_id: str, anchor_y: int, checkpoint_file: Path):
        self.run_id = run_id
        self.anchor_y = anchor_y
        self.checkpoint_file = checkpoint_file
        self.current_t = 0
        self.completed_intervals = []
        self.survivors = []
        self.work_units_executed = 0

    def load_checkpoint_if_exists(self) -> bool:
        if not self.checkpoint_file.is_file():
            return False
        with open(self.checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        is_valid, errors = validate_checkpoint_schema(data)
        if not is_valid:
            raise ValueError(f"Corrupted checkpoint: {errors}")
        self.run_id = data["run_id"]
        self.anchor_y = data["anchor_y"]
        self.current_t = data["current_t"]
        self.completed_intervals = [list(interval) for interval in data["completed_intervals"]]
        return True

    def save_checkpoint(self) -> None:
        state = {
            "run_id": self.run_id,
            "method_id": "OPQM_CRT_HYBRID_11",
            "anchor_y": self.anchor_y,
            "current_t": self.current_t,
            "completed_intervals": self.completed_intervals,
            "survivor_count": len(self.survivors),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        is_valid, errors = validate_checkpoint_schema(state)
        assert is_valid, f"Generated checkpoint violates schema: {errors}"

        # Atomic write pattern: write to tmp then atomic rename
        tmp_path = self.checkpoint_file.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp_path.replace(self.checkpoint_file)

    def execute_bounded_unit(self, t_start: int, t_end: int, sieve_depth: int = 50) -> List[int]:
        # Check for duplicate execution
        for interval in self.completed_intervals:
            if interval[0] <= t_start and t_end <= interval[1]:
                return []  # Already completed, zero redundant work

        unit_survivors = Phase11ContractAdapter.sieve_survivors(self.anchor_y, t_start, t_end, sieve_depth)
        self.survivors.extend(unit_survivors)
        self.completed_intervals.append([t_start, t_end])
        self.current_t = t_end
        self.work_units_executed += 1
        self.save_checkpoint()
        return unit_survivors


@pytest.mark.phase11_tier3
def test_combo_campaign_checkpoints_atomically_per_work_unit(tmp_path: Path) -> None:
    """Verifies that the campaign engine creates a valid, compliant checkpoint

    after executing each bounded work unit.
    """
    ckpt_path = tmp_path / "checkpoint_stage1.json"
    runner = MockCampaignRunner("run_test_atomic", anchor_y=5, checkpoint_file=ckpt_path)

    runner.execute_bounded_unit(1, 100)
    assert ckpt_path.is_file()

    with open(ckpt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    is_valid, errors = validate_checkpoint_schema(data)
    assert is_valid is True, f"Checkpoint invalid: {errors}"
    assert data["current_t"] == 100
    assert data["completed_intervals"] == [[1, 100]]


@pytest.mark.phase11_tier3
def test_combo_interrupted_campaign_resumes_without_duplicate_work(tmp_path: Path) -> None:
    """Confirms that when a campaign is interrupted, a new runner resuming from the checkpoint

    resumes exactly from current_t and performs zero redundant computation on prior intervals.
    """
    ckpt_path = tmp_path / "checkpoint_resume.json"

    # Run 1: completes intervals [1, 50] and [51, 100]
    runner1 = MockCampaignRunner("run_resume", anchor_y=5, checkpoint_file=ckpt_path)
    res1_1 = runner1.execute_bounded_unit(1, 50)
    res1_2 = runner1.execute_bounded_unit(51, 100)
    assert runner1.work_units_executed == 2

    # Simulate crash and resume with Run 2
    runner2 = MockCampaignRunner("run_resume", anchor_y=5, checkpoint_file=ckpt_path)
    resumed = runner2.load_checkpoint_if_exists()
    assert resumed is True
    assert runner2.current_t == 100
    assert runner2.completed_intervals == [[1, 50], [51, 100]]

    # Resuming attempts to re-execute interval [1, 50] -> should be skipped
    redundant_result = runner2.execute_bounded_unit(1, 50)
    assert redundant_result == []
    assert runner2.work_units_executed == 0  # Zero redundant work executed

    # Resumed runner executes next interval [101, 150]
    res2_next = runner2.execute_bounded_unit(101, 150)
    assert runner2.work_units_executed == 1
    assert runner2.current_t == 150
    assert len(runner2.completed_intervals) == 3


@pytest.mark.phase11_tier3
def test_combo_staged_campaign_monotonic_progress_invariant(tmp_path: Path) -> None:
    """Verifies that across multiple stage intervals, current_t strictly monotonically increases

    and completed_intervals form an ordered, contiguous progression.
    """
    ckpt_path = tmp_path / "checkpoint_monotonic.json"
    runner = MockCampaignRunner("run_monotonic", anchor_y=5, checkpoint_file=ckpt_path)

    intervals = [(1, 20), (21, 40), (41, 60), (61, 80)]
    for start, end in intervals:
        runner.execute_bounded_unit(start, end)
        assert runner.current_t == end

    with open(ckpt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check contiguous sequence
    for i in range(len(data["completed_intervals"]) - 1):
        prev_end = data["completed_intervals"][i][1]
        next_start = data["completed_intervals"][i + 1][0]
        assert next_start == prev_end + 1, f"Gap or overlap between intervals: {prev_end} -> {next_start}"


@pytest.mark.phase11_tier3
def test_combo_campaign_detects_corrupted_checkpoint(tmp_path: Path) -> None:
    """Confirms that the campaign engine safely catches and rejects a corrupted

    or malformed checkpoint JSON without silently corrupting search state.
    """
    ckpt_path = tmp_path / "checkpoint_corrupted.json"
    # Write corrupted data missing required fields
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump({"run_id": "corrupted", "current_t": -10}, f)

    runner = MockCampaignRunner("run_corrupt", anchor_y=5, checkpoint_file=ckpt_path)
    with pytest.raises(ValueError, match="Corrupted checkpoint"):
        runner.load_checkpoint_if_exists()
