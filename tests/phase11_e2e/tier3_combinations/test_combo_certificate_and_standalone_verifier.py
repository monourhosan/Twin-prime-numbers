"""Tier 3 Integration Suite 5: Canonical Certificate (F19) x Standalone Verifier (F20).

Validates the pairwise interaction between:
1. Canonical 21-Field JSON Certificate.
2. Isolated Standalone Verifier (independent first-principles verification with zero search engine imports).
"""

import json
import pytest
from pathlib import Path
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import (
    validate_certificate_schema,
    validate_attestation_schema,
)


@pytest.mark.phase11_tier3
def test_combo_valid_certificate_unconditionally_verified(tmp_path: Path) -> None:
    """Verifies that a genuine canonical certificate is unconditionally verified

    by the standalone verifier, returning exit code 0 and an official attestation payload.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="verifier_valid_test")
    cert_path = tmp_path / "cert_opqm11_valid.json"
    attestation_dir = tmp_path / "attestations"
    attestation_dir.mkdir(parents=True, exist_ok=True)

    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    is_valid, logs, attestation = Phase11ContractAdapter.verify_certificate(cert_path, attestation_dir=attestation_dir)

    assert is_valid is True, f"Verifier rejected valid certificate: {logs}"
    assert "UNCONDITIONALLY_VERIFIED" in str(attestation.get("verdict")) or "exit_code" in attestation
    if "verdict" in attestation:
        ok_attest, errs = validate_attestation_schema(attestation)
        assert ok_attest is True, f"Attestation schema invalid: {errs}"


@pytest.mark.phase11_tier3
def test_combo_verifier_rejects_tampered_sha256(tmp_path: Path) -> None:
    """Confirms that the standalone verifier detects and rejects certificates

    with a tampered SHA-256 digest.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="tamper_hash_test")
    # Corrupt one hex character in the hash
    corrupted_hash = "0" + cert["certificate_sha256"][1:]
    cert["certificate_sha256"] = corrupted_hash

    cert_path = tmp_path / "cert_tampered_hash.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    is_valid, logs, _ = Phase11ContractAdapter.verify_certificate(cert_path)
    assert is_valid is False, "Verifier must reject tampered SHA-256 digest"
    assert any("SHA-256" in line or "mismatch" in line or "exit_code" in str(logs) for line in logs)


@pytest.mark.phase11_tier3
def test_combo_verifier_rejects_tampered_gap(tmp_path: Path) -> None:
    """Confirms that the standalone verifier detects and rejects certificates

    where the difference B - A != 2 (gap violation).
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="tamper_gap_test")
    # Tamper upper prime to make gap != 2
    cert["upper_prime"] = str(int(cert["upper_prime"]) + 2)
    cert["difference"] = 4
    # Recompute hash so hash check passes, forcing the mathematical gap check to fail
    from tests.phase11_e2e.contracts.schemas import compute_canonical_sha256
    cert["certificate_sha256"] = compute_canonical_sha256(cert)

    cert_path = tmp_path / "cert_tampered_gap.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    is_valid, logs, _ = Phase11ContractAdapter.verify_certificate(cert_path)
    assert is_valid is False, "Verifier must reject certificates with gap != 2"


@pytest.mark.phase11_tier3
def test_combo_verifier_rejects_underfactored_or_invalid_proof(tmp_path: Path) -> None:
    """Confirms that the standalone verifier detects and rejects certificates

    where the divisor F is insufficient to satisfy the Pocklington size condition (F^2 > B),
    even if the certificate JSON schema and hash are internally self-consistent.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="insufficient_F_test")
    # Tamper F so that F^2 <= B
    cert["parameters"]["F"] = "10"
    cert["factorization"]["factors_F"] = {"2": 1, "5": 1}

    from tests.phase11_e2e.contracts.schemas import compute_canonical_sha256
    cert["certificate_sha256"] = compute_canonical_sha256(cert)

    cert_path = tmp_path / "cert_insufficient_F.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    is_valid, logs, _ = Phase11ContractAdapter.verify_certificate(cert_path)
    assert is_valid is False, "Verifier must reject certificates failing Pocklington condition"


@pytest.mark.phase11_tier3
def test_combo_verifier_handles_nonexistent_or_malformed_path(tmp_path: Path) -> None:
    """Confirms that the verifier handles non-existent or unparseable JSON files gracefully

    returning False rather than an unhandled crash.
    """
    non_existent = tmp_path / "does_not_exist.json"
    is_valid, logs, _ = Phase11ContractAdapter.verify_certificate(non_existent)
    assert is_valid is False

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{this is not valid json:", encoding="utf-8")
    is_valid_malformed, logs_malformed, _ = Phase11ContractAdapter.verify_certificate(malformed)
    assert is_valid_malformed is False
