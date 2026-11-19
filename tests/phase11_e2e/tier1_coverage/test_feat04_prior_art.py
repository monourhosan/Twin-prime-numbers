"""Feature 4: Prior Art Literature Review and Novelty Assessment.

Verifies:
1. PRIOR_ART.md existence and structure in research/phase11/PRIOR_ART.md.
2. Comprehensive survey of PrimePages Top 20 Twin Primes records.
3. Analysis of Tony Forbes prime k-tuple / constellation registry.
4. Algorithmic comparison with PrimeGrid Twin Prime Search (LLR, TwinGen).
5. Review of recent 2024-2026 preprints and systematic differentiation matrix.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


PRIOR_ART_PATH = Path("research/phase11/PRIOR_ART.md")


@pytest.mark.phase11_tier1
def test_f04_prior_art_file_exists() -> None:
    """Verifies PRIOR_ART.md exists and contains substantial literature analysis."""
    if not PRIOR_ART_PATH.is_file():
        if Phase11ContractAdapter.get_mode() == "LIVE":
            pytest.fail(f"LIVE mode mandates {PRIOR_ART_PATH}")
        pytest.skip(f"{PRIOR_ART_PATH} not yet available")

    content = PRIOR_ART_PATH.read_text(encoding="utf-8")
    assert len(content) > 3000, f"Prior art review too brief: {len(content)} characters"
    assert "Prior Art Review" in content


@pytest.mark.phase11_tier1
def test_f04_primepages_top20_review() -> None:
    """Verifies PrimePages Top 20 Twin Primes records are surveyed and tabulated."""
    if not PRIOR_ART_PATH.is_file():
        pytest.skip(f"{PRIOR_ART_PATH} not yet available")

    content = PRIOR_ART_PATH.read_text(encoding="utf-8")
    assert "PrimePages" in content or "t5k.org" in content
    # Check for record holder and formula
    assert "2996863034895" in content or "Tom Greer" in content
    assert "388,342" in content or "388342" in content
    assert "Proth" in content or "exponential" in content.lower()


@pytest.mark.phase11_tier1
def test_f04_tony_forbes_comparison() -> None:
    """Verifies comparison with Tony Forbes prime k-tuple constellation methods."""
    if not PRIOR_ART_PATH.is_file():
        pytest.skip(f"{PRIOR_ART_PATH} not yet available")

    content = PRIOR_ART_PATH.read_text(encoding="utf-8")
    assert "Tony Forbes" in content or "Forbes" in content
    assert "k-tuple" in content or "constellation" in content.lower()


@pytest.mark.phase11_tier1
def test_f04_primegrid_algorithms_comparison() -> None:
    """Verifies algorithmic comparison with PrimeGrid TPS (LLR, GWNUM, TwinGen)."""
    if not PRIOR_ART_PATH.is_file():
        pytest.skip(f"{PRIOR_ART_PATH} not yet available")

    content = PRIOR_ART_PATH.read_text(encoding="utf-8")
    assert "PrimeGrid" in content
    assert "LLR" in content or "Lucas-Lehmer-Riesel" in content
    assert "TwinGen" in content or "GWNUM" in content or "NewPGen" in content


@pytest.mark.phase11_tier1
def test_f04_recent_preprints_and_differentiation() -> None:
    """Verifies review of 2024-2026 preprints and systematic comparison matrix."""
    if not PRIOR_ART_PATH.is_file():
        pytest.skip(f"{PRIOR_ART_PATH} not yet available")

    content = PRIOR_ART_PATH.read_text(encoding="utf-8")
    # Preprints / recent citations
    assert "2025" in content or "2026" in content
    assert "preprint" in content.lower() or "literature" in content.lower()
    # Comparison table
    assert "Exponential Proth" in content or "Proth" in content
    assert "OPQM-CRT" in content or "HYBRID-11" in content
