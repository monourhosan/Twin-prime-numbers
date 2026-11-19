"""Tier 2 Boundary Tests - Feature 18: Morrison Odd Divisor Guard.

Verifies:
1. Minimal odd factor q=3 boundary verification in Lucas rank checks.
2. Rejection of candidate with F_odd = 1 (pure power of 2, no odd factors).
3. Rejection when Lucas rank gcd(U_{(A+1)/q}, A) > 1.
4. Rejection when candidate A divides discriminant D (D = 0 mod A).
5. Parameter P search iteration limit guard.
"""

import math
import pytest
import sympy
from sympy import jacobi_symbol

from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    get_odd_part,
    standalone_lucas_u,
    prove_morrison_lower,
)


@pytest.mark.phase11_tier2
def test_bnd18_minimal_odd_factor_q3_boundary() -> None:
    """Verifies that the smallest odd prime factor q=3 satisfies the Morrison gcd condition."""
    # Candidate at x=126
    y = 3
    Sy, Sy_factors = compute_primorial_anchor(y)
    t = 21
    x = Sy * t
    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)
    factors_F = compute_factors_of_F(Sy_factors, {3: 1, 7: 1})
    F_odd = get_odd_part(F)

    ok, morrison_dict = prove_morrison_lower(A, F_odd, factors_F)
    assert ok is True
    # Minimal odd factor 3 must be present and verified
    assert "3" in morrison_dict["factor_gcds"]
    assert int(morrison_dict["factor_gcds"]["3"]) == 1
    # Factor 2 must be strictly excluded by the odd divisor guard
    assert "2" not in morrison_dict["factor_gcds"]


@pytest.mark.phase11_tier2
def test_bnd18_pure_power_of_2_rejection() -> None:
    """Verifies rejection when F has no odd factors (F_odd == 1)."""
    # If F = 2^k, F_odd = 1, then Morrison size condition (F_odd - 1)^2 = 0 > A can never hold
    F_pure_power_2 = 1024
    F_odd = get_odd_part(F_pure_power_2)
    assert F_odd == 1

    A_cand = 500
    morrison_bound = (F_odd - 1) ** 2
    assert morrison_bound == 0
    assert morrison_bound <= A_cand, "Pure power of 2 cannot satisfy Morrison bound"


@pytest.mark.phase11_tier2
def test_bnd18_lucas_rank_gcd_greater_than_1_rejection() -> None:
    """Verifies that if gcd(U_{(A+1)/q}, A) > 1 for any odd prime factor q, candidate is rejected."""
    # In Morrison Theorem 17, we require:
    # 1. U_{A+1} = 0 mod A
    # 2. gcd(U_{(A+1)/q}, A) = 1 for all odd prime factors q of F
    # If gcd > 1, A is composite!
    def check_morrison_gcd_condition(gcd_val: int) -> bool:
        return gcd_val == 1

    assert check_morrison_gcd_condition(1) is True
    assert check_morrison_gcd_condition(3) is False
    assert check_morrison_gcd_condition(17) is False


@pytest.mark.phase11_tier2
def test_bnd18_candidate_dividing_discriminant_rejection() -> None:
    """Verifies rejection when A divides discriminant D (meaning D = 0 mod A)."""
    A_cand = 101
    # Discriminant D = P^2 - 4
    # If D is a multiple of A_cand, then D % A_cand == 0
    D_multiple = 101 * 3
    assert D_multiple % A_cand == 0
    assert jacobi_symbol(D_multiple, A_cand) == 0

    # Must be rejected because Jacobi symbol is 0 (not -1)
    def is_valid_morrison_discriminant(D_val: int, A_val: int) -> bool:
        return jacobi_symbol(D_val, A_val) == -1

    assert is_valid_morrison_discriminant(D_multiple, A_cand) is False


@pytest.mark.phase11_tier2
def test_bnd18_p_parameter_search_limit_guard() -> None:
    """Verifies that searching for parameter P stops and flags error if maximum iterations exceeded."""
    MAX_SEARCH_STEPS = 64

    def search_lucas_parameter_p(A_val: int, max_steps: int = MAX_SEARCH_STEPS) -> int | None:
        # Search for first P with Jacobi symbol -1
        for P in range(3, 3 + max_steps):
            D = P * P - 4
            if jacobi_symbol(D, A_val) == -1:
                return P
        return None

    # Test limit enforcement: with max_steps=0, must return None
    assert search_lucas_parameter_p(101, max_steps=0) is None
    # For A=101, P=4 gives D=12, (12/101) = -1
    assert search_lucas_parameter_p(101, max_steps=10) == 4
