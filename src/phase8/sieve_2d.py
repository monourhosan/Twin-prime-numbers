"""
Adaptive Dual-axis Exponent Sieve (ADES-8) Engine.
Implements:
- 2D segmented bitset sieve over (n, t) tiles.
- Row-to-row modular recurrence:
    a_{n+1} = a_n * 2^(-1) mod r
    eliminating logarithmic modular exponentiation on all rows after n_start.
- Exact digit boundary and k < 2^n filtering per row.
- Direct modular reference siever for 100% bitwise cross-verification.
"""

import time
from typing import List, Tuple, Optional, Dict, Any
from src.phase8.math import (
    get_small_primes,
    get_primorial_multiplier,
    solve_modular_roots,
    ades8_recurrence_step,
    ades8_roots_from_a,
    exact_digit_t_bounds
)


class ADES8TwoDimSieve:
    """
    Two-dimensional segmented sieve across adjacent exponents n and t-space.
    """
    def __init__(self, R: int = 13, sieve_limit: int = 100000):
        self.R = R
        self.M = get_primorial_multiplier(R)
        self.sieve_limit = sieve_limit

        # Sieve primes: all odd primes <= sieve_limit coprime to M
        all_primes = get_small_primes(sieve_limit)
        self.sieve_primes = [p for p in all_primes if p > 2 and self.M % p != 0]

        # Precompute modular inverse of 2 mod r for each sieve prime
        self.inv2_table = [pow(2, -1, p) for p in self.sieve_primes]
        self.num_primes = len(self.sieve_primes)

    def sieve_tile_recurrence(
        self,
        n_start: int,
        n_height: int,
        t_start: int,
        t_width: int,
        digit_band: Optional[int] = None
    ) -> Tuple[List[Tuple[int, int]], Dict[str, float]]:
        """
        Variant C (Optimized ADES-8):
        Sieves an (n_height x t_width) tile using modular root recurrence.
        Returns list of surviving (n, t) tuples and timing breakdown.
        """
        t0 = time.perf_counter()
        survivors: List[Tuple[int, int]] = []

        # 1. Initialize a_n at n_start for all primes
        # a_n = (M * 2^n_start)^(-1) mod p
        a_current = [
            pow((self.M * pow(2, n_start, p)) % p, -1, p)
            for p in self.sieve_primes
        ]
        t_init = time.perf_counter()

        time_marking = 0.0

        for row_idx in range(n_height):
            n = n_start + row_idx

            # Exact digit filtering bounds for this row
            if digit_band is not None:
                _, _, t_min, t_max = exact_digit_t_bounds(digit_band, self.M, n)
                if t_min > t_max or t_start > t_max or (t_start + t_width - 1) < t_min:
                    # Update recurrence for next row and skip sieving this row
                    for i in range(self.num_primes):
                        a_current[i] = (a_current[i] * self.inv2_table[i]) % self.sieve_primes[i]
                    continue
            else:
                t_min = 0
                t_max = 1 << 62

            t_mark_start = time.perf_counter()
            # Allocate local bytearray sieve: 0 = survivor, 1 = composite
            sieve = bytearray(t_width)

            primes = self.sieve_primes
            inv2s = self.inv2_table

            for i in range(self.num_primes):
                p = primes[i]
                b = inv2s[i]
                a_val = a_current[i]

                # Modular roots for this row
                # t_minus = ((a_val - 1) * b) % p
                # t_plus  = ((-a_val - 1) * b) % p
                t_minus = ((a_val - 1) * b) % p
                t_plus = ((-a_val - 1) * b) % p

                # Local offsets
                idx_minus = (t_minus - t_start) % p
                idx_plus = (t_plus - t_start) % p

                # Mark multiples
                for pos in range(idx_minus, t_width, p):
                    sieve[pos] = 1
                for pos in range(idx_plus, t_width, p):
                    sieve[pos] = 1

                # Advance recurrence for next row
                a_current[i] = (a_val * b) % p

            time_marking += (time.perf_counter() - t_mark_start)

            # Collect survivors within valid digit bounds
            row_t_min = max(t_start, t_min)
            row_t_max = min(t_start + t_width - 1, t_max)
            start_local = row_t_min - t_start
            end_local = row_t_max - t_start

            for local_idx in range(start_local, end_local + 1):
                if sieve[local_idx] == 0:
                    survivors.append((n, t_start + local_idx))

        total_time = time.perf_counter() - t0
        metrics = {
            "total_time_sec": total_time,
            "setup_time_sec": t_init - t0,
            "marking_time_sec": time_marking,
            "num_survivors": len(survivors)
        }
        return survivors, metrics

    def sieve_tile_reference_2d(
        self,
        n_start: int,
        n_height: int,
        t_start: int,
        t_width: int,
        digit_band: Optional[int] = None
    ) -> Tuple[List[Tuple[int, int]], Dict[str, float]]:
        """
        Variant B (CPU Reference 2D):
        Recomputes modular roots on every row independently without recurrence.
        """
        t0 = time.perf_counter()
        survivors: List[Tuple[int, int]] = []
        time_marking = 0.0

        for row_idx in range(n_height):
            n = n_start + row_idx

            if digit_band is not None:
                _, _, t_min, t_max = exact_digit_t_bounds(digit_band, self.M, n)
                if t_min > t_max or t_start > t_max or (t_start + t_width - 1) < t_min:
                    continue
            else:
                t_min = 0
                t_max = 1 << 62

            t_mark_start = time.perf_counter()
            sieve = bytearray(t_width)

            primes = self.sieve_primes
            for p in primes:
                t_minus, t_plus = solve_modular_roots(self.M, n, p)

                idx_minus = (t_minus - t_start) % p
                idx_plus = (t_plus - t_start) % p

                for pos in range(idx_minus, t_width, p):
                    sieve[pos] = 1
                for pos in range(idx_plus, t_width, p):
                    sieve[pos] = 1

            time_marking += (time.perf_counter() - t_mark_start)

            row_t_min = max(t_start, t_min)
            row_t_max = min(t_start + t_width - 1, t_max)
            start_local = row_t_min - t_start
            end_local = row_t_max - t_start

            for local_idx in range(start_local, end_local + 1):
                if sieve[local_idx] == 0:
                    survivors.append((n, t_start + local_idx))

        total_time = time.perf_counter() - t0
        metrics = {
            "total_time_sec": total_time,
            "marking_time_sec": time_marking,
            "num_survivors": len(survivors)
        }
        return survivors, metrics

    def sieve_row_baseline_1d(
        self,
        n: int,
        t_start: int,
        t_width: int,
        digit_band: Optional[int] = None
    ) -> Tuple[List[int], Dict[str, float]]:
        """
        Variant A (HDC-7 1D Baseline):
        Fixed-exponent 1D segmented sieve.
        """
        t0 = time.perf_counter()
        survivors_t: List[int] = []

        if digit_band is not None:
            _, _, t_min, t_max = exact_digit_t_bounds(digit_band, self.M, n)
            if t_min > t_max or t_start > t_max or (t_start + t_width - 1) < t_min:
                return [], {"total_time_sec": time.perf_counter() - t0, "num_survivors": 0}
        else:
            t_min = 0
            t_max = 1 << 62

        sieve = bytearray(t_width)
        for p in self.sieve_primes:
            t_minus, t_plus = solve_modular_roots(self.M, n, p)
            idx_minus = (t_minus - t_start) % p
            idx_plus = (t_plus - t_start) % p

            for pos in range(idx_minus, t_width, p):
                sieve[pos] = 1
            for pos in range(idx_plus, t_width, p):
                sieve[pos] = 1

        row_t_min = max(t_start, t_min)
        row_t_max = min(t_start + t_width - 1, t_max)
        start_local = row_t_min - t_start
        end_local = row_t_max - t_start

        for local_idx in range(start_local, end_local + 1):
            if sieve[local_idx] == 0:
                survivors_t.append(t_start + local_idx)

        total_time = time.perf_counter() - t0
        return survivors_t, {"total_time_sec": total_time, "num_survivors": len(survivors_t)}
