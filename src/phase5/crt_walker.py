"""
Phase 5 Method S1: Certificate-First Smooth-Center CRT-Class Walker and Modular Sieve.
Implements:
1. Small prime sieve of Eratosthenes.
2. Exact forbidden residue calculations: t != +/- F^{-1} (mod q) for primes q coprime to F.
3. Precomputed admissible CRT wheel classes over a bounded modulus W.
4. Segmented incremental modular filter (mark-disallowed-bits).
5. Enumerate-only-admissible-classes generator.
"""

import math
from typing import List, Tuple, Dict, Generator, Optional
from .candidates import SmoothCenterFamily

def generate_primes_up_to(limit: int) -> List[int]:
    """Generates all primes up to limit using the Sieve of Eratosthenes."""
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    p = 2
    while p * p <= limit:
        if sieve[p]:
            sieve[p * p : limit + 1 : p] = bytearray((limit - p * p) // p + 1)
        p += 1
    return [i for i, is_prime in enumerate(sieve) if is_prime]

class ForbiddenResidues:
    """Computes and stores forbidden residue classes modulo small odd primes q coprime to F."""
    def __init__(self, family: SmoothCenterFamily, primes: List[int]):
        self.family: SmoothCenterFamily = family
        self.forbidden: Dict[int, Tuple[int, int]] = {}
        F = family.F
        for q in primes:
            if q % 2 == 0 or q in family.prime_factors:
                continue
            # w = F^{-1} mod q
            inv = pow(F % q, -1, q)
            neg_inv = (q - inv) % q
            self.forbidden[q] = (inv, neg_inv)

    def is_admissible(self, t: int, q: int) -> bool:
        """Returns True iff t is admissible modulo prime q."""
        if q not in self.forbidden:
            return True
        r = t % q
        inv, neg_inv = self.forbidden[q]
        return r != inv and r != neg_inv

class CRTWheel:
    """
    Constructs an admissible CRT residue class wheel over a set of small primes coprime to F.
    Wheel modulus W = prod(q_i).
    Admissible classes R_adm = {r in [0, W-1] : r != +/- F^{-1} mod q_i for all q_i}.
    """
    def __init__(self, family: SmoothCenterFamily, wheel_primes: List[int]):
        self.family: SmoothCenterFamily = family
        self.primes: List[int] = [q for q in wheel_primes if q > 2 and q not in family.prime_factors]
        self.forbidden_calc = ForbiddenResidues(family, self.primes)
        
        # Compute modulus W
        self.W: int = 1
        for q in self.primes:
            self.W *= q
            
        # Enumerate admissible residues in [0, W - 1]
        self.admissible_residues: List[int] = []
        for r in range(self.W):
            ok = True
            for q in self.primes:
                if not self.forbidden_calc.is_admissible(r, q):
                    ok = False
                    break
            if ok:
                self.admissible_residues.append(r)
                
        self.num_admissible = len(self.admissible_residues)
        self.survival_ratio = self.num_admissible / self.W if self.W > 0 else 1.0

    def walk_classes(self, t_start: int, t_end: int) -> Generator[int, None, None]:
        """
        Method S1 variant: Enumerate-only-admissible-classes generator.
        Steps through wheel blocks, yielding t in [t_start, t_end) that match admissible residues.
        """
        if self.W <= 0 or not self.admissible_residues:
            for t in range(t_start, t_end):
                yield t
            return

        first_block = t_start // self.W
        last_block = t_end // self.W
        
        for block in range(first_block, last_block + 1):
            base = block * self.W
            for r in self.admissible_residues:
                t = base + r
                if t_start <= t < t_end:
                    yield t

class SegmentedSCCAFilter:
    """
    Method S1 segmented modular sieve:
    Given [t_start, t_end) and primes coprime to F up to sieve_limit,
    crosses off forbidden residues in a high-speed bit/bytearray mask.
    """
    def __init__(self, family: SmoothCenterFamily, sieve_limit: int):
        self.family: SmoothCenterFamily = family
        self.sieve_limit: int = sieve_limit
        primes = generate_primes_up_to(sieve_limit)
        self.sieve_primes: List[int] = [q for q in primes if q > 2 and q not in family.prime_factors]
        self.forbidden = ForbiddenResidues(family, self.sieve_primes)

    def sieve_segment(self, t_start: int, t_end: int) -> List[int]:
        """
        Sieves the interval [t_start, t_end) and returns all surviving t values.
        """
        if t_end <= t_start:
            return []
        
        length = t_end - t_start
        # 1 = surviving / admissible, 0 = eliminated
        mask = bytearray([1]) * length
        
        for q in self.sieve_primes:
            inv, neg_inv = self.forbidden.forbidden[q]
            
            # Eliminate t == inv (mod q)
            # Find first t >= t_start with t % q == inv
            rem = t_start % q
            offset = (inv - rem) % q
            if offset < length:
                mask[offset : length : q] = bytearray((length - offset - 1) // q + 1)
                
            # Eliminate t == neg_inv (mod q)
            offset = (neg_inv - rem) % q
            if offset < length:
                mask[offset : length : q] = bytearray((length - offset - 1) // q + 1)
                
        # Collect survivors
        survivors = [t_start + i for i, is_alive in enumerate(mask) if is_alive and (t_start + i) > 0]
        return survivors
