"""
Tiered probable-prime screening for twin-prime candidates (A = 6m - 1, B = 6m + 1, or Method Q).
Fast compositeness rejection using small-prime division, Fermat base-2, and 25-round Miller-Rabin.
Supports A-first vs B-first screening order benchmarking.
"""

import time
from typing import Optional, List, Tuple, Dict, Any
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

def is_probable_prime_fast(n: int, rounds: int = 25) -> bool:
    """Uses gmpy2.is_prime if available (BPSW + Miller-Rabin), else deterministic Miller-Rabin."""
    if HAVE_GMPY2:
        # gmpy2.is_prime returns True if probable prime
        return bool(gmpy2.is_prime(gmpy2.mpz(n), rounds))
    return miller_rabin_test(n, DETERMINISTIC_MR_BASES[:rounds])

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
        self.mr_rounds = mr_rounds
        self.mr_bases = DETERMINISTIC_MR_BASES[:mr_rounds]

    def screen_pair(
        self,
        A: int,
        B: int,
        order: str = "A_first"
    ) -> Tuple[bool, bool, bool, Optional[str]]:
        """
        Screens candidate pair (A, B).
        order: "A_first" or "B_first".
        Returns (is_dual_prp, is_A_prp, is_B_prp, rejection_reason).
        """
        # Small divisor check
        for p in SMALL_SCREENING_PRIMES:
            if A != p and A % p == 0:
                return False, False, False, f"A divisible by {p}"
            if B != p and B % p == 0:
                return False, False, False, f"B divisible by {p}"

        if order == "A_first":
            # Test A first
            if not is_probable_prime_fast(A, self.mr_rounds):
                return False, False, False, "A failed PRP"
            # A passed, test B
            if not is_probable_prime_fast(B, self.mr_rounds):
                return False, True, False, "B failed PRP"
            return True, True, True, None
        else:
            # Test B first
            if not is_probable_prime_fast(B, self.mr_rounds):
                return False, False, False, "B failed PRP"
            # B passed, test A
            if not is_probable_prime_fast(A, self.mr_rounds):
                return False, False, True, "A failed PRP"
            return True, True, True, None

    def screen_candidate(self, m: int) -> ScreeningResult:
        """Runs candidate pair 6m +/- 1 through progressive filters."""
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
        
        if powmod(2, B - 1, B) != 1:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, is_left_prp=False, stage_passed="FERMAT_LEFT", rejection_reason="B failed Fermat base-2", elapsed_ms=elapsed)
            
        # 3. Miller-Rabin test on Left (A)
        if not miller_rabin_test(A, self.mr_bases):
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, stage_passed="FERMAT", rejection_reason="A failed Miller-Rabin", elapsed_ms=elapsed)
        
        # 4. Miller-Rabin test on Right (B)
        if not miller_rabin_test(B, self.mr_bases):
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ScreeningResult(candidate=pair, is_left_prp=True, stage_passed="MR_LEFT", rejection_reason="B failed Miller-Rabin", elapsed_ms=elapsed)
        
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


def benchmark_screening_order(candidates: List[Tuple[int, int]]) -> Dict[str, Any]:
    """
    Benchmarks A-first vs B-first screening order on a fixed list of candidate pairs (A, B).
    """
    screener = CandidateScreener(mr_rounds=25)
    
    # Benchmark A-first
    t0 = time.perf_counter()
    a_first_dual = 0
    a_first_rejections = 0
    for A, B in candidates:
        dual, is_a, is_b, _ = screener.screen_pair(A, B, order="A_first")
        if dual:
            a_first_dual += 1
        else:
            a_first_rejections += 1
    t_a_first = time.perf_counter() - t0

    # Benchmark B-first
    t0 = time.perf_counter()
    b_first_dual = 0
    b_first_rejections = 0
    for A, B in candidates:
        dual, is_a, is_b, _ = screener.screen_pair(A, B, order="B_first")
        if dual:
            b_first_dual += 1
        else:
            b_first_rejections += 1
    t_b_first = time.perf_counter() - t0

    return {
        "candidate_count": len(candidates),
        "A_first": {
            "elapsed_seconds": t_a_first,
            "rate_pairs_per_sec": len(candidates) / max(t_a_first, 1e-6),
            "dual_prp": a_first_dual,
            "rejections": a_first_rejections
        },
        "B_first": {
            "elapsed_seconds": t_b_first,
            "rate_pairs_per_sec": len(candidates) / max(t_b_first, 1e-6),
            "dual_prp": b_first_dual,
            "rejections": b_first_rejections
        },
        "recommended_order": "A_first" if t_a_first <= t_b_first else "B_first"
    }
