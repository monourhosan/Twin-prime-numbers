"""
Vectorized Segmented Dual-Residue Bitset Sieve (Strategy S1).
High-performance C-level NumPy slice striding for candidate forms k = 6t + 3.
Zero scalar loops over individual candidates; bounded memory footprint.
"""

from typing import List, Tuple, Optional
import numpy as np

def generate_primes(limit: int) -> np.ndarray:
    """Fast linear/NumPy prime sieve up to limit."""
    if limit < 2:
        return np.array([], dtype=np.int64)
    s = np.ones(limit + 1, dtype=bool)
    s[:2] = False
    sqrt_lim = int(limit**0.5)
    for i in range(2, sqrt_lim + 1):
        if s[i]:
            s[i * i : limit + 1 : i] = False
    return np.flatnonzero(s)

class SegmentedSieveS1:
    """
    Strategy S1: Vectorized segmented bitset sieve over candidates k = 6t + 3.
    """
    def __init__(self, n: int, sieve_depth: int = 50_000):
        self.n = n
        self.sieve_depth = sieve_depth
        all_primes = generate_primes(sieve_depth)
        # Sieve primes > 3
        self.primes = [int(p) for p in all_primes if p > 3]

        # Precompute modular residues and offsets
        # For each prime q > 3, precompute:
        # inv6 = 6^(-1) mod q
        # r_minus = inv(2^n, q) mod q -> t_minus = inv6 * (r_minus - 3) mod q
        # r_plus = (-r_minus) mod q    -> t_plus  = inv6 * (r_plus - 3) mod q
        self.sieve_params: List[Tuple[int, int, int]] = []
        for q in self.primes:
            a = pow(2, n, q)
            if a == 0:
                continue
            inv_a = pow(a, -1, q)
            r_minus = inv_a % q
            r_plus = (q - inv_a) % q
            inv6 = pow(6, -1, q)
            t_minus = (inv6 * (r_minus - 3)) % q
            t_plus = (inv6 * (r_plus - 3)) % q
            self.sieve_params.append((q, t_minus, t_plus))

    def sieve_window(self, k_start: int, k_end: int) -> List[int]:
        """
        Sieves all k in [k_start, k_end) satisfying:
        k = 6t + 3, k*2^n - 1 != 0 mod q, and k*2^n + 1 != 0 mod q for all q <= sieve_depth.
        """
        if k_start >= k_end:
            return []

        # Find bounds for t: k = 6t + 3 -> t = (k - 3) // 6
        # Smallest t such that 6t + 3 >= k_start
        t_start = max(0, (k_start - 3 + 5) // 6)
        # Largest t such that 6t + 3 < k_end
        t_end = max(t_start, (k_end - 3 + 5) // 6)

        length = t_end - t_start
        if length <= 0:
            return []

        # Bounded bitset: length bytes
        alive = np.ones(length, dtype=bool)

        # Vectorized strided marking
        for q, t_minus, t_plus in self.sieve_params:
            i_minus = (t_minus - t_start) % q
            alive[i_minus :: q] = False

            if t_plus != t_minus:
                i_plus = (t_plus - t_start) % q
                alive[i_plus :: q] = False

        # Extract surviving k values
        surviving_indices = np.flatnonzero(alive)
        survivors = []
        for idx in surviving_indices:
            k = 6 * (t_start + int(idx)) + 3
            if k_start <= k < k_end:
                survivors.append(k)

        return survivors
