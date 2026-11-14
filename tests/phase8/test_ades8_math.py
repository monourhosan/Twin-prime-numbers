"""
Unit tests for Phase 8 ADES-8 mathematical foundations.
"""

import pytest
from src.phase8.math import (
    get_small_primes,
    get_primorial_multiplier,
    exact_digit_t_bounds,
    solve_modular_roots,
    ades8_recurrence_step,
    ades8_roots_from_a,
    compute_candidate_pair,
    jacobi_symbol,
    lucas_v_montgomery,
    lucas_v_matrix,
    deterministic_miller_rabin_64
)


def test_primorial_multiplier():
    assert get_primorial_multiplier(2) == 1
    assert get_primorial_multiplier(3) == 3
    assert get_primorial_multiplier(5) == 15
    assert get_primorial_multiplier(7) == 105
    assert get_primorial_multiplier(11) == 1155
    assert get_primorial_multiplier(13) == 15015


def test_exact_digit_bounds_1515d():
    D = 1515
    M = 15015
    n = 5000
    k_min, k_max, t_min, t_max = exact_digit_t_bounds(D, M, n)
    assert t_min <= t_max
    assert k_max < (1 << n)

    # Verify boundary candidate lengths
    k_low, C_low, A_low, B_low = compute_candidate_pair(M, t_min, n)
    k_high, C_high, A_high, B_high = compute_candidate_pair(M, t_max, n)

    assert len(str(A_low)) == D
    assert len(str(B_low)) == D
    assert len(str(A_high)) == D
    assert len(str(B_high)) == D


def test_modular_roots_divisibility():
    M = 15015
    n = 50
    test_primes = [17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
    for r in test_primes:
        t_minus, t_plus = solve_modular_roots(M, n, r)
        _, _, A_minus, B_minus = compute_candidate_pair(M, t_minus, n)
        _, _, A_plus, B_plus = compute_candidate_pair(M, t_plus, n)
        # r must divide A_minus = C-1
        assert A_minus % r == 0
        # r must divide B_plus = C+1
        assert B_plus % r == 0


def test_ades8_recurrence_vs_direct_oracle():
    M = 15015
    n_base = 5000
    H = 16
    primes = [p for p in get_small_primes(500) if p > 13]

    for p in primes:
        b = pow(2, -1, p)
        alpha_0 = (M * pow(2, n_base, p)) % p
        a = pow(alpha_0, -1, p)
        for row in range(H):
            n = n_base + row
            exp_minus, exp_plus = solve_modular_roots(M, n, p)
            rec_minus, rec_plus = ades8_roots_from_a(a, b, p)
            assert rec_minus == exp_minus
            assert rec_plus == exp_plus
            a = ades8_recurrence_step(a, b, p)


def test_primorial_coprimality_guarantee():
    M = 15015  # 3 * 5 * 7 * 11 * 13
    primes_dividing_M = [3, 5, 7, 11, 13]
    for t in range(5):
        for n in range(20, 25):
            k, C, A, Bprime = compute_candidate_pair(M, t, n)
            assert C % 6 == 0
            for p in primes_dividing_M:
                assert A % p != 0, f"p={p} divides A for t={t}, n={n}"
                assert Bprime % p != 0, f"p={p} divides B for t={t}, n={n}"


def test_lucas_montgomery_vs_matrix():
    # Test for various k, P, mod
    P = 15
    mod = 1000000007
    for k in (1, 3, 5, 17, 33, 105, 1001):
        v_mont = lucas_v_montgomery(k, P, mod)
        v_mat = lucas_v_matrix(k, P, mod)
        assert v_mont == v_mat, f"Mismatch at k={k}: {v_mont} != {v_mat}"


def test_deterministic_miller_rabin_64():
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 1000000007, 4294967311]
    for p in primes:
        assert deterministic_miller_rabin_64(p) is True

    composites = [1, 4, 6, 8, 9, 15, 21, 25, 27, 35, 1000000005, 4294967297]
    for c in composites:
        assert deterministic_miller_rabin_64(c) is False
