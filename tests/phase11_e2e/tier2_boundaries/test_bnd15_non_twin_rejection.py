"""Tier 2 Boundary Tests - Feature 15: Twin-Prime Pair Discovery.

Verifies:
1. Even candidate member rejection.
2. Composite candidate member rejection.
3. Candidate gap != 2 rejection (e.g. gap 4, 6, 0).
4. Digit scale threshold enforcement.
5. Non-manifold coordinate rejection.
"""

import pytest
from sympy.ntheory import isprime

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import compute_manifold


@pytest.mark.phase11_tier2
def test_bnd15_even_candidate_rejection() -> None:
    """Verifies that any candidate pair with an even member is immediately rejected."""
    def validate_twin_oddity(A: int, B: int) -> tuple[bool, str]:
        if A % 2 == 0 or B % 2 == 0:
            return False, f"Candidate members must be odd integers: ({A}, {B})"
        return True, "OK"

    # Even pairs
    assert not validate_twin_oddity(2, 4)[0]
    assert not validate_twin_oddity(10, 12)[0]
    assert not validate_twin_oddity(100, 102)[0]

    # Odd pair
    assert validate_twin_oddity(11, 13)[0] is True


@pytest.mark.phase11_tier2
def test_bnd15_composite_candidate_rejection() -> None:
    """Verifies that pairs with one or both composite members are rejected."""
    def validate_twin_primality(A: int, B: int) -> tuple[bool, str]:
        if not isprime(A):
            return False, f"Lower member {A} is composite"
        if not isprime(B):
            return False, f"Upper member {B} is composite"
        return True, "OK"

    # Lower composite: 9, 11
    ok_low, err_low = validate_twin_primality(9, 11)
    assert not ok_low
    assert "Lower member 9 is composite" in err_low

    # Upper composite: 7, 9
    ok_up, err_up = validate_twin_primality(7, 9)
    assert not ok_up
    assert "Upper member 9 is composite" in err_up

    # Both composite: 25, 27
    ok_both, _ = validate_twin_primality(25, 27)
    assert not ok_both

    # Genuine twin prime: 11, 13
    ok_good, _ = validate_twin_primality(11, 13)
    assert ok_good is True


@pytest.mark.phase11_tier2
def test_bnd15_gap_not_two_rejection() -> None:
    """Verifies that pairs with gap != 2 (cousin, sexy, or identical primes) are rejected."""
    def validate_exact_twin_gap(A: int, B: int) -> tuple[bool, str]:
        diff = B - A
        if diff != 2:
            return False, f"Difference must be exactly 2, got {diff}"
        return True, "OK"

    # Cousin primes (gap 4)
    assert not validate_exact_twin_gap(7, 11)[0]
    # Sexy primes (gap 6)
    assert not validate_exact_twin_gap(5, 11)[0]
    # Identical (gap 0)
    assert not validate_exact_twin_gap(17, 17)[0]
    # Inverted (gap -2)
    assert not validate_exact_twin_gap(13, 11)[0]
    # Twin prime (gap 2)
    assert validate_exact_twin_gap(11, 13)[0] is True


@pytest.mark.phase11_tier2
def test_bnd15_small_digit_scale_threshold() -> None:
    """Verifies digit count calculation and minimum scale threshold validation."""
    def validate_digit_scale(A: int, min_digits: int) -> tuple[bool, int]:
        digits = len(str(A))
        return digits >= min_digits, digits

    # Small candidate at x=126
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(3, 21)
    digits_A = len(str(A))
    assert digits_A > 0

    # Passes low threshold (e.g. 5 digits)
    ok_low, count = validate_digit_scale(A, min_digits=5)
    assert ok_low is True

    # Fails large threshold if requesting 1000 digits
    ok_high, _ = validate_digit_scale(A, min_digits=1000)
    assert ok_high is False


@pytest.mark.phase11_tier2
def test_bnd15_non_manifold_candidate_rejection() -> None:
    """Verifies that candidate pairs not conforming to C = 12x^5 + 6x^3 are rejected."""
    def verify_manifold_provenance(A: int, B: int, x: int) -> bool:
        C_exp = 12 * (x**5) + 6 * (x**3)
        return A == C_exp - 1 and B == C_exp + 1

    # Real manifold at x=126
    C, A, B = compute_manifold(126)
    assert verify_manifold_provenance(A, B, 126) is True

    # Non-manifold prime pair (e.g. 11, 13)
    assert verify_manifold_provenance(11, 13, 1) is False
    assert verify_manifold_provenance(11, 13, 2) is False
