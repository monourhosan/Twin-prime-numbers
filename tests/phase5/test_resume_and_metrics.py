"""
Regression tests for Work-Unit Metrics and Resume Integrity (P1-F).
Verifies:
- complete_work_unit persists measured survivors and PRP counts rather than fabricated zeros.
- Partial work-unit with interrupted verification resumes safely without duplicate discoveries.
- Legacy SQLite schemas migrate or read safely.
"""

import sqlite3
import tempfile
from pathlib import Path
import pytest

from src.phase5.storage import Phase5Storage

def test_complete_work_unit_persists_actual_measurements():
    """Scenario 18: Measured survivor and PRP counts are persisted faithfully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Phase5Storage(db_path)
        
        wu_id = "wu_test_1"
        storage.register_work_unit(wu_id, "fam_x", {"sieve_limit": 100}, 1, 1000, 100)
        
        # Complete with measured telemetry
        storage.complete_work_unit(wu_id, survivors=142, dual_prp=3, proven=1)
        
        with storage._get_connection() as conn:
            row = conn.execute("SELECT survivors, dual_prp, proven, status FROM work_units WHERE work_unit_id = ?", (wu_id,)).fetchone()
            assert row["status"] == "COMPLETE"
            assert row["survivors"] == 142
            assert row["dual_prp"] == 3
            assert row["proven"] == 1

def test_interrupted_verification_resumes_without_duplicate():
    """Scenario 17: Partial work unit with interrupted verification resumes cleanly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Phase5Storage(db_path)
        
        wu_id = "wu_test_2"
        storage.register_work_unit(wu_id, "fam_x", {"sieve_limit": 100}, 1, 1000, 100)
        
        # Lease unit
        leased = storage.lease_work_unit("worker_1", lease_duration_sec=0.1) # short expiry
        assert leased is not None
        
        # Interrupted: candidate recorded as VERIFICATION_FAILED or PRP_BOTH, but NOT discovery
        pair_id = storage.canonical_pair_id(1019, 1021)
        storage.record_candidate("fam_x", 4, 1019, 1021, 4, "VERIFICATION_FAILED", pair_id)
        
        # No discovery was recorded
        with storage._get_connection() as conn:
            assert len(conn.execute("SELECT * FROM discoveries").fetchall()) == 0
            
        # Re-lease after lease expiry
        import time
        time.sleep(0.15)
        re_leased = storage.lease_work_unit("worker_2", lease_duration_sec=60.0)
        assert re_leased is not None
        assert re_leased["work_unit_id"] == wu_id

def test_legacy_schema_migration_preserves_data():
    """Legacy database without pair_id column migrates cleanly without data loss."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "legacy.db"
        # Create legacy schema without pair_id in discoveries
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
        CREATE TABLE discoveries (
            discovery_id TEXT PRIMARY KEY,
            family_id TEXT NOT NULL,
            t INTEGER NOT NULL,
            digits INTEGER NOT NULL,
            A_str TEXT NOT NULL,
            B_str TEXT NOT NULL,
            cert_path TEXT NOT NULL,
            sha256 TEXT NOT NULL UNIQUE,
            novelty_status TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        """)
        conn.execute("""
        INSERT INTO discoveries VALUES ('disc_1', 'fam', 1, 4, '1019', '1021', 'c.json', 'sha_old', 'NEW_TO_REPO_ONLY', 12345.0);
        """)
        conn.commit()
        conn.close()
        
        # Instantiate Phase5Storage -> must migrate automatically
        storage = Phase5Storage(db_path)
        with storage._get_connection() as conn:
            cols = [col["name"] for col in conn.execute("PRAGMA table_info(discoveries)").fetchall()]
            assert "pair_id" in cols
            row = conn.execute("SELECT * FROM discoveries WHERE discovery_id = 'disc_1'").fetchone()
            assert row["A_str"] == "1019"
            assert row["sha256"] == "sha_old"
