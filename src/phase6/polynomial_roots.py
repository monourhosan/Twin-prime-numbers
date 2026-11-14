"""
Phase 6: Polynomial Modular Root Solver.
Solves quadratic and linear modular congruences to determine exact forbidden
residue classes for Method Q and Method R sieves.
"""

from typing import List, Set, Dict, Optional, Tuple
import gmpy2


def tonelli_shanks(n: int, p: int) -> Optional[int]:
    """
    Computes a modular square root r such that r^2 = n (mod p),
    where p is an odd prime. Returns None if n is a quadratic non-residue.
    """
    n = n % p
    if n == 0:
        return 0
    if p == 2:
        return n
    leg = gmpy2.legendre(n, p)
    if leg != 1:
        return None

    # Optimized branch: p = 3 (mod 4)
    if p % 4 == 3:
        return int(pow(n, (p + 1) // 4, p))

    # General Tonelli-Shanks algorithm
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1

    # Find non-residue z
    z = 2
    while gmpy2.legendre(z, p) != -1:
        z += 1

    c = pow(z, q, p)
    r = pow(n, (q + 1) // 2, p)
    t = pow(n, q, p)
    m = s

    while t != 1:
        temp = t
        i = 0
        for i in range(1, m):
            temp = (temp * temp) % p
            if temp == 1:
                break
        b = pow(c, 1 << (m - i - 1), p)
        r = (r * b) % p
        c = (b * b) % p
        t = (t * c) % p
        m = i

    return r


def compute_method_q_forbidden_j(q: int, h: int, S: int) -> List[int]:
    """
    Computes all forbidden residues j mod q for candidate parameter t = 2j + 1
    such that A = x^2 - hx - 1 = 0 (mod q) or B = x^2 - hx + 1 = 0 (mod q),
    where x = S * t.
    Returns sorted list of distinct forbidden j in [0, q - 1].
    """
    if q <= 3:
        return []
    if S % q == 0:
        # If q | S, x = 0 (mod q), so A = -1 (mod q) and B = +1 (mod q).
        # Neither can be 0 mod q for q >= 3.
        return []

    inv_2 = pow(2, -1, q)
    inv_S = pow(S, -1, q)

    D_A = (h * h + 4) % q
    D_B = (h * h - 4) % q

    roots_x: Set[int] = set()

    # Roots for A: x^2 - hx - 1 = 0 (mod q)
    leg_A = gmpy2.legendre(D_A, q)
    if leg_A == 1:
        sqrt_A = tonelli_shanks(D_A, q)
        if sqrt_A is not None:
            roots_x.add(((h + sqrt_A) * inv_2) % q)
            roots_x.add(((h - sqrt_A) * inv_2) % q)
    elif leg_A == 0:
        roots_x.add((h * inv_2) % q)

    # Roots for B: x^2 - hx + 1 = 0 (mod q)
    leg_B = gmpy2.legendre(D_B, q)
    if leg_B == 1:
        sqrt_B = tonelli_shanks(D_B, q)
        if sqrt_B is not None:
            roots_x.add(((h + sqrt_B) * inv_2) % q)
            roots_x.add(((h - sqrt_B) * inv_2) % q)
    elif leg_B == 0:
        roots_x.add((h * inv_2) % q)

    # Map x roots to t, then to j where t = 2j + 1
    # t = x * S^-1 (mod q)
    # 2j = t - 1 (mod q) => j = (t - 1) * 2^-1 (mod q)
    forbidden_j: Set[int] = set()
    for rx in roots_x:
        rt = (rx * inv_S) % q
        rj = ((rt - 1) * inv_2) % q
        forbidden_j.add(rj)

    return sorted(forbidden_j)


def compute_method_r_forbidden_j(q: int, C0: int) -> List[int]:
    """
    For Method R: C = C0 + 6j, A = C - 1, B = C + 1.
    A = 0 (mod q) => 6j = 1 - C0 (mod q) => j = (1 - C0) * 6^-1 (mod q)
    B = 0 (mod q) => 6j = -1 - C0 (mod q) => j = (-1 - C0) * 6^-1 (mod q)
    """
    if q <= 3:
        return []
    inv_6 = pow(6, -1, q)
    j_A = ((1 - C0) * inv_6) % q
    j_B = ((-1 - C0) * inv_6) % q
    if j_A == j_B:
        return [j_A]
    return sorted([j_A, j_B])
