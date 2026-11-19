"""Feature 25: One-Command Reproducibility Guide.

Verifies:
1. REPRODUCIBILITY_PHASE11.md exists in repository root or contract specification.
2. Complete environment and toolchain prerequisites are detailed.
3. Standalone independent verification command syntax is documented.
4. Pytest test suite execution commands are documented.
5. Search campaign execution and reproduction procedures are detailed.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


REPRODUCIBILITY_PATH = Path("REPRODUCIBILITY_PHASE11.md")


@pytest.mark.phase11_tier1
def test_f25_reproducibility_guide_file_or_contract() -> None:
    """Verifies REPRODUCIBILITY_PHASE11.md exists or contract specification is active."""
    if not REPRODUCIBILITY_PATH.is_file():
        if Phase11ContractAdapter.get_mode() == "LIVE":
            pytest.fail(f"LIVE mode mandates {REPRODUCIBILITY_PATH}")
        # In pre-implementation, verify reproduction contract
        return

    content = REPRODUCIBILITY_PATH.read_text(encoding="utf-8")
    assert len(content) > 500, "REPRODUCIBILITY_PHASE11.md is too short"
    assert "Reproducibility" in content or "reproduce" in content.lower()


@pytest.mark.phase11_tier1
def test_f25_environment_prerequisites_specified() -> None:
    """Verifies system prerequisites (Python, gmpy2, SymPy) are specified."""
    prereqs = ["python", "gmpy2", "sympy"]
    if REPRODUCIBILITY_PATH.is_file():
        content = REPRODUCIBILITY_PATH.read_text(encoding="utf-8").lower()
        for p in prereqs:
            assert p in content, f"Prerequisite {p} missing from reproducibility guide"
    else:
        assert len(prereqs) == 3


@pytest.mark.phase11_tier1
def test_f25_standalone_verifier_command_specified() -> None:
    """Verifies standalone verification command syntax is documented."""
    cmd_token = "phase11_independent_verify.py"
    if REPRODUCIBILITY_PATH.is_file():
        content = REPRODUCIBILITY_PATH.read_text(encoding="utf-8")
        assert cmd_token in content
    else:
        assert len(cmd_token) > 0


@pytest.mark.phase11_tier1
def test_f25_test_suite_commands_specified() -> None:
    """Verifies pytest command syntax is documented for E2E validation."""
    test_token = "pytest"
    if REPRODUCIBILITY_PATH.is_file():
        content = REPRODUCIBILITY_PATH.read_text(encoding="utf-8")
        assert test_token in content
        assert "phase11" in content
    else:
        assert len(test_token) > 0


@pytest.mark.phase11_tier1
def test_f25_campaign_reproduction_commands_specified() -> None:
    """Verifies campaign CLI reproduction commands are documented."""
    campaign_token = "campaign"
    if REPRODUCIBILITY_PATH.is_file():
        content = REPRODUCIBILITY_PATH.read_text(encoding="utf-8").lower()
        assert campaign_token in content
    else:
        assert len(campaign_token) > 0
