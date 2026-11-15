"""
Regression tests for Phase 5 Campaign Status CLI (P1-D).
Verifies:
- Custom DB path is correctly read and displayed.
- Config-specified DB path is correctly resolved.
- Missing DB reports clearly and does not silently instantiate a blank DB.
- Multiple campaigns have isolated status outputs.
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.phase5.cli import run_status
from src.phase5.storage import Phase5Storage

def test_status_reads_custom_db_path(capsys):
    """Scenario 15: status --db reads and outputs the exact specified database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "custom_campaign.db"
        storage = Phase5Storage(db_path)
        storage.record_discovery("fam_a", 10, 15, 10007, 10009, "c.json", "sha_x", "NEW_TO_REPO_ONLY")
        
        class Args:
            db = str(db_path)
            config = None
            campaign = "custom"
            
        run_status(Args())
        captured = capsys.readouterr().out
        assert str(db_path.resolve()) in captured
        assert "Discoveries: 1" in captured
        assert "fam_a" in captured

def test_status_missing_db_does_not_instantiate(capsys):
    """Scenario 16: status on nonexistent DB reports clearly without creating it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = Path(tmpdir) / "no_such_db.db"
        assert not nonexistent.exists()
        
        class Args:
            db = str(nonexistent)
            config = None
            campaign = "test"
            
        run_status(Args())
        captured = capsys.readouterr().out
        assert "No database found" in captured
        assert not nonexistent.exists(), "Status must not instantiate blank DB"

def test_isolated_multiple_campaigns(capsys):
    """Multiple campaigns with distinct DB paths maintain isolated metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db1 = Path(tmpdir) / "c1.db"
        db2 = Path(tmpdir) / "c2.db"
        
        s1 = Phase5Storage(db1)
        s1.record_discovery("fam1", 1, 10, 101, 103, "c1.json", "sha1", "NEW_TO_REPO_ONLY")
        
        s2 = Phase5Storage(db2)
        s2.record_discovery("fam2", 2, 20, 201, 203, "c2.json", "sha2", "NEW_TO_REPO_ONLY")
        
        class Args1:
            db = str(db1)
            config = None
            campaign = "c1"
        run_status(Args1())
        out1 = capsys.readouterr().out
        assert "fam1" in out1
        assert "fam2" not in out1
        
        class Args2:
            db = str(db2)
            config = None
            campaign = "c2"
        run_status(Args2())
        out2 = capsys.readouterr().out
        assert "fam2" in out2
        assert "fam1" not in out2
