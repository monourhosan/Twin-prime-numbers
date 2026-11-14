"""
High-Performance Segmented Sieve in Compact t-Space for HDC-7.
Leverages primorial exclusion and dual modular root marking.
"""

import time
from typing import List, Tuple, Dict, Any, Generator
from src.phase7.math import get_small_primes, solve_modular_roots


class CompactTSieve:
    """
    Segmented bitset sieve operating exclusively in compact index space t.
    Each candidate center is C = M_B * (2t + 1) * 2^n.
    """
    def __init__(self, MB: int, n: int, sieve_depth: int = 50000):
        self.MB = MB
        self.n = n
        self.sieve_depth = sieve_depth
        self._init_sieve_primes()

    def _init_sieve_primes(self) -> None:
        """Precomputes primes up to sieve_depth excluding divisors of 2*MB."""
        all_primes = get_small_primes(self.sieve_depth)
        # Exclude primes dividing 2 * MB (they have no forbidden roots and divide neither member)
        self.sieve_primes = [p for p in all_primes if (self.MB % p != 0 and p != 2)]

        # Precompute modular roots (t_plus, t_minus) for each prime
        self.roots: List[Tuple[int, int, int]] = []
        for r in self.sieve_primes:
            t_plus, t_minus = solve_modular_roots(self.MB, self.n, r)
            self.roots.append((r, t_plus, t_minus))

    def sieve_segment(self, t_start: int, t_end: int) -> Tuple[List[int], Dict[str, Any]]:
        """
        Sieves the half-open interval [t_start, t_end).
        Returns list of survivor t indices and sieve performance telemetry.
        """
        span = t_end - t_start
        if span <= 0:
            return [], {"span": 0, "survivors": 0, "survival_rate": 0.0, "time_sec": 0.0}

        t0 = time.perf_counter()
        # bytearray initialized to 1 (True = alive)
        # 0 = marked composite by sieve prime
        alive = bytearray([1]) * span

        for r, t_plus, t_minus in self.roots:
            # Mark t_plus: t = t_plus + m * r
            # Find first t >= t_start with t = t_plus mod r
            first_plus = t_start + ((t_plus - (t_start % r)) % r)
            offset_plus = first_plus - t_start
            alive[offset_plus:span:r] = b"\x00" * len(range(offset_plus, span, r))

            # Mark t_minus: t = t_minus + m * r
            first_minus = t_start + ((t_minus - (t_start % r)) % r)
            offset_minus = first_minus - t_start
            alive[offset_minus:span:r] = b"\x00" * len(range(offset_minus, span, r))

        # Collect surviving indices
        survivors = [t_start + i for i, is_alive in enumerate(alive) if is_alive]
        elapsed = time.perf_counter() - t0

        telemetry = {
            "span": span,
            "survivors": len(survivors),
            "survival_rate": len(survivors) / span if span > 0 else 0.0,
            "primes_count": len(self.roots),
            "sieve_depth": self.sieve_depth,
            "time_sec": elapsed,
            "rate_centers_per_sec": span / elapsed if elapsed > 0 else 0.0
        }
        return survivors, telemetry
