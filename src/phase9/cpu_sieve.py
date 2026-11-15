"""
Phase 9 CPU Segmented Sieve Reference Engine.
Sieves candidate multipliers t in [t_start, t_end] using precomputed modular root plans.
Maintains exact bit-for-bit equivalence with the NVIDIA GeForce MX250 GPU sieve.
"""

from typing import List, Set, Dict, Any
import numpy as np
import gmpy2
from sympy import primerange

from .math import get_forbidden_t_residues


class SievePrimePlan:
    """
    Holds precomputed forbidden roots t mod q for a single prime modulus q.
    """
    __slots__ = ('q', 'roots')

    def __init__(self, q: int, roots: List[int]):
        self.q = q
        self.roots = roots


def prepare_sieve_plan(
    S_y: int,
    y_anchor: int,
    Q_bound: int
) -> List[SievePrimePlan]:
    """
    Precomputes forbidden roots t mod q for all primes q in (y_anchor, Q_bound].
    """
    plan: List[SievePrimePlan] = []
    primes = list(primerange(y_anchor + 1, Q_bound + 1))
    for q in primes:
        S_y_mod_q = int(S_y % q)
        if S_y_mod_q != 0:
            roots = get_forbidden_t_residues(q, S_y_mod_q)
            if roots:
                plan.append(SievePrimePlan(q, sorted(list(roots))))
    return plan


class CPUSieve:
    """
    Segmented bitset sieve over odd integers t in [t_start, t_end].
    """

    def __init__(self, plan: List[SievePrimePlan]):
        self.plan = plan

    def sieve_segment(self, t_start: int, t_end: int) -> List[int]:
        """
        Sieves odd candidate multipliers t in [t_start, t_end].
        Returns list of surviving t values.
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
