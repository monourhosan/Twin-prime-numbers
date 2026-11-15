"""
Phase 9 Multi-Stage Candidate Screening Engine.
Implements rapid hierarchical triage:
1. Multiplier primality check (is_small_prime_deterministic for t < 2^64)
2. Fermat base-2 test on B(t)
3. Fermat base-2 test on A(t)
4. Multi-base Miller-Rabin testing on B and A
5. Baillie-PSW probable-prime confirmation
"""

import time
from enum import Enum
from typing import Tuple, Optional
import gmpy2

from .anchor import is_small_prime_deterministic
from .math import construct_pair


class CandidateStatus(str, Enum):
    COMPOSITE = "COMPOSITE"
    SINGLE_PRP = "SINGLE_PRP"
    DUAL_PRP = "DUAL_PRP"


def miller_rabin_test(n: int, bases=(2, 3, 5, 7, 11)) -> bool:
    """
    Standard arbitrary-precision Miller-Rabin test over specified bases.
    """
    n_mpz = gmpy2.mpz(n)
    if n_mpz < 2:
        return False
    if n_mpz in (2, 3, 5, 7, 11):
        return True
    if n_mpz % 2 == 0:
        return False

    d = n_mpz - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a % n_mpz == 0:
            continue
        x = gmpy2.powmod(a, d, n_mpz)
        if x == 1 or x == n_mpz - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n_mpz
            if x == n_mpz - 1:
                break
        else:
            return False
    return True


def screen_candidate_t(
    S_y: int,
    t: int,
    require_prime_t: bool = True
) -> Tuple[CandidateStatus, Optional[Tuple[int, int, int]]]:
    """
    Screens candidate multiplier t.
    Returns (CandidateStatus, (C, A, B) or None).
    """
    # Stage 0: Check multiplier t
    if require_prime_t and not is_small_prime_deterministic(t):
        return CandidateStatus.COMPOSITE, None

    x = S_y * t
    C, A, B = construct_pair(x)

    A_mpz = gmpy2.mpz(A)
    B_mpz = gmpy2.mpz(B)

    # Stage 1: Fast Fermat base-2 on upper member B
    if gmpy2.powmod(2, B_mpz - 1, B_mpz) != 1:
        return CandidateStatus.COMPOSITE, None

    # Stage 2: Fast Fermat base-2 on lower member A
    if gmpy2.powmod(2, A_mpz - 1, A_mpz) != 1:
        return CandidateStatus.SINGLE_PRP, None

    # Stage 3: Miller-Rabin multi-base on B
    if not miller_rabin_test(B, bases=(2, 3, 5, 7, 11)):
        return CandidateStatus.COMPOSITE, None

    # Stage 4: Miller-Rabin multi-base on A
    if not miller_rabin_test(A, bases=(2, 3, 5, 7, 11)):
        return CandidateStatus.SINGLE_PRP, None

    # Stage 5: Lucas / BPSW confirmation via gmpy2.is_prime (BPSW test)
    if gmpy2.is_prime(B_mpz) == 0 or gmpy2.is_prime(A_mpz) == 0:
        return CandidateStatus.COMPOSITE, None

    return CandidateStatus.DUAL_PRP, (C, A, B)
