"""Feature 11: CRT Inverse Pre-Filtering.

Verifies:
1. Sieve modulus M_filter construction from prime basis Q.
2. Admissible residue class identification modulo individual prime moduli.
3. Chinese Remainder Theorem combination of admissible residues.
4. 100% small-prime survival guarantee for candidates generated from progression.
5. Linear progression stepping t = t_0 + j * M_filter preserving non-divisibility.
"""

import math
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import compute_primorial_anchor


def solve_crt(residues: list[int], moduli: list[int]) -> int:
    """Solves system x = r_i mod m_i for pairwise coprime moduli."""
    M = 1
    for m in moduli:
        M *= m
    x = 0
    for r, m in zip(residues, moduli):
        Mi = M // m
        inv = pow(Mi, -1, m)
        x = (x + r * Mi * inv) % M
    return x


@pytest.mark.phase11_tier1
def test_f11_modulus_construction() -> None:
    """Verifies construction of filter modulus M_filter as product of basis primes."""
    basis_primes = [7, 11, 13]
    expected_M = 7 * 11 * 13  # 1001
    M_filter = math.prod(basis_primes)
    assert M_filter == expected_M
    assert math.gcd(M_filter, 30) == 1  # Coprime to Sy=30 (y=5)


@pytest.mark.phase11_tier1
def test_f11_admissible_residue_selection() -> None:
    """Verifies finding admissible residues modulo q avoiding roots of A and B."""
    y = 5
    Sy, _ = compute_primorial_anchor(y)  # Sy = 30
    q = 17  # Prime 17 has roots for C(x) +/- 1

    # Find admissible residues mod 17
    admissible = []
    roots = []
    for r in range(q):
        x = Sy * r
        c_mod = (12 * pow(x % q, 5, q) + 6 * pow(x % q, 3, q)) % q
        a_mod = (c_mod - 1) % q
        b_mod = (c_mod + 1) % q
        if a_mod == 0 or b_mod == 0:
            roots.append(r)
        else:
            admissible.append(r)

    # Must find roots and admissible residues
    assert len(roots) > 0, f"Expected roots for q={q}"
    assert len(admissible) > 0, f"Expected admissible residues for q={q}"
    assert len(admissible) + len(roots) == q


@pytest.mark.phase11_tier1
def test_f11_crt_combination() -> None:
    """Verifies combining admissible residues via Chinese Remainder Theorem."""
    basis = [17, 19]
    # Pick known admissible residues > 0
    r_17 = 2  # not in [1, 3, 8, 9, 14, 16]
    r_19 = 2  # not in [1, 4, 15, 18]
    t0 = solve_crt([r_17, r_19], basis)
    assert t0 % 17 == r_17
    assert t0 % 19 == r_19
    assert t0 > 0


@pytest.mark.phase11_tier1
def test_f11_100_percent_small_prime_survival() -> None:
    """Verifies that 100% of candidates from CRT progression survive small basis primes."""
    y = 5
    Sy, _ = compute_primorial_anchor(y)
    basis = [17, 19, 23]
    M_filter = math.prod(basis)

    # Find strictly positive admissible residues for each
    admissible_per_q = {}
    for q in basis:
        admissible_per_q[q] = []
        for r in range(1, q):
            x = (Sy * r) % q
            c = (12 * pow(x, 5, q) + 6 * pow(x, 3, q)) % q
            if (c - 1) % q != 0 and (c + 1) % q != 0:
                admissible_per_q[q].append(r)

    # Pick first non-zero admissible residue from each
    chosen_residues = [admissible_per_q[q][0] for q in basis]
    t0 = solve_crt(chosen_residues, basis)
    if t0 == 0:
        t0 += M_filter

    # Test progression for j = 0..10
    for j in range(10):
        t = t0 + j * M_filter
        _, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        for q in basis:
            assert A % q != 0, f"A divisible by basis prime {q} at j={j}"
            assert B % q != 0, f"B divisible by basis prime {q} at j={j}"


@pytest.mark.phase11_tier1
def test_f11_progression_generator_stepping() -> None:
    """Verifies that progression generator steps monotonically by M_filter."""
    M_filter = 1001
    t0 = 42
    progression = [t0 + j * M_filter for j in range(10)]
    for i in range(len(progression) - 1):
        assert progression[i + 1] - progression[i] == M_filter
    assert progression[0] == t0
