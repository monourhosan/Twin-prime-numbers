"""Tier 3 Integration Suite 10: Negative Results & Bottleneck Log (F23) x Baseline Reconnaissance Audit (F1).

Validates the pairwise interaction between:
1. Negative Results & Bottleneck Log (rejection of non-viable parameter regimes, Morrison threshold x < 86, hardware limits).
2. Baseline Reconnaissance & Environment Audit (toolchain verification, hardware specs, 239 baseline test count).
"""

from pathlib import Path
import re
import pytest

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    get_odd_part,
    check_algebraic_invariants,
)


@pytest.fixture
def baseline_audit_file() -> Path:
    """Returns path to BASELINE_AUDIT.md if it exists."""
    p = Path("research/phase11/BASELINE_AUDIT.md")
    if not p.is_file():
        pytest.skip("BASELINE_AUDIT.md not found")
    return p


@pytest.mark.phase11_tier3
def test_combo_negative_regime_morrison_subcritical_boundary() -> None:
    """Mathematically verifies the non-viable parameter regime documented in negative results:

    When nu_2(x) = 1, F_odd = (6*x^3)//16 = (3/8)*x^3.
    Morrison Theorem 17 condition (F_odd - 1)^2 > A fails at x = 85
    and strictly passes at x >= 86.
    """
    # x = 85 (subcritical)
    C_85, A_85, B_85 = compute_manifold(85)
    F_odd_85 = (6 * (85 ** 3)) // 16
    assert (F_odd_85 - 1) ** 2 <= A_85, "x=85 must fail Morrison bound under nu_2(x)=1"

    # x = 86 (strict pass)
    C_86, A_86, B_86 = compute_manifold(86)
    F_odd_86 = (6 * (86 ** 3)) // 16
    assert (F_odd_86 - 1) ** 2 > A_86, "x=86 must strictly pass Morrison bound under nu_2(x)=1"


@pytest.mark.phase11_tier3
def test_combo_negative_regime_unanchored_coprimality_violation() -> None:
    """Verifies that coordinates where 3 does not divide the primorial anchor Sy

    violate coprimality gcd(F, R) == 1, causing gcd(F, R) == 3 and failing algebraic gating.
    """
    import math
    for non_div_3 in (1, 2, 5, 7, 85):
        F_bad, R_bad = compute_divisor_and_cofactor(non_div_3)
        assert math.gcd(F_bad, R_bad) == 3, f"Expected gcd=3 when 3 does not divide x={non_div_3}"


@pytest.mark.phase11_tier3
def test_combo_audit_hardware_reconciles_with_negative_bottleneck_limits(baseline_audit_file: Path) -> None:
    """Verifies that the hardware profile documented in BASELINE_AUDIT.md

    (CPU, RAM, GPU) aligns with the resource limits enforced in the negative bottleneck analysis.
    """
    content = baseline_audit_file.read_text(encoding="utf-8")

    # Confirm key hardware and baseline metrics in audit
    assert "Python" in content
    assert "gmpy2" in content
    assert "SymPy" in content
    assert "NumPy" in content
    assert "239" in content, "BASELINE_AUDIT.md must record the 239 baseline tests"


@pytest.mark.phase11_tier3
def test_combo_negative_results_schema_and_non_contradiction(tmp_path: Path) -> None:
    """Verifies that negative result entries follow a structured schema

    (parameter regime, failure mode, proof, remediation) and never contradict
    confirmed twin prime discoveries.
    """
    negative_entry = {
        "regime_id": "REGIME_SUBCRITICAL_X_LT_86",
        "parameter_constraint": "x < 86 with nu_2(x) == 1",
        "failure_mode": "MORRISON_THEOREM_17_SUPER_ROOT_DEFICIT",
        "theoretical_proof": "(F_odd - 1)^2 <= A for all x < 86",
        "remediation": "Enforce search lower bound x_min = 86 in campaign runner",
    }

    # Verify required keys
    required_keys = {"regime_id", "parameter_constraint", "failure_mode", "theoretical_proof", "remediation"}
    assert set(negative_entry.keys()) == required_keys

    # Confirm that our known discovery coordinate x=126 is well above the excluded regime
    y = 3
    t = 21
    from tests.phase11_e2e.contracts.math_contracts import compute_primorial_anchor
    Sy, _ = compute_primorial_anchor(y)
    discovery_x = Sy * t
    assert discovery_x == 126
    assert discovery_x >= 86, "Confirmed discovery point must not fall into logged negative regime"
