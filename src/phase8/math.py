"""
Mathematical Foundations for Phase 8 ADES-8 Architecture.
Implements:
- Odd primorial multiplier computation M_R = product_{3 <= p <= R} p
- Exact parameter boundary solving for target digit bands (10^(D-1)+1 <= C <= 10^D-2)
- ADES-8 modular root recurrence:
    a_{n+1} = a_n * 2^(-1) mod r
    t_{minus} = (a_n - 1) * 2^(-1) mod r  (r | C - 1)
    t_{plus}  = (-a_n - 1) * 2^(-1) mod r (r | C + 1)
- Jacobi symbol and Lucas V_k sequences (Montgomery ladder and 2x2 companion matrix)
- Deterministic 64-bit Miller-Rabin primality test
"""

import math
from typing import Tuple, List, Optional

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False


def get_small_primes(limit: int) -> List[int]:
    """Generates all prime numbers up to limit via simple eratosthenes sieve."""
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            sieve[i * i : limit + 1 : i] = bytearray(len(range(i * i, limit + 1, i)))
    return [i for i, is_p in enumerate(sieve) if is_p]


def get_primorial_multiplier(R: int) -> int:
    """
    Computes odd primorial multiplier M_R = product of odd primes 3 <= p <= R.
    For R < 3, returns 1.
    """
    if R < 3:
        return 1
    primes = get_small_primes(R)
    m = 1
    for p in primes:
        if 3 <= p <= R:
            m *= p
    return m


def exact_digit_t_bounds(D: int, M: int, n: int) -> Tuple[int, int, int, int]:
    """
    Computes exact integer bounds for k and t such that:
    10^(D-1) + 1 <= C <= 10^D - 2 where C = k * 2^n and k = M * (2t + 1).
    Enforces k < 2^n.
    Returns (k_min, k_max, t_min, t_max).
    If bounds are empty or k < 2^n is impossible, returns (0, -1, 0, -1).
    """
    two_n = 1 << n
    low_C = 10**(D - 1) + 1
    high_C = 10**D - 2

    k_min = (low_C + two_n - 1) // two_n
    k_max = min((high_C) // two_n, two_n - 1)

    if k_min > k_max:
        return 0, -1, 0, -1

    # k = M * (2t + 1)
    odd_min = (k_min + M - 1) // M
    if odd_min % 2 == 0:
        odd_min += 1
    t_min = (odd_min - 1) // 2

    odd_max = k_max // M
    if odd_max % 2 == 0:
        odd_max -= 1
    t_max = (odd_max - 1) // 2

    if t_min > t_max:
        return 0, -1, 0, -1

    return k_min, k_max, t_min, t_max


def solve_modular_roots(M: int, n: int, r: int) -> Tuple[int, int]:
    """
    Direct modular root solver for sieve prime r (r does not divide 2*M):
    alpha = (M * 2^n) mod r
    u = alpha^(-1) mod r
    b = 2^(-1) mod r
    t_minus = ((u - 1) * b) mod r -> r | (C - 1) = A
    t_plus  = ((-u - 1) * b) mod r -> r | (C + 1) = B'
    """
    alpha = (M * pow(2, n, r)) % r
    u = pow(alpha, -1, r)
    b = pow(2, -1, r)
    t_minus = ((u - 1) * b) % r
    t_plus = ((-u - 1) * b) % r
    return t_minus, t_plus


def ades8_recurrence_step(a_n: int, b_r: int, r: int) -> int:
    """
    Computes a_{n+1} from a_n using modular multiplication:
    a_{n+1} = (a_n * b_r) mod r, where b_r = 2^(-1) mod r.
    Cost: exactly 1 multiplication and 1 reduction in Z/rZ.
    """
    return (a_n * b_r) % r


def ades8_roots_from_a(a_n: int, b_r: int, r: int) -> Tuple[int, int]:
    """
    Computes the pair of root residues (t_minus, t_plus) from a_n and b_r:
    t_minus = ((a_n - 1) * b_r) mod r  -> r | (C - 1)
    t_plus  = ((-a_n - 1) * b_r) mod r -> r | (C + 1)
    """
    t_minus = ((a_n - 1) * b_r) % r
    t_plus = ((-a_n - 1) * b_r) % r
    return t_minus, t_plus


def compute_candidate_pair(M: int, t: int, n: int) -> Tuple[int, int, int, int]:
    """
    Computes exact integers k, C, A, B' from primorial parameters:
    k = M * (2t + 1)
    C = k * 2^n
    A = C - 1
    B' = C + 1
    """
    k = M * (2 * t + 1)
    two_n = 1 << n
    if k >= two_n:
        raise ValueError(f"Theorem requirement k < 2^n violated: k={k} >= 2^{n}")
    C = k * two_n
    return k, C, C - 1, C + 1


def jacobi_symbol(a: int, n: int) -> int:
    """Computes Jacobi symbol (a / n) for positive odd n."""
    if n <= 0 or n % 2 == 0:
        raise ValueError(f"Jacobi symbol requires positive odd modulus, got {n}")
    if HAVE_GMPY2:
        return int(gmpy2.jacobi(a, n))

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
    Computes Lucas sequence term V_k(P, 1) mod mod using Montgomery binary ladder.
    V_0 = 2, V_1 = P, V_{2m} = V_m^2 - 2, V_{2m+1} = V_m * V_{m+1} - P.
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod

    v0 = P % mod
    v1 = (pow(P, 2, mod) - 2) % mod

    bits = bin(k)[3:]  # Skip '0b1'
    for bit in bits:
        if bit == '1':
            v0 = (v0 * v1 - P) % mod
            v1 = (pow(v1, 2, mod) - 2) % mod
        else:
            v1 = (v0 * v1 - P) % mod
            v0 = (pow(v0, 2, mod) - 2) % mod

    return v0


def lucas_v_matrix(k: int, P: int, mod: int) -> int:
    """
    Independent 2x2 companion matrix powering for Lucas V_k(P, 1) mod mod.
    Companion matrix M = [[P, -1], [1, 0]].
    [V_k, V_{k-1}]^T = M^(k-1) * [P, 2]^T.
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod

    def mat_mul_2x2(A, B, m):
        return [
            [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % m, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % m],
            [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % m, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % m]
        ]

    base = [[P % mod, (-1) % mod], [1, 0]]
    res = [[1, 0], [0, 1]]
    exp = k - 1
    while exp > 0:
        if exp % 2 == 1:
            res = mat_mul_2x2(res, base, mod)
        base = mat_mul_2x2(base, base, mod)
        exp //= 2

    vk = (res[0][0] * P + res[0][1] * 2) % mod
    return vk


def deterministic_miller_rabin_64(n: int) -> bool:
    """
    Deterministic Miller-Rabin test for integers n < 2^64.
    Uses the 7-base set from Jiang & Deng (2014):
    {2, 325, 9375, 28178, 450775, 9780504, 1795265022}.
    Guaranteed deterministic with zero false positives or negatives for 64-bit integers.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a % n == 0:
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
