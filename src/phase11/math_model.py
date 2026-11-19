"""Phase 11 Production Arbitrary-Precision Mathematical Engine Core (OPQM-11).

Odd-Parity Quintic Manifold with CRT-Kernel Inverse Sieve:
  C(x) = 12*x^5 + 6*x^3 = 6*x^3 * (2*x^2 + 1)
  A(x) = C(x) - 1
  B(x) = C(x) + 1
  where x = S_y * t.

AST Constraint: Strictly ZERO float() conversions permitted in this module.
All calculations use exact arbitrary-precision integer arithmetic (int, gmpy2.mpz).
"""

from typing import Any

import gmpy2
from sympy.ntheory import primerange


def compute_primorial(y: int) -> int:
    """Computes exact primorial S_y = product_{p <= y} p.

    Requires y >= 3 so that 2 * 3 = 6 divides S_y.
    """
    if y < 3:
        raise ValueError(f"Anchor prime y must be >= 3 to ensure 6 | S_y, got {y}")
    prod = 1
    for p in primerange(2, y + 1):
        prod *= p
    return int(prod)


def compute_manifold(x: int) -> tuple[int, int, int]:
    """Computes manifold coordinates (C, A, B) on the OPQM manifold for coordinate x.

    C(x) = 12*x^5 + 6*x^3
    A(x) = C(x) - 1
    B(x) = C(x) + 1
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    x_mpz = gmpy2.mpz(x)
    x3 = x_mpz ** 3
    x5 = x3 * (x_mpz ** 2)
    C = 12 * x5 + 6 * x3
    A = C - 1
    B = C + 1
    return int(C), int(A), int(B)


def compute_candidate_pair(y: int, t: int) -> tuple[int, int, int]:
    """Computes (C, A, B) for anchor prime y and multiplier t.

    Coordinate x = S_y * t.
    Interface contract for Phase11ContractAdapter.
    """
    if y < 3:
        raise ValueError(f"Anchor y must be >= 3, got {y}")
    if t <= 0:
        raise ValueError(f"Multiplier t must be positive, got {t}")
    Sy = compute_primorial(y)
    x = Sy * t
    return compute_manifold(x)


def compute_divisor_and_cofactor(x: int) -> tuple[int, int]:
    """Computes algebraic divisor F(x) = 6*x^3 and cofactor R(x) = 2*x^2 + 1."""
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    x_mpz = gmpy2.mpz(x)
    F = 6 * (x_mpz ** 3)
    R = 2 * (x_mpz ** 2) + 1
    return int(F), int(R)


def get_odd_part(n: int) -> int:
    """Returns the odd part of n by dividing out all factors of 2."""
    if n <= 0:
        raise ValueError(f"Number n must be positive, got {n}")
    tz = (n & -n).bit_length() - 1
    return n >> tz


def check_algebraic_invariants(x: int) -> dict[str, Any]:
    """Verifies all algebraic invariants for integer coordinate x:

    1. B - A == 2
    2. C % 6 == 0
    3. C == F * R
    4. gcd(F, R) == 1
    5. F^2 > B (Pocklington dominance, holds for all x >= 1)
    6. (F_odd - 1)^2 > A (Morrison dominance, holds for x >= 86 when nu_2(x) == 1)
    """
    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)
    diff = B - A
    c_mod_6 = C % 6
    c_prod_match = (C == F * R)
    coprimality = int(gmpy2.gcd(F, R))
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
