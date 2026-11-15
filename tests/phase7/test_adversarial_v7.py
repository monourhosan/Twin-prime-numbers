"""
Adversarial Mutation Tests for Phase 7 HDC-7 Certificate Verifier.
Validates that every single mutated field causes fail-closed rejection,
even when canonical SHA-256 is recomputed to match the mutated payload.
"""

import copy
import json
import tempfile
from pathlib import Path
import pytest
from scripts.phase7_independent_verify import verify_certificate_v7, compute_canonical_sha256


CERT_PATH = Path("proofs/phase7/certificates/cert_hdc7_1510d_B13_n4985_t15658.json")


@pytest.fixture
def base_cert_data():
    with open(CERT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_mutation(data_mutated, expected_err_substr=None):
    # Recompute hash so the hash check itself does not fail unless hash is what's being tested
    data_mutated["sha256"] = compute_canonical_sha256(data_mutated)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(data_mutated, tmp, indent=2)
        tmp_path = Path(tmp.name)

    try:
        ok, logs, att = verify_certificate_v7(tmp_path)
        assert not ok, f"Expected verification failure for mutated certificate, but it passed! Logs: {logs}"
        if expected_err_substr:
            assert any(expected_err_substr in l for l in logs), f"Expected error '{expected_err_substr}' not found in logs: {logs}"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_base_certificate_passes():
    ok, logs, att = verify_certificate_v7(CERT_PATH)
    assert ok, f"Base certificate failed verification: {logs}"


def test_mutate_k_even(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["representation"]["k"] = "470224756"
    run_mutation(d, "odd")


def test_mutate_k_zero(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["representation"]["k"] = "0"
    run_mutation(d, "k > 0")


def test_mutate_n(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["representation"]["n"] = 4986
    run_mutation(d)


def test_mutate_center(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["pair"]["center_decimal"] = str(int(d["pair"]["center_decimal"]) + 6)
    run_mutation(d, "mismatch")


def test_mutate_lower_member(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["pair"]["lower_decimal"] = str(int(d["pair"]["lower_decimal"]) - 2)
    run_mutation(d, "mismatch")


def test_mutate_upper_member(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["pair"]["upper_decimal"] = str(int(d["pair"]["upper_decimal"]) + 2)
    run_mutation(d, "mismatch")


def test_mutate_digit_count(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["pair"]["digits"] = 1509
    run_mutation(d, "Declared digit count mismatch")


def test_mutate_difference(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["pair"]["difference"] = 4
    run_mutation(d, "Declared difference mismatch")


def test_mutate_proth_witness(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["proofs"]["upper_member"]["witness_w"] = 2  # 2 is not a valid Proth witness here
    run_mutation(d, "Proth congruence failed")


def test_mutate_llr_parameter(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["proofs"]["lower_member"]["parameter_P"] = 5  # Different P
    run_mutation(d)


def test_mutate_jacobi_condition(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["proofs"]["lower_member"]["jacobi_conditions"]["(15-2/A)"] = -1
    run_mutation(d, "Jacobi")


def test_mutate_u0(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["proofs"]["lower_member"]["u0"] = "123456789"
    run_mutation(d, "Initial u0 mismatch")


def test_mutate_llr_round_count(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["proofs"]["lower_member"]["llr_rounds"] = 4982
    run_mutation(d, "LLR rounds mismatch")


def test_mutate_final_residue(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["proofs"]["lower_member"]["final_residue"] = 1
    run_mutation(d, "final residue")


def test_mutate_primorial_metadata(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["representation"]["M_B"] = "15016"
    run_mutation(d, "Primorial product mismatch")


def test_tamper_certificate_sha256(base_cert_data):
    d = copy.deepcopy(base_cert_data)
    d["sha256"] = "0" * 64
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(d, tmp, indent=2)
        tmp_path = Path(tmp.name)
    try:
        ok, logs, _ = verify_certificate_v7(tmp_path)
        assert not ok
        assert any("SHA-256 mismatch" in l for l in logs)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
