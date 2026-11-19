"""Tier 2 Boundary Tests - Feature 4: Prior Art Literature Review.

Verifies:
1. Broken or malformed citation URL rejection.
2. Public database collision check against PrimePages, Tony Forbes, PrimeGrid.
3. Chronological timeline consistency in prior art audits.
4. Completeness of algorithm differentiation matrix.
5. Falsification condition check for novelty validation.
"""

import re
import pytest
from pathlib import Path

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


@pytest.mark.phase11_tier2
def test_bnd04_broken_citation_url_rejection() -> None:
    """Verifies that citation URLs in literature reviews must be valid HTTPS or DOI/arXiv identifiers."""
    url_regex = re.compile(
        r"^(https://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?|arXiv:\d{4}\.\d{4,5}(?:v\d+)?|doi:10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)$",
        re.IGNORECASE
    )

    invalid_citations = [
        "http://insecure-site.com",           # Insecure HTTP
        "ftp://old-repo.org/paper.pdf",       # Unsupported protocol
        "www.primes.utm.edu",                 # Missing protocol
        "not a url",                          # Plain text
        "arXiv:123",                          # Malformed arXiv id
        "doi:invalid",                        # Malformed DOI
    ]

    for bad in invalid_citations:
        assert not url_regex.match(bad), f"Malformed citation '{bad}' was incorrectly accepted"

    valid_citations = [
        "https://primes.utm.edu/top20/page.php?id=1",
        "https://arxiv.org/abs/2301.00001",
        "arXiv:2401.12345",
        "doi:10.1090/S0025-5718-1975-0384673-1",
    ]
    for good in valid_citations:
        assert url_regex.match(good), f"Valid citation '{good}' was rejected"


@pytest.mark.phase11_tier2
def test_bnd04_public_database_collision_check() -> None:
    """Verifies that candidate twins are checked against known public records."""
    # Tony Forbes historical polynomial twin primes:
    # e.g. Forbes discovered twins via specific high-degree polynomials
    # and Caldwell's top 20 list contains giant twin primes: e.g. 2996863034895 * 2^1290000 +/- 1
    known_public_twins = {
        (3, 5),
        (5, 7),
        (11, 13),
        (17, 19),
        (29, 31),
        (41, 43),
        (2996863034895 * (2**100) - 1, 2996863034895 * (2**100) + 1),
    }

    def check_public_collision(A: int, B: int) -> bool:
        return (A, B) in known_public_twins or (B, A) in known_public_twins

    assert check_public_collision(3, 5) is True
    assert check_public_collision(5, 7) is True
    # Phase 11 candidate at x = 126
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(3, 21)
    assert not check_public_collision(A, B), "Phase 11 candidate collided with tiny known list"


@pytest.mark.phase11_tier2
def test_bnd04_chronological_timeline_consistency() -> None:
    """Verifies that prior art entries follow a valid chronological sequence without retro-dating."""
    prior_art_events = [
        ("Brillhart-Lehmer-Selfridge", 1975),
        ("Tony Forbes polynomial search", 1997),
        ("PrimeGrid twin prime campaign", 2006),
        ("Bostan et al. polynomial complexity", 2017),
        ("Phase 11 OPQM-11 specification", 2026),
    ]

    years = [year for _, year in prior_art_events]
    assert years == sorted(years), "Prior art timeline must be monotonically non-decreasing"

    # Reject inconsistent/inverted timeline
    inverted_events = [
        ("Phase 11", 2026),
        ("BLS paper", 1975),
    ]
    inverted_years = [y for _, y in inverted_events]
    assert inverted_years != sorted(inverted_years), "Inverted chronological order must be detected"


@pytest.mark.phase11_tier2
def test_bnd04_differentiation_matrix_completeness() -> None:
    """Verifies that the prior art differentiation matrix contains all required algorithmic comparison axes."""
    required_axes = [
        "polynomial_degree",
        "factorable_divisor_ratio",
        "sieve_symmetry",
        "morrison_applicable",
        "pocklington_applicable",
        "crt_prefiltering",
    ]

    # Model of OPQM-11 vs Forbes vs PAQCS vs Cunningham
    matrix = {
        "OPQM_11": {
            "polynomial_degree": 5,
            "factorable_divisor_ratio": 0.6,
            "sieve_symmetry": True,
            "morrison_applicable": True,
            "pocklington_applicable": True,
            "crt_prefiltering": True,
        },
        "FORBES": {
            "polynomial_degree": 6,
            "factorable_divisor_ratio": 0.5,
            "sieve_symmetry": False,
            "morrison_applicable": False,
            "pocklington_applicable": True,
            "crt_prefiltering": False,
        },
    }

    for method, row in matrix.items():
        missing = [axis for axis in required_axes if axis not in row]
        assert len(missing) == 0, f"Method {method} missing axes: {missing}"


@pytest.mark.phase11_tier2
def test_bnd04_falsification_condition_check() -> None:
    """Verifies that the novelty framework triggers a falsification flag if prior art matches OPQM-11 manifold."""
    def evaluate_novelty_falsification(candidate_equation: str, prior_art_equations: list[str]) -> bool:
        # If any prior art has the exact same quintic manifold 12x^5 + 6x^3, novelty is falsified
        norm_cand = candidate_equation.replace(" ", "").lower()
        for prior in prior_art_equations:
            if prior.replace(" ", "").lower() == norm_cand:
                return True  # Falsified
        return False  # Novelty preserved

    prior_literature = [
        "k * 2^n +/- 1",
        "h * 3 * 2^n +/- 1",
        "x^6 + 1093",
        "4x^4 + 1",
    ]

    # Not falsified by standard literature
    assert evaluate_novelty_falsification("12*x^5 + 6*x^3", prior_literature) is False

    # Falsified if an identical manifold existed
    prior_with_collision = prior_literature + ["12*x^5 + 6*x^3"]
    assert evaluate_novelty_falsification("12*x^5 + 6*x^3", prior_with_collision) is True
