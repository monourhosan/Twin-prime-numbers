"""
PAQCS Candidate Screening Cascade (Phase 8).
Executes fast Fermat and Miller-Rabin probable-prime filtering
on sieve survivors.
"""

from typing import List, Tuple, Optional, Dict, Any
import gmpy2
from .paqcs_math import construct_pair


def screen_candidate_single(
    S_y: int,
    t: int,
    h: int = 3
) -> Tuple[bool, bool, int, int]:
    """
    Screens a single candidate t:
    Returns (is_single_prp, is_dual_prp, A, B).
    Evaluates lower member A first; only if A is PRP does it evaluate B.
    """
    x, C, A, B = construct_pair(S_y, t, h=h)

    # 1. Fermat PRP base 2 on lower member A
    if gmpy2.powmod(2, A - 1, A) != 1:
        return False, False, A, B

    # Miller-Rabin check on A (base 3)
    if gmpy2.is_prime(A, 5) == 0:
        return False, False, A, B

    # A is PRP! Now test upper member B
    if gmpy2.powmod(2, B - 1, B) != 1:
        return True, False, A, B

    # Miller-Rabin check on B (base 3)
    if gmpy2.is_prime(B, 5) == 0:
        return True, False, A, B

    # Both passed! Dual-PRP candidate found!
    return True, True, A, B


def screen_batch_worker(args: Tuple[int, List[int], int]) -> List[Tuple[int, bool, bool]]:
    """Worker function for parallel batch screening."""
    S_y, t_list, h = args
    results = []
    for t in t_list:
        is_single, is_dual, _, _ = screen_candidate_single(S_y, t, h=h)
        if is_single:
            results.append((t, is_single, is_dual))
    return results
