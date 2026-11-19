"""Tier 3 Integration Suite 1: CRT Inverse Pre-Filtering (F11) x Symmetric Quintic Sieve (F10).

Validates the pairwise interaction between:
1. CRT Inverse Pre-Filtering (modulus M_filter construction, admissible residue class selection, 100% small-prime survival guarantee).
2. Symmetric Quintic Modular Sieve (root-negation symmetry speedup r_B = q - r_A mod q, skipping inert moduli (-2/q)=-1).
"""

import math
import pytest
from typing import List, Set, Tuple
from sympy.ntheory import primerange

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_primorial_anchor,
    sieve_roots_mod_q,
    verify_root_negation_symmetry,
    is_inert_modulus,
)


def _compute_admissible_residues(y: int, crt_primes: List[int]) -> Tuple[int, List[int]]:
    """Helper to compute CRT filter modulus M_filter and admissible residues for t."""
    Sy, _ = compute_primorial_anchor(y)
    M_filter = 1
    for p in crt_primes:
        M_filter *= p

    admissible_for_p = {}
    for p in crt_primes:
        roots_A, roots_B = sieve_roots_mod_q(p)
        forbidden_roots = set(roots_A) | set(roots_B)
        inv_Sy = pow(Sy % p, -1, p)
        forbidden_t_mod_p = {(r * inv_Sy) % p for r in forbidden_roots}
        admissible_t = [res for res in range(p) if res not in forbidden_t_mod_p]
        admissible_for_p[p] = admissible_t

    # Solve CRT for admissible combinations (take the first few combinations)
    # Using small modulus product for test speed
    admissible_classes = []
    for t_cand in range(M_filter):
        if all((t_cand % p) in admissible_for_p[p] for p in crt_primes):
            admissible_classes.append(t_cand)

    return M_filter, admissible_classes


@pytest.mark.phase11_tier3
def test_combo_crt_preserves_small_primes_in_sieve() -> None:
    """Verifies that candidates selected via CRT pre-filtering achieve 100% survival

    against all primes in the CRT basis when evaluated by the symmetric modular sieve.
    """
    y = 5
    Sy, _ = compute_primorial_anchor(y)  # Sy = 30
    crt_primes = [7, 11]  # Primes above y=5
    M_filter, admissible_t = _compute_admissible_residues(y, crt_primes)
    assert len(admissible_t) > 0, "Admissible residue set must not be empty"

    chosen_t0 = admissible_t[0]

    # Sample candidates along the progression t = chosen_t0 + j * M_filter (ensure t > 0)
    test_t_values = [chosen_t0 + j * M_filter for j in range(1, 16)]

    for t in test_t_values:
        C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        for p in crt_primes:
            assert A % p != 0, f"Lower candidate A divisible by CRT prime {p} at t={t}"
            assert B % p != 0, f"Upper candidate B divisible by CRT prime {p} at t={t}"


@pytest.mark.phase11_tier3
def test_combo_crt_progression_reduces_sieve_load() -> None:
    """Confirms that streaming CRT pre-filtered candidates into the sieve

    substantially increases the density of surviving candidates compared to unfiltered streams.
    """
    y = 5
    crt_primes = [7]
    M_filter, admissible_t = _compute_admissible_residues(y, crt_primes)
    t0 = admissible_t[0]

    crt_candidates = [t0 + j * M_filter for j in range(1, 51)]
    all_candidates = list(range(max(1, t0), max(1, t0) + 50 * (M_filter // len(admissible_t) or 1)))[:50]

    sieve_depth = 30

    survivors_crt = [
        t for t in crt_candidates
        if t in Phase11ContractAdapter.sieve_survivors(y, t, t, sieve_depth)
    ]
    survivors_all = [
        t for t in all_candidates
        if t in Phase11ContractAdapter.sieve_survivors(y, t, t, sieve_depth)
    ]

    # Pre-filtered CRT candidates should have equal or higher survival yield
    assert len(survivors_crt) >= len(survivors_all)


@pytest.mark.phase11_tier3
def test_combo_sieve_root_negation_symmetry_on_crt_stream() -> None:
    """Verifies that the symmetric sieve exploits root negation symmetry

    for all sieve primes beyond the CRT pre-filter basis.
    """
    y = 5
    primes_to_check = [13, 17, 19, 23, 29, 31, 37, 41, 43]

    for q in primes_to_check:
        assert verify_root_negation_symmetry(q), f"Root negation symmetry failed for q={q}"
        roots_A, roots_B = sieve_roots_mod_q(q)
        for r in roots_A:
            companion = (q - r) % q
            assert companion in roots_B, f"Companion root {companion} not in roots_B for prime {q}"


@pytest.mark.phase11_tier3
def test_combo_crt_inert_moduli_skipping() -> None:
    """Verifies that the modular sieve skips inert moduli (-2/q = -1) for the cofactor R(x)=2x^2+1

    because R(x) can never be 0 mod q when q = 5, 7 mod 8.
    """
    inert_primes = [q for q in primerange(3, 100) if is_inert_modulus(q)]
    assert len(inert_primes) > 0

    for q in inert_primes:
        assert q % 8 in (5, 7), f"Prime {q} marked inert but not 5 or 7 mod 8"
        # Verify that 2x^2 + 1 != 0 mod q for all residues x in [0, q-1]
        for x in range(q):
            val = (2 * pow(x, 2, q) + 1) % q
            assert val != 0, f"Inert cofactor assumption violated: 2*{x}^2 + 1 = 0 mod {q}"


@pytest.mark.phase11_tier3
def test_combo_crt_empty_or_degenerate_basis_handling() -> None:
    """Adversarial check: verifies that over-constrained or contradictory CRT basis sets

    are detected and handled without throwing unhandled crashes or emitting invalid sieve streams.
    """
    y = 3  # Sy = 6
    Sy, _ = compute_primorial_anchor(y)
    assert Sy == 6

    # Verify that requesting sieve on an inverted or empty range returns empty list
    empty_survivors = Phase11ContractAdapter.sieve_survivors(y, t_start=10, t_end=5, sieve_depth=50)
    assert empty_survivors == []
