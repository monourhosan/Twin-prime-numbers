"""
Phase 11 Independent Mathematical Reference Oracle (HYBRID-11).
Built strictly with SymPy symbolic expressions, finite-field polynomial solvers, and isprime.
Completely decoupled with zero dependencies on prototype.py.
"""


import sympy as sp
from sympy.ntheory import isprime, primerange


def get_symbolic_polynomials() -> tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr, sp.Expr]:
    """
    Returns symbolic polynomial expressions (C, A, B, F, R) over Symbol('x').
    """
    x = sp.Symbol('x')
    C = 12 * x**5 + 6 * x**3
    A = C - 1
    B = C + 1
    F = 6 * x**3
    R = 2 * x**2 + 1
    return C, A, B, F, R


def verify_symbolic_invariants() -> dict[str, bool]:
    """
    Symbolically verifies OPQM-11 algebraic identities over Z[x] and Q[x]:
      1. twin_gap_identity: simplify(B - A) == 2
      2. center_factorization: simplify(C - F * R) == 0
      3. antisymmetry_C: simplify(C(-x) + C(x)) == 0
      4. candidate_reflection: simplify(B(-x) + A(x)) == 0
      5. irreducibility_A: Poly(A, domain=QQ).is_irreducible == True
      6. irreducibility_B: Poly(B, domain=QQ).is_irreducible == True
    """
    x = sp.Symbol('x')
    C, A, B, F, R = get_symbolic_polynomials()
    
    gap_diff = sp.simplify(B - A)
    factor_diff = sp.simplify(C - F * R)
    antisym_C = sp.simplify(C.subs(x, -x) + C)
    reflect_BA = sp.simplify(B.subs(x, -x) + A)
    
    poly_A = sp.Poly(A, x, domain=sp.QQ)
    poly_B = sp.Poly(B, x, domain=sp.QQ)
    
    return {
        "twin_gap_identity": gap_diff == 2,
        "center_factorization": factor_diff == 0,
        "antisymmetry_C": antisym_C == 0,
        "candidate_reflection": reflect_BA == 0,
        "irreducibility_A": poly_A.is_irreducible,
        "irreducibility_B": poly_B.is_irreducible,
    }


def compute_center(x: int) -> int:
    """
    Computes C(x) = 12x^5 + 6x^3 via SymPy evaluation.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    x_sym = sp.Symbol('x')
    C_sym = 12 * x_sym**5 + 6 * x_sym**3
    return int(C_sym.subs(x_sym, x))


def compute_pair(x: int) -> tuple[int, int]:
    """
    Computes (A(x), B(x)) via SymPy evaluation.
    """
    C = compute_center(x)
    return C - 1, C + 1


def factorable_divisor(x: int) -> int:
    """
    Computes algebraic divisor kernel F(x) = 6x^3 via SymPy evaluation.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    x_sym = sp.Symbol('x')
    return int((6 * x_sym**3).subs(x_sym, x))


def cofactor(x: int) -> int:
    """
    Computes algebraic cofactor R(x) = 2x^2 + 1 via SymPy evaluation.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    x_sym = sp.Symbol('x')
    return int((2 * x_sym**2 + 1).subs(x_sym, x))


def verify_invariants(x: int) -> dict[str, bool]:
    """
    Independently verifies integer invariants using SymPy primitives.
    """
    if x <= 0:
        raise ValueError(f"Coordinate x must be positive, got {x}")
    
    C = compute_center(x)
    A, B = compute_pair(x)
    F = factorable_divisor(x)
    R = cofactor(x)
    
    # 2-adic valuation of F = 6*x^3 under canonical OPQM-11 manifold:
    v2_F = (F & -F).bit_length() - 1
    F_odd = F >> 4 if v2_F <= 4 else (F >> v2_F)
    
    gap_is_two = (B - A == 2)
    center_mod_6 = (C % 6 == 0)
    a_mod_6 = (A % 6 == 5)
    b_mod_6 = (B % 6 == 1)
    gcd_f_r = (sp.gcd(F, R) == 1)
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
    Independently solves roots of B(x) mod q and A(x) mod q using SymPy's GF(q) domain.
    Normalizes roots mod q to guarantee standard [0, q-1] representation.
    Asserts root-negation symmetry internally.
    """
    if q < 2 or q in (2, 3):
        return [], []
    
    x = sp.Symbol('x')
    Fq = sp.GF(q)
    
    p_B = sp.Poly(12 * x**5 + 6 * x**3 + 1, x, domain=Fq)
    roots_B = sorted({int(r) % q for r in p_B.ground_roots()})
    
    p_A = sp.Poly(12 * x**5 + 6 * x**3 - 1, x, domain=Fq)
    roots_A = sorted({int(r) % q for r in p_A.ground_roots()})
    
    # Verify root-negation symmetry internally
    expected_A = sorted((q - r) % q for r in roots_B)
    assert roots_A == expected_A, f"Symmetry broken in oracle at q={q}: {roots_A} != {expected_A}"
    
    return roots_A, roots_B


def compute_primorial(y: int) -> int:
    """
    Computes S_y = product of all primes <= y using sympy.primerange.
    """
    if y < 3:
        raise ValueError(f"Primorial anchor y must be >= 3, got {y}")
    primes = list(primerange(2, y + 1))
    return int(sp.prod(primes))


def generate_candidates(
    anchor_y: int,
    t_range: tuple[int, int],
    crt_basis: list[int] | None = None,
    odd_only: bool = True
) -> list[tuple[int, int, int]]:
    """
    Independently generates candidate tuples (t, A, B) using SymPy primitives.
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
            inv_Sy = int(sp.mod_inverse(S_y % q, q))
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
    Independently sieves candidates using sympy.primerange.
    """
    if not candidates or prime_limit < 2:
        return list(candidates)
    
    primes = list(primerange(2, prime_limit + 1))
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


def verify_primality(p: int) -> bool:
    """
    Deterministic primality check using SymPy's isprime.
    """
    return bool(isprime(p))


def find_survivor_primes(
    candidates: list[tuple[int, int, int]]
) -> list[tuple[int, int, int]]:
    """
    Filters candidates to find genuine twin primes where both members are prime.
    """
    return [c for c in candidates if verify_primality(c[1]) and verify_primality(c[2])]
