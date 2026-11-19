"""Tier 3 Integration Suite 4: Dual-BLS Prover (F17) x Canonical Certificate Builder (F19).

Validates the pairwise interaction between:
1. Deterministic Dual-BLS Certification (Pocklington and Morrison provers).
2. Canonical 21-Field JSON Certificate generation, canonical serialization, and SHA-256 hashing.
"""

import copy
import json
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import (
    CANONICAL_CERTIFICATE_FIELDS,
    compute_canonical_sha256,
    validate_certificate_schema,
)


@pytest.mark.phase11_tier3
def test_combo_prover_output_maps_to_canonical_21_fields() -> None:
    """Verifies that the certificate generated from the Dual-BLS prover

    contains exactly the 21 canonical fields specified in the Phase 11 standard.
    """
    # y=3, t=21 is a verified DUAL_PRP with x=126
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="test_combo_prover_cert_01")

    assert isinstance(cert, dict)
    assert len(cert.keys()) == 21, f"Expected exactly 21 fields, got {len(cert.keys())}"
    assert set(cert.keys()) == set(CANONICAL_CERTIFICATE_FIELDS)

    # Validate against schema validator
    is_valid, errors = validate_certificate_schema(cert, strict_field_count=True, verify_hash=True)
    assert is_valid is True, f"Certificate failed schema validation: {errors}"


@pytest.mark.phase11_tier3
def test_combo_certificate_canonical_sha256_digest_integrity() -> None:
    """Verifies that the canonical SHA-256 digest is deterministically computed

    excluding the 'certificate_sha256' field itself, and matches the recorded hash.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="sha256_integrity_check")

    declared_hash = cert["certificate_sha256"]
    computed_hash = compute_canonical_sha256(cert)

    assert len(declared_hash) == 64
    assert declared_hash == computed_hash


@pytest.mark.phase11_tier3
def test_combo_certificate_tamper_detection_in_witnesses() -> None:
    """Confirms that tampering with any prover witness (Pocklington base or Morrison parameter)

    invalidates the certificate hash and is flagged by the schema validator.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="tamper_test")

    # 1. Tamper with Pocklington witness
    tampered_upper = copy.deepcopy(cert)
    first_factor = list(tampered_upper["witnesses_upper"].keys())[0]
    tampered_upper["witnesses_upper"][first_factor] += 1  # Alter witness base

    is_valid, errors = validate_certificate_schema(tampered_upper, strict_field_count=True, verify_hash=True)
    assert is_valid is False
    assert any("SHA-256 digest mismatch" in err for err in errors)

    # 2. Tamper with Morrison parameter P
    tampered_lower = copy.deepcopy(cert)
    tampered_lower["witnesses_lower"]["parameter_P"] += 2

    is_valid, errors = validate_certificate_schema(tampered_lower, strict_field_count=True, verify_hash=True)
    assert is_valid is False
    assert any("SHA-256 digest mismatch" in err for err in errors)


@pytest.mark.phase11_tier3
def test_combo_certificate_strict_field_count_enforcement() -> None:
    """Verifies that introducing unexpected or unauthorized fields causes immediate failure

    under strict canonical schema enforcement.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="strict_fields_test")

    cert_extra = copy.deepcopy(cert)
    cert_extra["unauthorized_debug_metadata"] = {"status": "injected"}

    is_valid, errors = validate_certificate_schema(cert_extra, strict_field_count=True, verify_hash=False)
    assert is_valid is False
    assert any("Extraneous fields present" in err for err in errors)


@pytest.mark.phase11_tier3
def test_combo_certificate_serialization_roundtrip_stability(tmp_path) -> None:
    """Verifies that writing the certificate to disk as JSON and reloading it

    preserves bit-exact content and identical canonical SHA-256 digest.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="roundtrip_test")
    file_path = tmp_path / "cert_test.json"

    # Write out with standard canonical formatting
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    with open(file_path, "r", encoding="utf-8") as f:
        loaded_cert = json.load(f)

    is_valid, errors = validate_certificate_schema(loaded_cert, strict_field_count=True, verify_hash=True)
    assert is_valid is True, f"Reloaded certificate failed validation: {errors}"
    assert loaded_cert["certificate_sha256"] == cert["certificate_sha256"]
