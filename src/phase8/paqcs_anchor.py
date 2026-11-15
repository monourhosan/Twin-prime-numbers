"""
PAQCS Primorial Anchor & Factorization Module (Phase 8).
Constructs, verifies, and manages the large primorial anchor S_y
and the complete factorization of x = S_y * t.
"""

import hashlib
import json
import math
from typing import List, Tuple, Dict, Any


def is_small_prime_deterministic(p: int) -> bool:
    """Deterministic trial division primality test for integers up to 10^14."""
    if p < 2:
        return False
    if p in (2, 3):
        return True
    if p % 2 == 0 or p % 3 == 0:
        return False
    d = 5
    while d * d <= p:
        if p % d == 0 or p % (d + 2) == 0:
            return False
        d += 6
    return True


def sieve_primes_up_to(bound: int) -> List[int]:
    """Generates all primes up to bound using an exact boolean sieve."""
    if bound < 2:
        return []
    sieve = bytearray([1]) * (bound + 1)
    sieve[0] = sieve[1] = 0
    for p in range(2, int(math.isqrt(bound)) + 1):
        if sieve[p]:
            sieve[p * p : bound + 1 : p] = bytearray([0]) * len(sieve[p * p : bound + 1 : p])
    return [i for i, is_p in enumerate(sieve) if is_p]


def factor_small_int(n: int) -> List[Tuple[int, int]]:
    """Completely factors an integer n <= 10^9 via trial division, returning (prime, multiplicity)."""
    assert n > 0
    factors = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            exp = 0
            while n % d == 0:
                exp += 1
                n //= d
            factors.append((d, exp))
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append((n, 1))
    return factors


class PrimorialAnchor:
    """
    Manages the primorial anchor S_y = product_{3 <= p <= y, p prime} p.
    """

    def __init__(self, y: int = 1780):
        self.y = y
        self.primes = [p for p in sieve_primes_up_to(y) if p > 2]
        self.S_y = 1
        for p in self.primes:
            self.S_y *= p
        self.digits = len(str(self.S_y))
        
        # Verify deterministic primality of all factors
        for p in self.primes:
            assert is_small_prime_deterministic(p), f"Anchor factor {p} failed primality test!"

        # Canonical SHA-256 of prime factor list
        raw_list = ",".join(str(p) for p in self.primes)
        self.factors_sha256 = hashlib.sha256(raw_list.encode('utf-8')).hexdigest()

    def get_manifest(self) -> Dict[str, Any]:
        return {
            "y_bound": self.y,
            "prime_count": len(self.primes),
            "smallest_prime": self.primes[0],
            "largest_prime": self.primes[-1],
            "S_y_decimal": str(self.S_y),
            "S_y_digits": self.digits,
            "factors_sha256": self.factors_sha256,
            "primes_list": self.primes
        }

    def compute_min_t(self, target_digits: int = 1511, h: int = 3) -> int:
        """
        Computes the minimum odd integer t such that
        A = x(x - h) - 1 >= 10^(target_digits - 1), where x = S_y * t.
        Uses exact integer binary search.
        """
        target_A = 10 ** (target_digits - 1)
        lo = 1
        hi = 10 ** 900
        while lo < hi:
            mid = (lo + hi) // 2
            if mid * (mid - h) - 1 >= target_A:
                hi = mid
            else:
                lo = mid + 1
        min_x = lo
        t_min = (min_x + self.S_y - 1) // self.S_y
        if t_min % 2 == 0:
            t_min += 1
        return t_min

    def factor_x(self, t: int) -> Tuple[List[int], Dict[int, int]]:
        """
        Produces the complete prime factorization of x = S_y * t.
        Returns:
            distinct_primes: sorted list of distinct prime factors of x.
            multiplicities: dict mapping each prime factor to its exponent in x.
        """
        assert t > 0 and t % 2 == 1, "t must be positive odd integer"
        t_factors = factor_small_int(t)
        
        multiplicities: Dict[int, int] = {p: 1 for p in self.primes}
        for p, exp in t_factors:
            assert is_small_prime_deterministic(p), f"t factor {p} failed primality test!"
            multiplicities[p] = multiplicities.get(p, 0) + exp

        distinct_primes = sorted(multiplicities.keys())
        return distinct_primes, multiplicities
