"""
Unit tests for Phase 6 forbidden residue classes modulo sieve primes.
"""

import pytest
from src.phase6.center_sieve import get_forbidden_residues, is_small_prime_equality
from src.phase6.primes import generate_primes_up_to

def test_forbidden_residue_classes_against_brute_force():
    """Verify that 6m - 1 = 0 mod q iff m = 6^(-1) mod q, and 6m + 1 = 0 mod q iff m = -6^(-1) mod q."""
    primes = generate_primes_up_to(200)
    for q in primes:
        if q < 5:
            continue
        inv6, neg_inv6 = get_forbidden_residues(q)
        assert inv6 != neg_inv6, f"Forbidden residues must be distinct for prime {q}"
        
        # Test all residues m in [0, q-1]
        for m in range(q):
            A = 6 * m - 1
            B = 6 * m + 1
            if m == inv6:
                assert A % q == 0, f"Expected 6*{m} - 1 = 0 mod {q}"
            else:
                assert A % q != 0, f"Unexpected 6*{m} - 1 = 0 mod {q}"
                
            if m == neg_inv6:
                assert B % q == 0, f"Expected 6*{m} + 1 = 0 mod {q}"
            else:
                assert B % q != 0, f"Unexpected 6*{m} + 1 = 0 mod {q}"

def test_distinctness_up_to_1000():
    """Confirms that for all primes 5 <= q <= 1000, 6^(-1) != -6^(-1) mod q."""
    primes = generate_primes_up_to(1000)
    for q in primes:
        if q >= 5:
            inv6, neg_inv6 = get_forbidden_residues(q)
            assert inv6 != neg_inv6

def test_invalid_prime_rejection():
    """Verifies that primes 2 and 3 raise ValueError."""
    with pytest.raises(ValueError):
        get_forbidden_residues(2)
    with pytest.raises(ValueError):
        get_forbidden_residues(3)

def test_small_prime_equality_cases():
    """Verify small prime equality edge cases."""
    # For m=1: A = 5, B = 7
    assert is_small_prime_equality(1, 5) is True
    assert is_small_prime_equality(1, 7) is True
    assert is_small_prime_equality(1, 11) is False
    # For m=2: A = 11, B = 13
    assert is_small_prime_equality(2, 11) is True
    assert is_small_prime_equality(2, 13) is True
