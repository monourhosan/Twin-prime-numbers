"""Feature 10: Symmetric Quintic Modular Sieve.

Verifies:
1. Root-negation symmetry r_B = (q - r_A) mod q between upper and lower candidates.
2. Inert quadratic cofactor classification (-2/q = -1 <=> q = 5, 7 mod 8).
3. Automatic skipping of prime moduli dividing the primorial anchor S_y.
4. Sieve survivor generation and correctness via Phase11ContractAdapter.
5. Monotonic survivor reduction with increasing sieve depth.
"""

from pathlib import Path
import pytest
from sympy.ntheory import primerange
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    verify_root_negation_symmetry,
    is_inert_modulus,
    compute_primorial_anchor,
    trial_division,
)


@pytest.mark.phase11_tier1
def test_f10_root_negation_symmetry() -> None:
    """Verifies that for any prime q, roots satisfy r_B = (q - r_A) mod q."""
    test_primes = [q for q in primerange(5, 100)]
    for q in test_primes:
        assert verify_root_negation_symmetry(q), f"Symmetry failed for prime {q}"


@pytest.mark.phase11_tier1
def test_f10_inert_moduli_classification() -> None:
    """Verifies inert moduli (-2/q = -1) are exactly primes q = 5, 7 mod 8."""
    test_primes = [q for q in primerange(3, 150)]
    for q in test_primes:
        is_inert = is_inert_modulus(q)
        expected = (q % 8 in (5, 7))
        assert is_inert == expected, f"Inert check mismatch at prime {q}: {is_inert} != {expected}"


@pytest.mark.phase11_tier1
def test_f10_sieve_skips_multiples_of_Sy() -> None:
    """Verifies primes dividing S_y never divide A(x) or B(x) because x = 0 mod p."""
    Sy, Sy_factors = compute_primorial_anchor(7)  # primes 2, 3, 5, 7
    for p in Sy_factors.keys():
        for t in range(1, 10):
            C, A, B = Phase11ContractAdapter.compute_candidate_pair(7, t)
            assert A % p != 0, f"A divisible by anchor prime {p} for t={t}"
            assert B % p != 0, f"B divisible by anchor prime {p} for t={t}"


@pytest.mark.phase11_tier1
def test_f10_sieve_survivor_execution_via_adapter() -> None:
    """Verifies that adapter sieve returns survivors free of small factors."""
    y = 5
    t_start = 1
    t_end = 50
    depth = 100

    survivors = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, depth)
    assert isinstance(survivors, list)
    assert len(survivors) > 0

    for t in survivors:
        _, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        assert trial_division(A, depth) is True
        assert trial_division(B, depth) is True


@pytest.mark.phase11_tier1
def test_f10_vectorized_sieve_density_reduction() -> None:
    """Verifies increasing sieve depth monotonically eliminates more candidates."""
    y = 3
    t_start = 1
    t_end = 100

    survivors_depth_20 = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, 20)
    survivors_depth_100 = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, 100)
    survivors_depth_500 = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, 500)

    assert len(survivors_depth_20) >= len(survivors_depth_100)
    assert len(survivors_depth_100) >= len(survivors_depth_500)
    # Check strict subset property
    assert set(survivors_depth_500).issubset(set(survivors_depth_100))
    assert set(survivors_depth_100).issubset(set(survivors_depth_20))
