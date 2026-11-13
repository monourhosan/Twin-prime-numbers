"""
Deterministic primality proof generator for general-integer twin pairs.
Implements Pocklington BLS Theorem 4 on B = 6m + 1 and Morrison BLS Theorem 17 on A = 6m - 1.
"""

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import sympy
from sympy.ntheory import factorint

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False

def jacobi_symbol(a: int, n: int) -> int:
    """Computes Jacobi symbol (a / n) for positive odd n."""
    if n <= 0 or n % 2 == 0:
        raise ValueError(f"Jacobi symbol requires positive odd modulus, got {n}")
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

def lucas_uv(P: int, Q: int, k: int, N: int) -> Tuple[int, int]:
    """
    Computes Lucas sequence terms (U_k, V_k) modulo N for parameters P, Q=1
    using 2x2 companion matrix exponentiation.
    Matrix: [[P, -1], [1, 0]]
    """
    if k == 0:
        return 0, 2
    if k == 1:
        return 1, P % N

    # Binary exponentiation on 2x2 matrix mod N
    # State: [[m00, m01], [m10, m11]]
    a00, a01 = 1, 0
    a10, a11 = 0, 1 # Identity

    b00, b01 = P % N, (-1) % N
    b10, b11 = 1, 0

    exponent = k
    while exponent > 0:
        if exponent & 1:
            # A = A * B
            t00 = (a00 * b00 + a01 * b10) % N
            t01 = (a00 * b01 + a01 * b11) % N
            t10 = (a10 * b00 + a11 * b10) % N
            t11 = (a10 * b01 + a11 * b11) % N
            a00, a01, a10, a11 = t00, t01, t10, t11
        # B = B * B
        t00 = (b00 * b00 + b01 * b10) % N
        t01 = (b00 * b01 + b01 * b11) % N
        t10 = (b10 * b00 + b11 * b10) % N
        t11 = (b10 * b01 + b11 * b11) % N
        b00, b01, b10, b11 = t00, t01, t10, t11
        exponent >>= 1

    # [U_{k+1}, -U_k]^T = M^k [1, 0]^T -> a10 is U_k
    u_k = a10 % N
    # V_k = 2 * U_{k+1} - P * U_k = 2 * a00 - P * a10 mod N
    v_k = (2 * a00 - P * a10) % N
    return u_k, v_k

def is_prime_trial_division(n: int, limit: int = 10000000) -> bool:
    """Exact deterministic trial division for factors up to limit."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    while d * d <= n and d <= limit:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    if d * d > n:
        return True
    # Factor is too large to prove unconditionally by trial division within budget
    return False

class DeterministicPairProver:
    """Proves primality of both members A = 6m - 1 and B = 6m + 1 using center factorization."""
    def __init__(self, factor_timeout_sec: float = 30.0):
        self.factor_timeout_sec = factor_timeout_sec

    def factor_center(self, m: int) -> Optional[Dict[int, int]]:
        """Factors center m completely. Returns factor dict {prime: exp} or None."""
        try:
            factors = factorint(m, limit=100000, use_ecm=False, use_pm1=False, use_rho=False)
            # Verify complete factorization: product must equal m
            prod = 1
            for p, exp in factors.items():
                if not is_prime_trial_division(p):
                    return None
                prod *= (p ** exp)
            if prod == m:
                return factors
            return None
        except Exception:
            return None

    def prove_upper_pocklington(self, B: int, factors_6m: Dict[int, int]) -> Optional[Dict[str, Any]]:
        """
        Proves B = 6m + 1 using Pocklington BLS Theorem 4 with F = 6m > sqrt(B).
        R = 1, so F / B ~ 1.
        """
        F = B - 1
        prime_factors = sorted(factors_6m.keys())
        
        # Search for a valid base a
        witness_a = None
        for a in range(2, 200):
            # 1. a^(B-1) = 1 mod B
            if pow(a, B - 1, B) != 1:
                continue
            # 2. gcd(a^((B-1)/q) - 1, B) == 1 for all prime q | 6m
            valid = True
            for q in prime_factors:
                power = pow(a, (B - 1) // q, B)
                if math.gcd(power - 1, B) != 1:
                    valid = False
                    break
            if valid:
                witness_a = a
                break
                
        if witness_a is None:
            return None

        return {
            "theorem": "Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington N-1)",
            "candidate": str(B),
            "digits": len(str(B)),
            "F": str(F),
            "R": "1",
            "factored_fraction": "1.0",
            "prime_factors": prime_factors,
            "witness_a": witness_a,
            "verification": {
                "fermat_congruence": f"{witness_a}^(B-1) = 1 mod B",
                "coprimality_condition": "gcd(a^((B-1)/q) - 1, B) == 1 for all q in factors"
            }
        }

    def prove_lower_morrison(self, A: int, factors_6m: Dict[int, int]) -> Optional[Dict[str, Any]]:
        """
        Proves A = 6m - 1 using Morrison BLS Theorem 17 with odd factored part F_odd > sqrt(A).
        """
        odd_prime_factors = [q for q in sorted(factors_6m.keys()) if q > 2]
        F_odd = 1
        for q in odd_prime_factors:
            F_odd *= (q ** factors_6m[q])
            
        # Theorem 17 requires 2*F_odd > sqrt(A) + 1 or (F_odd - 1)^2 > A
        sqrt_A = int(A**0.5)
        if 2 * F_odd <= sqrt_A + 1 and (F_odd - 1) * (F_odd - 1) <= A:
            return None

        # Search parameter P such that Jacobi((P^2 - 4) / A) == -1
        chosen_P = None
        for P in range(3, 500):
            D = P * P - 4
            if jacobi_symbol(D, A) == -1:
                # Check Lucas sequence condition: U_{A+1}(P, 1) == 0 mod A
                u_full, _ = lucas_uv(P, 1, A + 1, A)
                if u_full != 0:
                    continue
                # Check gcd(U_{(A+1)/q}(P, 1), A) == 1 for all odd prime q | F_odd
                valid = True
                for q in odd_prime_factors:
                    u_sub, _ = lucas_uv(P, 1, (A + 1) // q, A)
                    if math.gcd(u_sub, A) != 1:
                        valid = False
                        break
                if valid:
                    chosen_P = P
                    break

        if chosen_P is None:
            return None

        return {
            "theorem": "Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison N+1)",
            "candidate": str(A),
            "digits": len(str(A)),
            "F_odd": str(F_odd),
            "odd_prime_factors": odd_prime_factors,
            "parameter_P": chosen_P,
            "parameter_Q": 1,
            "discriminant_D": chosen_P * chosen_P - 4,
            "jacobi_symbol": -1,
            "verification": {
                "lucas_zero_congruence": f"U_{{A+1}}({chosen_P}, 1) = 0 mod A",
                "lucas_coprimality_condition": "gcd(U_{(A+1)/q}(P, 1), A) == 1 for all odd q in F_odd"
            }
        }

    def prove_pair(self, m: int) -> Optional[Dict[str, Any]]:
        """
        Generates complete primality certificates for both A = 6m - 1 and B = 6m + 1.
        """
        t0 = time.perf_counter()
        A = 6 * m - 1
        B = 6 * m + 1

        # 1. Factor m
        factors_m = self.factor_center(m)
        if factors_m is None:
            return None

        # Build factors of 6m = 2 * 3 * m
        factors_6m = dict(factors_m)
        factors_6m[2] = factors_6m.get(2, 0) + 1
        factors_6m[3] = factors_6m.get(3, 0) + 1

        # 2. Prove B with Pocklington
        proof_B = self.prove_upper_pocklington(B, factors_6m)
        if proof_B is None:
            return None

        # 3. Prove A with Morrison
        proof_A = self.prove_lower_morrison(A, factors_6m)
        if proof_A is None:
            return None

        elapsed = time.perf_counter() - t0
        return {
            "proof_type": "DUAL_CLASSICAL_BLS",
            "status": "CERTIFIED_PRIMES",
            "center_m": str(m),
            "center_C": str(6 * m),
            "digits_lower": len(str(A)),
            "digits_upper": len(str(B)),
            "factors_of_center": {str(p): exp for p, exp in sorted(factors_6m.items())},
            "proof_lower_A": proof_A,
            "proof_upper_B": proof_B,
            "prover_wall_time_sec": elapsed
        }
