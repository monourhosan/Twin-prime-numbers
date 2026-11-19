"""Phase 11 Symmetric Quintic Modular Sieve.

High-throughput CPU NumPy vectorized segmented sieve exploiting:
  1. Root-negation symmetry r_A = (q - r_B) mod q.
  2. Automatic skipping of primes q <= y (since q | S_y -> q never divides A or B).
  3. Inert quadratic cofactor classification: (-2/q) = -1 <=> q = 5, 7 mod 8.
"""


import numpy as np
from sympy.ntheory import primerange

from .inverse_crt import find_roots_mod_q
from .math_model import compute_primorial


def is_inert_modulus(q: int) -> bool:
    """Checks if prime modulus q is inert for quadratic cofactor R(x) = 2x^2 + 1.

    (-2/q) = -1 <=> q = 5, 7 mod 8.
    """
    if q < 3:
        return False
    return (q % 8) in (5, 7)


class SievePrimePlan:
    """Precomputed forbidden multiplier residues t mod q for prime modulus q."""

    __slots__ = ("forbidden_t_roots", "q")

    def __init__(self, q: int, forbidden_t_roots: list[int]):
        self.q = q
        self.forbidden_t_roots = forbidden_t_roots


def prepare_sieve_plan(y: int, sieve_depth: int) -> list[SievePrimePlan]:
    """Precomputes forbidden roots t mod q for all primes q in (y, sieve_depth].

    Primes q <= y are skipped automatically since q | S_y -> A, B never = 0 mod q.
    """
    Sy = compute_primorial(y)
    plan: list[SievePrimePlan] = []
    primes = list(primerange(y + 1, sieve_depth + 1))

    for q in primes:
        Sy_mod_q = Sy % q
        if Sy_mod_q == 0:
            continue
        inv_Sy = pow(Sy_mod_q, -1, q)
        # Solve roots of B mod q
        _, roots_B = find_roots_mod_q(q)
        if not roots_B:
            continue
        # Map roots of B and A to t mod q
        # Root negation symmetry applies directly: r_{t, A} = (q - r_{t, B}) % q
        forbidden_t: set[int] = set()
        for r_B in roots_B:
            rt_B = (r_B * inv_Sy) % q
            rt_A = (q - rt_B) % q
            forbidden_t.add(rt_B)
            forbidden_t.add(rt_A)

        plan.append(SievePrimePlan(q, sorted(forbidden_t)))

    return plan


def sieve_survivors(
    y: int,
    t_start: int,
    t_end: int,
    sieve_depth: int,
    odd_only: bool = False
) -> list[int]:
    """Executes symmetric modular sieve on interval [t_start, t_end].

    Returns list of surviving multiplier values t.
    Contract interface for Phase11ContractAdapter.
    """
    if t_start > t_end:
        return []

    plan = prepare_sieve_plan(y, sieve_depth)

    if not odd_only:
        # Full interval [t_start, t_end]
        n_candidates = t_end - t_start + 1
        alive = np.ones(n_candidates, dtype=np.uint8)

        for p_plan in plan:
            q = p_plan.q
            for r_t in p_plan.forbidden_t_roots:
                rem = (r_t - t_start) % q
                i0 = rem
                if i0 < n_candidates:
                    alive[i0::q] = 0

        survivor_indices = np.where(alive)[0]
        return [int(t_start + i) for i in survivor_indices]
    else:
        # Odd-only interval (used for discovery campaigns to ensure nu_2(x) = 1)
        first_odd = t_start if (t_start % 2 == 1) else t_start + 1
        last_odd = t_end if (t_end % 2 == 1) else t_end - 1
        if first_odd > last_odd:
            return []

        n_candidates = (last_odd - first_odd) // 2 + 1
        alive = np.ones(n_candidates, dtype=np.uint8)

        for p_plan in plan:
            q = p_plan.q
            for r_t in p_plan.forbidden_t_roots:
                # Find first odd t >= first_odd with t = r_t mod q
                rem = (r_t - first_odd) % q
                t0 = first_odd + rem
                if t0 % 2 == 0:
                    t0 += q
                i0 = (t0 - first_odd) // 2
                if i0 < n_candidates:
                    alive[i0::q] = 0

        survivor_indices = np.where(alive)[0]
        return [int(first_odd + 2 * i) for i in survivor_indices]
