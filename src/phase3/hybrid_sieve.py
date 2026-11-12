"""
Hybrid Dual-Residue Streaming Sieve (Strategy S2 - HDRSS).
Combines:
1. Vectorized bitset striding for small primes (q <= stride_cutoff);
2. Direct sparse modular filtering for large primes (stride_cutoff < q <= sieve_depth);
Minimizes cache line misses and avoids redundant memory traversals.
"""

from typing import List, Tuple
import numpy as np

from .segmented_sieve import generate_primes

class HybridSieveS2:
    """
    Strategy S2: Hybrid strided bitset marking for small primes + sparse modular check for large primes.
    """
    def __init__(self, n: int, sieve_depth: int = 50_000, stride_cutoff: int = 10_000):
        self.n = n
        self.sieve_depth = sieve_depth
        self.stride_cutoff = min(stride_cutoff, sieve_depth)

        all_primes = generate_primes(sieve_depth)
        primes_gt3 = [int(p) for p in all_primes if p > 3]

        # Partition primes into small (strided) and large (sparse check)
        self.strided_params: List[Tuple[int, int, int]] = []
        self.sparse_params: List[Tuple[int, int, int]] = []

        for q in primes_gt3:
            a = pow(2, n, q)
            if a == 0:
                continue
            inv_a = pow(a, -1, q)
            r_minus = inv_a % q
            r_plus = (q - inv_a) % q

            if q <= self.stride_cutoff:
                inv6 = pow(6, -1, q)
                t_minus = (inv6 * (r_minus - 3)) % q
                t_plus = (inv6 * (r_plus - 3)) % q
                self.strided_params.append((q, t_minus, t_plus))
            else:
                self.sparse_params.append((q, r_minus, r_plus))

    def sieve_window(self, k_start: int, k_end: int) -> List[int]:
        if k_start >= k_end:
            return []

        t_start = max(0, (k_start - 3 + 5) // 6)
        t_end = max(t_start, (k_end - 3 + 5) // 6)

        length = t_end - t_start
        if length <= 0:
            return []

        # Stage 1: Vectorized bitset striding for q <= stride_cutoff
        alive = np.ones(length, dtype=bool)
        for q, t_minus, t_plus in self.strided_params:
            i_minus = (t_minus - t_start) % q
            alive[i_minus :: q] = False

            if t_plus != t_minus:
                i_plus = (t_plus - t_start) % q
                alive[i_plus :: q] = False

        surviving_indices = np.flatnonzero(alive)
        if len(surviving_indices) == 0:
            return []

        # Extract intermediate candidate k values
        candidates = []
        for idx in surviving_indices:
            k = 6 * (t_start + int(idx)) + 3
            if k_start <= k < k_end:
                candidates.append(k)

        # Stage 2: Sparse modular check for stride_cutoff < q <= sieve_depth
        if not self.sparse_params or not candidates:
            return candidates

        survivors = []
        for k in candidates:
            passed = True
            for q, r_minus, r_plus in self.sparse_params:
                k_mod = k % q
                if k_mod == r_minus or k_mod == r_plus:
                    passed = False
                    break
            if passed:
                survivors.append(k)

        return survivors
