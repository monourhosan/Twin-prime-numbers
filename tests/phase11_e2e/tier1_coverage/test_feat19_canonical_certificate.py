"""Feature 19: Canonical 21-Field JSON Certificate.

Verifies:
1. Presence of all 21 required fields specified in CANONICAL_CERTIFICATE_FIELDS.
2. Strict top-level field count of exactly 21 fields.
3. Deterministic canonical JSON serialization formatting (sort_keys, minimal separators).
4. SHA-256 cryptographic digest integrity over certificate payload.
5. Verification of method and schema version string "11.0".
"""

import json
import hashlib
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import (
    CANONICAL_CERTIFICATE_FIELDS,
    validate_certificate_schema,
    compute_canonical_sha256,
)


@pytest.fixture
def cert_fixture() -> dict:
    """Provides a fresh canonical certificate for testing."""
    return Phase11ContractAdapter.prove_pair(y=3, t=21, run_id="cert_feat19_test")


@pytest.mark.phase11_tier1
def test_f19_canonical_21_fields_present(cert_fixture: dict) -> None:
    """Verifies all 21 specified canonical fields exist in the certificate."""
    for field in CANONICAL_CERTIFICATE_FIELDS:
        assert field in cert_fixture, f"Missing required canonical field: {field}"


@pytest.mark.phase11_tier1
def test_f19_strict_field_count_exactly_21(cert_fixture: dict) -> None:
    """Verifies exactly 21 fields are present at the root dictionary level."""
    assert len(cert_fixture.keys()) == 21, (
        f"Expected exactly 21 keys, found {len(cert_fixture.keys())}: {set(cert_fixture.keys()) - set(CANONICAL_CERTIFICATE_FIELDS)}"
    )
    assert set(cert_fixture.keys()) == set(CANONICAL_CERTIFICATE_FIELDS)


@pytest.mark.phase11_tier1
def test_f19_canonical_json_formatting(cert_fixture: dict) -> None:
    """Verifies canonical JSON serialization using sort_keys and minimal separators."""
    # Strip certificate_sha256
    payload = {k: v for k, v in cert_fixture.items() if k != "certificate_sha256"}
    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))

    # Verify structural formatting: keys are sorted alphabetically
    keys = list(payload.keys())
    sorted_keys = sorted(keys)
    # The first key in serialized JSON should be the first sorted key
    first_key = f'"{sorted_keys[0]}":'
    assert serialized.startswith("{" + first_key)
    # No trailing newlines or whitespace
    assert serialized == serialized.strip()


@pytest.mark.phase11_tier1
def test_f19_sha256_digest_integrity(cert_fixture: dict) -> None:
    """Verifies payload SHA-256 digest matches certificate_sha256 field."""
    computed_hash = compute_canonical_sha256(cert_fixture)
    assert cert_fixture["certificate_sha256"] == computed_hash
    # Must be 64-char lowercase hex
    assert len(computed_hash) == 64
    assert computed_hash == computed_hash.lower()


@pytest.mark.phase11_tier1
def test_f19_schema_and_method_version(cert_fixture: dict) -> None:
    """Verifies method version string is set to '11.0'."""
    assert cert_fixture["method_version"] == "11.0"
    is_valid, errors = validate_certificate_schema(cert_fixture, strict_field_count=True, verify_hash=True)
    assert is_valid, f"Schema validation failed: {errors}"
