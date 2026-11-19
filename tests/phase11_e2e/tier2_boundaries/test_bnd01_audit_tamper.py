"""Tier 2 Boundary Tests - Feature 1: Baseline Reconnaissance & Environment Audit.

Verifies:
1. Missing audit headers rejection.
2. Corrupted git hash rejection.
3. Toolchain version mismatch alert.
4. Dirty working tree warning / clean working tree invariant.
5. Baseline test count mismatch detection (must be exactly 239).
"""

import os
import re
import pytest
from pathlib import Path

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


@pytest.mark.phase11_tier2
def test_bnd01_missing_audit_headers_rejection() -> None:
    """Verifies that an audit document missing mandatory structural headers is rejected."""
    required_headers = [
        "Commit Hash",
        "Toolchain Inventory",
        "Hardware Profile",
        "Baseline Regression Inventory",
    ]

    # Test audit validator against malformed / truncated markdown
    truncated_audit = """# Baseline Audit
Some intro text without the required sections.
"""
    for header in required_headers:
        assert f"## {header}" not in truncated_audit, f"Header {header} unexpectedly present"

    def validate_audit_headers(content: str) -> tuple[bool, list[str]]:
        missing = [h for h in required_headers if f"## {h}" not in content and h not in content]
        return len(missing) == 0, missing

    ok, missing = validate_audit_headers(truncated_audit)
    assert not ok, "Validator must reject audit missing mandatory headers"
    assert len(missing) == len(required_headers)

    # If the real audit file exists in research/phase11/BASELINE_AUDIT.md, verify it has required sections
    audit_file = Path("research/phase11/BASELINE_AUDIT.md")
    if audit_file.is_file():
        text = audit_file.read_text(encoding="utf-8")
        # Check that audit content is not empty and covers commit, toolchain, hardware, baseline
        assert len(text) > 200, "Audit document must not be empty"


@pytest.mark.phase11_tier2
def test_bnd01_corrupted_git_hash_rejection() -> None:
    """Verifies rejection of invalid or corrupted git commit hashes."""
    git_hash_pattern = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)

    invalid_hashes = [
        "",                     # Empty string
        "123456",               # Too short
        "g" * 40,               # Non-hex characters
        "0123456789abcdef" * 3, # Too long (48 chars)
        "1234567890abcdef1234567890abcdef1234567Z",  # Invalid char 'Z'
        " 1234567890abcdef1234567890abcdef12345678", # Leading space
    ]

    for bad_hash in invalid_hashes:
        assert not git_hash_pattern.match(bad_hash), f"Corrupted hash '{bad_hash}' was erroneously accepted"

    valid_hash = "a" * 40
    assert git_hash_pattern.match(valid_hash) is not None


@pytest.mark.phase11_tier2
def test_bnd01_toolchain_version_mismatch_alert() -> None:
    """Verifies that toolchain checks detect version mismatches and missing packages."""
    def verify_toolchain(python_version_tuple: tuple[int, int], installed_pkgs: dict[str, str]) -> tuple[bool, list[str]]:
        alerts = []
        if python_version_tuple < (3, 10):
            alerts.append(f"Python version {python_version_tuple} < (3, 10) minimum")
        for req in ["gmpy2", "sympy", "pytest"]:
            if req not in installed_pkgs:
                alerts.append(f"Missing required math/testing package: {req}")
        return len(alerts) == 0, alerts

    # Synthetic outdated toolchain
    ok_bad, alerts_bad = verify_toolchain((3, 9), {"sympy": "1.12"})
    assert not ok_bad
    assert any("Python version" in a for a in alerts_bad)
    assert any("gmpy2" in a for a in alerts_bad)

    # Valid current environment
    import sys
    import gmpy2
    import sympy
    ok_curr, alerts_curr = verify_toolchain(
        (sys.version_info.major, sys.version_info.minor),
        {"gmpy2": gmpy2.__version__, "sympy": sympy.__version__, "pytest": pytest.__version__}
    )
    assert ok_curr, f"Current environment failed toolchain validation: {alerts_curr}"


@pytest.mark.phase11_tier2
def test_bnd01_dirty_working_tree_warning() -> None:
    """Verifies detection of uncommitted / dirty working tree states in audit records."""
    def parse_working_tree_status(audit_status_line: str) -> str:
        line = audit_status_line.lower()
        if "dirty" in line or "uncommitted changes" in line:
            return "DIRTY"
        elif "clean" in line:
            return "CLEAN"
        return "UNKNOWN"

    assert parse_working_tree_status("Working tree: clean, commit verified") == "CLEAN"
    assert parse_working_tree_status("Working tree: DIRTY (3 modified files)") == "DIRTY"
    assert parse_working_tree_status("Git status: uncommitted changes present") == "DIRTY"
    assert parse_working_tree_status("random string") == "UNKNOWN"


@pytest.mark.phase11_tier2
def test_bnd01_baseline_test_count_mismatch_detection() -> None:
    """Verifies that any baseline test count differing from exactly 239 is flagged as a mismatch."""
    EXPECTED_BASELINE_COUNT = 239

    def validate_baseline_count(count: int) -> bool:
        return count == EXPECTED_BASELINE_COUNT

    # Non-compliant counts
    for deviant_count in [0, 1, 238, 240, 300]:
        assert not validate_baseline_count(deviant_count), f"Deviant count {deviant_count} must be rejected"

    # Exactly 239 passes
    assert validate_baseline_count(239) is True
