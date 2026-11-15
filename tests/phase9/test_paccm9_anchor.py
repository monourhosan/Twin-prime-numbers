"""
Unit tests for Primorial Anchor and factorization integrity.
"""

import math
import pytest
from sympy import primerange

from src.phase9.anchor import PrimorialAnchor, is_small_prime_deterministic, factor_small_int
from src.phase9.math import construct_pair


def test_small_prime_deterministic():
    # Known primes
    primes = list(primerange(2, 1000))
    for p in primes:
        assert is_small_prime_deterministic(p), f"Prime {p} rejected by deterministic MR"

    # Known composites
    composites = [4, 6, 8, 9, 10, 12, 14, 15, 21, 25, 27, 33, 35, 49, 77, 91, 561, 1105, 1729]
    for c in composites:
        assert not is_small_prime_deterministic(c), f"Composite {c} accepted as prime"


def test_anchor_factorization_integrity():
    for y in [5, 11, 23, 53]:
        anchor = PrimorialAnchor(y=y)
        for t in [7, 13, 31, 79]:
            x = anchor.compute_x(t)
            C, A, B = construct_pair(x)
            factors = anchor.get_F_factorization(t, t_is_prime=True)

            # Reconstruct F
            F = 1
            for p, exp in factors.items():
                F *= p ** exp

            expected_F = 2 * (x ** 2)
            assert F == expected_F, f"F product mismatch: got {F}, expected {expected_F}"

            # Verify coprimality gcd(F, 3x + 1) == 1
            assert math.gcd(F, 3 * x + 1) == 1

            # Verify size condition F^2 > B
            assert F * F > B
            assert F * F > A

            # Verify F divides B - 1
            assert (B - 1) % F == 0
            assert (A + 1) % F == 0


def test_factor_small_int():
    test_cases = {
        12: {2: 2, 3: 1},
        100: {2: 2, 5: 2},
        2310: {2: 1, 3: 1, 5: 1, 7: 1, 11: 1},
        13: {13: 1}
    }
    for n, expected in test_cases.items():
        assert factor_small_int(n) == expected
