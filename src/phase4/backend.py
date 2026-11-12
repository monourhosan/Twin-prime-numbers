"""
Phase 4 Multiprecision Arithmetic Backend Adapter.
Provides high-performance arbitrary-precision arithmetic using gmpy2 when installed,
with automatic fallback to pure Python arbitrary-precision arithmetic.
Enforces strict consistency verification between backends.
"""

from typing import List, Tuple

_HAS_GMPY2 = False
try:
    import gmpy2
    _HAS_GMPY2 = True
except ImportError:
    _HAS_GMPY2 = False

def has_gmpy2() -> bool:
    return _HAS_GMPY2

def pow_mod(base: int, exp: int, mod: int, use_gmpy: bool = True) -> int:
    """Computes (base^exp) mod mod using gmpy2 if available, else native Python."""
    if _HAS_GMPY2 and use_gmpy:
        return int(gmpy2.powmod(gmpy2.mpz(base), gmpy2.mpz(exp), gmpy2.mpz(mod)))
    return pow(base, exp, mod)

def square_sub_2_mod(u: int, mod: int, use_gmpy: bool = True) -> int:
    """
    Computes (u^2 - 2) mod mod.
    Optimized for the Lucas-Lehmer-Riesel recurrence.
    """
    if _HAS_GMPY2 and use_gmpy:
        u_mpz = gmpy2.mpz(u)
        m_mpz = gmpy2.mpz(mod)
        res = gmpy2.f_mod(gmpy2.square(u_mpz) - 2, m_mpz)
        return int(res)
    return (pow(u, 2, mod) - 2) % mod

def jacobi(a: int, n: int, use_gmpy: bool = True) -> int:
    """Computes Jacobi symbol (a / n)."""
    if _HAS_GMPY2 and use_gmpy:
        return int(gmpy2.jacobi(gmpy2.mpz(a), gmpy2.mpz(n)))
    # Fallback first-principles
    from .math_family import jacobi_symbol
    return jacobi_symbol(a, n)

def miller_rabin_test(n: int, base: int) -> bool:
    """
    Fast probable-prime screening for odd candidate n.
    When gmpy2 is available, executes compiled C-level Miller-Rabin testing.
    Falls back to pure Python standard Miller-Rabin iteration.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    if _HAS_GMPY2:
        return bool(gmpy2.is_prime(gmpy2.mpz(n), 25))

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    x = pow_mod(base, d, n, use_gmpy=False)
    if x == 1 or x == n - 1:
        return True

    for _ in range(s - 1):
        x = pow_mod(x, 2, n, use_gmpy=False)
        if x == n - 1:
            return True
    return False

def verify_backend_consistency() -> bool:
    """
    Validates that gmpy2 and Python native arithmetic give 100% identical residues
    across arbitrary-precision test vectors.
    """
    if not _HAS_GMPY2:
        return True

    test_vectors = [
        (7, 672, 15993 * (1 << 672) + 1),
        (5, 1024, 254697 * (1 << 1024) + 1),
        (5, 1664, 1183377 * (1 << 1664) + 1),
    ]

    for w, n, B in test_vectors:
        exp = (B - 1) // 2
        res_py = pow(w, exp, B)
        res_gmp = pow_mod(w, exp, B, use_gmpy=True)
        if res_py != res_gmp:
            raise RuntimeError(f"Backend mismatch: Python {res_py} != gmpy2 {res_gmp}")

    return True
