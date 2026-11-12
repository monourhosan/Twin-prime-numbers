"""
Phase 4 Dual-Residue Sieving Engines: R0, R1, and R2.
- R0: Phase 3 S1 baseline (retains NumPy-strided segmented sieve on odd k).
- R1: Optimized t-space block sieve (direct k=6t+3 compact representation, 3x memory efficiency).
- R2: Proof-cost-aware adaptive hybrid sieve with dynamic depth balancing.
Includes trusted reference oracle for differential correctness testing.
"""

import time
import math
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from sympy import primerange

from .math_family import k_to_t, t_to_k, compute_t_residues_for_prime

class ReferenceSieveOracle:
    """
    Independent reference trial-division sieve oracle.
    Used exclusively in testing and validation to establish ground truth.
    """
    def __init__(self, n: int, sieve_depth: int):
        self.n = n
        self.sieve_depth = sieve_depth
        self.primes = list(primerange(5, sieve_depth + 1))

    def is_survivor(self, k: int) -> bool:
        """Returns True if neither k*2^n-1 nor k*2^n+1 has an odd prime factor <= sieve_depth."""
        if k % 2 == 0 or k % 3 != 0:
            return False
        for q in self.primes:
            r = pow(2, self.n, q)
            # check (k*2^n - 1) mod q == 0 <=> (k*r - 1) % q == 0
            if (k * r - 1) % q == 0:
                return False
            # check (k*2^n + 1) mod q == 0 <=> (k*r + 1) % q == 0
            if (k * r + 1) % q == 0:
                return False
        return True

    def sieve_window(self, k_start: int, k_end: int) -> List[int]:
        survivors = []
        for k in range(k_start, k_end):
            if k % 2 == 1 and k % 3 == 0:
                if self.is_survivor(k):
                    survivors.append(k)
        return survivors

class SieveR0_S1Baseline:
    """
    R0: Preserved Phase 3 Strategy S1 baseline.
    Segments odd k using NumPy slice striding.
    """
    def __init__(self, n: int, sieve_depth: int):
        self.n = n
        self.sieve_depth = sieve_depth
        self.primes = np.array(list(primerange(5, sieve_depth + 1)), dtype=np.int64)
        self.inv_2_n = np.zeros(len(self.primes), dtype=np.int64)
        for i, q in enumerate(self.primes):
            self.inv_2_n[i] = pow(int(pow(2, n, int(q))), -1, int(q))

    def sieve_window(self, k_start: int, k_end: int) -> List[int]:
        # Align to odd k
        if k_start % 2 == 0:
            k_start += 1
        if k_end <= k_start:
            return []

        num_odd = (k_end - k_start + 1) // 2
        alive = np.ones(num_odd, dtype=bool)

        # 3-divisibility filter (k = 6t + 3)
        rem_3 = (k_start % 6)
        if rem_3 == 1:
            first_valid = 1 # k_start + 2
        elif rem_3 == 3:
            first_valid = 0 # k_start
        else: # rem_3 == 5
            first_valid = 2 # k_start + 4

        wheel_mask = np.zeros(num_odd, dtype=bool)
        wheel_mask[first_valid::3] = True
        alive &= wheel_mask

        for i, q in enumerate(self.primes):
            inv = self.inv_2_n[i]
            # k = inv (mod q) => k*2^n - 1 divisible by q
            rem = (int(inv) - k_start) % int(q)
            if rem % 2 != 0:
                rem += int(q)
            idx_minus = rem // 2
            if idx_minus < num_odd:
                alive[idx_minus::int(q)] = False

            # k = -inv (mod q) => k*2^n + 1 divisible by q
            rem_p = (-int(inv) - k_start) % int(q)
            if rem_p % 2 != 0:
                rem_p += int(q)
            idx_plus = rem_p // 2
            if idx_plus < num_odd:
                alive[idx_plus::int(q)] = False

        survivor_indices = np.flatnonzero(alive)
        return (k_start + 2 * survivor_indices).tolist()

class SieveR1_TSpace:
    """
    R1: Optimized t-space block sieve (direct compact k = 6t + 3 representation).
    Precomputes forbidden (t_minus, t_plus) per prime, eliminating candidate mapping
    and reducing memory footprint by 3x compared to odd-k buffers.
    """
    def __init__(self, n: int, sieve_depth: int):
        self.n = n
        self.sieve_depth = sieve_depth
        primes = list(primerange(5, sieve_depth + 1))
        self.primes = np.array(primes, dtype=np.int64)
        self.t_minus_table = np.zeros(len(primes), dtype=np.int64)
        self.t_plus_table = np.zeros(len(primes), dtype=np.int64)

        for i, q in enumerate(primes):
            tm, tp = compute_t_residues_for_prime(q, n)
            self.t_minus_table[i] = tm
            self.t_plus_table[i] = tp

    def sieve_window(self, k_start: int, k_end: int) -> List[int]:
        if k_end <= k_start:
            return []

        # Find first admissible k >= k_start where k = 6t + 3
        rem = k_start % 6
        if rem <= 3:
            k0 = k_start + (3 - rem)
        else:
            k0 = k_start + (9 - rem)

        if k0 >= k_end:
            return []

        # Find last admissible k < k_end where k = 6t + 3
        rem_end = (k_end - 1) % 6
        if rem_end >= 3:
            k1 = (k_end - 1) - (rem_end - 3)
        else:
            k1 = (k_end - 1) - (rem_end + 3)

        if k1 < k0:
            return []

        t0 = k_to_t(k0)
        t1 = k_to_t(k1)
        num_t = (t1 - t0) + 1

        alive = np.ones(num_t, dtype=bool)

        for i in range(len(self.primes)):
            q = int(self.primes[i])
            tm = int(self.t_minus_table[i])
            tp = int(self.t_plus_table[i])

            # Stride for t_minus
            start_m = (tm - (t0 % q)) % q
            if start_m < num_t:
                alive[start_m::q] = False

            # Stride for t_plus
            start_p = (tp - (t0 % q)) % q
            if start_p < num_t:
                alive[start_p::q] = False

        survivor_t = np.flatnonzero(alive)
        return [t_to_k(t0 + int(idx)) for idx in survivor_t]

class SieveR2_Adaptive:
    """
    R2: Proof-Cost-Aware Adaptive Hybrid Sieve.
    Evaluates empirical survivor density after base cutoff Q0 = 10,000.
    Dynamically extends sieve depth to Q1 if and only if predicted PRP savings exceed
    additional sieve execution latency.
    """
    def __init__(self, n: int, initial_depth: int = 10_000, max_depth: int = 100_000):
        self.n = n
        self.initial_depth = initial_depth
        self.max_depth = max_depth
        self.engine_r1_base = SieveR1_TSpace(n, initial_depth)
        self.engine_r1_full = SieveR1_TSpace(n, max_depth) if max_depth > initial_depth else None

    def sieve_window(self, k_start: int, k_end: int, prp_cost_ms: float = 0.5) -> List[int]:
        # Step 1: Base pass with initial depth
        survivors = self.engine_r1_base.sieve_window(k_start, k_end)
        if not survivors or not self.engine_r1_full:
            return survivors

        window_span = k_end - k_start
        survivor_count = len(survivors)
        survivor_fraction = survivor_count / max(1, window_span // 6)

        # Cost model:
        # Time without extra sieve: survivor_count * prp_cost_ms
        # Time with extra sieve: extra_sieve_latency + (survivor_count * (1 - reduction)) * prp_cost_ms
        # Heuristic reduction from 10k to 100k sieve: ~15% further reduction
        expected_prp_savings = survivor_count * 0.15 * prp_cost_ms
        estimated_extra_sieve_time = 0.0002 * (self.max_depth - self.initial_depth) # ~18ms for 90k

        if expected_prp_savings > estimated_extra_sieve_time:
            # Profitably execute full sieve
            return self.engine_r1_full.sieve_window(k_start, k_end)
        return survivors
