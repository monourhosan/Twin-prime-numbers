"""
Deterministic Primality Proof Engine for Phase 3 (HDRSS).
Enforces strict mathematical preconditions and provable status distinctions:
PROVEN / COMPOSITE / INCONCLUSIVE.
"""

from enum import Enum
from typing import Tuple, Optional, Dict, Any, List

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

def lucas_v_montgomery(k: int, P: int, mod: int) -> int:
    """
    Computes V_k(P, 1) mod mod using Montgomery doubling ladder in O(log k).
    Recurrence relations:
      V_{2m}   = (V_m^2 - 2) mod mod
      V_{2m+1} = (V_m * V_{m+1} - P) mod mod
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod

    v = P % mod
    w = (P * P - 2) % mod

    # Iterate through bits of k from second most significant bit
    bits = bin(k)[3:] # skip '0b1'
    for b in bits:
        if b == '1':
            v = (v * w - P) % mod
            w = (w * w - 2) % mod
        else:
            w = (v * w - P) % mod
            v = (v * v - 2) % mod

    return v

def validate_proth_preconditions(k: int, n: int, B: int) -> Tuple[bool, str]:
    if k <= 0 or k % 2 == 0:
        return False, f"k must be positive odd integer, got {k}"
    if n < 1:
        return False, f"n must be >= 1, got {n}"
    if k >= (1 << n):
        return False, f"Theorem precondition k < 2^n violated: k={k} >= 2^{n}"
    expected_B = k * (1 << n) + 1
    if B != expected_B:
        return False, f"B mismatch: got {B}, expected {expected_B}"
    if B <= 2:
        return False, f"B must be > 2, got {B}"
    return True, "Preconditions valid"

def validate_llr_preconditions(k: int, n: int, A: int) -> Tuple[bool, str]:
    if k <= 0 or k % 2 == 0:
        return False, f"k must be positive odd integer, got {k}"
    if n < 2:
        return False, f"LLR theorem requires n >= 2, got {n}"
    if k >= (1 << n):
        return False, f"Theorem precondition k < 2^n violated: k={k} >= 2^{n}"
    expected_A = k * (1 << n) - 1
    if A != expected_A:
        return False, f"A mismatch: got {A}, expected {expected_A}"
    if A <= 3:
        return False, f"A must be > 3, got {A}"
    return True, "Preconditions valid"

def proth_prove(
    k: int,
    n: int,
    B: int,
    witness_candidates: Optional[List[int]] = None
) -> Tuple[ProofStatus, Optional[int], str]:
    """
    Proves primality of B = k*2^n + 1 using Proth's theorem:
      w^((B-1)/2) == -1 (mod B) => B is prime.
    """
    valid, msg = validate_proth_preconditions(k, n, B)
    if not valid:
        return ProofStatus.INCONCLUSIVE, None, msg

    if witness_candidates is None:
        witness_candidates = [3, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

    exp = (B - 1) // 2
    for w in witness_candidates:
        if jacobi_symbol(w, B) == -1:
            pow_val = pow(w, exp, B)
            if pow_val == B - 1:
                return ProofStatus.PROVEN, w, f"Proth witness w={w} passed: w^((B-1)/2) == -1 mod B"
            else:
                return ProofStatus.COMPOSITE, w, f"Proth witness w={w} with Jacobi=-1 failed power test: composite"

    # Fallback to direct check if no candidate had Jacobi=-1
    for w in witness_candidates[:5]:
        if pow(w, exp, B) == B - 1:
            return ProofStatus.PROVEN, w, f"Proth witness w={w} satisfied congruence: prime"

    return ProofStatus.INCONCLUSIVE, None, "No witness candidate satisfied Proth condition"

def llr_prove(
    k: int,
    n: int,
    A: int,
    parameter_candidates: Optional[List[int]] = None
) -> Tuple[ProofStatus, Optional[int], Optional[int], str]:
    """
    Proves primality of A = k*2^n - 1 using Lucas-Lehmer-Riesel / BLS Theorem 8.
    Parameters P must satisfy:
      Jacobi(P-2, A) == 1 and Jacobi(P+2, A) == -1.
    Sequence:
      u_0 = V_k(P, 1) mod A, u_{i+1} = u_i^2 - 2 mod A.
      u_{n-2} == 0 mod A <=> A is prime.
    """
    valid, msg = validate_llr_preconditions(k, n, A)
    if not valid:
        return ProofStatus.INCONCLUSIVE, None, None, msg

    if parameter_candidates is None:
        parameter_candidates = [3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22, 24]

    chosen_P = None
    for p_cand in parameter_candidates:
        if jacobi_symbol(p_cand - 2, A) == 1 and jacobi_symbol(p_cand + 2, A) == -1:
            chosen_P = p_cand
            break

    if chosen_P is None:
        return ProofStatus.INCONCLUSIVE, None, None, "No parameter P in search pool satisfied Riesel Jacobi conditions"

    # Initial value u0
    u0 = lucas_v_montgomery(k, chosen_P, A)

    # Iteration: u_{i+1} = u_i^2 - 2 mod A
    u = u0
    for _ in range(n - 2):
        u = (pow(u, 2, A) - 2) % A

    if u == 0:
        return ProofStatus.PROVEN, chosen_P, u0, f"LLR proof verified: u_{{n-2}} == 0 mod A with P={chosen_P}"
    else:
        return ProofStatus.COMPOSITE, chosen_P, u0, f"LLR proof completed: u_{{n-2}} != 0 mod A (A is composite)"
