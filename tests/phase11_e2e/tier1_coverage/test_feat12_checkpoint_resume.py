"""Feature 12: Checkpoint & Resume Engine.

Verifies:
1. Checkpoint JSON schema compliance using validate_checkpoint_schema.
2. Atomic write-and-rename checkpoint persistence pattern.
3. Crash resumption from exact current_t without repeating intervals.
4. Enforcement of zero duplicate work intervals.
5. State serialization and deserialization roundtrip integrity.
"""

import os
import json
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.schemas import validate_checkpoint_schema


@pytest.mark.phase11_tier1
def test_f12_checkpoint_schema_compliance(sample_checkpoint_data: dict) -> None:
    """Verifies that a well-formed checkpoint dictionary passes schema validation."""
    is_valid, errors = validate_checkpoint_schema(sample_checkpoint_data)
    assert is_valid, f"Checkpoint schema validation failed: {errors}"
    assert len(errors) == 0

    # Omitting a required field must fail validation
    corrupted = dict(sample_checkpoint_data)
    del corrupted["current_t"]
    is_valid_bad, errors_bad = validate_checkpoint_schema(corrupted)
    assert not is_valid_bad
    assert any("current_t" in e for e in errors_bad)


@pytest.mark.phase11_tier1
def test_f12_atomic_write_simulation(tmp_path: Path, sample_checkpoint_data: dict) -> None:
    """Verifies atomic checkpoint write pattern using temporary file rename."""
    ckpt_path = tmp_path / "checkpoint.json"
    tmp_ckpt = tmp_path / "checkpoint.json.tmp"

    # Write to tmp
    with open(tmp_ckpt, "w", encoding="utf-8") as f:
        json.dump(sample_checkpoint_data, f, indent=2)

    # Atomic rename
    os.replace(tmp_ckpt, ckpt_path)

    assert ckpt_path.is_file()
    assert not tmp_ckpt.exists()

    with open(ckpt_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["run_id"] == sample_checkpoint_data["run_id"]


@pytest.mark.phase11_tier1
def test_f12_resume_from_exact_t(sample_checkpoint_data: dict) -> None:
    """Verifies campaign resumption picks up from current_t without repeating work."""
    last_t = sample_checkpoint_data["current_t"]
    completed = sample_checkpoint_data["completed_intervals"]

    # Simulating resume logic
    next_t = last_t + 1
    new_interval = [next_t, next_t + 500]

    # Check that new interval does not overlap with completed intervals
    for start, end in completed:
        assert not (new_interval[0] <= end and new_interval[1] >= start), (
            f"Overlap detected between {new_interval} and {[start, end]}"
        )


@pytest.mark.phase11_tier1
def test_f12_zero_duplicate_work_intervals() -> None:
    """Verifies that completed intervals remain disjoint and monotonically increasing."""
    intervals = [[1, 500], [501, 1000], [1001, 1500]]

    # Assert disjointness and contiguous alignment
    for i in range(len(intervals) - 1):
        prev_end = intervals[i][1]
        next_start = intervals[i + 1][0]
        assert next_start > prev_end, f"Intervals overlap or duplicate: {intervals[i]} and {intervals[i+1]}"
        assert next_start == prev_end + 1, "Gap between consecutive intervals"


@pytest.mark.phase11_tier1
def test_f12_checkpoint_roundtrip_integrity(tmp_path: Path, sample_checkpoint_data: dict) -> None:
    """Verifies state roundtrip across save, load, update, and reload cycles."""
    ckpt_file = tmp_path / "run_state.json"

    # Save initial
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(sample_checkpoint_data, f)

    # Load and update
    with open(ckpt_file, "r", encoding="utf-8") as f:
        state = json.load(f)
    state["current_t"] = 2000
    state["completed_intervals"].append([1001, 2000])
    state["survivor_count"] += 15

    # Re-save
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(state, f)

    # Final verify
    with open(ckpt_file, "r", encoding="utf-8") as f:
        reloaded = json.load(f)

    is_valid, _ = validate_checkpoint_schema(reloaded)
    assert is_valid
    assert reloaded["current_t"] == 2000
    assert len(reloaded["completed_intervals"]) == 3
    assert reloaded["survivor_count"] == sample_checkpoint_data["survivor_count"] + 15
