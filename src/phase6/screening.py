"""
Tiered probable-prime screening for twin-prime candidates (A = 6m - 1, B = 6m + 1).
Fast compositeness rejection using small-prime division, Fermat base-2, and 25-round Miller-Rabin.
"""

import time
from typing import Optional, List, Tuple
from src.phase6.models import CandidatePair, ScreeningResult

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False

# Deterministic base sequence for 25-round Miller-Rabin
DETERMINISTIC_MR_BASES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97
]

SMALL_SCREENING_PRIMES = [
    5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79,
    83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163,
    167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257
]

def powmod(base: int, exp: int, mod: int) -> int:
    """Exact modular exponentiation using gmpy2 if available, else built-in pow."""
    if HAVE_GMPY2:
        return int(gmpy2.powmod(gmpy2.mpz(base), gmpy2.mpz(exp), gmpy2.mpz(mod)))
    return pow(base, exp, mod)

def miller_rabin_test(n: int, bases: List[int] = DETERMINISTIC_MR_BASES) -> bool:
    """
    Evaluates strong Miller-Rabin test on n with specified base set.
    Returns True if n passes all base witnesses (probable prime), False if definitely composite.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
        
    # Decompose n - 1 = d * 2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
        
    for a in bases:
        if a >= n:
            continue
        x = powmod(a, d, n)
        if x == 1 or x == n - 1:
            continue
        composite = True
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                composite = False
                break
        if composite:
            return False
    return True

class CandidateScreener:
    """Multi-stage screening pipeline for twin candidate centers."""
    def __init__(self, mr_rounds: int = 25):
        self.mr_bases = DETERMINISTIC_MR_BASES[:mr_rounds]

    def screen_candidate(self, m: int) -> ScreeningResult:
        """Runs candidate pair through progressive filters."""
        t0 = time.perf_counter()
        pair = CandidatePair.from_m(m)
        A = pair.A
        B = pair.B
        
        # 1. Small-prime divisibility
        for p in SMALL_SCREENING_PRIMES:
            if A != p and A % p == 0:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return ScreeningResult(candidate=pair, stage_passed="NONE", rejection_reason=f"A divisible by {p}", elapsed_ms=elapsed)
            if B != p and B % p == 0:
                elapsed = (time.perf_counter() - t0) * 1000.0
                return ScreeningResult(candidate=pair, stage_passed="NONE", rejection_reason=f"B divisible by {p}", elapsed_ms=elapsed)
                
        # 2. Fermat Base-2 Test
        if powmod(2, A - 1, A) != 1:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, stage_passed="DIVISIBILITY", rejection_reason="A failed Fermat base-2", elapsed_ms=elapsed)
        is_left_fermat = True
        
        if powmod(2, B - 1, B) != 1:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, is_left_prp=False, stage_passed="FERMAT_LEFT", rejection_reason="B failed Fermat base-2", elapsed_ms=elapsed)
            
        # 3. Miller-Rabin test on Left (A)
        if not miller_rabin_test(A, self.mr_bases):
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, stage_passed="FERMAT", rejection_reason="A failed Miller-Rabin", elapsed_ms=elapsed)
        is_left_prp = True
        
        # 4. Miller-Rabin test on Right (B)
        if not miller_rabin_test(B, self.mr_bases):
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, is_left_prp=True, stage_passed="MR_LEFT", rejection_reason="B failed Miller-Rabin", elapsed_ms=elapsed)
        is_right_prp = True
        
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ScreeningResult(
            candidate=pair,
            is_left_prp=True,
            is_right_prp=True,
            is_dual_prp=True,
            stage_passed="MILLER_RABIN",
            rejection_reason=None,
            elapsed_ms=elapsed
        )
