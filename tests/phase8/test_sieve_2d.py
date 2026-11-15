"""
Unit and integration tests for Phase 8 2D sieve engine.
"""

import pytest
from src.phase8.sieve_2d import ADES8TwoDimSieve
from src.phase8.math import compute_candidate_pair, get_small_primes, exact_digit_t_bounds


def test_2d_sieve_variants_identical_survivors():
    """
    Compares Variant B (CPU reference 2D) and Variant C (ADES-8 recurrence).
    Confirms exact 100% bitwise survivor equality.
    """
    sieve = ADES8TwoDimSieve(R=13, sieve_limit=10000)
    surv_rec, m_rec = sieve.sieve_tile_recurrence(n_start=5000, n_height=8, t_start=20000, t_width=2000)
    surv_ref, m_ref = sieve.sieve_tile_reference_2d(n_start=5000, n_height=8, t_start=20000, t_width=2000)

    assert len(surv_rec) > 0
    assert surv_rec == surv_ref


def test_2d_sieve_vs_1d_baseline_row_by_row():
    """
    Compares Variant C (ADES-8 2D) against Variant A (1D fixed exponent baseline).
    Each row of the 2D tile must match the 1D sieve exactly.
    """
    sieve = ADES8TwoDimSieve(R=13, sieve_limit=5000)
    n_start = 100
    n_height = 4
    t_start = 500
    t_width = 1000

    surv_2d, _ = sieve.sieve_tile_recurrence(n_start=n_start, n_height=n_height, t_start=t_start, t_width=t_width)

    # Reconstruct row by row using 1D baseline
    surv_1d_combined = []
    for row in range(n_height):
        n = n_start + row
        surv_row, _ = sieve.sieve_row_baseline_1d(n=n, t_start=t_start, t_width=t_width)
        for t_val in surv_row:
            surv_1d_combined.append((n, t_val))

    assert surv_2d == surv_1d_combined


def test_survivor_coprimality_to_sieve_primes():
    """
    Confirms that for any survivor (n, t), neither C-1 nor C+1 has any prime factor <= S.
    """
    sieve_limit = 2000
    sieve = ADES8TwoDimSieve(R=13, sieve_limit=sieve_limit)
    survivors, _ = sieve.sieve_tile_recurrence(n_start=200, n_height=2, t_start=100, t_width=500)

    primes = [p for p in get_small_primes(sieve_limit) if p > 2 and sieve.M % p != 0]

    for n, t in survivors[:50]:  # Test first 50 survivors
        _, _, A, Bprime = compute_candidate_pair(sieve.M, t, n)
        for p in primes:
            assert A % p != 0, f"Prime {p} divides A for survivor ({n}, {t})"
            assert Bprime % p != 0, f"Prime {p} divides Bprime for survivor ({n}, {t})"


def test_sieve_with_digit_bounds():
    """
    Ensures that sieve with digit_band=1515 filters out candidates outside the digit band.
    """
    sieve = ADES8TwoDimSieve(R=13, sieve_limit=2000)
    # n=5000 has t_min=23576, t_max=235757
    survivors, _ = sieve.sieve_tile_recurrence(
        n_start=5000,
        n_height=2,
        t_start=20000,  # Below t_min
        t_width=5000,   # Span [20000, 24999]
        digit_band=1515
    )

    for n, t in survivors:
        _, _, t_min, t_max = exact_digit_t_bounds(1515, sieve.M, n)
        assert t >= t_min, f"t={t} < t_min={t_min}"
        assert t <= t_max, f"t={t} > t_max={t_max}"
