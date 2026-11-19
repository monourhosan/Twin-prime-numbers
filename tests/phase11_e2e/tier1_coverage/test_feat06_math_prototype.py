"""Feature 6: Minimal Mathematical Prototype.

Verifies:
1. Prototype candidate pair generation via Phase11ContractAdapter.
2. Exact coordinate computation C(x) = 12x^5 + 6x^3, A = C - 1, B = C + 1.
3. Invariant checks: B - A = 2 and C = 0 mod 6.
4. Exact prime factorization decomposition of divisor F(x) = 6x^3.
5. Super-root inequality verification F^2 > B and (F_odd - 1)^2 > A.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_primorial_anchor,
    compute_factors_of_F,
    compute_divisor_and_cofactor,
    get_odd_part,
)


@pytest.mark.phase11_tier1
def test_f06_prototype_execution_via_adapter() -> None:
    """Verifies that the prototype computes candidates (C, A, B) via the adapter."""
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(y=3, t=1)
    # y=3 -> S_3 = 2*3 = 6; t=1 -> x=6
    # C(6) = 12*(6^5) + 6*(6^3) = 12*7776 + 6*216 = 93312 + 1296 = 94608
    assert C == 94608
    assert A == 94607
    assert B == 94609


@pytest.mark.phase11_tier1
def test_f06_exact_coordinate_algebraic_computation() -> None:
    """Verifies exact coordinate formula across multiple anchor and multiplier values."""
    for y in [3, 5, 7]:
        Sy, _ = compute_primorial_anchor(y)
        for t in [1, 3, 5, 11]:
            x = Sy * t
            expected_C = 12 * (x ** 5) + 6 * (x ** 3)
            C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
            assert C == expected_C
            assert A == expected_C - 1
            assert B == expected_C + 1


@pytest.mark.phase11_tier1
def test_f06_gap_and_center_congruence() -> None:
    """Verifies B - A = 2 and C = 0 mod 6 for prototype candidates."""
    for y in [3, 5]:
        for t in [1, 7, 13]:
            C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
            assert B - A == 2
            assert C % 6 == 0
            assert A % 6 == 5
            assert B % 6 == 1


@pytest.mark.phase11_tier1
def test_f06_exact_factor_list_of_F() -> None:
    """Verifies that prime factors of F = 6*(S_y * t)^3 are derived analytically."""
    Sy, Sy_factors = compute_primorial_anchor(5)  # Sy = 30 = 2*3*5
    t_factors = {7: 1}  # t = 7
    factors_F = compute_factors_of_F(Sy_factors, t_factors)

    # x = 30 * 7 = 210 = 2 * 3 * 5 * 7
    # F = 6 * x^3 = 2 * 3 * 2^3 * 3^3 * 5^3 * 7^3 = 2^4 * 3^4 * 5^3 * 7^3
    assert factors_F[2] == 4
    assert factors_F[3] == 4
    assert factors_F[5] == 3
    assert factors_F[7] == 3

    # Product of prime powers equals F
    F_prod = 1
    for p, exp in factors_F.items():
        F_prod *= (p ** exp)
    expected_F = 6 * (210 ** 3)
    assert F_prod == expected_F


@pytest.mark.phase11_tier1
def test_f06_super_root_inequality_prototype() -> None:
    """Verifies that the prototype validates F^2 > B and (F_odd - 1)^2 > A."""
    # Test on coordinate x = 210 (Sy=30, t=7)
    x = 210
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(5, 7)
    F, R = compute_divisor_and_cofactor(x)
    assert F * F > B

    # Odd part of F
    F_odd = get_odd_part(F)
    assert (F_odd - 1) ** 2 > A
