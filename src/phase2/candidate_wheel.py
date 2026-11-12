"""
CRT Wheel module for preselecting admissible k residues for k * 2^n +/- 1.
"""

from typing import List, Set, Tuple
import math

class CandidateWheel:
    """
    Precomputes admissible residue classes for odd k modulo M = 2 * prod(wheel_primes).
    Ensures that for all primes q in wheel_primes, neither k*2^n - 1 nor k*2^n + 1
    is divisible by q.
    """

    def __init__(self, n: int, wheel_primes: List[int] = None):
        self.n = n
        if wheel_primes is None:
            wheel_primes = [3, 5, 7, 11, 13]
        self.wheel_primes = sorted(wheel_primes)

        # Modulus M = 2 * prod(wheel_primes)
        self.modulus = 2
        for p in self.wheel_primes:
            self.modulus *= p

        self.forbidden_per_prime = {}
        for q in self.wheel_primes:
            a = pow(2, n, q)
            inv_a = pow(a, -1, q)
            u1 = inv_a % q
            u2 = (q - inv_a) % q
            self.forbidden_per_prime[q] = {u1, u2}

        # Build allowed residues in [1, modulus) with k odd
        allowed = []
        for k in range(1, self.modulus, 2):
            # Necessary condition modulo 3: k must be divisible by 3
            if 3 in self.wheel_primes and (k % 3 != 0):
                continue
            admissible = True
            for q in self.wheel_primes:
                if q == 3:
                    continue
                if (k % q) in self.forbidden_per_prime[q]:
                    admissible = False
                    break
            if admissible:
                allowed.append(k)

        self.allowed_residues = sorted(allowed)
        self.survival_fraction = len(self.allowed_residues) / (self.modulus / 2.0)

    def is_admissible(self, k: int) -> bool:
        """Returns True if k satisfies all wheel congruences."""
        if k % 2 == 0:
            return False
        r = k % self.modulus
        # Binary search in sorted allowed residues
        import bisect
        idx = bisect.bisect_left(self.allowed_residues, r)
        return idx < len(self.allowed_residues) and self.allowed_residues[idx] == r

    def enumerate_window(self, k_start: int, k_end: int) -> List[int]:
        """
        Yields all k in [k_start, k_end) satisfying the wheel admissibility condition.
        """
        if k_start >= k_end:
            return []

        # Find base block
        candidates = []
        start_block = (k_start // self.modulus) * self.modulus
        end_block = ((k_end + self.modulus - 1) // self.modulus) * self.modulus

        for block in range(start_block, end_block + 1, self.modulus):
            for res in self.allowed_residues:
                k = block + res
                if k_start <= k < k_end:
                    candidates.append(k)
                elif k >= k_end:
                    break
        return candidates

CRTWheel = CandidateWheel

