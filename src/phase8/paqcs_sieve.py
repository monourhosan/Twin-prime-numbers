"""
PAQCS Segmented Modular Sieve Engine (Phase 8).
Executes segmented sieving over odd multiplier t in [t_start, t_end]
using modular root elimination up to sieve bound Q.
"""

import math
import time
from typing import List, Tuple, Dict, Any, Generator
import gmpy2
import numpy as np

from .paqcs_math import get_forbidden_t_residues


class SievePrimePlan:
    """
    Stores precomputed forbidden roots for a sieve prime q.
    """
    __slots__ = ('q', 'roots')

    def __init__(self, q: int, roots: List[int]):
        self.q = q
        self.roots = roots


def prepare_sieve_plan(
    S_y: int,
    y_anchor: int,
    Q_bound: int,
    h: int = 3
) -> List[SievePrimePlan]:
    """
    Precomputes forbidden residues t mod q for all primes q in (y_anchor, Q_bound].
    """
    plan = []
    # Primes > y_anchor up to Q_bound
    q = y_anchor + 1
    if q % 2 == 0:
        q += 1

    while q <= Q_bound:
        if gmpy2.is_prime(q):
            S_y_mod_q = int(S_y % q)
            if S_y_mod_q != 0:
                roots = get_forbidden_t_residues(q, S_y_mod_q, h=h)
                if roots:
                    plan.append(SievePrimePlan(q, list(roots)))
        q += 2

    return plan


class SegmentedPAQCSSieve:
    """
    Segmented bitset sieve over odd integers t in [t_start, t_end].
    """

    def __init__(self, plan: List[SievePrimePlan]):
        self.plan = plan

    def sieve_segment(self, t_start: int, t_end: int) -> List[int]:
        """
        Sieves odd t in [t_start, t_end], returning surviving t values.
        """
        assert t_start % 2 == 1, "t_start must be odd"
        assert t_end >= t_start, "t_end must be >= t_start"

        n_candidates = (t_end - t_start) // 2 + 1
        alive = np.ones(n_candidates, dtype=np.uint8)

        for p_plan in self.plan:
            q = p_plan.q
            for t_root in p_plan.roots:
                rem = (t_root - t_start) % q
                first_t = t_start + rem
                if first_t % 2 == 0:
                    first_t += q
                i0 = (first_t - t_start) // 2
                if i0 < n_candidates:
                    alive[i0::q] = 0

        survivor_indices = np.where(alive)[0]
        return [int(t_start + 2 * i) for i in survivor_indices]
