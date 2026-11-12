"""
Streaming Window Sieve combining CRT wheel prefiltering, modular elimination,
and bounded-memory candidate streaming.
"""

from typing import List, Tuple, Dict, Any, Generator
import numpy as np

from .candidate_wheel import CandidateWheel

def generate_primes_sieve(limit: int) -> np.ndarray:
    """Generates primes <= limit using a fast NumPy sieve."""
    if limit < 2:
        return np.array([], dtype=np.int64)
    s = np.ones(limit + 1, dtype=bool)
    s[:2] = False
    sqrt_lim = int(limit**0.5)
    for i in range(2, sqrt_lim + 1):
        if s[i]:
            s[i * i : limit + 1 : i] = False
    return np.flatnonzero(s)

class WindowSieve:
    """
    Sieves candidate values of k in windows [k_start, k_end) using:
    1. Precomputed CandidateWheel (eliminating primes in wheel_primes);
    2. Dual residue elimination for primes q with max(wheel_primes) < q <= sieve_depth.
    """

    def __init__(self, n: int, sieve_depth: int = 50_000, wheel_primes: List[int] = None):
        self.n = n
        self.sieve_depth = sieve_depth
        if wheel_primes is None:
            wheel_primes = [3, 5, 7, 11, 13]
        self.wheel = CandidateWheel(n, wheel_primes)
        self.max_wheel_p = max(self.wheel.wheel_primes)

        # Precompute primes between max_wheel_p and sieve_depth
        all_primes = generate_primes_sieve(self.sieve_depth)
        self.sieve_primes = [int(q) for q in all_primes if q > self.max_wheel_p]

        # Precompute modular inverses (2^n)^(-1) mod q for sieve primes
        self.sieve_forbidden = []
        for q in self.sieve_primes:
            a = pow(2, n, q)
            if a != 0:
                inv_a = pow(a, -1, q)
                self.sieve_forbidden.append((q, inv_a % q, (q - inv_a) % q))

    def sieve_window(self, k_start: int, k_end: int) -> List[int]:
        """
        Sieves the window [k_start, k_end) and returns all surviving k values.
        """
        # Step 1: Pre-filter using CRT wheel
        wheel_candidates = self.wheel.enumerate_window(k_start, k_end)
        if not wheel_candidates:
            return []

        # If window is small or few candidates survive, filter by direct residue check
        # For larger survivor sets, map to a local boolean array
        survivors = []
        two_pow_n = 1 << self.n

        for k in wheel_candidates:
            # Check against sieve primes
            cand_minus = k * two_pow_n - 1
            cand_plus = k * two_pow_n + 1

            eliminated = False
            for q, u1, u2 in self.sieve_forbidden:
                k_mod_q = k % q
                if k_mod_q == u1:
                    # Divisible by q; check exception cand_minus == q
                    if cand_minus > q:
                        eliminated = True
                        break
                elif k_mod_q == u2:
                    if cand_plus > q:
                        eliminated = True
                        break

            if not eliminated:
                survivors.append(k)

        return survivors
