"""
Phase 4 Probable-Prime (PRP) Screening Module.
Implements tri-state screening with compositeness witness preservation,
preventing conflation of PROBABLE_PRIME with PROVEN_PRIME.
"""

from enum import Enum
from typing import Tuple, List, Optional
from .backend import pow_mod, miller_rabin_test

class PRPStatus(Enum):
    COMPOSITE = "COMPOSITE"
    PROBABLE_PRIME = "PROBABLE_PRIME"
    INCONCLUSIVE = "INCONCLUSIVE"

def test_prp_candidate(val: int, bases: List[int] = (2, 3, 5)) -> Tuple[PRPStatus, Optional[int]]:
    """
    Tests an odd integer candidate using Miller-Rabin bases.
    Returns (PRPStatus, witness_or_failed_base).
    """
    if val <= 1:
        return PRPStatus.COMPOSITE, None
    if val in (2, 3):
        return PRPStatus.PROBABLE_PRIME, None
    if val % 2 == 0:
        return PRPStatus.COMPOSITE, 2

    for b in bases:
        passed = miller_rabin_test(val, b)
        if not passed:
            return PRPStatus.COMPOSITE, b

    return PRPStatus.PROBABLE_PRIME, None

def screen_pair_prp(
    A: int,
    B: int,
    bases: List[int] = (2, 3, 5),
    screen_order: str = "B_then_A"
) -> Tuple[PRPStatus, PRPStatus, Optional[str]]:
    """
    Screens candidate twin-prime pair (A = k*2^n - 1, B = k*2^n + 1).
    Supports measured screen order:
    - 'B_then_A': screens upper candidate B first (cheaply eliminates ~50% before checking A)
    - 'A_then_B': screens lower candidate A first
    """
    if screen_order == "B_then_A":
        st_B, w_B = test_prp_candidate(B, bases=bases)
        if st_B != PRPStatus.PROBABLE_PRIME:
            return PRPStatus.INCONCLUSIVE, st_B, f"B failed base {w_B}"
        st_A, w_A = test_prp_candidate(A, bases=bases)
        if st_A != PRPStatus.PROBABLE_PRIME:
            return st_A, st_B, f"A failed base {w_A}"
        return PRPStatus.PROBABLE_PRIME, PRPStatus.PROBABLE_PRIME, None
    else:
        st_A, w_A = test_prp_candidate(A, bases=bases)
        if st_A != PRPStatus.PROBABLE_PRIME:
            return st_A, PRPStatus.INCONCLUSIVE, f"A failed base {w_A}"
        st_B, w_B = test_prp_candidate(B, bases=bases)
        if st_B != PRPStatus.PROBABLE_PRIME:
            return st_A, st_B, f"B failed base {w_B}"
        return PRPStatus.PROBABLE_PRIME, PRPStatus.PROBABLE_PRIME, None
