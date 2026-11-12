"""
Fast Probable-Prime (PRP) screening filters for candidate pairs (A, B).
Rejects composite candidates cheaply before expensive deterministic proof sequences.
PRP results are strictly labeled as PROBABLE_PRIME, never PROVEN.
"""

from typing import Tuple

def miller_rabin_test(n: int, bases=(2, 3, 5)) -> bool:
    """
    Deterministic Miller-Rabin probable primality test for specified bases.
    Returns False if n is definitively composite, True if probable prime.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    # Write n - 1 as 2^s * d
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
            return False
    return True

def prp_screen_pair(A: int, B: int) -> Tuple[bool, bool]:
    """
    Screens candidate pair (A, B) = (k*2^n - 1, k*2^n + 1).
    Returns (a_prp, b_prp). Both must be True for pair to be a twin-PRP candidate.
    """
    a_prp = miller_rabin_test(A, bases=[2, 3])
    if not a_prp:
        return False, False
    b_prp = miller_rabin_test(B, bases=[2, 3])
    return a_prp, b_prp
