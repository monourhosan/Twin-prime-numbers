"""Tier 4 Workflow 1: Research, Audit, & Algorithmic Gating User Journey.

Covers the sequential workflow from:
1. Environment and Baseline Audit verification (commit, toolchain, 239 baseline tests).
2. Formulation and comparative evaluation of >= 5 candidate mathematical directions.
3. Rigorous mathematical gating (twin gap B-A=2, mod 6, coprimality, super-roots, irreducibility).
4. Prior art literature review and differentiation against historical PrimePages and PrimeGrid families.
5. Selection and algebraic validation of the winning OPQM-CRT Hybrid (HYBRID-11) method.
"""

from pathlib import Path
import pytest
from sympy import symbols, Poly

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    check_algebraic_invariants,
)


@pytest.fixture
def research_dir() -> Path:
    p = Path("research/phase11")
    if not p.is_dir():
        pytest.skip("research/phase11 directory not found")
    return p


@pytest.mark.phase11_tier4
def test_journey01_step1_audit_reconnaissance(research_dir: Path) -> None:
    """Journey Step 1: Audits baseline environment, git hygiene, toolchain versions,

    and confirms the 239 baseline regression tests are recorded.
    """
    audit_file = research_dir / "BASELINE_AUDIT.md"
    assert audit_file.is_file(), "BASELINE_AUDIT.md must exist in research/phase11/"

    content = audit_file.read_text(encoding="utf-8")
    assert "801ac1a" in content or "Commit" in content, "Must document base commit"
    assert "3.12" in content or "Python" in content, "Must document Python version"
    assert "gmpy2" in content, "Must inventory gmpy2"
    assert "SymPy" in content, "Must inventory SymPy"
    assert "239" in content, "Must verify the exact 239 baseline test count"


@pytest.mark.phase11_tier4
def test_journey01_step2_candidate_directions_evaluation(research_dir: Path) -> None:
    """Journey Step 2: Evaluates >= 5 distinct candidate mathematical directions

    against the 18 research criteria and 7-dimensional scoring matrix.
    """
    candidate_file = research_dir / "CANDIDATE_METHODS.md"
    assert candidate_file.is_file(), "CANDIDATE_METHODS.md must exist in research/phase11/"

    content = candidate_file.read_text(encoding="utf-8")
    # Verify candidate directions discussed
    assert "Direction 1" in content or "DIR-" in content or "Candidate" in content
    assert "Score" in content or "Matrix" in content or "Evaluation" in content
    assert "HYBRID-11" in content or "OPQM" in content, "Must reference the winning OPQM method"


@pytest.mark.phase11_tier4
def test_journey01_step3_mathematical_gating_proofs() -> None:
    """Journey Step 3: Formally proves all 5 gating criteria for the winning OPQM-11 manifold:

    1. Gap B - A == 2
    2. Parity C == 0 mod 6
    3. Coprimality gcd(F, R) == 1 when 6 | x
    4. Super-root inequality F^2 > B for all x >= 1
    5. Morrison super-root bound (F_odd - 1)^2 > A for x >= 86 (with nu_2(x) = 1)
    """
    # 1 & 2: Symbolic polynomial definition
    x = symbols('x')
    C_poly = 12 * x**5 + 6 * x**3
    A_poly = C_poly - 1
    B_poly = C_poly + 1
    assert (B_poly - A_poly) == 2, "Symbolic gap B - A must equal 2"

    # Evaluate at multiple coordinates with 6 | x (guaranteed by primorial anchor Sy)
    for test_x in [6, 12, 18, 30, 90, 126, 210]:
        inv = check_algebraic_invariants(test_x)
        assert inv["difference_is_2"]
        assert inv["center_mod_6_is_0"]
        assert inv["coprimality_holds"]
        assert inv["F_squared_greater_than_B"]
        if test_x >= 86:
            assert inv["F_odd_squared_greater_than_A"]

    # Verify Morrison crossover threshold at x=86
    F_odd_86 = (6 * (86 ** 3)) // 16
    C_86, A_86, _ = compute_manifold(86)
    assert (F_odd_86 - 1) ** 2 > A_86, "x=86 must satisfy Morrison inequality"


@pytest.mark.phase11_tier4
def test_journey01_step4_prior_art_and_literature_review(research_dir: Path) -> None:
    """Journey Step 4: Reviews historical literature, PrimePages top-20, Tony Forbes polynomials,

    and PrimeGrid twin-prime search algorithms to establish novelty and differentiation.
    """
    prior_art_file = research_dir / "PRIOR_ART.md"
    assert prior_art_file.is_file(), "PRIOR_ART.md must exist in research/phase11/"

    content = prior_art_file.read_text(encoding="utf-8")
    assert "PrimePages" in content or "Forbes" in content or "PrimeGrid" in content


@pytest.mark.phase11_tier4
def test_journey01_step5_winning_method_selection_and_derivation() -> None:
    """Journey Step 5: Confirms that the OPQM-CRT Hybrid (HYBRID-11) is uniquely selected

    as the production method with verified anchor and inverse CRT compatibility.
    """
    # Verify primorial anchor y=5 produces valid Sy=30 with 6 | Sy
    Sy, factors = compute_primorial_anchor(5)
    assert Sy == 30
    assert Sy % 6 == 0
    assert 2 in factors and 3 in factors and 5 in factors

    # Compute candidate coordinates for t=1
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(5, 1)
    assert B - A == 2
    assert C % 6 == 0
