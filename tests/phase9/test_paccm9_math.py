"""
Unit tests for Phase 9 mathematical foundations and algorithms.
"""

import math
import pytest
import sympy as sp
import gmpy2

from src.phase9.math import (
    construct_pair,
    solve_cubic_roots_mod_q,
    get_forbidden_t_residues,
    lucas_u_mod,
    find_morrison_params
)
from src.phase9.anchor import PrimorialAnchor, is_small_prime_deterministic


def test_construct_pair_properties():
    # Test for several x values
    for x in [6, 30, 210, 2310, 30030]:
        C, A, B = construct_pair(x)
        # Gap of 2
        assert B - A == 2
        # C is even and divisible by 6
        assert C % 6 == 0
        assert A % 2 == 1 and B % 2 == 1
        assert A % 3 != 0 and B % 3 != 0
        # Check algebraic identity: C = 2*x^2*(3x + 1)
        assert C == 2 * (x ** 2) * (3 * x + 1)
        assert A == 6 * (x ** 3) + 2 * (x ** 2) - 1
        assert B == 6 * (x ** 3) + 2 * (x ** 2) + 1


def test_anchor_immunity():
    # Verify that neither A nor B has any prime factor <= y
    anchor = PrimorialAnchor(y=13)
    for t in [1, 3, 5, 7, 11, 13, 17, 19]:
        x = anchor.compute_x(t)
        C, A, B = construct_pair(x)
        for p in anchor.primes:
            assert A % p != 0, f"A is divisible by anchor prime {p}"
            assert B % p != 0, f"B is divisible by anchor prime {p}"
            assert math.gcd(A, p) == 1
            assert math.gcd(B, p) == 1


def test_cubic_root_finder():
    # For every prime q in [5, 200], verify every returned root is an exact root
    for q in sp.primerange(5, 200):
        for sign in (1, -1):
            roots = solve_cubic_roots_mod_q(q, sign)
            for r in roots:
                assert 0 <= r < q
                val = (6 * (r ** 3) + 2 * (r ** 2) + sign) % q
                assert val == 0, f"Root {r} failed for q={q}, sign={sign}"


def test_forbidden_residues():
    anchor = PrimorialAnchor(y=5) # primes 2, 3, 5
    for q in sp.primerange(7, 100):
        S_y_mod_q = anchor.S_y % q
        forbidden_t = get_forbidden_t_residues(q, S_y_mod_q)
        for t in forbidden_t:
            x = (anchor.S_y * t) % q
            val_B = (6 * (x ** 3) + 2 * (x ** 2) + 1) % q
            val_A = (6 * (x ** 3) + 2 * (x ** 2) - 1) % q
            assert val_A == 0 or val_B == 0, f"Forbidden t={t} did not annihilate mod q={q}"


def test_lucas_u_matrix_powering():
    # Fibonacci sequence: P=1, Q=-1 => F_0=0, F_1=1, F_2=1, F_3=2, F_4=3, F_5=5, F_6=8, F_7=13
    expected_fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    for k, expected in enumerate(expected_fib):
        res = lucas_u_mod(1, -1, k, 10000)
        assert res == expected, f"Fibonacci mismatch at k={k}: got {res}, expected {expected}"


def test_morrison_params_finder():
    # For odd primes A in 100..500, find_morrison_params must find P with (D/A) == -1
    for A in sp.primerange(101, 500):
        P, D = find_morrison_params(A)
        assert P >= 3
        assert D == P * P - 4
        assert gmpy2.jacobi(D, A) == -1
        # Also check U_{A+1}(P, 1) == 0 mod A
        u = lucas_u_mod(P, 1, A + 1, A)
        assert u == 0, f"U_{{A+1}} failed for A={A}, P={P}"
