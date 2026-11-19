"""Tier 2 Boundary Tests - Feature 6: Minimal Mathematical Prototype.

Verifies:
1. Rejection of non-positive coordinate x or multiplier t <= 0.
2. Rejection of primorial anchor y with 6 not dividing S_y (y < 3).
3. Large coordinate scaling without precision loss.
4. Composite multiplier t sharing prime factors with S_y.
5. Deterministic repeatability across repeated prototype evaluations.
"""

import pytest
import gmpy2
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    check_algebraic_invariants,
)


@pytest.mark.phase11_tier2
def test_bnd06_non_positive_x_or_t_rejection() -> None:
    """Verifies that non-positive coordinates or multipliers are rejected with ValueError."""
    # Test x <= 0
    for invalid_x in [0, -1, -42, -1000]:
        with pytest.raises(ValueError, match="positive"):
            compute_manifold(invalid_x)
        with pytest.raises(ValueError, match="positive"):
            compute_divisor_and_cofactor(invalid_x)

    # Test t <= 0 via adapter
    for invalid_t in [0, -1, -5]:
        with pytest.raises(ValueError):
            Phase11ContractAdapter.compute_candidate_pair(3, invalid_t)


@pytest.mark.phase11_tier2
def test_bnd06_anchor_not_divisible_by_6_rejection() -> None:
    """Verifies that anchors with y < 3 (where 6 does not divide S_y) are rejected."""
    # y = 2 -> S_2 = 2 (not divisible by 6)
    with pytest.raises(ValueError, match="anchor y must be >= 3"):
        compute_primorial_anchor(2)

    with pytest.raises(ValueError, match="anchor y must be >= 3"):
        compute_primorial_anchor(1)

    with pytest.raises(ValueError, match="anchor y must be >= 3"):
        compute_primorial_anchor(0)

    # y = 3 -> S_3 = 6 (divisible by 6, valid)
    Sy, factors = compute_primorial_anchor(3)
    assert Sy == 6
    assert Sy % 6 == 0


@pytest.mark.phase11_tier2
def test_bnd06_large_exponent_scaling_precision() -> None:
    """Verifies exact arbitrary-precision integer arithmetic without float conversion for large x."""
    # Large coordinate x = 10^50
    large_x = 10**50
    C, A, B = compute_manifold(large_x)

    # C = 12 * (10^50)^5 + 6 * (10^50)^3 = 12 * 10^250 + 6 * 10^150
    expected_C = 12 * (10**250) + 6 * (10**150)
    assert C == expected_C
    assert A == expected_C - 1
    assert B == expected_C + 1
    assert B - A == 2

    # Verify no float conversion occurred by checking least significant digits
    assert str(A).endswith("99999")
    assert str(B).endswith("00001")


@pytest.mark.phase11_tier2
def test_bnd06_composite_t_sharing_factors_warning() -> None:
    """Verifies that composite t sharing factors with S_y accumulates exponents in F correctly."""
    # y = 5 -> S_5 = 2 * 3 * 5 = 30
    Sy, Sy_factors = compute_primorial_anchor(5)
    assert Sy_factors == {2: 1, 3: 1, 5: 1}

    # Let t = 2 * 3^2 * 7 = 126 (shares 2 and 3 with S_y, plus new factor 7)
    t_factors = {2: 1, 3: 2, 7: 1}
    factors_F = compute_factors_of_F(Sy_factors, t_factors)

    # F(x) = 6 * x^3 where x = S_y * t
    # x = (2 * 3 * 5) * (2 * 3^2 * 7) = 2^2 * 3^3 * 5^1 * 7^1
    # F = 2 * 3 * x^3 = 2 * 3 * (2^6 * 3^9 * 5^3 * 7^3) = 2^7 * 3^10 * 5^3 * 7^3
    assert factors_F[2] == 7
    assert factors_F[3] == 10
    assert factors_F[5] == 3
    assert factors_F[7] == 3

    # Direct arithmetic evaluation of F
    x = Sy * 126
    F, R = compute_divisor_and_cofactor(x)
    expected_F = 1
    for p, exp in factors_F.items():
        expected_F *= p**exp
    assert F == expected_F


@pytest.mark.phase11_tier2
def test_bnd06_deterministic_repeatability() -> None:
    """Verifies that prototype manifold evaluation is strictly deterministic across repeated calls."""
    runs = [Phase11ContractAdapter.compute_candidate_pair(3, 21) for _ in range(5)]
    first_run = runs[0]
    for r in runs[1:]:
        assert r == first_run, "Prototype evaluation must be bit-exact deterministic"
