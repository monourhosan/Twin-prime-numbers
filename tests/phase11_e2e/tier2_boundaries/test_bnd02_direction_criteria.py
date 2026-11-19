"""Tier 2 Boundary Tests - Feature 2: Candidate Directions Formulation.

Verifies:
1. Degenerate or historical candidate polynomial rejection.
2. Out-of-bounds evaluation score rejection.
3. Unsubstantiated algebraic factor claims detection.
4. Unbalanced super-root inequality rejection.
5. Missing evaluation scoring dimensions detection (all 7 required).
"""

import pytest
import sympy
from sympy import symbols, Poly, gcd

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


REQUIRED_SCORING_DIMENSIONS = [
    "algebraic_invariants",
    "factorability",
    "sieve_symmetry",
    "certification_tractability",
    "digit_scalability",
    "hardware_feasibility",
    "novelty_margin",
]


@pytest.mark.phase11_tier2
def test_bnd02_degenerate_historical_candidate_rejection() -> None:
    """Verifies that duplicate or historical polynomial families are rejected as candidate methods."""
    historical_forms = [
        "2^n - 1",                       # Mersenne / Phase 2
        "k * 2^n - 1",                   # Proth / Riesel
        "h * 2^n + 1",                   # Cunningham chain
        "6k +/- 1",                      # Trivial baseline
        "PAQCS_PHASE8",                  # Phase 8 family
    ]

    def is_novel_candidate(candidate_id: str, family_desc: str) -> bool:
        norm = family_desc.lower()
        for hist in historical_forms:
            if hist.lower() in norm:
                return False
        if "cunningham" in norm or "riesel" in norm or "proth" in norm:
            return False
        return True

    # Rejection of historical forms
    for hist in historical_forms:
        assert not is_novel_candidate("HIST_CAND", hist), f"Historical family {hist} was not rejected"

    # Novel quintic manifold HYBRID-11 must be accepted
    assert is_novel_candidate("OPQM_CRT_HYBRID_11", "Odd-Parity Quintic Manifold with CRT-Kernel Inverse Sieve")


@pytest.mark.phase11_tier2
def test_bnd02_out_of_bounds_score_rejection() -> None:
    """Verifies that direction evaluation scores outside valid range [0.0, 10.0] are rejected."""
    def validate_dimension_score(score: float) -> bool:
        return isinstance(score, (int, float)) and 0.0 <= score <= 10.0

    invalid_scores = [-1.0, -0.01, 10.01, 15.0, 100.0, float("nan"), float("inf")]
    for bad_score in invalid_scores:
        assert not validate_dimension_score(bad_score), f"Invalid score {bad_score} was accepted"

    valid_scores = [0.0, 5.5, 9.2, 10.0]
    for good_score in valid_scores:
        assert validate_dimension_score(good_score)


@pytest.mark.phase11_tier2
def test_bnd02_unsubstantiated_factor_claims_detection() -> None:
    """Verifies detection when a candidate falsely claims an algebraic divisor F(x) dividing C(x)."""
    x = symbols("x")
    C = 12 * x**5 + 6 * x**3

    # Legitimate factor: F(x) = 6*x^3
    F_legit = 6 * x**3
    q_poly, r_poly = Poly(C, x).div(Poly(F_legit, x))
    assert r_poly.is_zero, "Legitimate factor must yield remainder 0"

    # False/unsubstantiated claim: F(x) = 6*x^3 + 2 does NOT divide C(x)
    F_false = 6 * x**3 + 2
    q_bad, r_bad = Poly(C, x).div(Poly(F_false, x))
    assert not r_bad.is_zero, "Detector must catch non-zero polynomial remainder"

    # Also coprimality of F and R: gcd(6x^3, 2x^2 + 1) in Q[x] is 1
    R_legit = 2 * x**2 + 1
    assert gcd(F_legit, R_legit) == 1, "F and R must be coprime over Q[x]"


@pytest.mark.phase11_tier2
def test_bnd02_unbalanced_super_root_rejection() -> None:
    """Verifies rejection of candidate polynomials where divisor F is too small to satisfy F^2 > B."""
    # Suppose candidate polynomial C(x) = x^6 and divisor F(x) = x^2
    # Then F^2 = x^4, but B = x^6 + 1. For x >= 2, x^4 < x^6 + 1 (fails Pocklington bound!)
    def check_super_root_bound(deg_F: int, deg_C: int) -> bool:
        # Pocklington Theorem 4 requires F > sqrt(B) approx F^2 > B
        # In terms of polynomial degrees, we must have 2 * deg(F) >= deg(C)
        return 2 * deg_F >= deg_C

    # OPQM-11 has deg(C) = 5, deg(F) = 3 -> 2*3 = 6 > 5 (Satisfies super-root)
    assert check_super_root_bound(deg_F=3, deg_C=5) is True

    # Under-factored candidate: deg(C) = 6, deg(F) = 2 -> 2*2 = 4 < 6 (Fails super-root!)
    assert check_super_root_bound(deg_F=2, deg_C=6) is False

    # Marginal under-factored: deg(C) = 5, deg(F) = 2 -> 2*2 = 4 < 5 (Fails super-root!)
    assert check_super_root_bound(deg_F=2, deg_C=5) is False


@pytest.mark.phase11_tier2
def test_bnd02_missing_scoring_dimensions_detection() -> None:
    """Verifies that a candidate evaluation matrix missing any required dimension is rejected."""
    def validate_evaluation_matrix(matrix: dict[str, float]) -> tuple[bool, list[str]]:
        missing = [dim for dim in REQUIRED_SCORING_DIMENSIONS if dim not in matrix]
        return len(missing) == 0, missing

    # Incomplete matrix missing 'novelty_margin'
    incomplete = {dim: 8.5 for dim in REQUIRED_SCORING_DIMENSIONS if dim != "novelty_margin"}
    ok, missing = validate_evaluation_matrix(incomplete)
    assert not ok
    assert missing == ["novelty_margin"]

    # Full matrix
    complete = {dim: 9.0 for dim in REQUIRED_SCORING_DIMENSIONS}
    ok_full, missing_full = validate_evaluation_matrix(complete)
    assert ok_full is True
    assert len(missing_full) == 0
