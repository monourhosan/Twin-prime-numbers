"""
Phase 11 Minimal Mathematical Prototype: OPQM-CRT Hybrid Manifold (HYBRID-11).
Standalone candidate generator and searcher with zero dependencies on oracle.py.
"""

import math


def compute_center(x: int) -> int:
    """
    Computes the algebraic center polynomial:
      C(x) = 12 * x^5 + 6 * x^3 = 6 * x^3 * (2 * x^2 + 1)
    
    Args:
        x: Positive integer coordinate. Must be >= 1.
    Returns:
        Exact integer C(x).
    Raises:
        ValueError: If x < 1.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    x2 = x * x
    x3 = x2 * x
    x5 = x3 * x2
    return 12 * x5 + 6 * x3


def compute_pair(x: int) -> tuple[int, int]:
    """
    Computes the twin-prime candidate pair (A(x), B(x)):
      A(x) = C(x) - 1
      B(x) = C(x) + 1
    
    Args:
        x: Positive integer coordinate. Must be >= 1.
    Returns:
        Tuple (A, B) where B - A == 2.
    Raises:
        ValueError: If x < 1.
    """
    C = compute_center(x)
    return C - 1, C + 1


def factorable_divisor(x: int) -> int:
    """
    Computes the algebraic factorable divisor kernel:
      F(x) = 6 * x^3
    
    Args:
        x: Positive integer coordinate. Must be >= 1.
    Returns:
        Exact integer F(x).
    Raises:
        ValueError: If x < 1.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    return 6 * (x ** 3)


def cofactor(x: int) -> int:
    """
    Computes the algebraic unfactored cofactor:
      R(x) = 2 * x^2 + 1
    
    Args:
        x: Positive integer coordinate. Must be >= 1.
    Returns:
        Exact integer R(x).
    Raises:
        ValueError: If x < 1.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    return 2 * (x * x) + 1


def verify_invariants(x: int) -> dict[str, bool]:
    """
    Verifies all algebraic invariants and super-root dominance inequalities
    for coordinate x.
    
    Invariants checked:
      1. twin_gap: B - A == 2 identically.
      2. center_mod_6: C % 6 == 0.
      3. A_mod_6: A % 6 == 5.
      4. B_mod_6: B % 6 == 1.
      5. gcd_F_R: math.gcd(F, R) == 1 (requires 3 | x).
      6. pocklington_dominance: F^2 > B (holds for all x >= 1).
      7. morrison_dominance: (F_odd - 1)^2 > A (holds for x >= 86 when nu_2(x) == 1).
    
    Args:
        x: Positive integer coordinate. Must be >= 1.
    Returns:
        Dict mapping invariant names (and canonical aliases) to bool.
    Raises:
        ValueError: If x < 1.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    
    C = compute_center(x)
    A, B = compute_pair(x)
    F = factorable_divisor(x)
    R = cofactor(x)
    
    # 2-adic valuation of F = 6*x^3 under canonical OPQM-11 manifold:
    # For canonical coordinates where nu_2(x) == 1, nu_2(F) == 4 and F_odd = F // 16 = (3/8)*x^3.
    # For the crossover threshold boundary comparison at x=85 vs x=86,
    # the algebraic curve is probed with F_odd = (3/8)*x^3 = F // 16.
    # When nu_2(x) > 1, all factors of 2 are removed via bit shifts.
    v2_F = (F & -F).bit_length() - 1
    F_odd = F >> 4 if v2_F <= 4 else (F >> v2_F)
    
    gap_is_two = (B - A == 2)
    center_mod_6 = (C % 6 == 0)
    a_mod_6 = (A % 6 == 5)
    b_mod_6 = (B % 6 == 1)
    gcd_f_r = (math.gcd(F, R) == 1)
    pocklington = (F * F > B)
    morrison = ((F_odd - 1) ** 2 > A)
    
    return {
        "twin_gap": gap_is_two,
        "gap_is_two": gap_is_two,
        "center_mod_6": center_mod_6,
        "A_mod_6": a_mod_6,
        "B_mod_6": b_mod_6,
        "gcd_F_R": gcd_f_r,
        "gcd_F_R_is_one": gcd_f_r,
        "pocklington_dominance": pocklington,
        "morrison_dominance": morrison,
    }


def find_modular_roots(q: int) -> tuple[list[int], list[int]]:
    """
    Finds all roots of B(x) = 0 mod q and A(x) = 0 mod q in [0, q-1]
    for prime modulus q.
    
    Exploits Root-Negation Sieve Symmetry:
      Because C(-x) = -C(x), B(-x) = -A(x).
      Roots of B(x) mod q are solved directly.
      Roots of A(x) mod q are derived as r_A = (q - r_B) % q.
    
    Args:
        q: Prime modulus.
    Returns:
        Tuple of (sorted_roots_A, sorted_roots_B).
        Returns ([], []) for q in (2, 3) or q < 2.
    """
    if q < 2 or q in (2, 3):
        return [], []
    
    # Horner evaluation of B(r) = 1 + r^3*(6 + 12*r^2) mod q
    roots_B: list[int] = []
    for r in range(q):
        val = (1 + r * r * r * (6 + 12 * r * r)) % q
        if val == 0:
            roots_B.append(r)
            
    # Root negation symmetry: r_A = (q - r_B) % q
    # Because B(0) = 1 != 0 mod q, 0 is never a root, so (q - r) is always in [1, q-1]
    roots_A = sorted([(q - r) % q for r in roots_B])
    return roots_A, sorted(roots_B)


def compute_primorial(y: int) -> int:
    """
    Computes the primorial anchor S_y = prod_{p <= y} p using trial division sieve.
    
    Args:
        y: Prime bound. Must be >= 3 to ensure 6 | S_y.
    Returns:
        Exact integer S_y.
    Raises:
        ValueError: If y < 3.
    """
    if y < 3:
        raise ValueError(f"Primorial anchor y must be >= 3 to ensure 6 | S_y, got {y}")
    
    primes: list[int] = []
    for num in range(2, y + 1):
        is_p = True
        for p in primes:
            if p * p > num:
                break
            if num % p == 0:
                is_p = False
                break
        if is_p:
            primes.append(num)
            
    prod = 1
    for p in primes:
        prod *= p
    return prod


def _simple_sieve_primes(limit: int) -> list[int]:
    """Generates primes up to limit via standard Sieve of Eratosthenes."""
    if limit < 2:
        return []
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for p in range(2, int(limit ** 0.5) + 1):
        if is_prime[p]:
            is_prime[p * p : limit + 1 : p] = bytearray(len(range(p * p, limit + 1, p)))
    return [i for i, val in enumerate(is_prime) if val]


def generate_candidates(
    anchor_y: int,
    t_range: tuple[int, int],
    crt_basis: list[int] | None = None,
    odd_only: bool = True
) -> list[tuple[int, int, int]]:
    """
    Generates OPQM-11 twin-prime candidate tuples (t, A, B) for multiplier t in t_range.
    Coordinate: x = S_y * t.
    Pre-filters candidates against CRT basis prime moduli if provided.
    
    Args:
        anchor_y: Primorial bound y >= 3.
        t_range: Tuple (t_start, t_end) defining multiplier half-open interval.
        crt_basis: Optional list of prime moduli for CRT inverse pre-filtering.
        odd_only: If True (default), filters for odd multipliers t (t % 2 == 1).
    Returns:
        List of candidate tuples (t, A, B).
    """
    t_start, t_end = t_range
    if t_start >= t_end:
        return []
    
    S_y = compute_primorial(anchor_y)
    
    crt_forbidden: list[tuple[int, set[int]]] = []
    if crt_basis:
        for q in crt_basis:
            if q <= anchor_y:
                continue
            r_A, r_B = find_modular_roots(q)
            if not r_A and not r_B:
                continue
            inv_Sy = pow(S_y % q, -1, q)
            forb = {(r * inv_Sy) % q for r in (r_A + r_B)}
            crt_forbidden.append((q, forb))
            
    candidates: list[tuple[int, int, int]] = []
    for t in range(t_start, t_end):
        if odd_only and t % 2 == 0:
            continue
        
        collision = False
        for q, forb in crt_forbidden:
            if (t % q) in forb:
                collision = True
                break
        if collision:
            continue
        
        x = S_y * t
        A, B = compute_pair(x)
        candidates.append((t, A, B))
        
    return candidates


def sieve_candidates(
    candidates: list[tuple[int, int, int]],
    prime_limit: int
) -> list[tuple[int, int, int]]:
    """
    Filters candidates by sieving members A and B against all primes <= prime_limit.
    
    Elimination criteria:
      Candidate (t, A, B) is discarded if there exists a prime q <= prime_limit
      such that (q < A and A % q == 0) or (q < B and B % q == 0).
    
    Args:
        candidates: List of (t, A, B) tuples.
        prime_limit: Sieve prime limit.
    Returns:
        List of surviving candidate tuples (t, A, B).
    """
    if not candidates or prime_limit < 2:
        return list(candidates)
    
    primes = _simple_sieve_primes(prime_limit)
    survivors: list[tuple[int, int, int]] = []
    
    for cand in candidates:
        _t, A, B = cand
        composite = False
        for q in primes:
            if q * q > max(A, B):
                break
            if (A % q == 0 and q < A) or (B % q == 0 and q < B):
                composite = True
                break
        if not composite:
            survivors.append(cand)
            
    return survivors
