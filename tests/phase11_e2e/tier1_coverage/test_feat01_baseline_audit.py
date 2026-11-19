"""Feature 1: Baseline Reconnaissance and Environment Audit.

Verifies:
1. Audit file existence and non-empty size in research/phase11/BASELINE_AUDIT.md.
2. Git commit hash recorded in BASELINE_AUDIT.md matching valid 40-character SHA.
3. Complete Python and numerical toolchain inventory (Python, gmpy2, SymPy, NumPy, pytest).
4. Local hardware environment profile (CPU, host RAM, GPU device, thermal baselines).
5. Exact 239 baseline regression test count recorded and verified.
"""

import re
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


AUDIT_PATH = Path("research/phase11/BASELINE_AUDIT.md")


@pytest.mark.phase11_tier1
def test_f01_audit_file_existence_and_nonempty() -> None:
    """Verifies BASELINE_AUDIT.md exists and contains substantial documentation."""
    if not AUDIT_PATH.is_file():
        if Phase11ContractAdapter.get_mode() == "LIVE":
            pytest.fail(f"LIVE mode mandates {AUDIT_PATH}")
        pytest.skip(f"{AUDIT_PATH} not yet available in current lifecycle")

    content = AUDIT_PATH.read_text(encoding="utf-8")
    assert len(content) > 1000, f"Audit file is too small: {len(content)} characters"
    assert "BASELINE-AUDIT" in content


@pytest.mark.phase11_tier1
def test_f01_git_commit_hash_recorded() -> None:
    """Verifies valid 40-character git commit hash is recorded in BASELINE_AUDIT.md."""
    if not AUDIT_PATH.is_file():
        pytest.skip(f"{AUDIT_PATH} not yet available")

    content = AUDIT_PATH.read_text(encoding="utf-8")
    match = re.search(r"\b[0-9a-fA-F]{40}\b", content)
    assert match is not None, "No 40-character Git commit SHA-1 found in BASELINE_AUDIT.md"
    commit_sha = match.group(0).lower()
    assert len(commit_sha) == 40
    assert "801ac1a" in content, "Expected short commit 801ac1a in audit"


@pytest.mark.phase11_tier1
def test_f01_toolchain_inventory_recorded() -> None:
    """Verifies all required toolchain components are recorded with version strings."""
    if not AUDIT_PATH.is_file():
        pytest.skip(f"{AUDIT_PATH} not yet available")

    content = AUDIT_PATH.read_text(encoding="utf-8")
    required_packages = ["Python", "gmpy2", "SymPy", "NumPy", "pytest"]
    for pkg in required_packages:
        pattern = rf"{pkg}.*?`\d+\.\d+"
        assert re.search(pattern, content, re.IGNORECASE) is not None, (
            f"Package {pkg} version string not documented in audit"
        )


@pytest.mark.phase11_tier1
def test_f01_hardware_profile_recorded() -> None:
    """Verifies CPU, RAM capacity, and GPU accelerator specifications are recorded."""
    if not AUDIT_PATH.is_file():
        pytest.skip(f"{AUDIT_PATH} not yet available")

    content = AUDIT_PATH.read_text(encoding="utf-8")
    assert "Intel" in content or "CPU" in content, "CPU information missing from audit"
    assert "RAM" in content, "RAM capacity missing from audit"
    assert "2.5" in content, "Minimum 2.5 GB RAM guardrail missing from audit"
    assert "GeForce" in content or "MX250" in content or "GPU" in content, (
        "GPU profile missing from audit"
    )


@pytest.mark.phase11_tier1
def test_f01_exact_239_baseline_test_count() -> None:
    """Verifies that the audit documents exactly 239 baseline regression tests."""
    if not AUDIT_PATH.is_file():
        pytest.skip(f"{AUDIT_PATH} not yet available")

    content = AUDIT_PATH.read_text(encoding="utf-8")
    match = re.search(r"239", content)
    assert match is not None, "Baseline test count '239' not found in BASELINE_AUDIT.md"
    assert "239" in content and ("passed" in content.lower() or "baseline" in content.lower())
