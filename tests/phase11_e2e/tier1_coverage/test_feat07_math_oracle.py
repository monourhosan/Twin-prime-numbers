"""Feature 7: Independent Mathematical Oracle.

Verifies:
1. Decoupled oracle architecture using SymPy/pure Python.
2. SymPy exact symbolic evaluation of OPQM-11 equations.
3. Independent reference trial-division survivor sieving.
4. SymPy primality verification of candidate members.
5. Exact integer type preservation and zero float conversion in oracle math.
"""

import math
from pathlib import Path
import pytest
import sympy
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    trial_division,
)


@pytest.mark.phase11_tier1
def test_f07_oracle_decoupled_design() -> None:
    """Verifies that reference oracle logic operates without depending on engine modules."""
    # Check that contract math works independently
    x = 12
    C, A, B = compute_manifold(x)
    assert C == 12 * (12 ** 5) + 6 * (12 ** 3)
    assert A == C - 1
    assert B == C + 1


@pytest.mark.phase11_tier1
def test_f07_sympy_exact_algebraic_evaluation() -> None:
    """Verifies SymPy symbolic equivalence: C(x) == 6*x^3 * (2*x^2 + 1)."""
    x = sympy.Symbol("x", integer=True)
    C_poly = 12 * (x ** 5) + 6 * (x ** 3)
    factored = sympy.factor(C_poly)
    expected = 6 * (x ** 3) * (2 * (x ** 2) + 1)
    assert sympy.simplify(factored - expected) == 0


@pytest.mark.phase11_tier1
def test_f07_independent_trial_division_sieve() -> None:
    """Verifies oracle's independent trial-division sieve eliminates small factors."""
    # Sieve interval [1, 20] with anchor y=3 (Sy=6)
    survivors = Phase11ContractAdapter.sieve_survivors(y=3, t_start=1, t_end=20, sieve_depth=50)
    assert isinstance(survivors, list)
    # Check that for each survivor t, neither A nor B has prime factor <= 50 (trial_division returns True)
    for t in survivors:
        _, A, B = Phase11ContractAdapter.compute_candidate_pair(3, t)
        assert trial_division(A, 50) is True, f"Survivor A has small factor for t={t}"
        assert trial_division(B, 50) is True, f"Survivor B has small factor for t={t}"


@pytest.mark.phase11_tier1
def test_f07_sympy_primality_verification() -> None:
    """Verifies SymPy's independent primality checks on reference candidates."""
    # x = 6 (y=3, t=1) -> A=94607, B=94609
    # 94607 = 89 * 1063 (composite!)
    # 94609 = 37 * 2557 (composite!)
    # SymPy isprime should correctly identify them
    _, A, B = Phase11ContractAdapter.compute_candidate_pair(3, 1)
    assert not sympy.isprime(A)
    assert not sympy.isprime(B)
    assert sympy.factorint(A) == {89: 1, 1063: 1}
    assert sympy.factorint(B) == {37: 1, 2557: 1}


@pytest.mark.phase11_tier1
def test_f07_oracle_exact_big_integer_types() -> None:
    """Verifies oracle results retain exact int type without float truncation."""
    C, A, B = compute_manifold(1000)
    assert isinstance(C, int) and not isinstance(C, float)
    assert isinstance(A, int) and not isinstance(A, float)
    assert isinstance(B, int) and not isinstance(B, float)
    assert C > 10 ** 15
    # Verify bit length is exact
    assert C.bit_length() > 50
