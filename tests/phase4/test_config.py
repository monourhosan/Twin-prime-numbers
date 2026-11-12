"""
Phase 4 Configuration and CLI Precedence Tests.
"""

import pytest
import tempfile
from pathlib import Path
from src.phase4.config import Phase4Config

def test_default_config_valid():
    cfg = Phase4Config()
    cfg.validate()
    assert cfg.schema_version == "4.0"
    assert cfg.min_digits == 1000
    assert 3328 in cfg.exponents
    assert cfg.k_start == 3

def test_invalid_config_rejections():
    # Bad schema version
    with pytest.raises(ValueError):
        Phase4Config(schema_version="3.0").validate()

    # Bad min_digits
    with pytest.raises(ValueError):
        Phase4Config(min_digits=-5).validate()

    # Empty exponents
    with pytest.raises(ValueError):
        Phase4Config(exponents=[]).validate()

    # Even k_start
    with pytest.raises(ValueError):
        Phase4Config(k_start=4).validate()

    # k_start not divisible by 3
    with pytest.raises(ValueError):
        Phase4Config(k_start=5).validate()

    # k_end <= k_start
    with pytest.raises(ValueError):
        Phase4Config(k_start=9, k_end=5).validate()

def test_canonical_json_and_sha256():
    cfg1 = Phase4Config(campaign_id="test_camp", min_digits=1000)
    cfg2 = Phase4Config(campaign_id="test_camp", min_digits=1000)
    assert cfg1.canonical_json() == cfg2.canonical_json()
    assert cfg1.compute_sha256() == cfg2.compute_sha256()

    cfg3 = Phase4Config(campaign_id="test_camp", min_digits=1500)
    assert cfg1.compute_sha256() != cfg3.compute_sha256()

def test_save_and_load_roundtrip():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cfg = Phase4Config(campaign_id="roundtrip_camp", exponents=[3328, 5120], workers=2)
        cfg.save_to_file(tmp_path)

        loaded = Phase4Config.from_file(tmp_path)
        assert loaded.campaign_id == "roundtrip_camp"
        assert loaded.exponents == [3328, 5120]
        assert loaded.workers == 2
        assert loaded.compute_sha256() == cfg.compute_sha256()
    finally:
        tmp_path.unlink()
