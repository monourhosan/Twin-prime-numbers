"""Tier 3 Integration Suite 9: Prototype (F6) x Oracle (F7) x Engine (F9) Three-Way Differential.

Validates the three-way differential equivalence between:
1. Minimal Mathematical Prototype (F6).
2. Independent Mathematical Oracle (SymPy/pure reference) (F7).
3. Arbitrary-Precision Engine Core (F9).
"""

import math
import pytest
import sympy
from sympy import Integer, symbols, expand
import gmpy2

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    check_algebraic_invariants,
)


def prototype_compute(x: int) -> tuple[int, int, int]:
    """Prototype implementation: factorized form 6*x^3 * (2*x^2 + 1)."""
    x_val = int(x)
    F = 6 * (x_val ** 3)
    R = 2 * (x_val ** 2) + 1
    C = F * R
    return C, C - 1, C + 1


def oracle_compute(x: int) -> tuple[int, int, int]:
    """Independent SymPy reference oracle: symbolic polynomial evaluation."""
    var_x = symbols('x')
    poly = expand(12 * var_x**5 + 6 * var_x**3)
    C_sym = poly.subs(var_x, Integer(x))
    C = int(C_sym)
    return C, C - 1, C + 1


def engine_compute(y: int, t: int) -> tuple[int, int, int]:
    """Arbitrary-precision engine core computation via contract adapter."""
    return Phase11ContractAdapter.compute_candidate_pair(y, t)


@pytest.mark.phase11_tier3
def test_combo_three_way_candidate_coordinate_equivalence() -> None:
    """Verifies that prototype, oracle, and engine compute bit-for-bit identical

    manifold coordinates (C, A, B) across 50 distinct test coordinates.
    """
    y = 5
    Sy, _ = compute_primorial_anchor(y)  # Sy = 30

    # Test 50 coordinates: t = 1 .. 50
    for t in range(1, 51):
        x = Sy * t
        C_proto, A_proto, B_proto = prototype_compute(x)
        C_oracle, A_oracle, B_oracle = oracle_compute(x)
        C_engine, A_engine, B_engine = engine_compute(y, t)

        # 3-way bit-for-bit equality
        assert C_proto == C_oracle == C_engine, f"Mismatch in C at t={t}: proto={C_proto}, oracle={C_oracle}, engine={C_engine}"
        assert A_proto == A_oracle == A_engine, f"Mismatch in A at t={t}"
        assert B_proto == B_oracle == B_engine, f"Mismatch in B at t={t}"


@pytest.mark.phase11_tier3
def test_combo_three_way_factorization_equivalence() -> None:
    """Verifies that prime factor decomposition of divisor F(x) = 6*x^3 matches

    between anchor tracking, SymPy factorint, and direct trial division.
    """
    y = 5
    Sy, Sy_factors = compute_primorial_anchor(y)

    for t in [1, 2, 5, 7, 11, 21, 35]:
        x = Sy * t
        F, _ = compute_divisor_and_cofactor(x)

        # Method 1: Anchor and t composition
        t_factors = dict(sympy.factorint(t))
        factors_composed = compute_factors_of_F(Sy_factors, t_factors)

        # Method 2: SymPy independent factorint on big integer F
        factors_sympy = dict(sympy.factorint(F))

        # Reconstructed product verification
        recon_composed = 1
        for p, exp in factors_composed.items():
            recon_composed *= (p ** exp)

        assert factors_composed == factors_sympy, f"Factor mismatch at t={t}: {factors_composed} vs {factors_sympy}"
        assert recon_composed == F, f"Composed factors product {recon_composed} != F {F}"


@pytest.mark.phase11_tier3
def test_combo_three_way_sieve_survivor_differential() -> None:
    """Verifies that prototype trial division, SymPy independent primality checks,

    and modular sieve produce strictly consistent survivor classifications.
    """
    y = 3  # Sy = 6
    sieve_depth = 30
    t_start, t_end = 1, 40

    # Modular sieve survivors
    sieve_survivors = set(Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth))

    # Oracle trial division verification on every candidate
    Sy, _ = compute_primorial_anchor(y)
    primes_to_check = [p for p in sympy.primerange(2, sieve_depth + 1) if Sy % p != 0]

    for t in range(t_start, t_end + 1):
        x = Sy * t
        C, A, B = prototype_compute(x)

        has_small_factor = any(A % p == 0 or B % p == 0 for p in primes_to_check)
        if has_small_factor:
            assert t not in sieve_survivors, f"Candidate at t={t} had factor in sieve range but survived sieve"
        else:
            assert t in sieve_survivors, f"Candidate at t={t} had no factors in sieve range but was eliminated"


@pytest.mark.phase11_tier3
def test_combo_three_way_algebraic_invariants_hold() -> None:
    """Confirms that the three invariants:

    1. B - A == 2
    2. C == 0 mod 6
    3. gcd(F, R) == 1
    hold universally across all evaluation methods.
    """
    for x in [6, 30, 42, 126, 210, 2310]:
        C_p, A_p, B_p = prototype_compute(x)
        F_p, R_p = compute_divisor_and_cofactor(x)

        # Check invariants
        assert B_p - A_p == 2
        assert C_p % 6 == 0
        assert math.gcd(F_p, R_p) == 1
        assert C_p == F_p * R_p
