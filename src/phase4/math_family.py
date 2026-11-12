"""
Phase 4 Exact Mathematical Specifications and Number-Theoretic Foundations.
Implements:
- Admissible multiplier mapping: k = 6t + 3, k < 2^n, n >= 2
- Exact arbitrary-precision center, lower, and upper member generation
- Dual-residue forbidden modular arithmetic in t-space
- Proth and LLR theorem preconditions validation
- Jacobi symbol and Lucas V_k sequences (both Montgomery ladder and 2x2 matrix powering)
"""

from typing import Tuple, Optional

def k_to_t(k: int) -> int:
    """Converts admissible multiplier k = 6t + 3 to integer index t >= 0."""
    if k < 3 or k % 2 == 0 or k % 3 != 0:
        raise ValueError(f"k must be positive odd integer divisible by 3 (k=6t+3), got {k}")
    return (k - 3) // 6

def t_to_k(t: int) -> int:
    """Converts index t >= 0 to admissible multiplier k = 6t + 3."""
    if t < 0:
        raise ValueError(f"t must be >= 0, got {t}")
    return 6 * t + 3

def compute_pair_integers(k: int, n: int) -> Tuple[int, int]:
    """
    Computes exact integers A = k*2^n - 1 and B = k*2^n + 1.
    Requires k < 2^n and n >= 2.
    """
    if n < 2:
        raise ValueError(f"n must be >= 2, got {n}")
    if k <= 0 or k % 2 == 0:
        raise ValueError(f"k must be positive odd integer, got {k}")
    two_n = 1 << n
    if k >= two_n:
        raise ValueError(f"Theorem requirement k < 2^n violated: k={k} >= 2^{n}")
    center = k * two_n
    return center - 1, center + 1

def exact_decimal_digits(val: int) -> int:
    """Computes exact decimal digit count directly from integer representation."""
    return len(str(val))

def compute_t_residues_for_prime(q: int, n: int) -> Tuple[int, int]:
    """
    Derives forbidden t-residues modulo q for candidate k = 6t + 3:
    q | (k*2^n - 1) <=> t = t_minus (mod q)
    q | (k*2^n + 1) <=> t = t_plus (mod q)
    where q is an odd prime > 3.
    """
    if q <= 3 or q % 2 == 0:
        raise ValueError(f"q must be odd prime > 3, got {q}")
    pow_2_n = pow(2, n, q)
    r = pow(pow_2_n, -1, q)
    inv_6 = pow(6, -1, q)
    t_minus = ((r - 3) * inv_6) % q
    t_plus = ((-r - 3) * inv_6) % q
    return t_minus, t_plus

def jacobi_symbol(a: int, n: int) -> int:
    """
    Computes Jacobi symbol (a / n) for positive odd n from first principles.
    """
    if n <= 0 or n % 2 == 0:
        raise ValueError(f"Jacobi symbol requires positive odd denominator, got {n}")
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
    Computes Lucas V_k(P, 1) mod mod using binary Montgomery ladder:
    V_{2m} = V_m^2 - 2
    V_{2m+1} = V_m * V_{m+1} - P
    Cost: ~O(log k) modular multiplications.
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod

    v0 = P % mod
    v1 = (pow(P, 2, mod) - 2) % mod

    bits = bin(k)[3:] # skip '0b1'
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
    Computes Lucas V_k(P, 1) mod mod using 2x2 binary matrix exponentiation:
    [[P, -1], [1, 0]]^k * [P, 2]^T.
    Serves as an independent mathematical validation oracle.
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod

    def mat_mul(A, B):
        return [
            [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % mod, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % mod],
            [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % mod, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % mod]
        ]

    res = [[1, 0], [0, 1]]
    base = [[P % mod, (-1) % mod], [1, 0]]
    p = k
    while p > 0:
        if p % 2 == 1:
            res = mat_mul(res, base)
        base = mat_mul(base, base)
        p //= 2

    return (res[1][0] * (P % mod) + res[1][1] * 2) % mod

def validate_proth_preconditions(k: int, n: int, B: int) -> Tuple[bool, str]:
    """Validates hypotheses of Proth's Theorem for B = k*2^n + 1."""
    if n < 2:
        return False, f"n must be >= 2, got {n}"
    if k <= 0 or k % 2 == 0:
        return False, f"k must be positive odd integer, got {k}"
    if k >= (1 << n):
        return False, f"Proth precondition k < 2^n violated: {k} >= 2^{n}"
    if B != k * (1 << n) + 1:
        return False, f"B does not match k*2^n + 1"
    return True, "Valid Proth candidate"

def validate_llr_preconditions(k: int, n: int, A: int) -> Tuple[bool, str]:
    """Validates hypotheses of Lucas-Lehmer-Riesel Theorem for A = k*2^n - 1."""
    if n < 2:
        return False, f"n must be >= 2, got {n}"
    if k <= 0 or k % 2 == 0:
        return False, f"k must be positive odd integer, got {k}"
    if k >= (1 << n):
        return False, f"LLR precondition k < 2^n violated: {k} >= 2^{n}"
    if A != k * (1 << n) - 1:
        return False, f"A does not match k*2^n - 1"
    return True, "Valid LLR candidate"
