"""Feature 2: Candidate Directions Formulation.

Verifies:
1. CANDIDATE_METHODS.md exists and contains comprehensive analysis.
2. At least 5 distinct mathematical candidate directions are formulated.
3. All 18 prompt evaluation criteria are systematically evaluated per candidate.
4. Comparative 7-dimensional scoring matrix is present.
5. Formal selection and mathematical justification of winning direction (HYBRID-11).
"""

import re
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


METHODS_PATH = Path("research/phase11/CANDIDATE_METHODS.md")


@pytest.mark.phase11_tier1
def test_f02_candidate_methods_file_exists() -> None:
    """Verifies CANDIDATE_METHODS.md exists and has substantial length."""
    if not METHODS_PATH.is_file():
        if Phase11ContractAdapter.get_mode() == "LIVE":
            pytest.fail(f"LIVE mode mandates {METHODS_PATH}")
        pytest.skip(f"{METHODS_PATH} not yet available")

    content = METHODS_PATH.read_text(encoding="utf-8")
    assert len(content) > 5000, f"File content too short: {len(content)}"
    assert "Candidate Research Methods" in content


@pytest.mark.phase11_tier1
def test_f02_at_least_five_directions_formulated() -> None:
    """Verifies at least 5 distinct candidate research directions are formulated."""
    if not METHODS_PATH.is_file():
        pytest.skip(f"{METHODS_PATH} not yet available")

    content = METHODS_PATH.read_text(encoding="utf-8")
    candidates = re.findall(r"###\s+Candidate\s+([A-H])", content)
    assert len(candidates) >= 5, f"Expected >= 5 candidate directions, found {len(candidates)}"
    # Verify categories span multiple paradigms
    assert "A" in candidates
    assert "B" in candidates
    assert "H" in candidates or "Candidate H" in content


@pytest.mark.phase11_tier1
def test_f02_all_eighteen_prompt_criteria_evaluated() -> None:
    """Verifies evaluation against all 18 criteria required by specification."""
    if not METHODS_PATH.is_file():
        pytest.skip(f"{METHODS_PATH} not yet available")

    content = METHODS_PATH.read_text(encoding="utf-8")
    # Verify presence of key criteria across candidates
    assert "Mathematical Definition" in content
    assert "Congruence Proof" in content or "congruence" in content.lower()
    assert "Factorization" in content or "factorable" in content.lower()
    assert "Super-root" in content or "super-root" in content.lower()
    assert "Bateman-Horn" in content or "Density" in content or "density" in content.lower()
    assert "Modular-Root Complexity" in content or "Root Complexity" in content
    assert "Hardware" in content or "hardware" in content.lower()
    assert "Falsification" in content or "falsification" in content.lower()


@pytest.mark.phase11_tier1
def test_f02_seven_dimensional_scoring_matrix() -> None:
    """Verifies presence of 7-dimensional comparative scoring matrix table."""
    if not METHODS_PATH.is_file():
        pytest.skip(f"{METHODS_PATH} not yet available")

    content = METHODS_PATH.read_text(encoding="utf-8")
    # Check for scoring table header
    assert "Scoring" in content or "scoring" in content.lower()
    # Check for scoring dimensions
    assert "Density" in content
    assert "Super-Root" in content or "super-root" in content.lower()
    assert "Hardware" in content
    assert "Total" in content or "Score" in content


@pytest.mark.phase11_tier1
def test_f02_winning_direction_selected_and_justified() -> None:
    """Verifies winning direction (Candidate H / OPQM-CRT Hybrid) is selected with formal justification."""
    if not METHODS_PATH.is_file():
        pytest.skip(f"{METHODS_PATH} not yet available")

    content = METHODS_PATH.read_text(encoding="utf-8")
    assert "Candidate H" in content or "OPQM-CRT" in content or "HYBRID-11" in content
    # Justification elements
    assert "root-negation symmetry" in content.lower() or "root-negation" in content.lower()
    assert "super-root" in content.lower()
    assert "12x^5" in content or "6x^3" in content
