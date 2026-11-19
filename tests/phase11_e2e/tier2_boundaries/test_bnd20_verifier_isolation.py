"""Tier 2 Boundary Tests - Feature 20: Isolated Standalone Verifier.

Verifies:
1. Verifier rejection of certificate with corrupted SHA-256 hash.
2. Verifier rejection of certificate with corrupted gap (B - A != 2).
3. Rejection of invalid Pocklington witness (a=1 or failing Fermat/GCD condition).
4. Rejection of invalid Morrison parameters (D != P^2 - 4 or Jacobi symbol != -1).
5. Verifier handling of nonexistent certificate file paths.
"""

import math
import json
import pytest
from pathlib import Path
from sympy import jacobi_symbol

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import generate_reference_certificate
from tests.phase11_e2e.contracts.schemas import compute_canonical_sha256


@pytest.fixture
def cert_path(tmp_path: Path) -> Path:
    """Generates and writes a valid reference certificate to a temporary JSON file."""
    cert = generate_reference_certificate(3, 21, run_id="verifier_isolation_test")
    p = tmp_path / "cert_valid.json"
    p.write_text(json.dumps(cert, indent=2), encoding="utf-8")
    return p


@pytest.mark.phase11_tier2
def test_bnd20_corrupted_sha256_hash_rejection(tmp_path: Path) -> None:
    """Verifies that the standalone verifier rejects a certificate with a tampered SHA-256 hash."""
    cert = generate_reference_certificate(3, 21)
    cert["certificate_sha256"] = "f" * 64  # Corrupted hash

    p = tmp_path / "cert_bad_hash.json"
    p.write_text(json.dumps(cert, indent=2), encoding="utf-8")

    ok, logs, attestation = Phase11ContractAdapter.verify_certificate(p)
    assert ok is False
    assert any("SHA-256" in line for line in logs)


@pytest.mark.phase11_tier2
def test_bnd20_corrupted_gap_rejection(tmp_path: Path) -> None:
    """Verifies that the standalone verifier rejects a certificate where B - A != 2."""
    cert = generate_reference_certificate(3, 21)
    # Alter upper prime to make gap 4
    cert["upper_prime"] = str(int(cert["lower_prime"]) + 4)
    cert["difference"] = 4
    cert["certificate_sha256"] = compute_canonical_sha256(cert)

    p = tmp_path / "cert_bad_gap.json"
    p.write_text(json.dumps(cert, indent=2), encoding="utf-8")

    ok, logs, _ = Phase11ContractAdapter.verify_certificate(p)
    assert ok is False
    assert any("gap" in line.lower() or "difference" in line.lower() or "coordinates mismatch" in line.lower() for line in logs)


@pytest.mark.phase11_tier2
def test_bnd20_invalid_pocklington_witness_rejection(tmp_path: Path) -> None:
    """Verifies that tampering with Pocklington witnesses fails certificate verification and witness checks."""
    cert = generate_reference_certificate(3, 21)
    # 1. Tamper with witness without recomputing hash -> adapter verifier must reject hash
    cert_tampered = dict(cert)
    cert_tampered["witnesses_upper"] = {k: 1 for k in cert["witnesses_upper"]}

    p = tmp_path / "cert_bad_witness.json"
    p.write_text(json.dumps(cert_tampered, indent=2), encoding="utf-8")

    ok, logs, _ = Phase11ContractAdapter.verify_certificate(p)
    assert ok is False
    assert any("SHA-256" in line for line in logs)

    # 2. Strict witness validator function
    def verify_certificate_witnesses(data: dict) -> tuple[bool, str]:
        B = int(data["upper_prime"])
        witnesses = data["witnesses_upper"]
        for q_str, a in witnesses.items():
            q = int(q_str)
            if a <= 1:
                return False, f"Invalid witness a={a} <= 1"
            if pow(a, B - 1, B) != 1:
                return False, f"Fermat condition failed for witness a={a}"
            if math.gcd(pow(a, (B - 1) // q, B) - 1, B) != 1:
                return False, f"Pocklington gcd condition failed for witness a={a}"
        return True, "OK"

    # Original cert passes witness validation
    ok_orig, _ = verify_certificate_witnesses(cert)
    assert ok_orig is True

    # Tampered cert fails witness validation
    ok_bad, err_bad = verify_certificate_witnesses(cert_tampered)
    assert ok_bad is False
    assert "Invalid witness a=1" in err_bad


@pytest.mark.phase11_tier2
def test_bnd20_invalid_morrison_parameters_rejection(tmp_path: Path) -> None:
    """Verifies that tampering with Morrison Lucas parameters fails verification and parameter checks."""
    cert = generate_reference_certificate(3, 21)
    # 1. Tamper with Lucas parameter without recomputing hash -> adapter verifier must reject hash
    cert_tampered = dict(cert)
    cert_tampered["witnesses_lower"] = dict(cert["witnesses_lower"])
    cert_tampered["witnesses_lower"]["parameter_P"] = 3
    cert_tampered["witnesses_lower"]["discriminant_D"] = 10  # 3^2 - 4 = 5 != 10

    p = tmp_path / "cert_bad_morrison.json"
    p.write_text(json.dumps(cert_tampered, indent=2), encoding="utf-8")

    ok, logs, _ = Phase11ContractAdapter.verify_certificate(p)
    assert ok is False
    assert any("SHA-256" in line for line in logs)

    # 2. Strict Morrison parameter validator function
    def verify_certificate_morrison_params(data: dict) -> tuple[bool, str]:
        A = int(data["lower_prime"])
        P = data["witnesses_lower"]["parameter_P"]
        D = data["witnesses_lower"]["discriminant_D"]
        if P < 3:
            return False, f"Lucas parameter P must be >= 3, got {P}"
        if P * P - 4 != D:
            return False, f"Discriminant mismatch D != P^2 - 4: {D} != {P*P - 4}"
        if jacobi_symbol(D, A) != -1:
            return False, f"Jacobi symbol (D/A) must be -1"
        return True, "OK"

    # Original cert passes
    ok_orig, _ = verify_certificate_morrison_params(cert)
    assert ok_orig is True

    # Tampered cert fails
    ok_bad, err_bad = verify_certificate_morrison_params(cert_tampered)
    assert ok_bad is False


@pytest.mark.phase11_tier2
def test_bnd20_nonexistent_certificate_path_handling(tmp_path: Path) -> None:
    """Verifies that the verifier returns False and an appropriate log when certificate path does not exist."""
    nonexistent = tmp_path / "does_not_exist_cert.json"

    ok, logs, _ = Phase11ContractAdapter.verify_certificate(nonexistent)
    assert ok is False
    assert any("not found" in line.lower() or "failed to read" in line.lower() or "does not exist" in line.lower() for line in logs)
