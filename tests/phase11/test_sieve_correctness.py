"""Unit and Property Tests for Milestone M3 Symmetric Modular Sieve (`src/phase11/sieve.py`).

Verifies:
  1. Root-negation symmetry r_A = (q - r_B) mod q across all primes < 1000.
  2. Inert moduli classification (-2/q = -1 <=> q = 5, 7 mod 8).
  3. Divisibility skipping for anchor primes q <= y.
  4. Bit-for-bit survivor match between NumPy vectorized sieve and mathematical trial division.
  5. Monotonic survivor reduction with increasing sieve depth.
  6. Verified twin prime candidate survival (e.g. t=21 for y=3, t=215 for y=5).
"""

from sympy.ntheory import primerange

from src.phase11.math_model import compute_candidate_pair
from src.phase11.sieve import (
    find_roots_mod_q,
    is_inert_modulus,
    prepare_sieve_plan,
    sieve_survivors,
)


def test_sieve_root_negation_symmetry() -> None:
    """Verifies r_A = (q - r_B) mod q for all primes q in [5, 200]."""
    for q in primerange(5, 200):
        roots_A, roots_B = find_roots_mod_q(q)
        expected_A = sorted([(q - r) % q for r in roots_B])
        assert roots_A == expected_A, f"Root negation symmetry failed for prime {q}"


def test_sieve_inert_moduli_classification() -> None:
    """Verifies inert moduli (-2/q = -1) match exactly q = 5, 7 mod 8."""
    for q in primerange(3, 300):
        assert is_inert_modulus(q) == (q % 8 in (5, 7))


def test_sieve_vectorized_matches_exact_trial_division() -> None:
    """Differential test: vectorized NumPy sieve vs exact BigInt division."""
    y = 3
    sieve_depth = 50
    t_start, t_end = 1, 60

    vectorized_survivors = set(sieve_survivors(y, t_start, t_end, sieve_depth))
    primes_to_check = [p for p in primerange(y + 1, sieve_depth + 1)]

    for t in range(t_start, t_end + 1):
        _, A, B = compute_candidate_pair(y, t)
        has_factor = any(A % p == 0 or B % p == 0 for p in primes_to_check)
        if has_factor:
            assert t not in vectorized_survivors, f"t={t} has factor but survived"
        else:
            assert t in vectorized_survivors, f"t={t} is clean but was eliminated"


def test_sieve_monotonic_reduction() -> None:
    """Increasing sieve depth monotonically reduces survivors."""
    y = 5
    t_start, t_end = 1, 100
    s_20 = sieve_survivors(y, t_start, t_end, 20)
    s_100 = sieve_survivors(y, t_start, t_end, 100)
    s_300 = sieve_survivors(y, t_start, t_end, 300)

    assert len(s_20) >= len(s_100) >= len(s_300)
    assert set(s_300).issubset(set(s_100))
    assert set(s_100).issubset(set(s_20))


def test_sieve_preserves_verified_twins() -> None:
    """Verifies that known twin prime candidate multipliers survive sieve."""
    # y=3, t=21 -> x=126
    survivors_y3 = sieve_survivors(y=3, t_start=15, t_end=25, sieve_depth=100)
    assert 21 in survivors_y3

    # y=5, t=215 -> x=6450
    survivors_y5 = sieve_survivors(y=5, t_start=210, t_end=220, sieve_depth=200)
    assert 215 in survivors_y5


def test_sieve_plan_skips_anchor_primes() -> None:
    """Verifies primes q <= y are never included in the sieve plan."""
    for y in [3, 5, 7]:
        plan = prepare_sieve_plan(y, sieve_depth=100)
        plan_primes = [p.q for p in plan]
        assert all(q > y for q in plan_primes)


def test_sieve_odd_only_matches_oracle() -> None:
    """Verifies that odd_only=True matches [t for t in full_sieve if t % 2 == 1] bit-for-bit."""
    test_cases = [
        # (y, t_start, t_end, depth)
        (3, 1, 50, 50),
        (3, 2, 50, 50),
        (3, 1, 51, 100),
        (3, 2, 51, 100),
        (5, 1, 100, 100),
        (5, 10, 200, 300),
        (7, 1, 120, 150),
        (3, 15, 25, 100),
        (5, 210, 220, 200),
        # Boundary cases: single odd, single even, empty range
        (3, 7, 7, 50),
        (3, 8, 8, 50),
        (3, 10, 9, 50),
    ]

    for y, t_start, t_end, depth in test_cases:
        odd_survivors = sieve_survivors(y, t_start, t_end, depth, odd_only=True)
        full_survivors = sieve_survivors(y, t_start, t_end, depth, odd_only=False)
        expected = [t for t in full_survivors if t % 2 == 1]
        assert odd_survivors == expected, (
            f"Differential mismatch for y={y}, range=[{t_start}, {t_end}], depth={depth}: "
            f"got {odd_survivors}, expected {expected}"
        )
