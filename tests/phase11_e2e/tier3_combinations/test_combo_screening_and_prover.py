"""Tier 3 Integration Suite 3: Screening Pipeline (F16) x Dual-BLS Prover (F17).

Validates the pairwise interaction between:
1. Multi-Tier Primality Screening Pipeline (producing DUAL_PRP candidates).
2. Deterministic Dual-BLS Certification (Pocklington BLS Theorem 4 + Morrison BLS Theorem 17).
"""

import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    get_odd_part,
    prove_pocklington_upper,
    prove_morrison_lower,
    screen_candidate,
)


@pytest.mark.phase11_tier3
def test_combo_prover_rejects_composite_and_single_prp_candidates() -> None:
    """Verifies that the Dual-BLS prover rejects candidates that fail the screening pipeline

    (i.e., classified as COMPOSITE or SINGLE_PRP).
    """
    # Candidate known to be composite at y=3, t=1 (x=6):
    y = 3
    t = 1
    status, pair = Phase11ContractAdapter.screen_candidate(y, t)
    assert status in ("COMPOSITE", "SINGLE_PRP"), f"Candidate (y={y}, t={t}) should not be DUAL_PRP"

    # Attempting to prove an un-screened/composite candidate should raise ValueError
    with pytest.raises(ValueError, match="did not pass primality screening"):
        Phase11ContractAdapter.prove_pair(y, t)


@pytest.mark.phase11_tier3
def test_combo_screening_dual_prp_satisfies_prover_preconditions() -> None:
    """Confirms that when a candidate achieves DUAL_PRP status,

    all algebraic and size preconditions for Dual-BLS certification hold:
    1. B - 1 = F * R with F^2 > B.
    2. A + 1 = F * R with (F_odd - 1)^2 > A (for x >= 86).
    3. gcd(F, R) == 1.
    """
    # Use known small discovery coordinate x = 126 (y=3, t=21)
    y = 3
    t = 21
    Sy, Sy_factors = compute_primorial_anchor(y)
    x = Sy * t
    assert x == 126
    assert x >= 86, "x must exceed the Morrison lower threshold x=86"

    status, pair = Phase11ContractAdapter.screen_candidate(y, t)
    assert status == "DUAL_PRP", f"Expected (y={y}, t={t}) to be DUAL_PRP"

    C, A, B = pair
    F, R = compute_divisor_and_cofactor(x)
    F_odd = get_odd_part(F)

    # Check Pocklington size condition
    assert F * F > B, f"Pocklington size condition violated: {F*F} <= {B}"

    # Check Morrison size condition
    assert (F_odd - 1) ** 2 > A, f"Morrison size condition violated: {(F_odd - 1)**2} <= {A}"

    # Check coprimality
    import math
    assert math.gcd(F, R) == 1, f"Divisor and cofactor are not coprime: gcd({F}, {R}) != 1"


@pytest.mark.phase11_tier3
def test_combo_prover_produces_witnesses_for_screening_survivor() -> None:
    """Verifies that the prover successfully discovers witnesses for all prime factors

    of F for candidates that pass the screening pipeline.
    """
    y = 3
    t = 21
    Sy, Sy_factors = compute_primorial_anchor(y)
    x = Sy * t
    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)
    factors_F = compute_factors_of_F(Sy_factors, {3: 1, 7: 1})
    F_odd = get_odd_part(F)

    # Upper member Pocklington proof
    ok_upper, witnesses_B = prove_pocklington_upper(B, F, factors_F)
    assert ok_upper is True, "Pocklington proof should succeed for screening survivor"
    assert len(witnesses_B) == len(factors_F), "Must have witness for each prime factor of F"

    # Lower member Morrison proof
    ok_lower, morrison_result = prove_morrison_lower(A, F_odd, factors_F)
    assert ok_lower is True, "Morrison proof should succeed for screening survivor"
    assert morrison_result["jacobi_symbol"] == -1
    assert morrison_result["parameter_P"] > 2
    # Verify factor 2 is excluded from Morrison GCDs
    assert "2" not in morrison_result["factor_gcds"], "Factor 2 must be excluded by odd divisor guard"


@pytest.mark.phase11_tier3
def test_combo_prover_failure_on_underfactored_divisor() -> None:
    """Verifies that if the factored divisor F is truncated such that F^2 <= B,

    the prover correctly fails even on a candidate that passed screening.
    """
    y = 3
    t = 21
    Sy, Sy_factors = compute_primorial_anchor(y)
    x = Sy * t
    C, A, B = compute_manifold(x)

    # Incomplete/truncated factor list resulting in F_small^2 <= B
    truncated_factors = {2: 1}  # Only factor 2
    F_small = 2

    ok_upper, _ = prove_pocklington_upper(B, F_small, truncated_factors)
    assert ok_upper is False, "Pocklington must fail when F^2 <= B"

    ok_lower, _ = prove_morrison_lower(A, F_odd=1, factors_F=truncated_factors)
    assert ok_lower is False, "Morrison must fail when (F_odd - 1)^2 <= A"
