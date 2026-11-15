"""
PAQCS Core Mathematical Utilities (Phase 8).
Implements Tonelli-Shanks, modular quadratic root finding,
Lucas sequence evaluation, and exact integer pair construction.
"""

import math
from typing import List, Tuple, Set, Optional
import gmpy2


def tonelli_shanks(n: int, p: int) -> int:
    """
    Computes r such that r^2 = n mod p for odd prime p with (n/p) = 1.
    """
    if p % 4 == 3:
        return int(gmpy2.powmod(n, (p + 1) >> 2, p))

    # Factor p - 1 as s * 2^e
    s = p - 1
    e = 0
    while not (s & 1):
        s >>= 1
        e += 1

    # Find quadratic non-residue z
    z = 2
    while gmpy2.legendre(z, p) != -1:
        z += 1

    c = gmpy2.powmod(z, s, p)
    x = gmpy2.powmod(n, (s + 1) >> 1, p)
    t = gmpy2.powmod(n, s, p)
    m = e

    while t != 1:
        i = 1
        temp = (t * t) % p
        while temp != 1:
            temp = (temp * temp) % p
            i += 1
        b = gmpy2.powmod(c, 1 << (m - i - 1), p)
        x = (x * b) % p
        t = (t * b * b) % p
        c = (b * b) % p
        m = i

    return int(x)


def get_forbidden_t_residues(q: int, S_y_mod_q: int, h: int = 3) -> Set[int]:
    """
    Computes all forbidden residue classes t mod q such that
    either A = x(x-h)-1 = 0 mod q or B = x(x-h)+1 = 0 mod q,
    where x = S_y * t.
    Assumes q is an odd prime not dividing S_y (gcd(S_y, q) == 1).
    """
    inv_Sy = int(gmpy2.invert(S_y_mod_q, q))
    inv2 = int(gmpy2.invert(2, q))
    d_A = h * h + 4
    d_B = h * h - 4

    roots_t = set()

    # Roots for A: x^2 - hx - 1 = 0 mod q => (2x - h)^2 = h^2 + 4 mod q
    leg_A = gmpy2.legendre(d_A, q)
    if leg_A == 1:
        rA = tonelli_shanks(d_A, q)
        for r in (rA, q - rA):
            x = ((h + r) * inv2) % q
            t = (x * inv_Sy) % q
            roots_t.add(t)
    elif leg_A == 0:
        x = (h * inv2) % q
        t = (x * inv_Sy) % q
        roots_t.add(t)

    # Roots for B: x^2 - hx + 1 = 0 mod q => (2x - h)^2 = h^2 - 4 mod q
    leg_B = gmpy2.legendre(d_B, q)
    if leg_B == 1:
        rB = tonelli_shanks(d_B, q)
        for r in (rB, q - rB):
            x = ((h + r) * inv2) % q
            t = (x * inv_Sy) % q
            roots_t.add(t)
    elif leg_B == 0:
        x = (h * inv2) % q
        t = (x * inv_Sy) % q
        roots_t.add(t)

    return roots_t


def construct_pair(S_y: int, t: int, h: int = 3) -> Tuple[int, int, int, int]:
    """
    Given primorial anchor S_y, odd multiplier t, and odd multiple of 3 h,
    returns (x, C, A, B).
    """
    assert t % 2 == 1, "t must be odd"
    assert h % 2 == 1 and h % 3 == 0, "h must be odd multiple of 3"
    x = S_y * t
    C = x * (x - h)
    A = C - 1
    B = C + 1
    return x, C, A, B


def lucas_u_ladder(k: int, P: int, mod: int) -> int:
    """
    Computes Lucas sequence term U_k(P, 1) mod mod using fast binary ladder
    over (U_m, V_m) pairs with doubling and addition steps:
    U_{2m} = U_m * V_m (mod mod)
    V_{2m} = V_m^2 - 2 (mod mod)
    U_{2m+1} = (P * U_{2m} + V_{2m}) * 2^-1 (mod mod)
    V_{2m+1} = (D * U_{2m} + P * V_{2m}) * 2^-1 (mod mod)
    where D = P^2 - 4.
    """
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod

    D = P * P - 4
    inv2 = int(gmpy2.invert(2, mod))
    bits = bin(k)[2:]
    u = 0
    v = 2 % mod

    for bit in bits:
        u2 = (u * v) % mod
        v2 = (v * v - 2) % mod
        if bit == '1':
            u = ((P * u2 + v2) * inv2) % mod
            v = ((D * u2 + P * v2) * inv2) % mod
        else:
            u = u2
            v = v2
    return u
