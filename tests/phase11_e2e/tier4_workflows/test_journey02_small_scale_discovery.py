"""Tier 4 Workflow 2: Small Scale Twin-Prime Discovery User Journey.

Covers the complete, live end-to-end computational discovery pipeline:
1. Primorial anchor setup (y=3, Sy=6, factor decomposition).
2. Sieve progression setup with small-prime preservation.
3. Symmetric Quintic Modular Sieve execution.
4. Multi-tier screening pipeline (trial division, Fermat base-2, Miller-Rabin, Baillie-PSW) -> DUAL_PRP.
5. Deterministic Dual-BLS proving (Pocklington Theorem 4 on B + Morrison Theorem 17 on A).
6. Canonical 21-field JSON certificate generation and SHA-256 digest computation.
7. Independent standalone verification and attestation payload emission.
8. Dual novelty verification confirming repository uniqueness.
"""

import json
from pathlib import Path
import pytest

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    get_odd_part,
    check_algebraic_invariants,
    prove_pocklington_upper,
    prove_morrison_lower,
)
from tests.phase11_e2e.contracts.schemas import (
    validate_certificate_schema,
    validate_attestation_schema,
)


@pytest.mark.phase11_tier4
def test_journey02_end_to_end_small_scale_discovery(tmp_path: Path) -> None:
    """Executes the full discovery journey from anchor initialization through

    sieve, screening, proving, certificate emission, and independent verification.
    """
    # Step 1: Primorial Anchor initialization
    y = 3
    Sy, Sy_factors = compute_primorial_anchor(y)
    assert Sy == 6
    assert Sy % 6 == 0

    # Step 2 & 3: Sieve and identify candidate (known twin at t=21 -> x=126)
    target_t = 21
    survivors = Phase11ContractAdapter.sieve_survivors(y, t_start=15, t_end=25, sieve_depth=30)
    assert target_t in survivors, f"Target t={target_t} was unexpectedly eliminated by sieve"

    # Step 4: Multi-tier screening
    status, pair = Phase11ContractAdapter.screen_candidate(y, target_t)
    assert status == "DUAL_PRP", f"Expected DUAL_PRP at t={target_t}, got {status}"
    assert pair is not None
    C, A, B = pair
    assert B - A == 2
    assert C % 6 == 0

    # Step 5: Dual-BLS Certification
    x = Sy * target_t
    F, R = compute_divisor_and_cofactor(x)
    factors_F = compute_factors_of_F(Sy_factors, {3: 1, 7: 1})
    F_odd = get_odd_part(F)

    # Prove upper member B (Pocklington)
    ok_upper, witnesses_upper = prove_pocklington_upper(B, F, factors_F)
    assert ok_upper is True
    assert len(witnesses_upper) == len(factors_F)

    # Prove lower member A (Morrison)
    ok_lower, morrison_result = prove_morrison_lower(A, F_odd, factors_F)
    assert ok_lower is True
    assert morrison_result["jacobi_symbol"] == -1
    assert "2" not in morrison_result["factor_gcds"]

    # Step 6: Generate canonical 21-field JSON certificate
    cert = Phase11ContractAdapter.prove_pair(y, target_t, run_id="journey02_discovery")
    is_valid_schema, schema_errs = validate_certificate_schema(cert, strict_field_count=True, verify_hash=True)
    assert is_valid_schema is True, f"Certificate schema failed: {schema_errs}"
    assert cert["difference"] == 2
    assert int(cert["upper_prime"]) - int(cert["lower_prime"]) == 2

    cert_path = tmp_path / "cert_journey02.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    # Step 7: Independent Standalone Verifier invocation
    attestation_dir = tmp_path / "attestations"
    attestation_dir.mkdir(parents=True, exist_ok=True)
    is_verified, logs, attestation = Phase11ContractAdapter.verify_certificate(cert_path, attestation_dir=attestation_dir)
    assert is_verified is True, f"Independent verifier failed: {logs}"
    if "verdict" in attestation:
        ok_attest, attest_errs = validate_attestation_schema(attestation)
        assert ok_attest is True, f"Attestation schema invalid: {attest_errs}"

    # Step 8: Novelty verification
    novelty = Phase11ContractAdapter.check_novelty(A, B)
    assert novelty == "NOVEL_TO_REPOSITORY"


@pytest.mark.phase11_tier4
def test_journey02_composite_rejection_workflow() -> None:
    """Journey variation: verifies the complete failure handling workflow when non-twin

    or composite candidates are processed through the discovery pipeline.
    """
    y = 3
    # t=1 produces composite pair at x=6
    status, pair = Phase11ContractAdapter.screen_candidate(y, 1)
    assert status in ("COMPOSITE", "SINGLE_PRP")

    # Pipeline stops: prover and certificate generation are rejected
    with pytest.raises(ValueError, match="did not pass primality screening"):
        Phase11ContractAdapter.prove_pair(y, 1)


@pytest.mark.phase11_tier4
def test_journey02_tampered_discovery_certificate_fails_attestation(tmp_path: Path) -> None:
    """Journey variation: verifies that if an in-flight certificate is intercepted or tampered

    prior to standalone verification, attestation is refused with an error verdict.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="journey02_tamper_flight")
    # Mutate the coordinate string in parameters
    cert["parameters"]["x"] = "999999"

    cert_path = tmp_path / "cert_tampered_flight.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    is_verified, logs, _ = Phase11ContractAdapter.verify_certificate(cert_path)
    assert is_verified is False, "Tampered in-flight certificate must fail independent verification"
