"""
Probable Primality (PRP) Screening Module for Phase 3.
Explicitly distinguishes PROBABLE_PRIME from PROVEN.
Provides fast multi-base Miller-Rabin filters to discard composites cheaply.
"""

from enum import Enum
from typing import Tuple, List

class PRPStatus(Enum):
    COMPOSITE = "COMPOSITE"
    PROBABLE_PRIME = "PROBABLE_PRIME"

def miller_rabin_test(n: int, bases: List[int] = (2, 3)) -> PRPStatus:
    """
    Miller-Rabin test. If any witness shows compositeness, returns COMPOSITE.
    If all bases pass, returns PROBABLE_PRIME.
    """
    if n < 2:
        return PRPStatus.COMPOSITE
    if n in (2, 3):
        return PRPStatus.PROBABLE_PRIME
    if n % 2 == 0:
        return PRPStatus.COMPOSITE

    # n - 1 = 2^s * d
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        composite = True
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                composite = False
                break
        if composite:
            return PRPStatus.COMPOSITE

    return PRPStatus.PROBABLE_PRIME

def screen_pair_prp(A: int, B: int, bases: List[int] = (2, 3)) -> Tuple[PRPStatus, PRPStatus]:
    """
    Screens candidate pair (A, B) = (k*2^n - 1, k*2^n + 1).
    Tests B first (Proth side) then A (Riesel side).
    """
    status_B = miller_rabin_test(B, bases=bases)
    if status_B == PRPStatus.COMPOSITE:
        return PRPStatus.COMPOSITE, status_B

    status_A = miller_rabin_test(A, bases=bases)
    return status_A, status_B
