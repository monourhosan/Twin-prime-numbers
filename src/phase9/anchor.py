"""
Phase 9 Primorial Anchor & Factorization Utilities.
Implements exact primorial anchor construction, deterministic primality verification
for multiplier components (t < 2^64), and exact prime factorization tables for F = 2*x^2.
"""

import math
from typing import Dict, List, Tuple, Optional
import gmpy2
from sympy import primerange


def is_small_prime_deterministic(n: int) -> bool:
    """
    Jiang & Deng (2014) / Sinclair (2011) deterministic Miller-Rabin test
    for n < 2^64 using 7 proven bases:
    [2, 325, 9375, 28178, 450775, 9780504, 1795265022].
    Provably zero pseudoprimes below 2^64.
    """
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for sp in small_primes:
        if n == sp:
            return True
        if n % sp == 0:
            return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def factor_small_int(n: int) -> Dict[int, int]:
    """
    Returns prime factorization {prime: exponent} for small integer n.
    """
    factors: Dict[int, int] = {}
    if n <= 1:
        return factors

    # Factor out 2
    count_2 = 0
    while n % 2 == 0:
        count_2 += 1
        n //= 2
    if count_2 > 0:
        factors[2] = count_2

    # Trial division up to 10000
    d = 3
    while d * d <= n and d <= 10000:
        if n % d == 0:
            count = 0
            while n % d == 0:
                count += 1
                n //= d
            factors[d] = count
        d += 2

    if n > 1:
        if is_small_prime_deterministic(n):
            factors[n] = factors.get(n, 0) + 1
        else:
            # Simple Pollard rho fallback
            rem = int(gmpy2.mpz(n))
            while rem > 1:
                p = int(gmpy2.next_prime(1))
                found = False
                while p * p <= rem:
                    if rem % p == 0:
                        count = 0
                        while rem % p == 0:
                            count += 1
                            rem //= p
                        factors[p] = factors.get(p, 0) + count
                        found = True
                        break
                    p = int(gmpy2.next_prime(p))
                if not found:
                    factors[rem] = factors.get(rem, 0) + 1
                    break

    return factors


class PrimorialAnchor:
    """
    Constructs and manages the primorial anchor S_y = product_{p <= y} p.
    Maintains exact prime factor inventory for F = 2 * x^2 = 2 * S_y^2 * t^2.
    """

    def __init__(self, y: int):
        assert y >= 3, "Anchor prime y must be >= 3"
        self.y = y
        self.primes: List[int] = list(primerange(2, y + 1))
        
        # Exact product computation
        prod = 1
        for p in self.primes:
            prod *= p
        self.S_y = int(prod)
        self.digits = len(str(self.S_y))
        self.num_primes = len(self.primes)

    def compute_x(self, t: int) -> int:
        """Returns x = S_y * t."""
        return self.S_y * t

    def get_F_factorization(self, t: int, t_is_prime: bool = True) -> Dict[int, int]:
        """
        Returns exact prime factorization of F = 2 * x^2 = 2 * S_y^2 * t^2.
        Because S_y is square-free, each prime factor p <= y has:
          - p = 2: exponent = 2 * 1 + 1 = 3 (plus any 2-factors from t)
          - p > 2: exponent = 2 * 1 = 2 (plus any p-factors from t)
        If t is prime, t^2 contributes exponent 2 to factor t.
        """
        factors: Dict[int, int] = {}
        # Prime 2 has exponent 3 from 2 * 2^2
        factors[2] = 3
        for p in self.primes:
            if p != 2:
                factors[p] = 2

        if t_is_prime:
            assert is_small_prime_deterministic(t), f"Multiplier t={t} is not prime"
            if t in factors:
                factors[t] += 2
            else:
                factors[t] = 2
        else:
            t_factors = factor_small_int(t)
            for p, exp in t_factors.items():
                factors[p] = factors.get(p, 0) + 2 * exp

        return factors
