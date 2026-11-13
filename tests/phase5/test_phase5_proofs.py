"""
Unit & Adversarial Tests for Phase 5 Primality Proofs and Independent Verifier.
"""

import json
import pytest
from pathlib import Path

from src.phase5.candidates import SmoothCenterFamily
from src.phase5.primality import (
    prove_pocklington_upper,
    prove_morrison_lower,
    PrimalityStatus,
    prp_test
)
from src.phase5.certificate import TwinPrimeCertificateV5
from scripts.phase5_independent_verify import verify_certificate_v5_payload

def get_known_twin_pair():
    """Generates a small known twin prime pair with smooth center: C = 9450 * 3 = 28350."""
    fam = SmoothCenterFamily({2: 1, 3: 3, 5: 2, 7: 1}, family_id="fam_known")
    cand = fam.candidate(3) # A = 28349, B = 28351
    return fam, cand

def test_pocklington_upper_proof():
    fam, cand = get_known_twin_pair()
    status, witness_a, proof_dict, err = prove_pocklington_upper(
        cand.B, fam.F_odd, fam.odd_prime_factors
    )
    assert status == PrimalityStatus.PROVEN_PRIME
    assert witness_a is not None
    assert proof_dict["theorem"] == "Pocklington_BLS_1975_Theorem_4"
    assert err is None

def test_morrison_lower_proof():
    fam, cand = get_known_twin_pair()
    status, param_P, proof_dict, err = prove_morrison_lower(
        cand.A, fam.F_odd, fam.odd_prime_factors
    )
    assert status == PrimalityStatus.PROVEN_PRIME
    assert param_P is not None
    assert proof_dict["theorem"] == "Morrison_BLS_1975_Theorem_17"
    assert err is None

def test_carmichael_number_rejection():
    """Ensures Carmichael numbers like 561 cannot be proven prime."""
    # 561 = 3 * 11 * 17
    # Even if 561 is a pseudoprime, Pocklington or Morrison preconditions/checks fail
    status, witness, proof, err = prove_pocklington_upper(561, 15, [3, 5])
    assert status != PrimalityStatus.PROVEN_PRIME

def test_independent_verifier_valid_payload():
    fam, cand = get_known_twin_pair()
    _, witness_a, pock_proof, _ = prove_pocklington_upper(cand.B, fam.F_odd, fam.odd_prime_factors)
    _, param_P, morr_proof, _ = prove_morrison_lower(cand.A, fam.F_odd, fam.odd_prime_factors)

    cert = TwinPrimeCertificateV5(
        candidate=cand,
        lower_proof=morr_proof,
        upper_proof=pock_proof,
        search_provenance={"test": "unit_test"}
    )
    payload = cert.to_dict()

    is_valid, errors, evidence = verify_certificate_v5_payload(payload)
    assert is_valid is True
    assert len(errors) == 0
    assert evidence["payload_sha256_verified"] is True
    assert evidence["pocklington_witness_a"] == witness_a
    assert evidence["morrison_parameter_P"] == param_P

def test_adversarial_tamper_sha256():
    fam, cand = get_known_twin_pair()
    _, witness_a, pock_proof, _ = prove_pocklington_upper(cand.B, fam.F_odd, fam.odd_prime_factors)
    _, param_P, morr_proof, _ = prove_morrison_lower(cand.A, fam.F_odd, fam.odd_prime_factors)

    cert = TwinPrimeCertificateV5(cand, morr_proof, pock_proof, {"test": "tamper"})
    payload = cert.to_dict()

    # Tamper with SHA-256
    payload["sha256"] = "0" * 64
    is_valid, errors, _ = verify_certificate_v5_payload(payload)
    assert is_valid is False
    assert any("SHA-256 mismatch" in e for e in errors)

def test_adversarial_tamper_integer_values():
    fam, cand = get_known_twin_pair()
    _, witness_a, pock_proof, _ = prove_pocklington_upper(cand.B, fam.F_odd, fam.odd_prime_factors)
    _, param_P, morr_proof, _ = prove_morrison_lower(cand.A, fam.F_odd, fam.odd_prime_factors)

    cert = TwinPrimeCertificateV5(cand, morr_proof, pock_proof, {"test": "tamper"})
    payload = cert.to_dict()

    # Tamper with upper decimal integer (+2 makes gap 4)
    payload["upper_decimal"] = str(int(payload["upper_decimal"]) + 2)
    is_valid, errors, _ = verify_certificate_v5_payload(payload)
    assert is_valid is False
    assert any("mismatch" in e or "Gap is not 2" in e for e in errors)

def test_adversarial_tamper_witness():
    fam, cand = get_known_twin_pair()
    _, witness_a, pock_proof, _ = prove_pocklington_upper(cand.B, fam.F_odd, fam.odd_prime_factors)
    _, param_P, morr_proof, _ = prove_morrison_lower(cand.A, fam.F_odd, fam.odd_prime_factors)

    cert = TwinPrimeCertificateV5(cand, morr_proof, pock_proof, {"test": "tamper"})
    payload = cert.to_dict()

    # Replace witness base with an invalid base (e.g. 1)
    payload["primality_proofs"]["upper"]["witness_base_a"] = 1
    is_valid, errors, _ = verify_certificate_v5_payload(payload)
    assert is_valid is False
    assert any("witness" in e.lower() for e in errors)
