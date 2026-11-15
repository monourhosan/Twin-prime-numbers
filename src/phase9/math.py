"""
Phase 9 Core Mathematical Utilities.
Implements:
- Canonical cubic manifold construction: C(x) = 2*x^2*(3x + 1), A = C - 1, B = C + 1
- Modular cubic root solving over F_q for 6x^3 + 2x^2 +/- 1 = 0 mod q
- Forbidden residue mapping for multiplier t mod q
- Fast arbitrary-precision Lucas sequence evaluation U_k(P, Q) mod N via 2x2 companion matrix powering
- Morrison-BLS parameter discovery ((D/A) = -1)
"""

import math
from typing import List, Tuple, Set, Dict, Optional
import gmpy2
import sympy as sp


def construct_pair(x: int) -> Tuple[int, int, int]:
    """
    Given x, constructs (C, A, B) on the cubic manifold:
      C = 2 * x^2 * (3x + 1) = 6x^3 + 2x^2
      A = C - 1
      B = C + 1
    Guarantees:
      B - A = 2
      If 3 | x and 2 | x, then 6 | C, so A and B are odd and coprime to 3.
    """
    x_mpz = gmpy2.mpz(x)
    x2 = x_mpz * x_mpz
    C = 2 * x2 * (3 * x_mpz + 1)
    A = C - 1
    B = C + 1
    return int(C), int(A), int(B)


def solve_cubic_roots_mod_q(q: int, sign: int) -> List[int]:
    """
    Finds all roots x in F_q of 6x^3 + 2x^2 + sign = 0 mod q,
    where sign in {-1, +1} and q > 3 is prime.
    Returns sorted list of distinct root integers in [0, q-1].
    """
    assert q > 3, "Sieve prime q must be > 3"
    assert sign in (-1, 1), "sign must be -1 or +1"

    # Fast sympy GF(q) solver
    x_sym = sp.Symbol('x')
    poly = sp.Poly(6 * x_sym**3 + 2 * x_sym**2 + sign, x_sym, domain=sp.GF(q))
    roots = [int(r % q) for r in poly.ground_roots().keys()]
    return sorted(roots)


def get_forbidden_t_residues(q: int, S_y_mod_q: int) -> Set[int]:
    """
    Computes all forbidden residue classes t mod q such that
    either A(t) = 0 mod q or B(t) = 0 mod q, where x = S_y * t.
    Assumes q is an odd prime not dividing S_y (gcd(S_y, q) == 1).
    """
    inv_Sy = int(gmpy2.invert(S_y_mod_q, q))
    roots_t: Set[int] = set()

    # Roots for B: 6x^3 + 2x^2 + 1 = 0 mod q
    r_B = solve_cubic_roots_mod_q(q, sign=1)
    for rx in r_B:
        rt = (rx * inv_Sy) % q
        roots_t.add(rt)

    # Roots for A: 6x^3 + 2x^2 - 1 = 0 mod q
    r_A = solve_cubic_roots_mod_q(q, sign=-1)
    for rx in r_A:
        rt = (rx * inv_Sy) % q
        roots_t.add(rt)

    return roots_t


def lucas_u_mod(P: int, Q: int, k: int, mod: int) -> int:
    """
    Evaluates the Lucas sequence element U_k(P, Q) mod 'mod'
    using 2x2 companion matrix exponentiation.
    Initial state: U_0 = 0, U_1 = 1.
    Companion matrix M = [[P, -Q], [1, 0]] satisfies:
      M^k * [U_1, U_0]^T = [U_{k+1}, U_k]^T.
    Returns U_k mod 'mod'.
    """
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod

    m00, m01 = P % mod, (-Q) % mod
    m10, m11 = 1, 0

    r00, r01 = 1, 0
    r10, r11 = 0, 1

    bit_len = k.bit_length()
    for bit in range(bit_len - 1, -1, -1):
        # Square R
        t00 = (r00 * r00 + r01 * r10) % mod
        t01 = (r00 * r01 + r01 * r11) % mod
        t10 = (r10 * r00 + r11 * r10) % mod
        t11 = (r10 * r01 + r11 * r11) % mod
        r00, r01, r10, r11 = t00, t01, t10, t11

        if (k >> bit) & 1:
            # Multiply R by M
            t00 = (r00 * m00 + r01 * m10) % mod
            t01 = (r00 * m01 + r01 * m11) % mod
            t10 = (r10 * m00 + r11 * m10) % mod
            t11 = (r10 * m01 + r11 * m11) % mod
            r00, r01, r10, r11 = t00, t01, t10, t11

    return r10


def find_morrison_params(
    A: int,
    odd_factors: Optional[List[int]] = None,
    max_search: int = 500
) -> Tuple[int, int]:
    """
    Finds integer P such that D = P^2 - 4 satisfies Jacobi symbol (D / A) == -1.
    If odd_factors is provided, also ensures that:
      U_{A+1}(P, 1) == 0 mod A, and
      gcd(U_{(A+1)/q}(P, 1), A) == 1 for all q in odd_factors.
    Uses parameter Q = 1.
    Returns (P, D).
    """
    A_plus_1 = A + 1
    for P in range(3, max_search):
        D = P * P - 4
        is_sq = gmpy2.is_square(D)
        if not is_sq:
            if gmpy2.jacobi(D, A) == -1:
                if odd_factors:
                    u_full = lucas_u_mod(P, 1, A_plus_1, A)
                    if u_full != 0:
                        continue
                    # Check gcd for all odd factors
                    all_gcds_one = True
                    for q in odd_factors:
                        u_part = lucas_u_mod(P, 1, A_plus_1 // q, A)
                        if math.gcd(u_part, A) != 1:
                            all_gcds_one = False
                            break
                    if all_gcds_one:
                        return P, D
                else:
                    return P, D
    raise RuntimeError(f"Failed to find Morrison parameter P for A={A} within P < {max_search}")
