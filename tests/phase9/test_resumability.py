"""
Tests for Phase 9 Campaign Checkpoint, Interruption, and Resumption.
Verifies that no candidates are duplicated or skipped across interrupted runs.
"""

import tempfile
import json
from pathlib import Path
import pytest

from src.phase9.campaign import CampaignOrchestrator


def test_campaign_resumption_integrity():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Run batch 1: t in [1, 51]
        orch1 = CampaignOrchestrator(
            campaign_id="test_resume",
            anchor_y=5,
            t_start=1,
            t_end=51,
            sieve_depth=500,
            batch_size=10,
            use_gpu=False,
            stop_on_first_discovery=False,
            data_dir=tmp_path
        )
        s1 = orch1.run()
        first_current_t = orch1.current_t
        first_candidates = orch1.sieve_candidates_total
        assert first_current_t > 51

        # Now resume from the checkpoint
        orch2 = CampaignOrchestrator(
            campaign_id="test_resume",
            anchor_y=5,
            t_start=1,
            t_end=101,
            sieve_depth=500,
            batch_size=10,
            use_gpu=False,
            stop_on_first_discovery=False,
            data_dir=tmp_path
        )
        assert orch2.current_t == first_current_t
        assert orch2.sieve_candidates_total == first_candidates

        # Continue up to 101
        s2 = orch2.run()
        assert orch2.current_t > 101
        # Total candidates must match exact count for [1, 101]
        expected_total = (101 - 1) // 2 + 1
        assert orch2.sieve_candidates_total == expected_total
