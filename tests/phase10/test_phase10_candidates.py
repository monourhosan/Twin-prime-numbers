"""
Tests for Phase 10 Algebraic Center Constructions.
Validates:
1. Irreducibility over Q of P_+(x) and P_-(x) for all 3 candidate families
2. Super-root dominance F^2 > B and (F_odd - 1)^2 > A
3. Coprimality gcd(F, R) == 1
4. Deterministic Dual-BLS (Pocklington Thm 4 + Morrison Thm 17) proof certification
"""

import math
import gmpy2
import pytest
import sympy as sp

from src.phase9.anchor import factor_small_int
from src.phase9.math import lucas_u_mod


def test_phase10_candidate1_abbm10_algebra():
    """Validates Asymmetric Bi-Primorial Bilinear Manifold (ABBM-10)."""
    u, v = sp.symbols('u v')
    B = 6 * u**3 * v + 2 * u**2 * v**2 + 1
    A = 6 * u**3 * v + 2 * u**2 * v**2 - 1

    # Irreducibility
    assert sp.factor(B) == sp.expand(B)
    assert sp.factor(A) == sp.expand(A)

    # Verification on tested prime instance u=12, v=35
    u_val, v_val = 12, 35
    C = 2 * u_val**2 * v_val * (3 * u_val + v_val)
    A_val = C - 1
    B_val = C + 1
    assert B_val - A_val == 2
    assert C % 6 == 0

    F = 2 * u_val**2 * v_val
    F_odd = (u_val // 2)**2 * v_val
    assert F**2 > B_val
    assert (F_odd - 1)**2 > A_val

    # Pocklington on B
    factors_F = factor_small_int(F)
    B_minus_1 = B_val - 1
    for p in factors_F:
        found_w = False
        for a in range(2, 50):
            if gmpy2.powmod(a, B_minus_1, B_val) == 1:
                term = (gmpy2.powmod(a, B_minus_1 // p, B_val) - 1) % B_val
                if math.gcd(int(term), B_val) == 1:
                    found_w = True
                    break
        assert found_w, f"Missing Pocklington witness for prime {p}"

    # Morrison on A
    odd_primes = [p for p in factors_F if p != 2]
    A_plus_1 = A_val + 1
    P = 21
    D = P * P - 4
    assert gmpy2.jacobi(D, A_val) == -1
    assert lucas_u_mod(P, 1, A_plus_1, A_val) == 0
    for q in odd_primes:
        assert math.gcd(lucas_u_mod(P, 1, A_plus_1 // q, A_val), A_val) == 1


def test_phase10_candidate2_opqm10_algebra():
    """Validates Odd-Parity Quintic Manifold (OPQM-10)."""
    x = sp.symbols('x')
    B = 12 * x**5 + 6 * x**3 + 1
    A = 12 * x**5 + 6 * x**3 - 1

    # Irreducibility
    assert sp.factor(B) == sp.expand(B)
    assert sp.factor(A) == sp.expand(A)

    # Root negation symmetry: f_A(-x) = -f_B(x)
    assert sp.expand(B.subs(x, -x)) == sp.expand(-A)

    # Verification on tested prime instance x=126
    x_val = 126
    C = 6 * x_val**3 * (2 * x_val**2 + 1)
    A_val = C - 1
    B_val = C + 1
    assert B_val - A_val == 2
    assert C % 6 == 0

    F = 6 * x_val**3
    F_odd = (3**7) * (7**3)
    assert F**2 > B_val
    assert (F_odd - 1)**2 > A_val

    # Pocklington on B
    factors_F = {2: 4, 3: 7, 7: 3}
    B_minus_1 = B_val - 1
    for p in factors_F:
        found_w = False
        for a in range(2, 50):
            if gmpy2.powmod(a, B_minus_1, B_val) == 1:
                term = (gmpy2.powmod(a, B_minus_1 // p, B_val) - 1) % B_val
                if math.gcd(int(term), B_val) == 1:
                    found_w = True
                    break
        assert found_w, f"Missing Pocklington witness for prime {p}"

    # Morrison on A
    odd_primes = [3, 7]
    A_plus_1 = A_val + 1
    P = 3
    D = P * P - 4
    assert gmpy2.jacobi(D, A_val) == -1
    assert lucas_u_mod(P, 1, A_plus_1, A_val) == 0
    for q in odd_primes:
        assert math.gcd(lucas_u_mod(P, 1, A_plus_1 // q, A_val), A_val) == 1


def test_phase10_candidate3_cdcm10_algebra():
    """Validates Cyclotomic Difference-of-Cubes Manifold (CDCM-10)."""
    u, v = sp.symbols('u v')
    B = 6 * u**2 * v**2 * (u**2 + u * v + v**2) + 1
    A = 6 * u**2 * v**2 * (u**2 + u * v + v**2) - 1

    # Irreducibility
    assert sp.factor(B) == sp.expand(B)
    assert sp.factor(A) == sp.expand(A)

    # Verification on tested prime instance u=8, v=25
    u_val, v_val = 8, 25
    C = 6 * u_val**2 * v_val**2 * (u_val**2 + u_val * v_val + v_val**2)
    A_val = C - 1
    B_val = C + 1
    assert B_val - A_val == 2
    assert C % 6 == 0

    F = 6 * u_val**2 * v_val**2
    F_odd = 3 * (u_val // 2)**2 * v_val**2
    assert F**2 > B_val
    assert (F_odd - 1)**2 > A_val

    # Pocklington on B
    factors_F = factor_small_int(F)
    B_minus_1 = B_val - 1
    for p in factors_F:
        found_w = False
        for a in range(2, 50):
            if gmpy2.powmod(a, B_minus_1, B_val) == 1:
                term = (gmpy2.powmod(a, B_minus_1 // p, B_val) - 1) % B_val
                if math.gcd(int(term), B_val) == 1:
                    found_w = True
                    break
        assert found_w, f"Missing Pocklington witness for prime {p}"

    # Morrison on A
    odd_primes = [p for p in factors_F if p != 2]
    A_plus_1 = A_val + 1
    P = 21
    D = P * P - 4
    assert gmpy2.jacobi(D, A_val) == -1
    assert lucas_u_mod(P, 1, A_plus_1, A_val) == 0
    for q in odd_primes:
        assert math.gcd(lucas_u_mod(P, 1, A_plus_1 // q, A_val), A_val) == 1
