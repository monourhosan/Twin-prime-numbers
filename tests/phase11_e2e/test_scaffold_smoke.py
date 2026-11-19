"""Phase 11 E2E Scaffold Smoke Test.

Validates:
1. Pytest configuration and custom marker registration.
2. Phase11ContractAdapter mode switching (AUTO, LIVE, STUB).
3. OPQM-11 mathematical invariants (gap B-A=2, C mod 6 = 0, gcd(F, R) = 1).
4. Super-root inequalities (F^2 > B, (F_odd - 1)^2 > A, boundary x=85 vs x=86).
5. Sieve root-negation symmetry (r_A = q - r_B mod q) and inert moduli (-2/q = -1).
6. Multi-tier screening pipeline (trial division, Fermat base-2, Miller-Rabin, Baillie-PSW).
7. Dual-BLS provers (Pocklington Theorem 4, Morrison Theorem 17 with odd divisor guard).
8. Canonical 21-field JSON certificate generation, schema validation, and SHA-256 integrity.
9. Checkpoint and attestation schema validation helpers.
10. Historical inventory validation and novelty checking against repository records.
"""

import os
import math
import json
import pytest
from pathlib import Path
from typing import Dict, Any

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    get_odd_part,
    check_algebraic_invariants,
    sieve_roots_mod_q,
    verify_root_negation_symmetry,
    is_inert_modulus,
    trial_division,
    fermat_base2,
    miller_rabin,
    baillie_psw,
    screen_candidate,
    prove_pocklington_upper,
    prove_morrison_lower,
    standalone_lucas_u,
    generate_reference_certificate,
)
from tests.phase11_e2e.contracts.schemas import (
    CANONICAL_CERTIFICATE_FIELDS,
    compute_canonical_sha256,
    validate_certificate_schema,
    validate_checkpoint_schema,
    validate_attestation_schema,
    validate_historical_inventory_schema,
)


@pytest.mark.phase11_tier1
def test_pytest_configuration(pytestconfig: pytest.Config) -> None:
    """Confirms pytest configuration, pythonpath, and marker definitions."""
    markers = pytestconfig.getini("markers")
    marker_str = " ".join(markers)
    assert "phase11_tier1" in marker_str
    assert "phase11_tier2" in marker_str
    assert "phase11_tier3" in marker_str
    assert "phase11_tier4" in marker_str
    assert "slow" in marker_str


@pytest.mark.phase11_tier1
def test_contract_adapter_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies that Phase11ContractAdapter responds to AUTO, STUB, and LIVE modes."""
    # 1. AUTO mode (default)
    monkeypatch.setenv("PHASE11_TEST_MODE", "AUTO")
    assert Phase11ContractAdapter.get_mode() == "AUTO"
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(3, 1)
    assert B - A == 2

    # 2. STUB mode
    monkeypatch.setenv("PHASE11_TEST_MODE", "STUB")
    assert Phase11ContractAdapter.get_mode() == "STUB"
    C_stub, A_stub, B_stub = Phase11ContractAdapter.compute_candidate_pair(3, 1)
    assert (C_stub, A_stub, B_stub) == (C, A, B)

    # 3. LIVE mode enforcement: when src.phase11 is absent, raises RuntimeError
    monkeypatch.setenv("PHASE11_TEST_MODE", "LIVE")
    assert Phase11ContractAdapter.get_mode() == "LIVE"
    if not Phase11ContractAdapter.is_live_available():
        with pytest.raises(RuntimeError, match="LIVE mode requested"):
            Phase11ContractAdapter.compute_candidate_pair(3, 1)


@pytest.mark.phase11_tier1
def test_opqm11_algebraic_invariants() -> None:
    """Verifies algebraic invariants for OPQM-11 manifold across multiple coordinate scales.

    Invariants:
      1. B(x) - A(x) == 2
      2. C(x) == 0 mod 6
      3. C(x) == F(x) * R(x) where F(x) = 6x^3, R(x) = 2x^2 + 1
      4. gcd(F(x), R(x)) == 1 when 6 | x
    """
    # Multiples of 6 (guaranteed by 6 | S_y in OPQM-11)
    for x in (6, 12, 18, 24, 30, 90, 126, 174, 210, 600, 1002):
        inv = check_algebraic_invariants(x)
        assert inv["difference_is_2"], f"Gap violation at x={x}: {inv['difference']}"
        assert inv["center_mod_6_is_0"], f"Mod 6 violation at x={x}: {inv['center_mod_6']}"
        assert inv["factor_cofactor_product_match"], f"Product mismatch at x={x}"
        assert inv["coprimality_holds"], f"gcd(F, R) != 1 at x={x}: {inv['gcd_F_R']}"
        assert inv["F_squared_greater_than_B"], f"F^2 <= B at x={x}"

    # Confirm that 6 | S_y is essential: if 3 does not divide x, gcd(F, R) = 3
    for non_div_3 in (1, 2, 85, 86, 100, 1000):
        F_bad, R_bad = compute_divisor_and_cofactor(non_div_3)
        assert math.gcd(F_bad, R_bad) == 3, f"Expected gcd=3 when 3 does not divide x={non_div_3}"


@pytest.mark.phase11_tier2
def test_super_root_inequalities_boundary() -> None:
    """Verifies the super-root boundary crossover at x=85 vs x=86.

    For nu_2(x) = 1 (e.g. x = 2 * odd):
      F = 6*x^3 has factor 2^(1+3) = 16.
      F_odd = (6*x^3)/16 = (3/8)*x^3.
      At x = 85: (F_odd - 1)^2 < A(x) (fails Morrison bound).
      At x = 86: (F_odd - 1)^2 > A(x) (passes Morrison bound).
    """
    # x = 85
    C_85 = 12 * (85 ** 5) + 6 * (85 ** 3)
    A_85 = C_85 - 1
    F_odd_85 = (6 * (85 ** 3)) // 16
    morrison_85 = (F_odd_85 - 1) ** 2
    assert morrison_85 <= A_85, f"Expected x=85 to fail Morrison bound: {morrison_85} > {A_85}"

    # x = 86
    C_86 = 12 * (86 ** 5) + 6 * (86 ** 3)
    A_86 = C_86 - 1
    F_odd_86 = (6 * (86 ** 3)) // 16
    morrison_86 = (F_odd_86 - 1) ** 2
    assert morrison_86 > A_86, f"Expected x=86 to pass Morrison bound: {morrison_86} <= {A_86}"

    # F^2 > B holds for all x >= 1
    for x in range(1, 20):
        C, A, B = compute_manifold(x)
        F, R = compute_divisor_and_cofactor(x)
        assert F * F > B, f"F^2 <= B at x={x}"


@pytest.mark.phase11_tier1
def test_sieve_symmetry_and_inert_moduli() -> None:
    """Verifies modular sieve symmetry and inert modulus classification.

    1. Sieve root-negation symmetry: r_B = (q - r_A) mod q.
    2. Inert moduli: (-2/q) = -1 <=> q = 5, 7 mod 8.
       When inert, the quadratic cofactor R(x) = 2x^2 + 1 has zero roots mod q.
    """
    test_primes = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    for q in test_primes:
        assert verify_root_negation_symmetry(q), f"Root-negation symmetry failed for q={q}"

        inert = is_inert_modulus(q)
        if q % 8 in (5, 7):
            assert inert is True
            # Verify R(x) = 2x^2 + 1 mod q has NO roots
            r_roots = [x for x in range(q) if (2 * x * x + 1) % q == 0]
            assert len(r_roots) == 0, f"Expected R(x) to have 0 roots for inert q={q}, got {r_roots}"
        else:
            assert inert is False


@pytest.mark.phase11_tier1
def test_multi_tier_screening() -> None:
    """Tests the multi-tier screening pipeline: trial division, Fermat, MR, Baillie-PSW."""
    # Known primes
    assert trial_division(101) is True
    assert fermat_base2(101) is True
    assert miller_rabin(101) is True
    assert baillie_psw(101) is True

    # Carmichael number 561 = 3 * 11 * 17
    carmichael = 561
    assert fermat_base2(carmichael) is True, "Carmichael 561 passes Fermat base 2"
    assert miller_rabin(carmichael) is False, "Carmichael 561 must fail Miller-Rabin"
    assert baillie_psw(carmichael) is False, "Carmichael 561 must fail Baillie-PSW"

    # Known twin prime candidate pair at x = 126
    C, A, B = compute_manifold(126)
    status, pair = screen_candidate(A, B)
    assert status == "DUAL_PRP"
    assert pair == (A, B)


@pytest.mark.phase11_tier1
def test_dual_bls_certification() -> None:
    """Verifies Pocklington Theorem 4 on B and Morrison Theorem 17 on A (with odd divisor guard)."""
    # Candidate pair at x = 126 = S_3 * 21 = 6 * 21
    y = 3
    Sy, Sy_factors = compute_primorial_anchor(y)
    t = 21
    x = Sy * t
    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)
    t_factors = {3: 1, 7: 1}  # 21 = 3 * 7
    factors_F = compute_factors_of_F(Sy_factors, t_factors)
    F_odd = get_odd_part(F)

    # 1. Pocklington upper member B proof
    ok_upper, witnesses_B = prove_pocklington_upper(B, F, factors_F)
    assert ok_upper is True, "Upper member B failed Pocklington proof"
    assert len(witnesses_B) == len(factors_F)

    # 2. Morrison lower member A proof
    ok_lower, morrison_result = prove_morrison_lower(A, F_odd, factors_F)
    assert ok_lower is True, "Lower member A failed Morrison proof"
    assert "2" not in morrison_result["factor_gcds"], "Morrison singularity guard: factor 2 must be excluded"
    assert morrison_result["discriminant_D"] == morrison_result["parameter_P"] ** 2 - 4
    assert morrison_result["jacobi_symbol"] == -1


@pytest.mark.phase11_tier1
def test_canonical_certificate_generation_and_schema(tmp_path: Path) -> None:
    """Generates a complete 21-field canonical certificate and validates its schema and SHA-256."""
    cert = generate_reference_certificate(3, 21, run_id="smoke_test_run")

    # 1. Check exact field count and membership
    assert len(cert) == 21, f"Expected 21 fields, got {len(cert)}: {sorted(cert.keys())}"
    for field in CANONICAL_CERTIFICATE_FIELDS:
        assert field in cert, f"Missing canonical field: {field}"

    # 2. Schema validation
    is_valid, errors = validate_certificate_schema(cert, strict_field_count=True, verify_hash=True)
    assert is_valid is True, f"Schema validation failed: {errors}"

    # 3. Hash tamper detection
    tampered_cert = dict(cert)
    tampered_cert["certificate_sha256"] = "0" * 64
    is_valid_t, errors_t = validate_certificate_schema(tampered_cert, verify_hash=True)
    assert is_valid_t is False
    assert any("SHA-256 digest mismatch" in e for e in errors_t)

    # 4. Save and verify via adapter
    cert_file = tmp_path / "cert_smoke.json"
    with open(cert_file, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    ok, logs, attestation = Phase11ContractAdapter.verify_certificate(cert_file)
    assert ok is True
    assert attestation["verdict"] == "UNCONDITIONALLY_VERIFIED"


@pytest.mark.phase11_tier1
def test_checkpoint_and_attestation_schemas() -> None:
    """Tests JSON checkpoint and attestation schema validators."""
    # Valid checkpoint
    valid_cp = {
        "run_id": "cp_01",
        "method_id": "OPQM_CRT_HYBRID_11",
        "anchor_y": 5,
        "current_t": 500,
        "completed_intervals": [[1, 500]],
        "survivor_count": 12,
        "timestamp_utc": "2026-11-18T07:00:00+00:00",
    }
    ok_cp, errs_cp = validate_checkpoint_schema(valid_cp)
    assert ok_cp is True, f"Checkpoint validation failed: {errs_cp}"

    # Corrupted checkpoint (missing field)
    bad_cp = dict(valid_cp)
    del bad_cp["survivor_count"]
    ok_bad, errs_bad = validate_checkpoint_schema(bad_cp)
    assert ok_bad is False
    assert any("survivor_count" in e for e in errs_bad)

    # Valid attestation
    valid_att = {
        "schema_version": "11.0",
        "attestation_type": "INDEPENDENT_STRICT_MATHEMATICAL_VERIFICATION",
        "method": "OPQM_CRT_HYBRID_11",
        "target_certificate": "cert_test.json",
        "target_sha256": "a" * 64,
        "utc_attested": "2026-11-18T07:00:00+00:00",
        "digits": 12,
        "verifications": {"difference_check": "PASS"},
        "verdict": "UNCONDITIONALLY_VERIFIED",
    }
    ok_att, errs_att = validate_attestation_schema(valid_att)
    assert ok_att is True, f"Attestation validation failed: {errs_att}"


@pytest.mark.phase11_tier1
def test_adapter_sieve_and_novelty() -> None:
    """Verifies adapter sieve execution and historical inventory novelty checking."""
    # 1. Sieve execution on small interval
    survivors = Phase11ContractAdapter.sieve_survivors(3, 1, 30, sieve_depth=50)
    assert isinstance(survivors, list)
    # 21 should survive since x=126 generates prime pair
    assert 21 in survivors

    # 2. Historical inventory schema check
    inv_path = Path("research/phase9/historical_inventory.json")
    if inv_path.is_file():
        with open(inv_path, "r", encoding="utf-8") as f:
            inv_data = json.load(f)
        ok_inv, errs_inv = validate_historical_inventory_schema(inv_data)
        assert ok_inv is True, f"Historical inventory schema invalid: {errs_inv}"

        # 3. Novelty check on existing pair vs new pair
        p_hist = int(inv_data[0]["P"])
        q_hist = int(inv_data[0]["Q"])
        assert Phase11ContractAdapter.check_novelty(p_hist, q_hist) == "ALREADY_IN_REPOSITORY"
        assert Phase11ContractAdapter.check_novelty(381107634767, 381107634769) == "NOVEL_TO_REPOSITORY"
