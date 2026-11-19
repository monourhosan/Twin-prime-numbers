"""Unit and Property Tests for Checkpointing & Resumption Engine (`src/phase11/campaign.py`).

Verifies:
  1. Compliance with 7-field canonical checkpoint JSON schema.
  2. Atomic persistence and rename pattern.
  3. Resumption from exact current_t without work duplication.
  4. Detection and handling of corrupted checkpoints.
  5. State roundtrip and recovery under sudden interruption.
"""

import json
from pathlib import Path

from src.phase11.campaign import CampaignOrchestrator
from tests.phase11_e2e.contracts.schemas import validate_checkpoint_schema


def test_checkpoint_schema_conformance(tmp_path: Path) -> None:
    """Verifies generated checkpoint matches all required schema fields."""
    orchestrator = CampaignOrchestrator("test_schema_run", anchor_y=5, t_start=1, t_end=50, output_dir=tmp_path)
    orchestrator.run_work_unit(1, 50)

    ckpt_file = tmp_path / "test_schema_run_checkpoint.json"
    assert ckpt_file.is_file()

    with open(ckpt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    is_valid, errors = validate_checkpoint_schema(data)
    assert is_valid, f"Checkpoint schema validation failed: {errors}"
    assert data["anchor_y"] == 5
    assert data["current_t"] == 50
    assert data["completed_intervals"] == [[1, 50]]


def test_checkpoint_atomic_write_simulation(tmp_path: Path) -> None:
    """Verifies atomic rename leaves zero orphaned temporary files."""
    orchestrator = CampaignOrchestrator("test_atomic_run", anchor_y=3, t_start=1, t_end=20, output_dir=tmp_path)
    orchestrator.save_checkpoint()

    ckpt_file = tmp_path / "test_atomic_run_checkpoint.json"
    tmp_file = ckpt_file.with_suffix(".tmp")

    assert ckpt_file.is_file()
    assert not tmp_file.exists()


def test_checkpoint_resumption_no_duplicate_work(tmp_path: Path) -> None:
    """Verifies a resumed orchestrator continues from current_t with zero overlapping work."""
    # Run first stage [1, 50]
    orch1 = CampaignOrchestrator("resume_run", anchor_y=3, t_start=1, t_end=100, batch_size=50, output_dir=tmp_path)
    orch1.run_work_unit(1, 50)

    # Resume with second orchestrator
    orch2 = CampaignOrchestrator("resume_run", anchor_y=3, t_start=1, t_end=100, batch_size=50, output_dir=tmp_path)
    loaded = orch2.load_checkpoint_if_exists()
    assert loaded is True
    assert orch2.current_t == 50
    assert orch2.completed_intervals == [[1, 50]]

    # Re-executing already completed unit returns empty list (zero duplicate work)
    redundant = orch2.run_work_unit(1, 50)
    assert redundant == []

    # Executing next unit succeeds
    new_survivors = orch2.run_work_unit(51, 100)
    assert orch2.completed_intervals == [[1, 50], [51, 100]]
    assert orch2.current_t == 100
    assert isinstance(new_survivors, list)


def test_checkpoint_roundtrip_integrity(tmp_path: Path) -> None:
    """Verifies state roundtrip across save and reload cycles."""
    orch = CampaignOrchestrator("test_roundtrip", anchor_y=3, t_start=1, t_end=100, output_dir=tmp_path)
    orch.run_work_unit(1, 25)
    orch.run_work_unit(26, 50)

    orch_reloaded = CampaignOrchestrator("test_roundtrip", anchor_y=3, t_start=1, t_end=100, output_dir=tmp_path)
    assert orch_reloaded.load_checkpoint_if_exists() is True
    assert orch_reloaded.current_t == 50
    assert orch_reloaded.completed_intervals == [[1, 25], [26, 50]]
    assert orch_reloaded.survivor_count == orch.survivor_count


def test_checkpoint_truncated_json_handled_gracefully(tmp_path: Path) -> None:
    """Verifies truncated JSON checkpoint does not crash load_checkpoint_if_exists()."""
    orch = CampaignOrchestrator("test_trunc", anchor_y=3, t_start=1, t_end=20, output_dir=tmp_path)
    orch.checkpoint_file.write_text('{"run_id": "test_trunc", "anchor_y": 3, "cur', encoding="utf-8")

    assert orch.load_checkpoint_if_exists() is False
    # Orchestrator execute starts clean without crashing
    res = orch.execute()
    assert res["completed_intervals"] == [[1, 20]]


def test_checkpoint_empty_file_handled_gracefully(tmp_path: Path) -> None:
    """Verifies empty 0-byte checkpoint file does not crash load_checkpoint_if_exists()."""
    orch = CampaignOrchestrator("test_empty", anchor_y=3, t_start=1, t_end=20, output_dir=tmp_path)
    orch.checkpoint_file.write_text("", encoding="utf-8")

    assert orch.load_checkpoint_if_exists() is False


def test_checkpoint_missing_canonical_keys_handled_gracefully(tmp_path: Path) -> None:
    """Verifies missing required canonical keys return False without unhandled KeyError."""
    orch = CampaignOrchestrator("test_missing", anchor_y=3, t_start=1, t_end=20, output_dir=tmp_path)
    orch.checkpoint_file.write_text(json.dumps({"run_id": "test_missing"}), encoding="utf-8")

    assert orch.load_checkpoint_if_exists() is False


def test_checkpoint_invalid_types_handled_gracefully(tmp_path: Path) -> None:
    """Verifies invalid field types return False without unhandled ValueError/TypeError."""
    orch = CampaignOrchestrator("test_invalid_types", anchor_y=3, t_start=1, t_end=20, output_dir=tmp_path)
    invalid_data = {
        "run_id": "test_invalid_types",
        "anchor_y": "not_an_int",
        "current_t": "also_not_int",
        "completed_intervals": "invalid_interval_type",
        "survivor_count": "none",
    }
    orch.checkpoint_file.write_text(json.dumps(invalid_data), encoding="utf-8")

    assert orch.load_checkpoint_if_exists() is False


def test_checkpoint_corrupted_fallback_to_backup(tmp_path: Path) -> None:
    """Verifies that corrupted primary checkpoint seamlessly recovers from .bak backup."""
    orch = CampaignOrchestrator("test_bak_fallback", anchor_y=3, t_start=1, t_end=100, output_dir=tmp_path)

    # Corrupt primary
    orch.checkpoint_file.write_text('{"bad": json', encoding="utf-8")

    # Valid backup
    backup_file = orch.checkpoint_file.with_suffix(".bak")
    backup_data = {
        "run_id": "test_bak_fallback",
        "anchor_y": 3,
        "current_t": 40,
        "completed_intervals": [[1, 40]],
        "survivor_count": 5,
    }
    backup_file.write_text(json.dumps(backup_data), encoding="utf-8")

    assert orch.load_checkpoint_if_exists() is True
    assert orch.current_t == 40
    assert orch.completed_intervals == [[1, 40]]
    assert orch.survivor_count == 5
