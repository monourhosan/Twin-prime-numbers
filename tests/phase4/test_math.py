"""
Phase 4 Mathematics Acceptance Tests.
Validates exact formulas, digit counting, modular arithmetic, Jacobi symbols,
and Lucas recurrence equivalence between Montgomery ladder and 2x2 matrix powering.
"""

import pytest
import sympy
from src.phase4.math_family import (
    k_to_t, t_to_k, compute_pair_integers, exact_decimal_digits,
    compute_t_residues_for_prime, jacobi_symbol, lucas_v_montgomery, lucas_v_matrix,
    validate_proth_preconditions, validate_llr_preconditions
)
from src.phase4.backend import pow_mod, square_sub_2_mod, jacobi, has_gmpy2

def test_k_to_t_roundtrip():
    for t in [0, 1, 2, 5, 10, 100, 1000]:
        k = t_to_k(t)
        assert k % 2 == 1
        assert k % 3 == 0
        assert k_to_t(k) == t

def test_invalid_k():
    with pytest.raises(ValueError):
        k_to_t(1) # odd, but not divisible by 3
    with pytest.raises(ValueError):
        k_to_t(6) # divisible by 3, but even
    with pytest.raises(ValueError):
        k_to_t(-3)

def test_exact_integer_and_digits():
    # Test k=3, n=3328 (Target 1,000 digits)
    A, B = compute_pair_integers(3, 3328)
    assert B - A == 2
    d_A = exact_decimal_digits(A)
    d_B = exact_decimal_digits(B)
    assert d_A == 1003
    assert d_B == 1003

def test_jacobi_against_sympy():
    test_cases = [
        (3, 11), (5, 11), (7, 11),
        (2, 1000000007), (5, 1000000007),
        (3, 15993 * (1 << 672) - 1),
        (5, 254697 * (1 << 1024) - 1)
    ]
    for a, n in test_cases:
        res_sym = sympy.jacobi_symbol(a, n)
        res_std = jacobi_symbol(a, n)
        res_bke = jacobi(a, n)
        assert res_std == res_sym, f"Mismatch for jacobi({a}, {n})"
        assert res_bke == res_sym, f"Backend mismatch for jacobi({a}, {n})"

def test_lucas_montgomery_vs_matrix():
    mod = 1000000007
    P = 5
    for k in [1, 2, 3, 7, 15, 33, 100, 1024, 15993]:
        v_mont = lucas_v_montgomery(k, P, mod)
        v_matr = lucas_v_matrix(k, P, mod)
        assert v_mont == v_matr, f"Lucas mismatch at k={k}: {v_mont} != {v_matr}"

def test_proth_preconditions():
    # Valid
    valid, _ = validate_proth_preconditions(3, 3328, 3 * (1 << 3328) + 1)
    assert valid

    # Invalid k >= 2^n
    valid, msg = validate_proth_preconditions(17, 3, 17 * (1 << 3) + 1)
    assert not valid
    assert "k < 2^n" in msg

    # Invalid even k
    valid, _ = validate_proth_preconditions(4, 10, 4 * (1 << 10) + 1)
    assert not valid

def test_llr_preconditions():
    # Valid
    valid, _ = validate_llr_preconditions(3, 3328, 3 * (1 << 3328) - 1)
    assert valid

    # Invalid n < 2
    valid, msg = validate_llr_preconditions(3, 1, 5)
    assert not valid
