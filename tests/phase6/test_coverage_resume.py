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

def test_campaign_pause_signal_handling():
    """Verify that GITCSSCampaign safely detects a pause signal file and stops gracefully."""
    import json
    from src.phase6.campaign import GITCSSCampaign

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cfg = {
            "campaign_id": "test_pause_campaign",
            "p_min": "1000",
            "p_max": "100000",
            "sieve_limit": 1000,
            "segment_size": 500,
            "wheel_primes": [5, 7],
            "time_budget_seconds": 60,
            "historical_inventory": "research/phase5_audit/historical_inventory.json"
        }
        campaign = GITCSSCampaign(config=cfg, run_id="test_pause_run")
        # Write .pause file into run_dir before search
        pause_file = campaign.run_dir / ".pause"
        pause_file.write_text("PAUSE", encoding="utf-8")

        discoveries = campaign.run_bounded_search(max_segments=10)
        assert campaign.telemetry["segments_completed"] == 0
        assert not pause_file.exists(), "Pause file should be cleaned up upon handling"
        # Cleanup test campaign run dir
        import shutil, gc
        run_dir = campaign.run_dir
        del campaign
        gc.collect()
        if run_dir.exists():
            try:
                shutil.rmtree(run_dir)
            except Exception:
                pass
