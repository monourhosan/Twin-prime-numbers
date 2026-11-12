"""
Unit, property, and regression test suite for CATS.
"""

import pytest
import sympy
from src.cats.sieve import BoundedTwinSieve, StructuredTwinSieve
from src.cats.primality import (
    is_prime_u64,
    is_probable_prime,
    proth_prove,
    llr_prove,
    jacobi_symbol,
)
from src.cats.certificate import TwinPrimeCertificate

def test_bounded_sieve_small_range():
    """Verify exact twin prime count up to 100 (OEIS A001359)."""
    sieve = BoundedTwinSieve(2, 100)
    candidates, stats = sieve.run_sieve()
    twins = [p for p in candidates if is_prime_u64(p[0]) and is_prime_u64(p[1])]
    
    expected = [
        (3, 5), (5, 7), (11, 13), (17, 19),
        (29, 31), (41, 43), (59, 61), (71, 73)
    ]
    assert twins == expected
    assert len(twins) == 8

def test_bounded_sieve_1000():
    """Verify OEIS A001359 count up to 1,000 is exactly 35."""
    sieve = BoundedTwinSieve(2, 1000)
    candidates, _ = sieve.run_sieve()
    twins = [p for p in candidates if is_prime_u64(p[0]) and is_prime_u64(p[1])]
    assert len(twins) == 35
    assert twins[-1] == (881, 883)

def test_empty_interval():
    """Verify handling of interval with no twin primes."""
    sieve = BoundedTwinSieve(89, 100)
    candidates, _ = sieve.run_sieve()
    twins = [p for p in candidates if is_prime_u64(p[0]) and is_prime_u64(p[1])]
    assert len(twins) == 0

def test_special_pair_3_5():
    """Verify that (3, 5) is preserved when 2 <= min <= 3."""
    sieve = BoundedTwinSieve(3, 10)
    candidates, _ = sieve.run_sieve()
    twins = [p for p in candidates if is_prime_u64(p[0]) and is_prime_u64(p[1])]
    assert (3, 5) in twins
    assert (5, 7) in twins

def test_structured_sieve_small_cases():
    """Test k * 2^n +/- 1 structured search on small known pairs."""
    # n = 2: k * 4 +/- 1. For k=3: 12 +/- 1 = (11, 13)
    sieve = StructuredTwinSieve(n=2, k_min=1, k_max=10, sieve_depth=50)
    survivors, _ = sieve.run_sieve()
    assert 3 in survivors

def test_proth_theorem_provable():
    """Verify Proth's theorem proves B = 15 * 2^10 + 1 = 15361 is prime."""
    B = 15 * (1 << 10) + 1
    is_prime, witness = proth_prove(15, 10, B)
    assert is_prime is True
    assert witness is not None
    assert sympy.isprime(B)

def test_proth_rejects_composite():
    """Verify Proth's theorem rejects composite numbers."""
    # k = 9, n = 2 => B = 9 * 4 + 1 = 37 (prime)
    # k = 7, n = 2 => B = 7 * 4 + 1 = 29 (prime)
    # k = 5, n = 2 => B = 5 * 4 + 1 = 21 = 3 * 7 (composite)
    is_prime, _ = proth_prove(5, 2, 21)
    assert is_prime is False

def test_llr_prove_valid():
    """Verify LLR proves A = 15 * 2^10 - 1 = 15359 is prime."""
    A = 15 * (1 << 10) - 1
    is_prime, p_param, u0 = llr_prove(15, 10, A)
    assert is_prime is True
    assert p_param is not None
    assert sympy.isprime(A)

def test_llr_rejects_composite():
    """Verify LLR rejects composite numbers."""
    # k = 7, n = 3 => A = 7 * 8 - 1 = 55 = 5 * 11 (composite)
    is_prime, _, _ = llr_prove(7, 3, 55)
    assert is_prime is False

def test_certificate_tamper_detection():
    """Verify that tampering with any field invalidates the SHA-256 checksum."""
    cert = TwinPrimeCertificate(
        pair_type="Structured",
        p_minus_str="15359",
        p_plus_str="15361",
        digits=5,
        k=15,
        n=10,
        proth_witness=7,
        llr_witness=5,
        is_proven=True
    )
    assert cert.verify_checksum() is True

    # Tamper with p_plus
    cert.p_plus = "15363"
    assert cert.verify_checksum() is False
