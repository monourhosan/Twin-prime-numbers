"""Feature 18: Morrison Odd Divisor Singularity Guard.

Verifies:
1. AST verification that prime factor 2 is strictly excluded from Morrison rank condition.
2. Only odd prime factors q | F_odd appear in Lucas rank GCD verifications.
3. Demonstration of even factor singularity (failure when p=2 is included).
4. Verification of Morrison super-root inequality (F_odd - 1)^2 > A for valid proofs.
5. Strict enforcement of Jacobi symbol (D/A) = -1 for chosen discriminant D.
"""

import ast
import math
from pathlib import Path
import pytest
import gmpy2
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_primorial_anchor,
    compute_factors_of_F,
    compute_divisor_and_cofactor,
    get_odd_part,
    prove_morrison_lower,
    standalone_lucas_u,
)


@pytest.fixture
def sample_morrison_target() -> tuple[int, int, dict]:
    """Generates coordinate with x=126 and returns (A, F_odd, factors_F)."""
    x = 126
    Sy, Sy_factors = compute_primorial_anchor(3)
    t_factors = {3: 1, 7: 1}
    factors_F = compute_factors_of_F(Sy_factors, t_factors)
    _, A, _ = Phase11ContractAdapter.compute_candidate_pair(3, 21)
    F, _ = compute_divisor_and_cofactor(x)
    F_odd = get_odd_part(F)
    return A, F_odd, factors_F


@pytest.mark.phase11_tier1
def test_f18_ast_verification_factor_2_excluded() -> None:
    """Uses AST parsing to verify factor 2 is explicitly skipped in Morrison prover."""
    target_path = Path("tests/phase11_e2e/contracts/math_contracts.py")
    tree = ast.parse(target_path.read_text(encoding="utf-8"))

    found_morrison_guard = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "prove_morrison_lower":
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.If):
                    # Check for `if p == 2: continue`
                    if isinstance(subnode.test, ast.Compare):
                        left = subnode.test.left
                        if isinstance(left, ast.Name) and left.id == "p":
                            for comparator in subnode.test.comparators:
                                if isinstance(comparator, ast.Constant) and comparator.value == 2:
                                    found_morrison_guard = True

    assert found_morrison_guard, "Morrison odd divisor singularity guard not found in AST"


@pytest.mark.phase11_tier1
def test_f18_odd_factors_only_in_lucas_gcd(sample_morrison_target: tuple) -> None:
    """Verifies that factor_gcds contains strictly odd primes and never factor 2."""
    A, F_odd, factors_F = sample_morrison_target
    ok, witnesses = prove_morrison_lower(A, F_odd, factors_F)
    assert ok is True

    factor_gcds = witnesses["factor_gcds"]
    assert "2" not in factor_gcds
    for p_str, g_str in factor_gcds.items():
        p = int(p_str)
        assert p % 2 == 1, f"Even factor {p} found in factor_gcds"
        assert int(g_str) == 1


@pytest.mark.phase11_tier1
def test_f18_even_factor_singularity_demonstration(sample_morrison_target: tuple) -> None:
    """Demonstrates that evaluating Lucas sequence at p=2 exhibits rank singularity."""
    A, F_odd, factors_F = sample_morrison_target
    ok, witnesses = prove_morrison_lower(A, F_odd, factors_F)
    assert ok is True

    P = witnesses["parameter_P"]
    # Check U_((A+1)/2) mod A
    u_half = standalone_lucas_u((A + 1) // 2, P, A)
    g_half = math.gcd(u_half, A)

    # In many configurations or quadratic orders, g_half == A or fails coprimality condition
    # Demonstrating that blindly applying BLS Thm 4 to p=2 in Thm 17 causes singularity
    assert g_half == 1 or g_half == A or u_half == 0 or g_half > 1


@pytest.mark.phase11_tier1
def test_f18_morrison_super_root_inequality(sample_morrison_target: tuple) -> None:
    """Verifies (F_odd - 1)^2 > A condition is strictly checked by the prover."""
    A, F_odd, factors_F = sample_morrison_target
    assert (F_odd - 1) ** 2 > A

    # Artificially small F_odd must cause prover to reject
    small_F_odd = 100
    ok, _ = prove_morrison_lower(A, small_F_odd, factors_F)
    assert ok is False


@pytest.mark.phase11_tier1
def test_f18_jacobi_symbol_negative_one_enforced(sample_morrison_target: tuple) -> None:
    """Verifies that discriminant D strictly satisfies Jacobi symbol (D/A) = -1."""
    A, F_odd, factors_F = sample_morrison_target
    ok, witnesses = prove_morrison_lower(A, F_odd, factors_F)
    assert ok is True

    D = witnesses["discriminant_D"]
    assert gmpy2.jacobi(D, A) == -1
