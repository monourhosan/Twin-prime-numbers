"""
Screening Pipeline for HDC-7 Sieve Survivors.
Executes staged base-2 Fermat rejection followed by multi-base Miller-Rabin screening.
Strictly distinguishes Left PRP, Right PRP, and Dual PRP survivors.
"""

import time
from typing import Tuple, Dict, Any, Optional
from src.phase7.math import compute_candidate_pair

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False


class HDCScreener:
    """
    Two-stage screening pipeline:
    Stage 1: Fast base-2 Fermat PRP rejection on first member.
    Stage 2: Fast base-2 Fermat PRP on second member.
    Stage 3: Multi-base Miller-Rabin screening on dual survivors before expensive proof.
    """
    def __init__(self, use_gmpy2: bool = True, order: str = "A_first"):
        self.use_gmpy2 = use_gmpy2 and HAVE_GMPY2
        self.order = order # "A_first" or "B_first"

    def fermat_base2_test(self, N: int) -> bool:
        """Computes 2^(N-1) == 1 mod N."""
        if N <= 1 or N % 2 == 0:
            return False
        if self.use_gmpy2:
            return gmpy2.powmod(2, N - 1, N) == 1
        return pow(2, N - 1, N) == 1

    def mr_test(self, N: int, bases: Tuple[int, ...] = (2, 3, 5, 7, 11)) -> bool:
        """Multi-base Miller-Rabin screening test."""
        if N <= 1 or N % 2 == 0:
            return False
        if self.use_gmpy2:
            return bool(gmpy2.is_prime(gmpy2.mpz(N), 25))

        d = N - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for a in bases:
            if a % N == 0:
                continue
            x = pow(a, d, N)
            if x == 1 or x == N - 1:
                continue
            for _ in range(s - 1):
                x = pow(x, 2, N)
                if x == N - 1:
                    break
            else:
                return False
        return True

    def screen_pair(self, MB: int, t: int, n: int) -> Tuple[bool, bool, bool, Dict[str, Any]]:
        """
        Screens candidate corresponding to index t.
        Returns (is_left_prp, is_right_prp, is_dual_prp, telemetry).
        """
        t0 = time.perf_counter()
        k, C, A, Bprime = compute_candidate_pair(MB, t, n)

        is_a_prp = False
        is_b_prp = False
        stage1_time = 0.0
        stage2_time = 0.0

        if self.order == "A_first":
            # Screen A first
            s0 = time.perf_counter()
            if self.fermat_base2_test(A):
                is_a_prp = True
                stage1_time = time.perf_counter() - s0
                # Screen B
                s1 = time.perf_counter()
                if self.fermat_base2_test(Bprime):
                    is_b_prp = True
                    stage2_time = time.perf_counter() - s1
            else:
                stage1_time = time.perf_counter() - s0
        else:
            # Screen B first
            s0 = time.perf_counter()
            if self.fermat_base2_test(Bprime):
                is_b_prp = True
                stage1_time = time.perf_counter() - s0
                # Screen A
                s1 = time.perf_counter()
                if self.fermat_base2_test(A):
                    is_a_prp = True
                    stage2_time = time.perf_counter() - s1
            else:
                stage1_time = time.perf_counter() - s0

        is_dual = is_a_prp and is_b_prp
        if is_dual:
            # Multi-base confirmation
            if not (self.mr_test(A) and self.mr_test(Bprime)):
                is_dual = False

        total_time = time.perf_counter() - t0
        telemetry = {
            "t": t,
            "k": str(k),
            "A_digits": len(str(A)),
            "B_digits": len(str(Bprime)),
            "is_a_prp": is_a_prp,
            "is_b_prp": is_b_prp,
            "is_dual_prp": is_dual,
            "total_time_sec": total_time,
            "stage1_time_sec": stage1_time,
            "stage2_time_sec": stage2_time
        }
        return is_a_prp, is_b_prp, is_dual, telemetry
