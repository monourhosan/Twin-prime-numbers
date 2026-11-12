"""
Dual-Residue Sieve module for CATS.
Provides high-performance NumPy-accelerated bitsets for bounded and structured twin searches.
"""

from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from .primality import generate_primes, mod_inverse

class SieveStats:
    def __init__(self, total_candidates: int, survivors: int):
        self.total_candidates = total_candidates
        self.survivors = survivors
        self.eliminated = total_candidates - survivors
        self.survival_rate = survivors / max(1, total_candidates)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_candidates": self.total_candidates,
            "survivors": self.survivors,
            "eliminated": self.eliminated,
            "survival_rate": self.survival_rate,
        }

class BoundedTwinSieve:
    def __init__(self, min_val: int, max_val: int, sieve_depth: Optional[int] = None, use_dual_sieve: bool = True):
        self.min_val = max(2, min_val)
        self.max_val = max_val
        self.use_dual_sieve = use_dual_sieve
        sqrt_max = int(max_val**0.5)
        self.sieve_depth = min(sieve_depth, sqrt_max) if sieve_depth else sqrt_max

    def run_sieve(self) -> Tuple[List[Tuple[int, int]], SieveStats]:
        candidates = []
        # Special initial pair (3, 5)
        if self.min_val <= 3 and self.max_val >= 5:
            candidates.append((3, 5))

        # Centers m = 6r with 6r - 1 >= min_val and 6r + 1 <= max_val
        r_start = 1 if self.min_val <= 5 else (self.min_val + 5) // 6
        r_end = 0 if self.max_val < 7 else (self.max_val - 1) // 6

        if r_start > r_end:
            return candidates, SieveStats(len(candidates), len(candidates))

        num_r = r_end - r_start + 1
        alive = np.ones(num_r, dtype=bool)

        primes = generate_primes(self.sieve_depth)

        for q in primes:
            if q < 5:
                continue

            # 6r = +/- 1 mod q => r = +/- 6^(-1) mod q
            inv6 = pow(6, -1, int(q))
            u1 = inv6 % q
            u2 = (q - u1) % q

            residues = [u1, u2] if self.use_dual_sieve else [u1, u2]
            for u in residues:
                first_r = r_start + ((u - r_start) % q)
                start_idx = first_r - r_start
                if start_idx < num_r:
                    alive[start_idx::q] = False

            # Exception handling: if 6r - 1 == q or 6r + 1 == q, candidate equals sieve prime
            # For 6r - 1 = q => r = (q + 1) / 6
            if (q + 1) % 6 == 0:
                r_prime = (q + 1) // 6
                if r_start <= r_prime <= r_end:
                    alive[r_prime - r_start] = True
            if (q - 1) % 6 == 0:
                r_prime = (q - 1) // 6
                if r_start <= r_prime <= r_end:
                    alive[r_prime - r_start] = True

        surviving_indices = np.flatnonzero(alive)
        for idx in surviving_indices:
            r = r_start + int(idx)
            candidates.append((6 * r - 1, 6 * r + 1))

        stats = SieveStats(num_r + (1 if (self.min_val <= 3 and self.max_val >= 5) else 0), len(candidates))
        return candidates, stats

class StructuredTwinSieve:
    def __init__(self, n: int, k_min: int, k_max: int, sieve_depth: int, use_dual_sieve: bool = True):
        self.n = n
        self.k_min = k_min if k_min % 2 == 1 else k_min + 1
        self.k_max = k_max if k_max % 2 == 1 else k_max - 1
        self.sieve_depth = sieve_depth
        self.use_dual_sieve = use_dual_sieve

    def run_sieve(self) -> Tuple[List[int], SieveStats]:
        if self.k_min > self.k_max:
            return [], SieveStats(0, 0)

        num_odd_k = (self.k_max - self.k_min) // 2 + 1
        alive = np.ones(num_odd_k, dtype=bool)

        primes = generate_primes(self.sieve_depth)

        for q in primes:
            if q == 2:
                continue

            q_int = int(q)
            # a = 2^n mod q
            a = pow(2, self.n, q_int)
            if a == 0:
                continue

            # Modular inverse
            inv_a = pow(a, -1, q_int)
            u1 = inv_a % q_int
            u2 = (q_int - u1) % q_int

            # Index i in alive represents k = k_min + 2*i
            # 2*i = (u - k_min) mod q => i = 2^(-1) * (u - k_min) mod q
            inv2 = (q_int + 1) // 2

            two_pow_n = 1 << self.n
            if self.use_dual_sieve:
                # Combined dual elimination
                for u in (u1, u2):
                    start_i = (((u - self.k_min) % q_int) * inv2) % q_int
                    if start_i < num_odd_k:
                        alive[start_i::q_int] = False
            else:
                # Baseline: single residue sequential passes
                start_i1 = (((u1 - self.k_min) % q_int) * inv2) % q_int
                if start_i1 < num_odd_k:
                    alive[start_i1::q_int] = False
                start_i2 = (((u2 - self.k_min) % q_int) * inv2) % q_int
                if start_i2 < num_odd_k:
                    alive[start_i2::q_int] = False

            # Exception: candidate equals the sieve prime itself
            if (q_int + 1) % two_pow_n == 0:
                k_prime = (q_int + 1) // two_pow_n
                if self.k_min <= k_prime <= self.k_max and k_prime % 2 == 1:
                    alive[(k_prime - self.k_min) // 2] = True
            if (q_int - 1) % two_pow_n == 0:
                k_prime = (q_int - 1) // two_pow_n
                if self.k_min <= k_prime <= self.k_max and k_prime % 2 == 1:
                    alive[(k_prime - self.k_min) // 2] = True

        surviving_indices = np.flatnonzero(alive)
        survivors = [self.k_min + 2 * int(idx) for idx in surviving_indices]
        stats = SieveStats(num_odd_k, len(survivors))
        return survivors, stats
