"""
Unit tests for CoverageManager resumption and gap-free tracking.
"""

from pathlib import Path
import tempfile
from src.phase6.coverage import CoverageManager

def test_coverage_resume_and_manifest():
    """Verify that CoverageManager tracks segments, handles resumption, and exports manifest."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_coverage.db"
        manifest_path = Path(tmp_dir) / "test_manifest.json"
        
        cov = CoverageManager(db_path, manifest_path)
        assert cov.get_max_completed_m() == 0
        
        # Record segment 0: [1000, 2000)
        cov.record_completed_segment(
            segment_id=0,
            m_start=1000,
            m_end=2000,
            survivors=150,
            dual_prps=1,
            proven=0,
            elapsed_sec=0.05,
            timestamp_utc="2026-11-14T05:00:00Z"
        )
        assert cov.get_max_completed_m() == 2000
        assert manifest_path.exists()
        
        # Record segment 1: [2000, 3000)
        cov.record_completed_segment(
            segment_id=1,
            m_start=2000,
            m_end=3000,
            survivors=145,
            dual_prps=0,
            proven=0,
            elapsed_sec=0.04,
            timestamp_utc="2026-11-14T05:00:01Z"
        )
        assert cov.get_max_completed_m() == 3000
        
        # Test reload on new instance
        cov2 = CoverageManager(db_path, manifest_path)
        assert cov2.get_max_completed_m() == 3000
