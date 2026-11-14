"""
Phase 6: Search Family Definitions (Method Q and Method R).
Defines candidate representations, polynomial evaluations, factor tracking,
and deterministic anchor generation.
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Any
import gmpy2


def is_prime_deterministic_u64(n: int) -> bool:
    """
    Deterministic primality test for 64-bit integers n < 2^64
    using Jim Sinclair / Jaeschke proven deterministic Miller-Rabin bases.
    Also validated by trial division for smaller integers.
    """
    if n < 2:
        return False
    if n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    if n < 10000:
        d = 5
        while d * d <= n:
            if n % d == 0 or n % (d + 2) == 0:
                return False
            d += 6
        return True

    # Proven 7-base set for n < 2^64: 2, 325, 9375, 28178, 450775, 9780504, 1795265022
    bases = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        composite = True
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                composite = False
                break
        if composite:
            return False
    return True


def trial_factor_small_int(n: int) -> Dict[int, int]:
    """
    Complete factorization of positive integer n by trial division.
    Suitable for 16-32 bit values of t.
    """
    factors: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        if n % d == 0:
            cnt = 0
            while n % d == 0:
                cnt += 1
                n //= d
            factors[d] = cnt
        d = 3 if d == 2 else d + 2
    if n > 1:
        factors[n] = 1
    return factors


class MethodQFamily:
    """
    Method Q (QCP-6) candidate family:
    x = S * t
    h = 3 (or positive odd multiple of 3)
    C = x * (x - h)
    A = x^2 - h*x - 1
    B = x^2 - h*x + 1
    """

    def __init__(
        self,
        S_factors: Dict[int, int],
        h: int = 3,
        seed: Optional[int] = None
    ):
        if h < 3 or h % 2 == 0 or h % 3 != 0:
            raise ValueError(f"h must be an odd positive multiple of 3, got {h}")
        if 3 not in S_factors or S_factors[3] < 1:
            raise ValueError("S must be divisible by 3")
        if 2 in S_factors:
            raise ValueError("S must be odd (no factor 2 allowed)")

        self.h = h
        self.S_factors = dict(S_factors)
        self.seed = seed

        # Compute exact integer S
        S_val = 1
        for p, exp in self.S_factors.items():
            if not is_prime_deterministic_u64(p):
                raise ValueError(f"Factor {p} in S is not prime")
            S_val *= (p ** exp)
        self.S = S_val

    @classmethod
    def generate_fresh(
        cls,
        target_pair_digits: int,
        seed: int,
        h: int = 3,
        t_bits: int = 20
    ) -> "MethodQFamily":
        """
        Deterministically generates a fresh anchor S such that candidates A, B
        lie precisely within target_pair_digits when t ~ 2^t_bits.
        """
        rng = random.Random(seed)
        # Digits of x ~ target_pair_digits / 2
        target_x_digits = target_pair_digits // 2
        # Target digits of S ~ target_x_digits - digits(t)
        t_digits = int(t_bits * 0.30103) + 1
        target_S_digits = max(6, target_x_digits - t_digits)

        # Build S starting with 3
        factors: Dict[int, int] = {3: 1}
        cur_S = 3

        # Add distinct primes of ~7-8 digits (well within 64-bit deterministic trial division)
        prime_candidate = 10000000 + rng.randint(100, 100000)
        while len(str(cur_S)) < target_S_digits:
            while not is_prime_deterministic_u64(prime_candidate) or prime_candidate == 3:
                prime_candidate += 2
            factors[prime_candidate] = 1
            cur_S *= prime_candidate
            prime_candidate += rng.randint(1000, 50000)
            if prime_candidate % 2 == 0:
                prime_candidate += 1

        return cls(S_factors=factors, h=h, seed=seed)

    def evaluate(self, t: int) -> Tuple[int, int, int]:
        """
        Evaluates candidate center C and members (A, B) for odd integer t.
        Returns (A, B, C).
        """
        if t <= 0 or t % 2 == 0:
            raise ValueError(f"t must be odd and positive, got {t}")
        x = self.S * t
        if x <= self.h + 2:
            raise ValueError(f"x must exceed h + 2 ({self.h + 2}), got {x}")

        C = x * (x - self.h)
        A = x * x - self.h * x - 1
        B = x * x - self.h * x + 1
        return A, B, C

    def factor_proof_factor(self, t: int) -> Dict[int, int]:
        """
        Returns full prime factorization of proof factor F = x = S * t
        by combining S_factors with trial factorization of t.
        """
        t_factors = trial_factor_small_int(t)
        merged = dict(self.S_factors)
        for p, exp in t_factors.items():
            merged[p] = merged.get(p, 0) + exp

        # Assert product equals x
        x = self.S * t
        prod = 1
        for p, exp in merged.items():
            prod *= (p ** exp)
        if prod != x:
            raise RuntimeError(f"Factorization product {prod} != x {x}")
        return merged


class MethodRFamily:
    """
    Method R (General Integer Windows):
    C = C_0 + 6*j
    A = C - 1
    B = C + 1
    """

    def __init__(self, C0: int, seed: Optional[int] = None):
        if C0 % 6 != 0:
            raise ValueError(f"C0 must be divisible by 6, got {C0}")
        self.C0 = C0
        self.seed = seed

    @classmethod
    def generate_fresh(cls, target_digits: int, seed: int) -> "MethodRFamily":
        rng = random.Random(seed)
        # Generate random base of target_digits
        lower_bound = 10 ** (target_digits - 1)
        upper_bound = 10 ** target_digits - 1
        raw_val = rng.randint(lower_bound, upper_bound)
        # Align to multiple of 6
        C0 = raw_val - (raw_val % 6)
        if C0 < lower_bound:
            C0 += 6
        return cls(C0=C0, seed=seed)

    def evaluate(self, j: int) -> Tuple[int, int, int]:
        C = self.C0 + 6 * j
        return C - 1, C + 1, C
