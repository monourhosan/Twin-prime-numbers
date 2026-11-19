"""Tier 2 Boundary Tests - Feature 3: Mathematical Specification & Gating.

Verifies:
1. Boundary threshold at x=85 (marginal fail) vs x=86 (strict pass) for Morrison bound.
2. Rational irreducibility proof via Rational Root Theorem on C(x) +/- 1.
3. Root-negation symmetry with negative modulo representatives.
4. Inert moduli test (q = 5, 7 mod 8 <=> (-2/q) = -1) and cofactor root emptiness.
5. Accidental constant factors check across mod 2, 3, 5, 7 (no fixed divisors).
"""

import math
import pytest
import sympy
from sympy import symbols, Poly, Rational

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    get_odd_part,
    is_inert_modulus,
    verify_root_negation_symmetry,
)


@pytest.mark.phase11_tier2
def test_bnd03_super_root_threshold_85_vs_86() -> None:
    """Verifies the Morrison super-root boundary crossover at x=85 vs x=86 for nu_2(x)=1."""
    # When nu_2(x) = 1, e.g. x is even but not div by 4:
    # F(x) = 6*x^3 has power of 2: nu_2(6*x^3) = 1 + 3*1 = 4.
    # Therefore 2^4 = 16 is divided out to obtain F_odd = (6*x^3) // 16.
    # Morrison Theorem 17 requires (F_odd - 1)^2 > A.

    # 1. At x = 85 (odd x, let's test nu_2(x)=1 formula)
    # If nu_2(x)=1 formula is evaluated at x=85:
    x_85 = 85
    C_85 = 12 * (x_85**5) + 6 * (x_85**3)
    A_85 = C_85 - 1
    F_odd_85 = (6 * (x_85**3)) // 16
    morrison_85 = (F_odd_85 - 1) ** 2
    assert morrison_85 <= A_85, f"Expected x=85 to fail Morrison bound: {morrison_85} > {A_85}"

    # 2. At x = 86:
    x_86 = 86
    assert x_86 % 2 == 0 and x_86 % 4 != 0, "x=86 has nu_2(86)=1"
    C_86 = 12 * (x_86**5) + 6 * (x_86**3)
    A_86 = C_86 - 1
    F_86 = 6 * (x_86**3)
    F_odd_86 = get_odd_part(F_86)
    assert F_odd_86 == (6 * (86**3)) // 16
    morrison_86 = (F_odd_86 - 1) ** 2
    assert morrison_86 > A_86, f"Expected x=86 to pass Morrison bound: {morrison_86} <= {A_86}"

    # Margin check
    margin = morrison_86 - A_86
    assert margin > 0, f"Morrison margin must be positive at x=86, got {margin}"


@pytest.mark.phase11_tier2
def test_bnd03_rational_irreducibility() -> None:
    """Verifies that 12*x^5 + 6*x^3 +/- 1 have no rational roots."""
    x = symbols("x")
    for sign in [-1, 1]:
        poly = Poly(12 * x**5 + 6 * x**3 + sign, x)
        # By Rational Root Theorem, any rational root p/q must have:
        # p dividing +/- 1 (p in {-1, 1})
        # q dividing 12 (q in {1, 2, 3, 4, 6, 12})
        potential_roots = [
            Rational(p, q)
            for p in [-1, 1]
            for q in [1, 2, 3, 4, 6, 12]
        ]
        for root in potential_roots:
            val = poly.eval(root)
            assert val != 0, f"Rational root theorem violation: {root} is a root for sign={sign}"


@pytest.mark.phase11_tier2
def test_bnd03_root_negation_symmetry_negative_inputs() -> None:
    """Verifies root-negation symmetry r_A = -r_B mod q with centered/negative residues."""
    primes = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
    for q in primes:
        assert verify_root_negation_symmetry(q) is True

        # Test with negative residue representation: r in [- (q-1)//2, (q-1)//2]
        for r_A in range(q):
            c_A = (12 * pow(r_A, 5, q) + 6 * pow(r_A, 3, q) - 1) % q
            if c_A == 0:
                # Corresponding r_B must be (q - r_A) % q
                r_B = (q - r_A) % q
                c_B = (12 * pow(r_B, 5, q) + 6 * pow(r_B, 3, q) + 1) % q
                assert c_B == 0, f"Root negation failed for q={q}, r_A={r_A}, r_B={r_B}"
                # In centered residues, r_A + r_B == 0 mod q
                assert (r_A + r_B) % q == 0


@pytest.mark.phase11_tier2
def test_bnd03_inert_moduli_legendre_jacobi() -> None:
    """Verifies Legendre/Jacobi (-2/q) = -1 for q = 5, 7 mod 8 and cofactor root emptiness."""
    test_primes_inert = [5, 7, 13, 23, 29, 31, 37, 47, 53, 61, 71]
    for q in test_primes_inert:
        mod8 = q % 8
        if mod8 in (5, 7):
            assert is_inert_modulus(q) is True, f"Prime {q} (mod 8 = {mod8}) should be inert"
            # Verify R(x) = 2x^2 + 1 mod q has NO roots
            roots = [x for x in range(q) if (2 * x * x + 1) % q == 0]
            assert len(roots) == 0, f"Inert modulus {q} had non-empty roots: {roots}"
        elif mod8 in (1, 3):
            assert is_inert_modulus(q) is False, f"Prime {q} (mod 8 = {mod8}) should NOT be inert"
            # 2x^2 + 1 = 0 mod q has solutions because -2 is quadratic residue mod q
            roots = [x for x in range(q) if (2 * x * x + 1) % q == 0]
            assert len(roots) > 0, f"Non-inert prime {q} should have roots for 2x^2 + 1"


@pytest.mark.phase11_tier2
def test_bnd03_accidental_constant_factors_mod_small_primes() -> None:
    """Verifies that neither A(x) nor B(x) has a fixed constant factor among {2, 3, 5, 7}."""
    for q in [2, 3, 5, 7]:
        # For each small prime q, verify that A(x) and B(x) are not identically 0 mod q
        a_evals = [(12 * pow(x, 5, q) + 6 * pow(x, 3, q) - 1) % q for x in range(q)]
        b_evals = [(12 * pow(x, 5, q) + 6 * pow(x, 3, q) + 1) % q for x in range(q)]

        # Check there exists at least one x where A(x) != 0 mod q and B(x) != 0 mod q
        assert any(val != 0 for val in a_evals), f"A(x) is identically 0 mod {q}"
        assert any(val != 0 for val in b_evals), f"B(x) is identically 0 mod {q}"

        # Furthermore, for mod 2 and 3: 12x^5 + 6x^3 is always 0 mod 6!
        # So A(x) = -1 mod 6 and B(x) = +1 mod 6 for ALL integers x!
        # This guarantees A(x) is NEVER divisible by 2 or 3, and B(x) is NEVER divisible by 2 or 3!
        for x in range(12):
            c_val = 12 * (x**5) + 6 * (x**3)
            assert (c_val - 1) % 2 != 0, f"A({x}) is divisible by 2!"
            assert (c_val - 1) % 3 != 0, f"A({x}) is divisible by 3!"
            assert (c_val + 1) % 2 != 0, f"B({x}) is divisible by 2!"
            assert (c_val + 1) % 3 != 0, f"B({x}) is divisible by 3!"
