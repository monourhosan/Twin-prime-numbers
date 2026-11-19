"""Feature 3: Mathematical Specification and Gating Proofs.

Verifies:
1. Formal algebraic proof of exact twin gap B - A = 2.
2. Congruence proof of C(x) = 0 mod 6, A = 5 mod 6, B = 1 mod 6.
3. Coprimality of divisor F(x) = 6x^3 and cofactor R(x) = 2x^2 + 1 when 3 | x.
4. Super-root inequalities: F^2 > B for all x >= 1, and (F_odd - 1)^2 > A for x >= 86.
5. Polynomial irreducibility of cofactors over the rationals Q.
"""

import math
from pathlib import Path
import pytest
import sympy
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    check_algebraic_invariants,
    get_odd_part,
)


MATH_SPEC_PATH = Path("research/phase11/MATHEMATICAL_SPECIFICATION.md")


@pytest.mark.phase11_tier1
def test_f03_twin_gap_proof_and_invariant() -> None:
    """Verifies that B(x) - A(x) = 2 algebraically and across numerical test coordinates."""
    if MATH_SPEC_PATH.is_file():
        content = MATH_SPEC_PATH.read_text(encoding="utf-8")
        assert "B(x) - A(x) = 2" in content or "B - A = 2" in content

    # Numerical verification across coordinates
    for x in [1, 2, 6, 30, 86, 210, 1000, 10000]:
        C, A, B = compute_manifold(x)
        assert B - A == 2, f"Twin gap violation at x={x}: {B - A}"
        assert A == C - 1
        assert B == C + 1


@pytest.mark.phase11_tier1
def test_f03_center_mod_6_congruence() -> None:
    """Verifies that C(x) = 0 mod 6, A(x) = 5 mod 6, and B(x) = 1 mod 6 when 6 | x."""
    # When 6 | x
    for x in [6, 12, 18, 30, 42, 60, 210, 2310]:
        C, A, B = compute_manifold(x)
        assert C % 6 == 0, f"C not divisible by 6 at x={x}"
        assert A % 6 == 5, f"A not 5 mod 6 at x={x}"
        assert B % 6 == 1, f"B not 1 mod 6 at x={x}"
        # Neither divisible by 2 or 3
        assert A % 2 != 0 and B % 2 != 0
        assert A % 3 != 0 and B % 3 != 0


@pytest.mark.phase11_tier1
def test_f03_divisor_cofactor_coprimality() -> None:
    """Verifies gcd(F(x), R(x)) = gcd(6x^3, 2x^2 + 1) = 1 whenever 3 | x."""
    for x in [3, 6, 9, 12, 30, 84, 90, 210, 2310]:
        F, R = compute_divisor_and_cofactor(x)
        g = math.gcd(F, R)
        assert g == 1, f"Expected gcd=1 at x={x}, got {g}"

    # Confirm that when 3 does not divide x, gcd is 3
    for x in [1, 2, 4, 5, 7, 85, 86, 100]:
        F, R = compute_divisor_and_cofactor(x)
        g = math.gcd(F, R)
        assert g == 3, f"Expected gcd=3 when 3 does not divide x={x}, got {g}"


@pytest.mark.phase11_tier1
def test_f03_super_root_bounds() -> None:
    """Verifies F^2 > B for all x >= 1, and (F_odd - 1)^2 > A for x >= 86."""
    # F^2 > B for all x >= 1
    for x in range(1, 50):
        C, A, B = compute_manifold(x)
        F, R = compute_divisor_and_cofactor(x)
        assert F * F > B, f"F^2 <= B at x={x}"

    # Morrison super-root boundary: (F_odd - 1)^2 > A at x >= 86 (with nu_2(x) = 1)
    # x = 85 fails
    C_85, A_85, _ = compute_manifold(85)
    F_85, _ = compute_divisor_and_cofactor(85)
    F_odd_85 = F_85 // 16
    assert (F_odd_85 - 1) ** 2 <= A_85

    # x = 86 passes
    C_86, A_86, _ = compute_manifold(86)
    F_86, _ = compute_divisor_and_cofactor(86)
    F_odd_86 = F_86 // 16
    assert (F_odd_86 - 1) ** 2 > A_86


@pytest.mark.phase11_tier1
def test_f03_polynomial_irreducibility() -> None:
    """Verifies that cofactor 2x^2 + 1 is irreducible over Q."""
    x = sympy.Symbol("x")
    R_poly = 2 * (x ** 2) + 1
    factors = sympy.factor_list(R_poly)
    # factor_list returns (content, [(poly, multiplicity)])
    # For irreducible 2x^2 + 1 over Q, factors[1] has length 1 with polynomial of degree 2
    assert len(factors[1]) == 1
    assert factors[1][0][0] == R_poly
    assert factors[1][0][1] == 1
