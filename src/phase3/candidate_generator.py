"""
Candidate Multiplier Generator and Mathematical CRT Wheel (Phase 3).
Generates admissible k values in [k_start, k_end) satisfying:
1. k is positive and odd (k = 6t + 3);
2. CRT Wheel prefilter (primes 3, 5, 7, 11, 13, modulus 30,030);
3. Exactly 1,485 odd residues survive modulo 30,030 (9.890%).
"""

import bisect
from typing import List, Set, Generator

WHEEL_PRIMES = [3, 5, 7, 11, 13]
WHEEL_MODULUS = 30030 # 2 * 3 * 5 * 7 * 11 * 13

class Phase3Wheel:
    def __init__(self, n: int):
        self.n = n
        self.modulus = WHEEL_MODULUS
        self.wheel_primes = WHEEL_PRIMES

        # Forbidden classes per odd wheel prime
        # a = 2^n mod q, inv_a = a^(-1) mod q
        # k = inv_a mod q makes A divisible by q
        # k = -inv_a mod q makes B divisible by q
        forbidden_per_prime = {}
        for q in [5, 7, 11, 13]:
            a = pow(2, n, q)
            inv_a = pow(a, -1, q)
            forbidden_per_prime[q] = {inv_a % q, (q - inv_a) % q}

        # Sift odd residues modulo 30030
        survivors = []
        for k in range(3, self.modulus, 6): # Enforces k = 6t + 3 (k odd and divisible by 3)
            admissible = True
            for q in [5, 7, 11, 13]:
                if (k % q) in forbidden_per_prime[q]:
                    admissible = False
                    break
            if admissible:
                survivors.append(k)

        self.allowed_residues = sorted(survivors)
        assert len(self.allowed_residues) == 1485, f"Expected 1485 residues, got {len(self.allowed_residues)}"
        self.survival_fraction = len(self.allowed_residues) / 15015.0

    def is_admissible(self, k: int) -> bool:
        if k % 2 == 0 or k % 3 != 0:
            return False
        r = k % self.modulus
        idx = bisect.bisect_left(self.allowed_residues, r)
        return idx < len(self.allowed_residues) and self.allowed_residues[idx] == r

    def enumerate_window(self, k_start: int, k_end: int) -> List[int]:
        """Enumerates all wheel survivors in [k_start, k_end)."""
        if k_start >= k_end:
            return []
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
