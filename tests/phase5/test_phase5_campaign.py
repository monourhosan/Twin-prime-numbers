"""
Unit Tests for Phase 5 Campaign Orchestrator.
Validates campaign directory initialization, metadata snapshots, checkpointing, and resume logic.
"""

import json
import pytest
from pathlib import Path
from src.phase5.campaign import SCCA1510Campaign

def test_campaign_orchestrator_lifecycle(tmp_path):
    # Mock config with a small fast family
    config = {
        "schema_version": "5.0",
        "campaign_id": "test_campaign",
        "historical_inventory": str(Path("research/phase5_audit/historical_inventory.json")),
        "policy": "ROUND_ROBIN",
        "families": [
            {
                "family_id": "fam_toy",
                "exponents": {"2": 1, "3": 2, "5": 1},
                "t_batch_size": 50,
                "sieve_limit": 1000,
                "priority": 1
            }
        ]
    }

    run_id = "test_run_lifecycle_001"
    campaign = SCCA1510Campaign(config=config, run_id=run_id, resume=False)
    
    # Check that directories and metadata were created
    assert campaign.run_dir.exists()
    assert (campaign.run_dir / "config.json").exists()
    assert (campaign.run_dir / "environment.json").exists()
    assert (campaign.run_dir / "historical_inventory_hash.txt").exists()

    # Run 1 work unit
    discoveries = campaign.run_bounded_search(max_work_units=1, stop_on_discovery=False)
    assert campaign.telemetry["work_units_completed"] == 1
    assert (campaign.run_dir / "final_report.md").exists()
    assert (campaign.checkpoints_dir / "checkpoint_seq0001.json").exists()

    # Test resume on same run_id
    resumed_campaign = SCCA1510Campaign(config=config, run_id=run_id, resume=True)
    resumed_campaign.run_bounded_search(max_work_units=1, stop_on_discovery=False)
    assert resumed_campaign.telemetry["work_units_completed"] == 1

    # Cleanup test run directory
    import shutil, gc
    run_dir = campaign.run_dir
    reports_run_dir = campaign.reports_run_dir
    del campaign, resumed_campaign
    gc.collect()
    if run_dir.exists():
        shutil.rmtree(run_dir)
    if reports_run_dir.exists():
        shutil.rmtree(reports_run_dir)
