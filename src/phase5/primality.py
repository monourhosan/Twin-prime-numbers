"""
Phase 5 Primality Certification Engine.
Implements:
1. Miller-Rabin PRP screening (gmpy2 / pure Python).
2. Pocklington / BLS (1975) Theorem 4 deterministic certificate for upper member B = C + 1.
3. Morrison (1975) / BLS (1975) Theorem 17 deterministic certificate for lower member A = C - 1
   via 2x2 companion matrix binary exponentiation for Lucas sequence U_k(P, 1).
Maintains strict status transitions:
GENERATED -> SURVIVED_SIEVE -> PRP_LEFT -> PRP_BOTH -> PROVEN_LEFT -> PROVEN_BOTH -> INDEPENDENTLY_VERIFIED
"""

import math
from enum import Enum
from typing import Tuple, Optional, List, Dict, Any

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False

class PrimalityStatus(Enum):
    COMPOSITE = "COMPOSITE"
    PRP = "PRP"
    PROVEN_PRIME = "PROVEN_PRIME"
    INCONCLUSIVE = "INCONCLUSIVE"

def jacobi_symbol(a: int, n: int) -> int:
    """Computes Jacobi symbol (a / n) for positive odd integer n."""
    if HAVE_GMPY2:
        return int(gmpy2.jacobi(gmpy2.mpz(a), gmpy2.mpz(n)))
    
    if n <= 0 or n % 2 == 0:
        raise ValueError(f"Jacobi symbol requires positive odd n, got {n}")
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

def prp_test(n: int, rounds: int = 25) -> bool:
    """
    Probable-prime screening test (Miller-Rabin).
    Returns True if n is probably prime, False if definitively composite.
    NOTE: A True return is strictly PRP, NOT a proof.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    
    if HAVE_GMPY2:
        return gmpy2.is_prime(gmpy2.mpz(n), rounds) > 0

    # Pure Python Miller-Rabin
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    
    bases = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47][:rounds]
    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def matrix_mul_2x2_mod(A, B, mod: int):
    """Multiplies two 2x2 matrices modulo mod."""
    if HAVE_GMPY2:
        m = gmpy2.mpz(mod)
        return [
            [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % m, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % m],
            [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % m, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % m]
        ]
    return [
        [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % mod, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % mod],
        [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % mod, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % mod]
    ]

def matrix_pow_2x2_mod(M, exp: int, mod: int):
    """Computes M^exp mod mod via binary exponentiation."""
    if HAVE_GMPY2:
        m = gmpy2.mpz(mod)
        res = [[gmpy2.mpz(1), gmpy2.mpz(0)], [gmpy2.mpz(0), gmpy2.mpz(1)]]
        base = [[gmpy2.mpz(M[0][0]) % m, gmpy2.mpz(M[0][1]) % m],
                [gmpy2.mpz(M[1][0]) % m, gmpy2.mpz(M[1][1]) % m]]
    else:
        res = [[1, 0], [0, 1]]
        base = [[M[0][0] % mod, M[0][1] % mod], [M[1][0] % mod, M[1][1] % mod]]
    
    e = int(exp)
    while e > 0:
        if e & 1:
            res = matrix_mul_2x2_mod(res, base, mod)
        base = matrix_mul_2x2_mod(base, base, mod)
        e >>= 1
    return res

def lucas_u_matrix(k: int, P: int, mod: int) -> int:
    """
    Computes Lucas sequence term U_k(P, 1) mod mod using the 2x2 companion matrix:
    M = [[P, -1], [1, 0]].
    M^k = [[U_{k+1}, -U_k], [U_k, -U_{k-1}]] (mod mod).
    Returns U_k mod mod (entry [1][0]).
    """
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod
    M = [[P, -1], [1, 0]]
    Mk = matrix_pow_2x2_mod(M, k, mod)
    return int(Mk[1][0])

def prove_pocklington_upper(
    B: int,
    F_odd: int,
    odd_prime_factors: List[int],
    witness_pool: List[int] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)
) -> Tuple[PrimalityStatus, Optional[int], Optional[Dict[str, Any]], Optional[str]]:
    """
    Executes Pocklington / BLS (1975) Theorem 4 primality proof for upper member B:
    Preconditions:
    - B - 1 has factored divisor F_odd
    - Size condition: F_odd^2 > B
    Witness condition:
    There exists base a such that:
    1. a^(B - 1) == 1 (mod B)
    2. gcd(a^((B - 1)/q) - 1, B) == 1 for every prime factor q | F_odd.
    """
    # Preconditions check
    if B <= 2 or B % 2 == 0:
        return PrimalityStatus.INCONCLUSIVE, None, None, f"B must be positive odd > 2, got {B}"
    if (B - 1) % F_odd != 0:
        return PrimalityStatus.INCONCLUSIVE, None, None, f"F_odd does not divide B - 1"
    if F_odd * F_odd <= B:
        return PrimalityStatus.INCONCLUSIVE, None, None, f"Size condition F_odd^2 > B failed ({F_odd}^2 <= {B})"
    
    for a in witness_pool:
        # Check Fermat congruence
        if pow(a, B - 1, B) != 1:
            return PrimalityStatus.COMPOSITE, a, None, f"Fermat compositeness witness: base {a}"
        
        # Check gcd condition for all prime factors q | F_odd
        all_gcd_1 = True
        factor_gcds = {}
        for q in odd_prime_factors:
            exp_q = (B - 1) // q
            val = pow(a, exp_q, B)
            g = math.gcd((val - 1) % B, B)
            factor_gcds[str(q)] = str(g)
            if g != 1:
                all_gcd_1 = False
                break
                
        if all_gcd_1:
            proof_dict = {
                "theorem": "Pocklington_BLS_1975_Theorem_4",
                "member": "B = C + 1",
                "factored_divisor_F_odd": str(F_odd),
                "prime_factors": odd_prime_factors,
                "witness_base_a": a,
                "fermat_congruence": "1",
                "size_condition": f"F_odd^2 = {F_odd**2} > B = {B}",
                "factor_gcds": factor_gcds
            }
            return PrimalityStatus.PROVEN_PRIME, a, proof_dict, None
            
    return PrimalityStatus.INCONCLUSIVE, None, None, "Witness pool exhausted without satisfying all GCD conditions"

def prove_morrison_lower(
    A: int,
    F_odd: int,
    odd_prime_factors: List[int],
    param_pool: List[int] = tuple(range(3, 100))
) -> Tuple[PrimalityStatus, Optional[int], Optional[Dict[str, Any]], Optional[str]]:
    """
    Executes Morrison (1975) / BLS (1975) Theorem 17 primality proof for lower member A:
    Preconditions:
    - A + 1 has factored divisor F_odd
    - Size condition: (F_odd - 1)^2 > A
    Witness condition:
    There exists integer parameter P such that:
    1. Discriminant D = P^2 - 4 satisfies Jacobi symbol (D / A) == -1
    2. Lucas sequence term U_{A + 1}(P, 1) == 0 (mod A)
    3. gcd(U_{(A + 1)/q}(P, 1), A) == 1 for every prime factor q | F_odd.
    """
    # Preconditions check
    if A <= 2 or A % 2 == 0:
        return PrimalityStatus.INCONCLUSIVE, None, None, f"A must be positive odd > 2, got {A}"
    if (A + 1) % F_odd != 0:
        return PrimalityStatus.INCONCLUSIVE, None, None, f"F_odd does not divide A + 1"
    if (F_odd - 1) * (F_odd - 1) <= A:
        return PrimalityStatus.INCONCLUSIVE, None, None, f"Size condition (F_odd - 1)^2 > A failed"
        
    for P in param_pool:
        D = P * P - 4
        j = jacobi_symbol(D, A)
        if j != -1:
            continue
            
        # Check Condition 1: U_{A + 1} == 0 (mod A)
        u_full = lucas_u_matrix(A + 1, P, A)
        if u_full != 0:
            # Under valid Jacobi symbol (D/A) = -1, U_{A+1} != 0 proves A is composite
            return PrimalityStatus.COMPOSITE, P, None, f"Lucas sequence compositeness witness: U_{{A+1}} = {u_full} != 0 mod A with P={P}"
            
        # Check Condition 2: gcd(U_{(A + 1)/q}, A) == 1 for all prime factors q | F_odd
        all_gcd_1 = True
        factor_gcds = {}
        for q in odd_prime_factors:
            k_q = (A + 1) // q
            u_q = lucas_u_matrix(k_q, P, A)
            g = math.gcd(u_q, A)
            factor_gcds[str(q)] = str(g)
            if g != 1:
                all_gcd_1 = False
                break
                
        if all_gcd_1:
            proof_dict = {
                "theorem": "Morrison_BLS_1975_Theorem_17",
                "member": "A = C - 1",
                "factored_divisor_F_odd": str(F_odd),
                "prime_factors": odd_prime_factors,
                "parameter_P": P,
                "discriminant_D": D,
                "jacobi_D_mod_A": -1,
                "lucas_U_A_plus_1_mod_A": "0",
                "size_condition": f"(F_odd - 1)^2 = {(F_odd - 1)**2} > A = {A}",
                "factor_gcds": factor_gcds
            }
            return PrimalityStatus.PROVEN_PRIME, P, proof_dict, None
            
    return PrimalityStatus.INCONCLUSIVE, None, None, "Parameter pool exhausted without satisfying all Morrison conditions"
