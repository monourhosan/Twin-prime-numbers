"""
Phase 4 Deterministic Primality Proof Engine.
Implements:
1. Proth's Theorem for Upper Member B = k*2^n + 1
2. Lucas-Lehmer-Riesel (LLR) Theorem with Rödseth Parameters for Lower Member A = k*2^n - 1
Maintains strict status distinctions: PROVEN_PRIME, COMPOSITE, and INCONCLUSIVE.
"""

from enum import Enum
from typing import Tuple, Optional, List, Dict, Any
from .math_family import (
    validate_proth_preconditions, validate_llr_preconditions,
    lucas_v_montgomery
)
from .backend import pow_mod, square_sub_2_mod, jacobi

class ProofStatus(Enum):
    PROVEN_PRIME = "PROVEN_PRIME"
    COMPOSITE = "COMPOSITE"
    INCONCLUSIVE = "INCONCLUSIVE"

def proth_prove(
    k: int,
    n: int,
    B: int,
    witness_pool: List[int] = (3, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47),
    use_gmpy: bool = True
) -> Tuple[ProofStatus, Optional[int], Optional[str]]:
    """
    Executes Proth's Theorem primality proof for B = k*2^n + 1:
    If there exists an integer w such that w^((B-1)/2) == -1 (mod B),
    then B is unconditionally prime.
    """
    valid, msg = validate_proth_preconditions(k, n, B)
    if not valid:
        return ProofStatus.INCONCLUSIVE, None, f"Preconditions failed: {msg}"

    exp = (B - 1) // 2

    for w in witness_pool:
        res = pow_mod(w, exp, B, use_gmpy=use_gmpy)
        if res == B - 1:
            return ProofStatus.PROVEN_PRIME, w, None
        # If w^(B-1) != 1 mod B, B is unconditionally composite by Fermat
        fermat_check = pow_mod(res, 2, B, use_gmpy=use_gmpy)
        if fermat_check != 1:
            return ProofStatus.COMPOSITE, w, f"Fermat compositeness witness: base {w}"

    return ProofStatus.INCONCLUSIVE, None, "Witness pool exhausted"

def llr_prove(
    k: int,
    n: int,
    A: int,
    parameter_pool: List[int] = (3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22, 24),
    use_gmpy: bool = True
) -> Tuple[ProofStatus, Optional[int], Optional[int], Optional[str]]:
    """
    Executes Lucas-Lehmer-Riesel (LLR) Theorem primality proof for A = k*2^n - 1:
    Selects parameter P satisfying Jacobi symbols: (P-2/A) = 1 and (P+2/A) = -1.
    Sets u0 = V_k(P, 1) mod A.
    Iterates u_{j+1} = (u_j^2 - 2) mod A for n - 2 steps.
    If u_{n-2} == 0 mod A, A is unconditionally prime.
    """
    valid, msg = validate_llr_preconditions(k, n, A)
    if not valid:
        return ProofStatus.INCONCLUSIVE, None, None, f"Preconditions failed: {msg}"

    selected_p = None
    for p_cand in parameter_pool:
        j_minus = jacobi(p_cand - 2, A, use_gmpy=use_gmpy)
        j_plus = jacobi(p_cand + 2, A, use_gmpy=use_gmpy)
        if j_minus == 1 and j_plus == -1:
            selected_p = p_cand
            break

    if selected_p is None:
        return ProofStatus.INCONCLUSIVE, None, None, "No parameter P in pool satisfied Jacobi conditions"

    # Compute initial u0 = V_k(P, 1) mod A
    u0 = lucas_v_montgomery(k, selected_p, A)

    # Recurrence iteration: exactly n - 2 rounds
    u = u0
    for _ in range(n - 2):
        u = square_sub_2_mod(u, A, use_gmpy=use_gmpy)

    if u == 0:
        return ProofStatus.PROVEN_PRIME, selected_p, u0, None
    else:
        # Under valid Jacobi conditions, u_{n-2} != 0 proves compositeness
        return ProofStatus.COMPOSITE, selected_p, u0, f"Final residue u_{{n-2}} = {u} != 0"
