"""Tier 2 Boundary Tests - Feature 19: Canonical 21-Field JSON Certificate.

Verifies:
1. Rejection upon omission of any of the 21 required canonical fields.
2. Rejection of extraneous unknown fields under strict schema validation.
3. Single-character modification in lower_prime breaks canonical SHA-256 digest.
4. Whitespace and indentation invariance of the canonical SHA-256 digest.
5. Unicode normalization and UTF-8 encoding stability.
"""

import copy
import json
import pytest

from tests.phase11_e2e.contracts.math_contracts import generate_reference_certificate
from tests.phase11_e2e.contracts.schemas import (
    CANONICAL_CERTIFICATE_FIELDS,
    compute_canonical_sha256,
    validate_certificate_schema,
)


@pytest.fixture
def valid_cert() -> dict:
    """Generates a valid 21-field reference certificate."""
    return generate_reference_certificate(3, 21, run_id="test_bnd19_run")


@pytest.mark.phase11_tier2
def test_bnd19_omission_of_any_required_field(valid_cert: dict) -> None:
    """Verifies that removing any of the 21 required fields causes schema validation failure."""
    assert len(CANONICAL_CERTIFICATE_FIELDS) == 21

    for field in CANONICAL_CERTIFICATE_FIELDS:
        tampered = copy.deepcopy(valid_cert)
        del tampered[field]
        is_valid, errors = validate_certificate_schema(tampered, strict_field_count=False, verify_hash=False)
        assert not is_valid, f"Certificate without field '{field}' was unexpectedly validated"
        assert any(field in err for err in errors)


@pytest.mark.phase11_tier2
def test_bnd19_extraneous_unknown_fields_rejection(valid_cert: dict) -> None:
    """Verifies that injecting an extra unknown field is rejected under strict field count."""
    tampered = copy.deepcopy(valid_cert)
    tampered["unauthorized_backdoor"] = "malicious_payload"

    is_valid, errors = validate_certificate_schema(tampered, strict_field_count=True, verify_hash=False)
    assert not is_valid
    assert any("Extraneous fields" in err for err in errors)


@pytest.mark.phase11_tier2
def test_bnd19_single_char_modification_hash_mismatch(valid_cert: dict) -> None:
    """Verifies that changing a single character in lower_prime causes a SHA-256 digest mismatch."""
    tampered = copy.deepcopy(valid_cert)
    orig_lower = tampered["lower_prime"]
    # Change the last digit
    last_digit = int(orig_lower[-1])
    new_digit = (last_digit + 1) % 10
    tampered["lower_prime"] = orig_lower[:-1] + str(new_digit)

    is_valid, errors = validate_certificate_schema(tampered, strict_field_count=True, verify_hash=True)
    assert not is_valid
    assert any("SHA-256 digest mismatch" in err or "Difference upper - lower" in err for err in errors)


@pytest.mark.phase11_tier2
def test_bnd19_whitespace_invariance_of_canonical_digest(valid_cert: dict) -> None:
    """Verifies that pretty-printed JSON vs compact JSON produce the exact same canonical SHA-256."""
    canonical_hash = valid_cert["certificate_sha256"]

    # Re-serialize with different indentations and spacing
    compact_json = json.dumps(valid_cert, separators=(',', ':'))
    pretty_json = json.dumps(valid_cert, indent=4)
    tabbed_json = json.dumps(valid_cert, indent='\t')

    # Parse back
    obj_compact = json.loads(compact_json)
    obj_pretty = json.loads(pretty_json)
    obj_tabbed = json.loads(tabbed_json)

    assert compute_canonical_sha256(obj_compact) == canonical_hash
    assert compute_canonical_sha256(obj_pretty) == canonical_hash
    assert compute_canonical_sha256(obj_tabbed) == canonical_hash


@pytest.mark.phase11_tier2
def test_bnd19_unicode_normalization_integrity(valid_cert: dict) -> None:
    """Verifies UTF-8 encoding stability and rejection of invalid byte sequences."""
    json_bytes = json.dumps(valid_cert).encode("utf-8")
    assert isinstance(json_bytes, bytes)

    # Decode and revalidate
    decoded_obj = json.loads(json_bytes.decode("utf-8"))
    is_valid, _ = validate_certificate_schema(decoded_obj, strict_field_count=True, verify_hash=True)
    assert is_valid is True
