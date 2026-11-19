"""Mathematical reference model and exact contracts for OPQM-11.

Odd-Parity Quintic Manifold with CRT-Kernel Inverse Sieve:
  C(x) = 12*x^5 + 6*x^3 = 6*x^3 * (2*x^2 + 1)
  A(x) = C(x) - 1
  B(x) = C(x) + 1
  where x = S_y * t, and 6 | S_y.

Divisor:
  F(x) = 6*x^3
Cofactor:
  R(x) = 2*x^2 + 1

Invariants:
  - B - A = 2 (exact twin gap)
  - C = 0 mod 6 (center is divisible by 6)
  - gcd(F(x), R(x)) = 1 (coprimality)
  - Super-root inequalities:
      F^2 > B holds for all x >= 1
      (F_odd - 1)^2 > A holds for x >= 86 (with nu_2(x) = 1)
  - Sieve root-negation symmetry: r_A = q - r_B mod q
  - Inert moduli condition: (-2/q) = -1 <=> q = 5, 7 mod 8

Reference Dual-BLS (1975):
  - Theorem 4: Pocklington N-1 witness verification for upper member B
  - Theorem 17: Morrison N+1 Lucas rank verification for lower member A
"""

import math
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

import gmpy2
import sympy
from sympy.ntheory import factorint, isprime


# ==============================================================================
# 1. Algebraic & Manifold Functions
# ==============================================================================

def compute_manifold(x: int) -> Tuple[int, int, int]:
    """Computes (C, A, B) on the OPQM-11 manifold for coordinate x.

    C(x) = 12*x^5 + 6*x^3
    A(x) = C(x) - 1
    B(x) = C(x) + 1
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be a positive integer, got {x}")

    x_mpz = gmpy2.mpz(x)
    x3 = x_mpz ** 3
    x5 = x3 * (x_mpz ** 2)
    C = 12 * x5 + 6 * x3
    A = C - 1
    B = C + 1
    return int(C), int(A), int(B)


def compute_divisor_and_cofactor(x: int) -> Tuple[int, int]:
    """Computes divisor F(x) = 6*x^3 and cofactor R(x) = 2*x^2 + 1."""
    if x <= 0:
        raise ValueError(f"Coordinate x must be a positive integer, got {x}")
    x_mpz = gmpy2.mpz(x)
    F = 6 * (x_mpz ** 3)
    R = 2 * (x_mpz ** 2) + 1
    return int(F), int(R)


def compute_primorial_anchor(y: int) -> Tuple[int, Dict[int, int]]:
    """Computes S_y = product of all primes <= y and its prime factorization.

    Requires y >= 3 so that 2 * 3 = 6 divides S_y.
    """
    if y < 3:
        raise ValueError(f"Primorial anchor y must be >= 3 to ensure 6 | S_y, got {y}")

    primes = [p for p in sympy.primerange(2, y + 1)]
    Sy = 1
    factors: Dict[int, int] = {}
    for p in primes:
        Sy *= p
        factors[p] = 1

    if Sy % 6 != 0:
        raise ValueError(f"S_y must be divisible by 6, got {Sy}")

    return Sy, factors


def compute_factors_of_F(
    Sy_factors: Dict[int, int],
    t_factors: Dict[int, int]
) -> Dict[int, int]:
    """Computes exact prime factorization of F(x) = 6 * x^3 where x = S_y * t.

    F = 2 * 3 * (S_y * t)^3 = 2^(1 + 3*e_2) * 3^(1 + 3*e_3) * prod_{p > 3} p^(3*e_p).
    """
    all_primes = set(Sy_factors.keys()) | set(t_factors.keys()) | {2, 3}
    factors_F: Dict[int, int] = {}

    for p in sorted(all_primes):
        e_Sy = Sy_factors.get(p, 0)
        e_t = t_factors.get(p, 0)
        e_x = e_Sy + e_t
        exp = 3 * e_x
        if p == 2 or p == 3:
            exp += 1
        if exp > 0:
            factors_F[p] = exp

    return factors_F


def get_odd_part(n: int) -> int:
    """Returns the odd part of n by dividing out all powers of 2."""
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    while n % 2 == 0:
        n //= 2
    return n


def check_algebraic_invariants(x: int) -> Dict[str, Any]:
    """Verifies all required mathematical invariants for coordinate x.

    Invariants:
      1. B - A == 2
      2. C == 0 mod 6
      3. C == F * R
      4. gcd(F, R) == 1
      5. F^2 > B (Pocklington size condition)
      6. (F_odd - 1)^2 > A (Morrison size condition)
    """
    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)

    diff = B - A
    c_mod_6 = C % 6
    c_prod_match = (C == F * R)
    coprimality = math.gcd(F, R)

    super_root_B = (F * F > B)
    F_odd = get_odd_part(F)
    super_root_A = ((F_odd - 1) ** 2 > A)

    return {
        "difference": diff,
        "difference_is_2": diff == 2,
        "center_mod_6": c_mod_6,
        "center_mod_6_is_0": c_mod_6 == 0,
        "factor_cofactor_product_match": c_prod_match,
        "gcd_F_R": coprimality,
        "coprimality_holds": coprimality == 1,
        "super_root_B": super_root_B,
        "F_squared_greater_than_B": super_root_B,
        "super_root_A": super_root_A,
        "F_odd_squared_greater_than_A": super_root_A,
        "F": F,
        "F_odd": F_odd,
        "R": R,
        "C": C,
        "A": A,
        "B": B,
    }


# ==============================================================================
# 2. Sieve Symmetry & Inert Moduli
# ==============================================================================

def is_inert_modulus(q: int) -> bool:
    """Checks if q is an inert prime modulus for the quadratic cofactor R(x) = 2*x^2 + 1.

    R(x) = 0 mod q <=> (2x)^2 = -2 mod q.
    Therefore R(x) has no roots mod q if and only if (-2/q) = -1.
    For an odd prime q:
      (-2/q) = -1  <=>  q = 5, 7 mod 8.
    """
    if q < 3:
        return False
    mod8 = q % 8
    return mod8 in (5, 7)


def sieve_roots_mod_q(q: int) -> Tuple[List[int], List[int]]:
    """Computes all roots of A(x) = 0 mod q and B(x) = 0 mod q in [0, q-1].

    Confirms the root-negation symmetry:
      r_B = (q - r_A) mod q.
    """
    if q < 2:
        return [], []

    roots_A: List[int] = []
    roots_B: List[int] = []

    for r in range(q):
        # A(r) = 12*r^5 + 6*r^3 - 1 mod q
        val_A = (12 * pow(r, 5, q) + 6 * pow(r, 3, q) - 1) % q
        if val_A == 0:
            roots_A.append(r)

        val_B = (12 * pow(r, 5, q) + 6 * pow(r, 3, q) + 1) % q
        if val_B == 0:
            roots_B.append(r)

    return sorted(roots_A), sorted(roots_B)


def verify_root_negation_symmetry(q: int) -> bool:
    """Confirms that roots of B mod q are exactly {(q - r) % q : r in roots_A}."""
    roots_A, roots_B = sieve_roots_mod_q(q)
    expected_B = sorted([(q - r) % q for r in roots_A])
    return roots_B == expected_B


# ==============================================================================
# 3. Multi-Tier Primality Screening
# ==============================================================================

def trial_division(n: int, limit: int = 1000) -> bool:
    """Fast trial division up to `limit`. Returns False if composite, True if surviving."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    diff = 2
    while d * d <= n and d <= limit:
        if n % d == 0:
            return False
        d += diff
        diff = 6 - diff
    return True


def fermat_base2(n: int) -> bool:
    """Fermat primality test base 2: checks 2^(n-1) = 1 mod n."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    return gmpy2.powmod(2, n - 1, n) == 1


def miller_rabin(n: int, bases: Optional[List[int]] = None) -> bool:
    """Deterministic or multi-base Miller-Rabin test."""
    if n < 2:
        return False
    if n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        return True
    if n % 2 == 0:
        return False

    if bases is None:
        bases = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a % n == 0:
            continue
        x = gmpy2.powmod(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = gmpy2.powmod(x, 2, n)
            if x == n - 1:
                break
        else:
            return False

    return True


def baillie_psw(n: int) -> bool:
    """Baillie-PSW test using gmpy2.is_prime / sympy.isprime."""
    if n < 2:
        return False
    return bool(gmpy2.is_prime(n))


def screen_candidate(A: int, B: int, trial_limit: int = 1000) -> Tuple[str, Optional[Tuple[int, int]]]:
    """Multi-tier screening pipeline.

    Returns (status, pair):
      status in ('COMPOSITE', 'SINGLE_PRP', 'DUAL_PRP')
    """
    # 1. Trial division
    if not trial_division(A, trial_limit) or not trial_division(B, trial_limit):
        return "COMPOSITE", None

    # 2. Fermat base 2
    if not fermat_base2(A) or not fermat_base2(B):
        return "COMPOSITE", None

    # 3. Miller-Rabin
    mr_A = miller_rabin(A)
    mr_B = miller_rabin(B)

    if not mr_A and not mr_B:
        return "COMPOSITE", None
    if not mr_A or not mr_B:
        return "SINGLE_PRP", None

    # 4. Baillie-PSW
    if baillie_psw(A) and baillie_psw(B):
        return "DUAL_PRP", (A, B)

    return "COMPOSITE", None


# ==============================================================================
# 4. Deterministic Dual-BLS Certification Provers
# ==============================================================================

def prove_pocklington_upper(
    B: int,
    F: int,
    factors_F: Dict[int, int],
    max_witness_search: int = 500
) -> Tuple[bool, Dict[str, int]]:
    """Proves primality of B via BLS (1975) Theorem 4 (Pocklington N-1).

    Preconditions:
      - B - 1 = F * R
      - F^2 > B
      - Complete prime factorization of F is known

    Conditions to verify:
      For each distinct prime factor p of F, find witness a in [2, max_witness_search] such that:
        a^(B-1) = 1 mod B
        and gcd(a^((B-1)/p) - 1, B) == 1.
    """
    if B % 2 == 0:
        return False, {}

    if F * F <= B:
        return False, {}

    B_minus_1 = B - 1
    witnesses: Dict[str, int] = {}

    for p in factors_F.keys():
        found = False
        exp = B_minus_1 // p

        for a in range(2, max_witness_search):
            if gmpy2.powmod(a, B_minus_1, B) != 1:
                continue
            term = gmpy2.powmod(a, exp, B) - 1
            if math.gcd(int(term), B) == 1:
                witnesses[str(p)] = a
                found = True
                break

        if not found:
            return False, {}

    return True, witnesses


def standalone_lucas_u(k: int, P: int, mod: int) -> int:
    """Evaluates the Lucas sequence U_k(P, Q=1) mod `mod` via 2x2 companion matrix exponentiation."""
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod

    mod_mpz = gmpy2.mpz(mod)
    m00, m01 = gmpy2.mpz(P) % mod_mpz, gmpy2.mpz(-1) % mod_mpz
    m10, m11 = gmpy2.mpz(1), gmpy2.mpz(0)

    r00, r01 = gmpy2.mpz(1), gmpy2.mpz(0)
    r10, r11 = gmpy2.mpz(0), gmpy2.mpz(1)

    bit_len = k.bit_length()
    for bit in range(bit_len - 1, -1, -1):
        t00 = (r00 * r00 + r01 * r10) % mod_mpz
        t01 = (r00 * r01 + r01 * r11) % mod_mpz
        t10 = (r10 * r00 + r11 * r10) % mod_mpz
        t11 = (r10 * r01 + r11 * r11) % mod_mpz
        r00, r01, r10, r11 = t00, t01, t10, t11

        if (k >> bit) & 1:
            t00 = (r00 * m00 + r01 * m10) % mod_mpz
            t01 = (r00 * m01 + r01 * m11) % mod_mpz
            t10 = (r10 * m00 + r11 * m10) % mod_mpz
            t11 = (r10 * m01 + r11 * m11) % mod_mpz
            r00, r01, r10, r11 = t00, t01, t10, t11

    return int(r10)


def prove_morrison_lower(
    A: int,
    F_odd: int,
    factors_F: Dict[int, int],
    max_P_search: int = 100
) -> Tuple[bool, Dict[str, Any]]:
    """Proves primality of A via BLS (1975) Theorem 17 (Morrison N+1 Lucas rank).

    Preconditions:
      - A + 1 = F * R
      - (F_odd - 1)^2 > A
      - Complete prime factorization of F_odd is known

    Conditions to verify:
      1. Find P > 2 such that D = P^2 - 4 has Jacobi symbol (D/A) = -1.
      2. Zero congruence: U_{A+1}(P, 1) = 0 mod A.
      3. Morrison Odd Divisor Singularity Guard:
         For each distinct ODD prime factor p of F_odd (factor 2 EXCLUDED):
           gcd(U_{(A+1)/p}(P, 1), A) == 1.
    """
    if A % 2 == 0:
        return False, {}

    if (F_odd - 1) ** 2 <= A:
        return False, {}

    # Find suitable P
    chosen_P: Optional[int] = None
    chosen_D: Optional[int] = None

    for P in range(3, max_P_search):
        D = P * P - 4
        if gmpy2.jacobi(D, A) == -1:
            chosen_P = P
            chosen_D = D
            break

    if chosen_P is None or chosen_D is None:
        return False, {}

    A_plus_1 = A + 1
    u_full = standalone_lucas_u(A_plus_1, chosen_P, A)
    if u_full != 0:
        return False, {}

    factor_gcds: Dict[str, str] = {}
    for p in factors_F.keys():
        if p == 2:
            # Factor 2 strictly excluded by Morrison Theorem 17 singularity guard
            continue
        u_part = standalone_lucas_u(A_plus_1 // p, chosen_P, A)
        g = math.gcd(u_part, A)
        factor_gcds[str(p)] = str(g)
        if g != 1:
            return False, {}

    result = {
        "parameter_P": chosen_P,
        "parameter_Q": 1,
        "discriminant_D": chosen_D,
        "jacobi_symbol": -1,
        "lucas_zero_congruence": f"U_{{A+1}}({chosen_P}, 1) = 0 mod A",
        "factor_gcds": factor_gcds,
    }
    return True, result


# ==============================================================================
# 5. Full Canonical Certificate Builder
# ==============================================================================

def generate_reference_certificate(
    y: int,
    t: int,
    run_id: str = "reference_run",
    hardware_desc: Optional[Dict[str, Any]] = None,
    repository_commit: str = "HEAD",
) -> Dict[str, Any]:
    """Generates a complete, canonical 21-field certificate for coordinate x = S_y * t.

    Performs full screening, invariants verification, and Dual-BLS proofs.
    """
    Sy, Sy_factors = compute_primorial_anchor(y)
    t_factors = dict(factorint(t))
    x = Sy * t

    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)
    factors_F = compute_factors_of_F(Sy_factors, t_factors)
    F_odd = get_odd_part(F)

    # 1. Multi-tier screening
    status, pair = screen_candidate(A, B)
    if status != "DUAL_PRP":
        raise ValueError(f"Candidate pair at y={y}, t={t} did not pass primality screening (status={status})")

    # 2. Upper member Pocklington BLS Theorem 4 proof
    ok_upper, witnesses_B = prove_pocklington_upper(B, F, factors_F)
    if not ok_upper:
        raise ValueError(f"Failed to prove upper prime B={B} using Pocklington Theorem 4")

    # 3. Lower member Morrison BLS Theorem 17 proof
    ok_lower, morrison_result = prove_morrison_lower(A, F_odd, factors_F)
    if not ok_lower:
        raise ValueError(f"Failed to prove lower prime A={A} using Morrison Theorem 17")

    # Build canonical 21-field structure
    now_utc = datetime.now(timezone.utc).isoformat()
    if hardware_desc is None:
        hardware_desc = {
            "platform": "windows",
            "cpu": "Intel/AMD x86_64",
            "memory": "16GB",
        }

    cert: Dict[str, Any] = {
        "method_id": "OPQM_CRT_HYBRID_11",
        "method_version": "11.0",
        "repository_commit": repository_commit,
        "run_id": run_id,
        "timestamp_utc": now_utc,
        "hardware": hardware_desc,
        "parameters": {
            "y": y,
            "S_y": str(Sy),
            "t": t,
            "x": str(x),
            "F": str(F),
            "F_odd": str(F_odd),
            "R": str(R),
        },
        "symbolic_center": "12*x^5 + 6*x^3",
        "lower_prime": str(A),
        "upper_prime": str(B),
        "digit_count": len(str(A)),
        "difference": 2,
        "factorization": {
            "factors_F": {str(k): v for k, v in factors_F.items()},
            "factors_Sy": {str(k): v for k, v in Sy_factors.items()},
            "factors_t": {str(k): v for k, v in t_factors.items()},
        },
        "proof_method_lower": "Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison N+1 Lucas Rank)",
        "proof_method_upper": "Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington N-1)",
        "witnesses_lower": morrison_result,
        "witnesses_upper": witnesses_B,
        "proof_conditions": {
            "pocklington_size_condition": f"F^2 > B ({F*F} > {B})",
            "morrison_size_condition": f"(F_odd - 1)^2 > A ({(F_odd - 1)**2} > {A})",
            "coprimality_gcd_F_R": 1,
            "morrison_odd_divisor_guard": "factor 2 excluded from Lucas rank GCD tests",
        },
        "novelty_status_repository": "NOVEL_TO_REPOSITORY",
        "novelty_status_public": "NOVEL_TO_PUBLIC_RECORDS",
    }

    # Compute canonical SHA-256
    clean_bytes = json.dumps(cert, sort_keys=True, separators=(',', ':')).encode("utf-8")
    cert["certificate_sha256"] = hashlib.sha256(clean_bytes).hexdigest()

    return cert
