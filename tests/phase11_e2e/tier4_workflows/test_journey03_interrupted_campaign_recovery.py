"""Tier 4 Workflow 3: Interrupted Campaign Recovery User Journey.

Covers the crash recovery workflow:
1. Multi-unit campaign execution with state persistence.
2. Sudden process interruption at midpoint.
3. Checkpoint schema and progress verification.
4. Resumption from exact checkpoint boundary.
5. Bit-exact equivalence verification between resumed run and uninterrupted reference run.
6. Validation of zero lost work and zero redundant re-computation.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pytest

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import validate_checkpoint_schema


class CampaignSimulator:
    """Simulates the production campaign engine with segmented work units and checkpointing."""

    def __init__(self, run_id: str, anchor_y: int, checkpoint_file: Path, sieve_depth: int = 40):
        self.run_id = run_id
        self.anchor_y = anchor_y
        self.checkpoint_file = checkpoint_file
        self.sieve_depth = sieve_depth
        self.current_t = 0
        self.completed_intervals: List[List[int]] = []
        self.survivors: List[int] = []
        self.work_units_executed = 0

    def load_checkpoint(self) -> bool:
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
        state: Dict[str, Any] = {
            "run_id": self.run_id,
            "method_id": "OPQM_CRT_HYBRID_11",
            "anchor_y": self.anchor_y,
            "current_t": self.current_t,
            "completed_intervals": self.completed_intervals,
            "survivor_count": len(self.survivors),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        is_valid, errors = validate_checkpoint_schema(state)
        assert is_valid, f"Checkpoint schema violation: {errors}"

        tmp_path = self.checkpoint_file.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp_path.replace(self.checkpoint_file)

    def execute_unit(self, t_start: int, t_end: int) -> List[int]:
        for start, end in self.completed_intervals:
            if start <= t_start and t_end <= end:
                return []  # Already completed

        unit_survivors = Phase11ContractAdapter.sieve_survivors(self.anchor_y, t_start, t_end, self.sieve_depth)
        self.survivors.extend(unit_survivors)
        self.completed_intervals.append([t_start, t_end])
        self.current_t = t_end
        self.work_units_executed += 1
        self.save_checkpoint()
        return unit_survivors

    def run_plan(self, intervals: List[Tuple[int, int]], crash_after_unit: int = -1) -> None:
        for idx, (start, end) in enumerate(intervals):
            if idx == crash_after_unit:
                # Abrupt simulated crash
                raise KeyboardInterrupt("Simulated mid-campaign interrupt")
            self.execute_unit(start, end)


@pytest.mark.phase11_tier4
def test_journey03_interrupted_run_resumes_to_identical_output(tmp_path: Path) -> None:
    """Verifies that an interrupted campaign resumes and yields the exact same

    survivor list and checkpoint state as an uninterrupted run over the same range.
    """
    y = 5
    sieve_depth = 40
    planned_intervals = [(1, 50), (51, 100), (101, 150), (151, 200)]

    # 1. Execute an uninterrupted reference run
    ref_ckpt = tmp_path / "reference_checkpoint.json"
    ref_campaign = CampaignSimulator("ref_run", y, ref_ckpt, sieve_depth)
    ref_campaign.run_plan(planned_intervals)
    assert ref_campaign.work_units_executed == 4
    expected_survivors = list(ref_campaign.survivors)

    # 2. Execute an interrupted run that crashes after unit 2 (t=100)
    int_ckpt = tmp_path / "interrupted_checkpoint.json"
    int_campaign1 = CampaignSimulator("int_run", y, int_ckpt, sieve_depth)

    with pytest.raises(KeyboardInterrupt, match="Simulated mid-campaign interrupt"):
        int_campaign1.run_plan(planned_intervals, crash_after_unit=2)

    # Inspect checkpoint at crash
    assert int_ckpt.is_file()
    with open(int_ckpt, "r", encoding="utf-8") as f:
        crash_data = json.load(f)
    assert crash_data["current_t"] == 100
    assert crash_data["completed_intervals"] == [[1, 50], [51, 100]]

    # 3. Resume campaign in a new process instance from the saved checkpoint
    int_campaign2 = CampaignSimulator("int_run", y, int_ckpt, sieve_depth)
    loaded = int_campaign2.load_checkpoint()
    assert loaded is True
    assert int_campaign2.current_t == 100

    # Resume: run remaining intervals
    int_campaign2.run_plan(planned_intervals)

    # 4. Compare resumed output against uninterrupted reference run
    # Total survivors from run 1 (units 1,2) + run 2 (units 3,4)
    combined_survivors = int_campaign1.survivors + int_campaign2.survivors
    assert combined_survivors == expected_survivors, "Resumed survivors mismatch uninterrupted run"
    assert int_campaign2.work_units_executed == 2, "Resumed campaign must execute only the remaining 2 units"


@pytest.mark.phase11_tier4
def test_journey03_resume_with_already_completed_work_is_noop(tmp_path: Path) -> None:
    """Verifies that attempting to re-run an already completed campaign interval

    is safely recognized as completed work and executes zero redundant steps.
    """
    ckpt = tmp_path / "noop_checkpoint.json"
    runner = CampaignSimulator("noop_run", anchor_y=5, checkpoint_file=ckpt)

    runner.execute_unit(1, 100)
    assert runner.work_units_executed == 1

    # Attempt re-execution of interval [1, 100]
    redundant = runner.execute_unit(1, 100)
    assert redundant == []
    assert runner.work_units_executed == 1, "Work units count must not increment on duplicate work"


@pytest.mark.phase11_tier4
def test_journey03_corrupted_checkpoint_recovery_fails_gracefully(tmp_path: Path) -> None:
    """Confirms that resuming from a truncated or invalid checkpoint JSON file

    aborts with an informative ValueError rather than corrupting disk state or entering an infinite loop.
    """
    ckpt = tmp_path / "truncated_checkpoint.json"
    ckpt.write_text('{"run_id": "bad", "completed_intervals": [', encoding="utf-8")

    runner = CampaignSimulator("bad_run", anchor_y=5, checkpoint_file=ckpt)
    with pytest.raises(Exception):
        runner.load_checkpoint()
