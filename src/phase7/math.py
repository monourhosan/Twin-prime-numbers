"""
Number-Theoretic and Mathematical Foundations for HDC-7.
Implements:
- Primorial multiplier computation M_B
- Exact parameter boundary solving for D-digit targets (10^(D-1)+1 <= C <= 10^D-2)
- Modular root solving for compact t-space sieve (t_plus, t_minus mod r)
- Jacobi symbol and Lucas V_k sequences (both Montgomery ladder and 2x2 matrix powering)
- Deterministic 64-bit Miller-Rabin test (Jiang & Deng 2014)
"""

import math
from typing import Tuple, List, Optional

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False


def get_small_primes(limit: int) -> List[int]:
    """Generates all primes up to limit via simple sieve."""
    if limit < 2:
        return []
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]


def get_primorial_multiplier(B: int) -> int:
    """
    Computes odd primorial multiplier M_B = product of odd primes 3 <= p <= B.
    For B < 3, returns 1.
    """
    if B < 3:
        return 1
    primes = get_small_primes(B)
    mb = 1
    for p in primes:
        if 3 <= p <= B:
            mb *= p
    return mb


def exact_digit_t_bounds(D: int, MB: int, n: int) -> Tuple[int, int, int, int]:
    """
    Computes exact integer bounds for k and t such that:
    10^(D-1) + 1 <= C <= 10^D - 2 where C = k * 2^n and k = MB * (2t + 1).
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

    # k = MB * (2t + 1)
    # 2t + 1 >= ceil(k_min / MB)
    odd_min = (k_min + MB - 1) // MB
    if odd_min % 2 == 0:
        odd_min += 1
    t_min = (odd_min - 1) // 2

    odd_max = k_max // MB
    if odd_max % 2 == 0:
        odd_max -= 1
    t_max = (odd_max - 1) // 2

    if t_min > t_max:
        return 0, -1, 0, -1

    return k_min, k_max, t_min, t_max


def solve_modular_roots(MB: int, n: int, r: int) -> Tuple[int, int]:
    """
    Solves the two modular roots in compact t-space for sieve prime r (r does not divide 2*MB):
    alpha = (MB * 2^n) % r
    u = alpha^(-1) % r
    t_plus  = ((u - 1) * 2^(-1)) % r  -> C = +1 mod r -> r | (C - 1) = A
    t_minus = ((-u - 1) * 2^(-1)) % r -> C = -1 mod r -> r | (C + 1) = B'
    """
    alpha = (MB * pow(2, n, r)) % r
    u = pow(alpha, -1, r)
    inv_2 = pow(2, -1, r)
    t_plus = ((u - 1) * inv_2) % r
    t_minus = ((-u - 1) * inv_2) % r
    return t_plus, t_minus


def compute_candidate_pair(MB: int, t: int, n: int) -> Tuple[int, int, int, int]:
    """
    Computes exact integers k, C, A, B' from primorial parameters:
    k = MB * (2t + 1)
    C = k * 2^n
    A = C - 1
    B' = C + 1
    """
    k = MB * (2 * t + 1)
    two_n = 1 << n
    if k >= two_n:
        raise ValueError(f"Theorem requirement k < 2^n violated: k={k} >= 2^{n}")
    C = k * two_n
    return k, C, C - 1, C + 1


def jacobi_symbol(a: int, n: int) -> int:
    """Computes Jacobi symbol (a / n) for positive odd n from first principles."""
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

    bits = bin(k)[3:]
    for bit in bits:
        if bit == '1':
            v0 = (v0 * v1 - P) % mod
            v1 = (pow(v1, 2, mod) - 2) % mod
        else:
            v1 = (v0 * v1 - P) % mod
            v0 = (pow(v0, 2, mod) - 2) % mod
    return v0


def matrix_mult_2x2(A, B, mod):
    return [
        [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % mod, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % mod],
        [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % mod, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % mod]
    ]


def matrix_pow_2x2(M, power, mod):
    result = [[1, 0], [0, 1]]
    base = [[M[0][0] % mod, M[0][1] % mod], [M[1][0] % mod, M[1][1] % mod]]
    p = power
    while p > 0:
        if p & 1:
            result = matrix_mult_2x2(result, base, mod)
        base = matrix_mult_2x2(base, base, mod)
        p >>= 1
    return result


def lucas_v_matrix(k: int, P: int, mod: int) -> int:
    """
    Computes V_k(P, 1) mod mod using 2x2 companion matrix powering.
    Serves as an independent mathematical oracle for Montgomery ladder.
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod
    M = [[P % mod, (-1) % mod], [1, 0]]
    Mk = matrix_pow_2x2(M, k, mod)
    return (Mk[1][0] * (P % mod) + Mk[1][1] * 2) % mod


def miller_rabin_deterministic_64(n: int) -> bool:
    """
    Jiang & Deng (2014) / Sinclair (2011) deterministic Miller-Rabin test
    for n < 2^64 using 7 proven bases:
    [2, 325, 9375, 28178, 450775, 9780504, 1795265022].
    Provably zero pseudoprimes below 2^64.
    """
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for sp in small_primes:
        if n == sp:
            return True
        if n % sp == 0:
            return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
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
