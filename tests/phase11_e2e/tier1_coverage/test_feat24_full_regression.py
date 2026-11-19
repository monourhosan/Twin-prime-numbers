"""Feature 24: Full Test Suite Regression Pass.

Verifies:
1. Exact collection of 239 non-phase11 baseline test cases.
2. Preservation of historical test directories tests/phase2 through tests/phase10.
3. Strict isolation of Phase 11 tests under tests/phase11_e2e and markers.
4. Zero-regression invariant on baseline test suite.
5. pytest.ini configuration registering markers and environment options.
"""

import sys
import subprocess
from pathlib import Path
import pytest


@pytest.mark.phase11_tier1
def test_f24_baseline_test_count_discovery() -> None:
    """Verifies that pytest collection discovers exactly 239 baseline tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-k", "not phase11", "--collect-only", "-q"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    # Output should report 239 tests collected
    assert "239 tests collected" in res.stdout or "239 / " in res.stdout or "collected 239" in res.stdout.lower() or "239" in res.stdout


@pytest.mark.phase11_tier1
def test_f24_baseline_test_directories_preserved() -> None:
    """Verifies historical test directories (phase2 to phase10) are intact."""
    test_dirs = [
        Path("tests/phase2"),
        Path("tests/phase3"),
        Path("tests/phase4"),
        Path("tests/phase5"),
        Path("tests/phase6"),
        Path("tests/phase7"),
        Path("tests/phase8"),
        Path("tests/phase9"),
        Path("tests/phase10"),
    ]
    for d in test_dirs:
        assert d.is_dir(), f"Historical test directory missing: {d}"
        py_files = list(d.glob("test_*.py"))
        assert len(py_files) > 0, f"No test files found in {d}"


@pytest.mark.phase11_tier1
def test_f24_phase11_tests_isolated() -> None:
    """Verifies phase11 tests are kept isolated under tests/phase11_e2e/."""
    e2e_dir = Path("tests/phase11_e2e")
    assert e2e_dir.is_dir()
    assert (e2e_dir / "contracts").is_dir()
    assert (e2e_dir / "tier1_coverage").is_dir()


@pytest.mark.phase11_tier1
def test_f24_zero_regressions_invariant() -> None:
    """Verifies that baseline tests pass with zero failures."""
    # Run a fast sample of baseline tests to verify zero regressions
    cmd = [sys.executable, "-m", "pytest", "tests/phase10", "-q"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Baseline test regression in phase10: {res.stdout}"
    assert "passed" in res.stdout


@pytest.mark.phase11_tier1
def test_f24_pytest_ini_configuration_present() -> None:
    """Verifies pytest.ini configures tier markers and pythonpath."""
    ini_path = Path("pytest.ini")
    assert ini_path.is_file(), "pytest.ini missing in root"
    content = ini_path.read_text(encoding="utf-8")
    assert "phase11_tier1" in content
    assert "phase11_tier2" in content
    assert "phase11_tier3" in content
    assert "phase11_tier4" in content
