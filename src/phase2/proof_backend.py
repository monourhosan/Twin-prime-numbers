"""
Deterministic primality proof module for Proth (k*2^n + 1) and LLR (k*2^n - 1).
Enforces complete mathematical preconditions, Jacobi non-residue checks,
and fast Lucas doubling ladders.
"""

from enum import Enum
from typing import Tuple, Optional, List
from .fast_lucas import lucas_v_fast

class ProofStatus(Enum):
    PROVEN = "PROVEN"
    COMPOSITE = "COMPOSITE"
    INCONCLUSIVE = "INCONCLUSIVE"

def jacobi_symbol(a: int, n: int) -> int:
    """Computes Jacobi symbol (a / n) for positive odd n."""
    if n <= 0 or n % 2 == 0:
        return 0
    a = a % n
    t = 1
    while a != 0:
        while a % 2 == 0:
            a //= 2
            r = n % 8
            if r in (3, 5):
                t = -t
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            t = -t
        a = a % n
    return t if n == 1 else 0

def validate_proth_preconditions(k: int, n: int, B: int) -> Tuple[bool, str]:
    if k <= 0 or k % 2 == 0:
        return False, f"k must be positive odd integer, got k={k}"
    if n < 1:
        return False, f"n must be >= 1, got n={n}"
    if k >= (1 << n):
        return False, f"Proth theorem requires k < 2^n, got k={k} >= 2^{n}"
    expected_b = k * (1 << n) + 1
    if B != expected_b:
        return False, f"B mismatch: got {B}, expected k*2^n + 1 = {expected_b}"
    if B <= 2:
        return False, f"B must be > 2, got {B}"
    return True, "Preconditions valid"

def proth_prove(k: int, n: int, B: int) -> Tuple[ProofStatus, Optional[int], str]:
    """
    Applies Proth's Theorem to prove primality of B = k*2^n + 1 (k odd, k < 2^n).
    Theorem: If a^((B-1)/2) == -1 mod B, then B is prime.
    Euler Criterion: If Jacobi(a/B) == -1 and B is prime, then a^((B-1)/2) must be -1 mod B.
    Therefore, if Jacobi(a/B) == -1 and a^((B-1)/2) != -1 mod B, B is unconditionally COMPOSITE.
    """
    valid, msg = validate_proth_preconditions(k, n, B)
    if not valid:
        return ProofStatus.INCONCLUSIVE, None, msg

    exp = (B - 1) // 2
    witness_candidates = [3, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]

    found_quadratic_nonresidue = False
    for a in witness_candidates:
        if jacobi_symbol(a, B) == -1:
            found_quadratic_nonresidue = True
            power = pow(a, exp, B)
            if power == B - 1:
                return ProofStatus.PROVEN, a, f"Proth witness {a} passed: {a}^((B-1)/2) == -1 mod B"
            else:
                return ProofStatus.COMPOSITE, a, f"Proth witness {a} with Jacobi=-1 failed power test: composite"

    # Fallback witness test
    if not found_quadratic_nonresidue:
        if pow(3, exp, B) == B - 1:
            return ProofStatus.PROVEN, 3, "Witness 3 satisfied Proth condition"

    return ProofStatus.INCONCLUSIVE, None, "No witness with Jacobi=-1 found in candidate pool"

def validate_llr_preconditions(k: int, n: int, A: int) -> Tuple[bool, str]:
    if k <= 0 or k % 2 == 0:
        return False, f"k must be positive odd integer, got k={k}"
    if n < 2:
        return False, f"LLR requires n >= 2, got n={n}"
    if k >= (1 << n):
        return False, f"LLR requires k < 2^n, got k={k} >= 2^{n}"
    expected_a = k * (1 << n) - 1
    if A != expected_a:
        return False, f"A mismatch: got {A}, expected k*2^n - 1 = {expected_a}"
    if A <= 3:
        return False, f"A must be > 3, got {A}"
    return True, "Preconditions valid"

def llr_prove(k: int, n: int, A: int) -> Tuple[ProofStatus, Optional[int], Optional[int], str]:
    """
    Applies the Lucas-Lehmer-Riesel (LLR) / BLS Theorem 8 primality proof to A = k*2^n - 1.
    Preconditions: k odd, k < 2^n, n >= 2.
    Parameter P must satisfy Jacobi(P-2, A) == 1 and Jacobi(P+2, A) == -1.
    Sequence: u_0 = V_k(P, 1) mod A, u_{i+1} = u_i^2 - 2 mod A.
    Theorem: A is prime iff u_{n-2} == 0 mod A.
    """
    valid, msg = validate_llr_preconditions(k, n, A)
    if not valid:
        return ProofStatus.INCONCLUSIVE, None, None, msg

    chosen_p = None
    for p_cand in [3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22, 24]:
        if jacobi_symbol(p_cand - 2, A) == 1 and jacobi_symbol(p_cand + 2, A) == -1:
            chosen_p = p_cand
            break

    if chosen_p is None:
        return ProofStatus.INCONCLUSIVE, None, None, "No parameter P in search set satisfied Riesel Jacobi conditions"

    # Compute u0 = V_k(P, 1) mod A via O(log k) Montgomery ladder
    u0 = lucas_v_fast(k, chosen_p, A)

    # Iteration: u_{i+1} = (u_i^2 - 2) mod A for i in 0 .. n - 2
    u = u0
    for _ in range(n - 2):
        u = (pow(u, 2, A) - 2) % A

    if u == 0:
        return ProofStatus.PROVEN, chosen_p, u0, f"LLR proof verified: u_{{n-2}} == 0 mod A with P={chosen_p}"
    else:
        return ProofStatus.COMPOSITE, chosen_p, u0, f"LLR proof completed: u_{{n-2}} != 0 mod A (A is composite)"
