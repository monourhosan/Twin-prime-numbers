"""Canonical schema definitions and validators for Phase 11.

Covers:
- Canonical 21-field JSON certificate schema and canonical SHA-256 digest
- JSON checkpoint schema and state integrity validation
- Attestation schema and verification verdict validation
- Historical inventory schema and uniqueness validation
"""

import json
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

# Exactly 21 canonical fields specified in Phase 11 specification Section 15
CANONICAL_CERTIFICATE_FIELDS = [
    "method_id",
    "method_version",
    "repository_commit",
    "run_id",
    "timestamp_utc",
    "hardware",
    "parameters",
    "symbolic_center",
    "lower_prime",
    "upper_prime",
    "digit_count",
    "difference",
    "factorization",
    "proof_method_lower",
    "proof_method_upper",
    "witnesses_lower",
    "witnesses_upper",
    "proof_conditions",
    "novelty_status_repository",
    "novelty_status_public",
    "certificate_sha256",
]

CHECKPOINT_REQUIRED_FIELDS = [
    "run_id",
    "method_id",
    "anchor_y",
    "current_t",
    "completed_intervals",
    "survivor_count",
    "timestamp_utc",
]

ATTESTATION_REQUIRED_FIELDS = [
    "schema_version",
    "attestation_type",
    "method",
    "target_certificate",
    "target_sha256",
    "utc_attested",
    "digits",
    "verifications",
    "verdict",
]

INVENTORY_ENTRY_REQUIRED_FIELDS = [
    "canonical_key",
    "P",
    "Q",
    "digits_P",
    "digits_Q",
    "center_C",
    "difference",
    "certificate_path",
]


def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes the deterministic canonical SHA-256 hex digest of a certificate payload.

    Excludes the 'certificate_sha256' field itself to produce the payload hash.
    Uses sorted keys and minimal whitespace separators (',', ':').
    """
    clean_payload = {k: v for k, v in data.items() if k != "certificate_sha256"}
    canonical_json = json.dumps(clean_payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def validate_certificate_schema(
    data: Dict[str, Any],
    strict_field_count: bool = True,
    verify_hash: bool = True,
) -> Tuple[bool, List[str]]:
    """Validates a Phase 11 certificate against the canonical 21-field specification.

    Returns:
        (is_valid, error_list)
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return False, ["Certificate data must be a dictionary"]

    # Check field count if strict
    if strict_field_count:
        extra_fields = set(data.keys()) - set(CANONICAL_CERTIFICATE_FIELDS)
        if extra_fields:
            errors.append(f"Extraneous fields present in certificate: {sorted(extra_fields)}")

    # Check missing fields
    missing_fields = [f for f in CANONICAL_CERTIFICATE_FIELDS if f not in data]
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields}")

    if errors:
        return False, errors

    # Field-level validation
    if not isinstance(data["method_id"], str) or not data["method_id"]:
        errors.append("Field 'method_id' must be a non-empty string")

    if not isinstance(data["method_version"], str):
        errors.append("Field 'method_version' must be a string")

    if not isinstance(data["repository_commit"], str):
        errors.append("Field 'repository_commit' must be a string")

    if not isinstance(data["run_id"], str):
        errors.append("Field 'run_id' must be a string")

    if not isinstance(data["timestamp_utc"], str):
        errors.append("Field 'timestamp_utc' must be an ISO-8601 string")

    if not isinstance(data["parameters"], dict):
        errors.append("Field 'parameters' must be a dictionary")

    if not isinstance(data["symbolic_center"], str):
        errors.append("Field 'symbolic_center' must be a string")

    # Numeric representation validation
    try:
        lower_val = int(str(data["lower_prime"]))
        upper_val = int(str(data["upper_prime"]))
    except (ValueError, TypeError):
        errors.append("Fields 'lower_prime' and 'upper_prime' must be numeric decimal strings")
        lower_val, upper_val = 0, 0

    if lower_val > 0 and upper_val > 0:
        if upper_val - lower_val != 2:
            errors.append(f"Difference upper - lower must be 2, got {upper_val - lower_val}")
        if data["difference"] != 2:
            errors.append(f"Field 'difference' must be 2, got {data['difference']}")

        actual_digits = len(str(lower_val))
        if data["digit_count"] != actual_digits:
            errors.append(f"Field 'digit_count' ({data['digit_count']}) != len(lower_prime) ({actual_digits})")

    if not isinstance(data["factorization"], dict):
        errors.append("Field 'factorization' must be a dictionary")

    if not isinstance(data["proof_method_lower"], str):
        errors.append("Field 'proof_method_lower' must be a string")

    if not isinstance(data["proof_method_upper"], str):
        errors.append("Field 'proof_method_upper' must be a string")

    if not isinstance(data["witnesses_lower"], dict):
        errors.append("Field 'witnesses_lower' must be a dictionary")

    if not isinstance(data["witnesses_upper"], dict):
        errors.append("Field 'witnesses_upper' must be a dictionary")

    if not isinstance(data["proof_conditions"], dict):
        errors.append("Field 'proof_conditions' must be a dictionary")

    # SHA-256 check
    declared_sha256 = data.get("certificate_sha256", "")
    if not isinstance(declared_sha256, str) or len(declared_sha256) != 64:
        errors.append("Field 'certificate_sha256' must be a 64-character hex string")
    elif verify_hash:
        expected_sha256 = compute_canonical_sha256(data)
        if declared_sha256.lower() != expected_sha256.lower():
            errors.append(
                f"SHA-256 digest mismatch: declared={declared_sha256}, computed={expected_sha256}"
            )

    return (len(errors) == 0, errors)


def validate_checkpoint_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates search checkpoint JSON state."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Checkpoint data must be a dictionary"]

    for field in CHECKPOINT_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing checkpoint field: {field}")

    if errors:
        return False, errors

    if not isinstance(data["run_id"], str):
        errors.append("Field 'run_id' must be a string")
    if not isinstance(data["method_id"], str):
        errors.append("Field 'method_id' must be a string")
    if not isinstance(data["anchor_y"], int) or data["anchor_y"] <= 0:
        errors.append("Field 'anchor_y' must be a positive integer")
    if not isinstance(data["current_t"], int) or data["current_t"] < 0:
        errors.append("Field 'current_t' must be a non-negative integer")
    if not isinstance(data["completed_intervals"], list):
        errors.append("Field 'completed_intervals' must be a list of intervals")
    if not isinstance(data["survivor_count"], int) or data["survivor_count"] < 0:
        errors.append("Field 'survivor_count' must be a non-negative integer")
    if not isinstance(data["timestamp_utc"], str):
        errors.append("Field 'timestamp_utc' must be an ISO-8601 string")

    return (len(errors) == 0, errors)


def validate_attestation_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates verifier attestation JSON payload."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Attestation data must be a dictionary"]

    for field in ATTESTATION_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing attestation field: {field}")

    if errors:
        return False, errors

    if data["verdict"] not in ("UNCONDITIONALLY_VERIFIED", "VERIFIED", "PASS", "FAIL"):
        errors.append(f"Unexpected verdict: {data['verdict']}")

    if not isinstance(data["target_sha256"], str) or len(data["target_sha256"]) != 64:
        errors.append("Field 'target_sha256' must be a 64-char hex string")

    if not isinstance(data["verifications"], dict):
        errors.append("Field 'verifications' must be a dictionary")

    return (len(errors) == 0, errors)


def validate_historical_inventory_schema(data: Any) -> Tuple[bool, List[str]]:
    """Validates historical inventory list structure and individual entries."""
    errors: List[str] = []
    if not isinstance(data, list):
        return False, ["Historical inventory data must be a list of records"]

    seen_keys = set()
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Entry #{idx} is not a dictionary")
            continue

        for req in INVENTORY_ENTRY_REQUIRED_FIELDS:
            if req not in item:
                errors.append(f"Entry #{idx} missing required field: {req}")

        # Check difference and key uniqueness
        canon_key = item.get("canonical_key")
        if canon_key:
            if canon_key in seen_keys:
                errors.append(f"Duplicate entry found in inventory: {canon_key}")
            seen_keys.add(canon_key)

        p_str = item.get("P")
        q_str = item.get("Q")
        if p_str and q_str:
            try:
                p_val = int(str(p_str))
                q_val = int(str(q_str))
                if q_val - p_val != 2:
                    errors.append(f"Entry #{idx} ({canon_key}) does not have gap 2: {q_val - p_val}")
            except (ValueError, TypeError):
                errors.append(f"Entry #{idx} contains non-integer prime representations")

    return (len(errors) == 0, errors)
