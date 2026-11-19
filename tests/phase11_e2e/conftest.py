"""Shared pytest fixtures, configuration, and environment handling for Phase 11 E2E tests."""

import os
import json
import pytest
from pathlib import Path
from typing import Dict, Any, Generator

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_primorial_anchor,
    check_algebraic_invariants,
    generate_reference_certificate,
)
from tests.phase11_e2e.contracts.schemas import (
    compute_canonical_sha256,
    validate_certificate_schema,
    validate_checkpoint_schema,
)


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for Phase 11 E2E test suite tiers."""
    config.addinivalue_line("markers", "phase11_tier1: Tier 1 Feature Coverage tests")
    config.addinivalue_line("markers", "phase11_tier2: Tier 2 Boundary & Corner Case tests")
    config.addinivalue_line("markers", "phase11_tier3: Tier 3 Cross-Feature Combination tests")
    config.addinivalue_line("markers", "phase11_tier4: Tier 4 End-to-End Real-World Workflow tests")
    config.addinivalue_line("markers", "slow: Computationally intensive verification tests")


@pytest.fixture
def adapter() -> type[Phase11ContractAdapter]:
    """Provides access to the unified contract adapter."""
    return Phase11ContractAdapter


@pytest.fixture
def test_mode() -> str:
    """Returns the current test mode (AUTO, LIVE, STUB)."""
    return Phase11ContractAdapter.get_mode()


@pytest.fixture
def sample_anchor() -> tuple[int, int]:
    """Returns a valid primorial anchor (y=5, S_y=30)."""
    y = 5
    Sy, _ = compute_primorial_anchor(y)
    return y, Sy


@pytest.fixture
def sample_coordinates() -> tuple[int, int, int]:
    """Returns (C, A, B) for a small reference coordinate x = 126 (S_3=6, t=21)."""
    return compute_manifold(126)


@pytest.fixture
def sample_checkpoint_data() -> Dict[str, Any]:
    """Returns a valid search checkpoint state dictionary."""
    return {
        "run_id": "run_scaffold_test_01",
        "method_id": "OPQM_CRT_HYBRID_11",
        "anchor_y": 5,
        "current_t": 1000,
        "completed_intervals": [[1, 500], [501, 1000]],
        "survivor_count": 42,
        "timestamp_utc": "2026-11-18T07:00:00.000000+00:00",
    }


@pytest.fixture
def tmp_proofs_dir(tmp_path: Path) -> Path:
    """Creates and returns a temporary directory for proof artifacts."""
    proofs_dir = tmp_path / "proofs" / "phase11"
    proofs_dir.mkdir(parents=True, exist_ok=True)
    return proofs_dir
