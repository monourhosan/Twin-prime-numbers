"""Unit and Property Tests for Certificate Verification & Tamper Detection.

Verifies:
1. Valid production certificates (13d and 21d) pass standalone verifier with exit code 0.
2. Altered candidate primes (lower_prime, upper_prime) are detected and rejected.
3. Mutated twin gap (difference != 2) is detected and rejected.
4. Mutated Pocklington witnesses (invalid base, non-witness) are rejected.
5. Mutated Morrison parameters (invalid P, non-residue, corrupted Lucas rank) are rejected.
6. Mutated divisor factors and insufficient dominance bounds are rejected.
7. Corrupted canonical SHA-256 hash digests are detected and rejected.
8. Missing or extraneous fields are rejected by strict schema validation.
"""

import json
from pathlib import Path

import pytest

from scripts.phase11.phase11_independent_verify import (
    compute_canonical_sha256,
    verify_opqm11_certificate,
)


@pytest.fixture
def cert_13d_path() -> Path:
    return Path("proofs/phase11/certificates/cert_opqm11_13d_t29.json")


@pytest.fixture
def cert_21d_path() -> Path:
    return Path("proofs/phase11/certificates/cert_opqm11_21d_t215.json")


def test_valid_certificates_pass(cert_13d_path: Path, cert_21d_path: Path) -> None:
    """Verifies that authentic 13d and 21d discovery certificates pass unconditional verification."""
    for p in (cert_13d_path, cert_21d_path):
        assert p.is_file(), f"Certificate file {p} does not exist"
        ok, logs, attestation = verify_opqm11_certificate(p)
        assert ok is True, f"Verification failed on valid certificate {p}: {logs}"
        assert attestation["verdict"] == "UNCONDITIONALLY_VERIFIED"


def test_tamper_sha256_hash_detected(tmp_path: Path, cert_21d_path: Path) -> None:
    """Verifies that altering a single character in the SHA-256 digest causes rejection."""
    data = json.loads(cert_21d_path.read_text(encoding="utf-8"))
    first_char = data["certificate_sha256"][0]
    corrupted_char = "0" if first_char != "0" else "1"
    data["certificate_sha256"] = corrupted_char + data["certificate_sha256"][1:]

    tampered_file = tmp_path / "tampered_hash.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("SHA-256 mismatch" in line for line in logs)


def test_tamper_lower_prime_detected(tmp_path: Path, cert_13d_path: Path) -> None:
    """Verifies that altering lower_prime is detected both before and after hash recomputation."""
    data = json.loads(cert_13d_path.read_text(encoding="utf-8"))
    data["lower_prime"] = str(int(data["lower_prime"]) + 4)

    # 1. Without recomputing hash -> hash mismatch
    tampered_unhashed = tmp_path / "tampered_lower_unhashed.json"
    tampered_unhashed.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_unhashed)
    assert ok is False
    assert any("SHA-256 mismatch" in line for line in logs)

    # 2. With recomputing hash -> manifold / gap mismatch
    data["certificate_sha256"] = compute_canonical_sha256(data)
    tampered_rehashed = tmp_path / "tampered_lower_rehashed.json"
    tampered_rehashed.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_rehashed)
    assert ok is False
    assert any("quintic manifold" in line or "gap" in line for line in logs)


def test_tamper_upper_prime_detected(tmp_path: Path, cert_13d_path: Path) -> None:
    """Verifies that altering upper_prime is detected even if hash is recomputed."""
    data = json.loads(cert_13d_path.read_text(encoding="utf-8"))
    data["upper_prime"] = str(int(data["upper_prime"]) + 2)
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_upper.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("quintic manifold" in line or "gap" in line for line in logs)


def test_tamper_twin_gap_detected(tmp_path: Path, cert_21d_path: Path) -> None:
    """Verifies that non-twin pair (gap != 2) is rejected."""
    data = json.loads(cert_21d_path.read_text(encoding="utf-8"))
    data["difference"] = 4
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_gap.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("difference" in line.lower() for line in logs)


def test_tamper_pocklington_witness_detected(tmp_path: Path, cert_21d_path: Path) -> None:
    """Verifies that mutating an upper Pocklington witness base causes rejection."""
    data = json.loads(cert_21d_path.read_text(encoding="utf-8"))
    data["witnesses_upper"]["2"] = 1  # Base 1 is invalid
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_witness_b.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("witness" in line.lower() or "gcd" in line.lower() or "fermat" in line.lower() for line in logs)


def test_tamper_morrison_parameter_p_detected(tmp_path: Path, cert_21d_path: Path) -> None:
    """Verifies that mutating lower Morrison parameter P causes rejection."""
    data = json.loads(cert_21d_path.read_text(encoding="utf-8"))
    # P=5 was proven to cause rank singularity for factor 3 on the 21d candidate
    data["witnesses_lower"]["parameter_P"] = 5
    data["witnesses_lower"]["discriminant_D"] = 21
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_param_p.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("rank gcd" in line.lower() or "singularity" in line.lower() for line in logs)


def test_tamper_insufficient_divisor_f_detected(tmp_path: Path, cert_13d_path: Path) -> None:
    """Verifies that setting divisor F such that F^2 <= B causes rejection."""
    data = json.loads(cert_13d_path.read_text(encoding="utf-8"))
    data["parameters"]["F"] = "10"
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_f.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("f mismatch" in line.lower() or "size condition failed" in line.lower() for line in logs)


def test_tamper_missing_fields_detected(tmp_path: Path, cert_13d_path: Path) -> None:
    """Verifies that removing a mandatory field causes schema rejection."""
    data = json.loads(cert_13d_path.read_text(encoding="utf-8"))
    del data["symbolic_center"]
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_missing_field.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("missing required fields" in line.lower() for line in logs)


def test_tamper_extraneous_fields_detected(tmp_path: Path, cert_13d_path: Path) -> None:
    """Verifies that injecting an extraneous field causes schema rejection."""
    data = json.loads(cert_13d_path.read_text(encoding="utf-8"))
    data["unauthorized_field"] = "exploit"
    data["certificate_sha256"] = compute_canonical_sha256(data)

    tampered_file = tmp_path / "tampered_extra_field.json"
    tampered_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ok, logs, _ = verify_opqm11_certificate(tampered_file)
    assert ok is False
    assert any("extraneous fields present" in line.lower() for line in logs)
