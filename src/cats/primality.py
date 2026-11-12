"""
Primality testing and deterministic certification module for CATS.
"""

from typing import Optional, Tuple, List, Dict, Any
import numpy as np

def generate_primes(limit: int) -> np.ndarray:
    """Generates all primes <= limit using a fast NumPy sieve."""
    if limit < 2:
        return np.array([], dtype=np.int64)
    s = np.ones(limit + 1, dtype=bool)
    s[:2] = False
    sqrt_limit = int(limit**0.5)
    for i in range(2, sqrt_limit + 1):
        if s[i]:
            s[i * i : limit + 1 : i] = False
    return np.flatnonzero(s)

def mod_inverse(a: int, m: int) -> Optional[int]:
    """Returns the multiplicative inverse of a modulo m."""
    try:
        return pow(a, -1, m)
    except (ValueError, ZeroDivisionError):
        return None

def jacobi_symbol(a: int, n: int) -> int:
    """Computes the Jacobi symbol (a / n) for positive odd n."""
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

def is_prime_u64(n: int) -> bool:
    """Deterministic Miller-Rabin test for integers up to 2^64."""
    if n < 2:
        return False
    if n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        return True
    if any(n % p == 0 for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)):
        return False

    # Bases sufficient for deterministic testing up to 2^64
    bases = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    s = (n - 1).bit_length() - (n - 1).bit_length()  # count trailing zeros
    trailing_zeros = (n - 1) & -(n - 1)
    s = trailing_zeros.bit_length() - 1
    d = (n - 1) >> s

    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
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

def is_probable_prime(n: int, bases: Optional[List[int]] = None) -> bool:
    """Strong Miller-Rabin probable prime test for arbitrary-precision integers."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    if bases is None:
        bases = [2, 3, 5, 7, 11]

    # Factor n - 1 as 2^s * d
    n_minus_1 = n - 1
    s = 0
    d = n_minus_1
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n_minus_1:
            continue
        composite = True
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n_minus_1:
                composite = False
                break
        if composite:
            return False
    return True

def proth_prove(k: int, n: int, B: int) -> Tuple[bool, Optional[int]]:
    """
    Applies Proth's Theorem to prove the primality of B = k * 2^n + 1 (k odd, k < 2^n).
    Returns (True, witness_a) if proven prime, (False, None) if proven composite.
    """
    if k % 2 == 0 or (n < 64 and k >= (1 << n)):
        return False, None

    exp = (B - 1) // 2
    candidates = [3, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31]
    for a in candidates:
        if jacobi_symbol(a, B) == -1:
            if pow(a, exp, B) == B - 1:
                return True, a
            else:
                # If Jacobi symbol is -1 and a^((B-1)/2) != -1 mod B,
                # then by Euler's criterion, B is unconditionally COMPOSITE.
                return False, None

    # Fallback base
    if pow(3, exp, B) == B - 1:
        return True, 3

    return False, None

def llr_prove(k: int, n: int, A: int) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Applies the Lucas-Lehmer-Riesel (LLR) test to prove primality of A = k * 2^n - 1 (k odd, k < 2^n).
    Returns (True, P, u0) if proven prime, (False, None, None) if proven composite.
    """
    if k % 2 == 0 or (n < 64 and k >= (1 << n)) or n < 2:
        return False, None, None

    # Find starting parameter P such that Jacobi(P - 2, A) = 1 and Jacobi(P + 2, A) = -1
    chosen_p = None
    for p_cand in [4, 3, 5, 6, 8, 9, 10, 12, 14, 15]:
        if jacobi_symbol(p_cand - 2, A) == 1 and jacobi_symbol(p_cand + 2, A) == -1:
            chosen_p = p_cand
            break
    if chosen_p is None:
        chosen_p = 4

    # Compute u0 = V_k(P, 1) mod A
    # Lucas V sequence: V_0 = 2, V_1 = P, V_{m+1} = P * V_m - V_{m-1} mod A
    v_prev = 2
    v_curr = chosen_p
    for _ in range(1, k):
        v_next = (chosen_p * v_curr - v_prev) % A
        v_prev = v_curr
        v_curr = v_next
    u0 = v_curr

    # Repeated squaring: u_{i+1} = (u_i^2 - 2) mod A for i in 0 .. n - 2
    u = u0
    for _ in range(n - 2):
        u = (pow(u, 2, A) - 2) % A

    if u == 0:
        return True, chosen_p, u0
    else:
        return False, None, None
