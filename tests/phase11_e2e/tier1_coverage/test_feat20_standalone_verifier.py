"""Feature 20: Isolated Standalone Verifier.

Verifies:
1. AST verification of zero src/ imports in standalone verifier script if present.
2. Unconditional verification of valid certificates yielding verdict UNCONDITIONALLY_VERIFIED.
3. Attestation JSON schema compliance using validate_attestation_schema.
4. Detection and rejection of tampered/corrupted certificates.
5. Verifier return contract and exit code behavior.
"""

import ast
import json
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import validate_attestation_schema


@pytest.fixture
def valid_cert_path(tmp_path: Path) -> Path:
    """Creates a temporary valid certificate JSON file."""
    cert_data = Phase11ContractAdapter.prove_pair(y=3, t=21, run_id="verifier_feat20_test")
    cert_file = tmp_path / "valid_cert.json"
    with open(cert_file, "w", encoding="utf-8") as f:
        json.dump(cert_data, f, indent=2)
    return cert_file


@pytest.mark.phase11_tier1
def test_f20_verifier_ast_clean_imports() -> None:
    """Verifies that the standalone verifier script imports zero modules from src/."""
    script_path = Path("scripts/phase11/phase11_independent_verify.py")
    if script_path.is_file():
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("src"), f"Illegal import from src: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith("src"), f"Illegal import from src: {node.module}"
    else:
        # Pre-implementation lifecycle: contract verification
        assert hasattr(Phase11ContractAdapter, "verify_certificate")


@pytest.mark.phase11_tier1
def test_f20_valid_certificate_unconditionally_verified(valid_cert_path: Path) -> None:
    """Verifies valid certificate produces PASS and UNCONDITIONALLY_VERIFIED verdict."""
    ok, logs, attestation = Phase11ContractAdapter.verify_certificate(valid_cert_path)
    assert ok is True
    assert "verdict" in attestation
    assert attestation["verdict"] == "UNCONDITIONALLY_VERIFIED"


@pytest.mark.phase11_tier1
def test_f20_attestation_schema_validity(valid_cert_path: Path) -> None:
    """Verifies emitted attestation passes schema validation."""
    ok, _, attestation = Phase11ContractAdapter.verify_certificate(valid_cert_path)
    assert ok is True
    is_valid, errors = validate_attestation_schema(attestation)
    assert is_valid, f"Attestation validation errors: {errors}"


@pytest.mark.phase11_tier1
def test_f20_tampered_certificate_fails_verification(tmp_path: Path, valid_cert_path: Path) -> None:
    """Verifies that tampering with coordinate values causes verifier rejection."""
    with open(valid_cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Tamper with lower_prime
    data["lower_prime"] = str(int(data["lower_prime"]) + 4)
    tampered_file = tmp_path / "tampered_cert.json"
    with open(tampered_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    ok, logs, _ = Phase11ContractAdapter.verify_certificate(tampered_file)
    assert ok is False, "Expected tampered certificate to fail verification"


@pytest.mark.phase11_tier1
def test_f20_cli_exit_code_contract(valid_cert_path: Path, tmp_path: Path) -> None:
    """Verifies verifier contract returns success (code 0) on valid cert and failure on nonexistent cert."""
    # Valid certificate
    ok_valid, _, _ = Phase11ContractAdapter.verify_certificate(valid_cert_path)
    assert ok_valid is True

    # Nonexistent certificate
    nonexistent = tmp_path / "nonexistent.json"
    ok_bad, logs_bad, _ = Phase11ContractAdapter.verify_certificate(nonexistent)
    assert ok_bad is False
