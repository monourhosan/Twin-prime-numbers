"""
Adversarial tests for Phase 6 independent certificate verification.
Ensures that all corruptions, tampered payloads, and invalid parameters are 100% rejected.
"""

from src.phase6.proof_backend import DeterministicPairProver
from src.phase6.certificate_manifest import build_certificate_payload
from src.phase6.independent_verify import verify_phase6_certificate

def get_valid_payload():
    """Generates a certified valid payload for m=18 (107, 109)."""
    prover = DeterministicPairProver()
    proof = prover.prove_pair(18)
    return build_certificate_payload(18, proof, "test_campaign")

def test_valid_certificate_passes():
    """Verify clean certificate passes independent verification."""
    payload = get_valid_payload()
    is_valid, errors, evidence = verify_phase6_certificate(payload)
    assert is_valid is True
    assert len(errors) == 0

def test_tampered_difference_rejected():
    """Reject certificate if B - A != 2."""
    payload = get_valid_payload()
    payload["pair"]["upper_prime_B"] = str(int(payload["pair"]["upper_prime_B"]) + 2)
    is_valid, errors, _ = verify_phase6_certificate(payload)
    assert is_valid is False
    assert any("Difference mismatch" in e for e in errors)

def test_tampered_sha256_rejected():
    """Reject certificate if canonical SHA-256 is modified."""
    payload = get_valid_payload()
    payload["canonical_sha256"] = "0" * 64
    is_valid, errors, _ = verify_phase6_certificate(payload)
    assert is_valid is False
    assert any("Canonical SHA-256 digest mismatch" in e for e in errors)

def test_corrupted_pocklington_witness_rejected():
    """Reject certificate if Pocklington witness a is invalid."""
    payload = get_valid_payload()
    # Change witness a to 1
    payload["proofs"]["proof_upper_B"]["witness_a"] = 1
    is_valid, errors, _ = verify_phase6_certificate(payload)
    assert is_valid is False
    assert any("Invalid Pocklington witness" in e or "congruence failed" in e for e in errors)

def test_corrupted_morrison_parameter_rejected():
    """Reject certificate if Morrison parameter P fails Jacobi or Lucas condition."""
    payload = get_valid_payload()
    # For A = 107: D = P^2 - 4. If P=4, D=12, (12/107) = (3/107) = - (107/3) = -(2/3) = -(-1) = +1!
    payload["proofs"]["proof_lower_A"]["parameter_P"] = 4
    is_valid, errors, _ = verify_phase6_certificate(payload)
    assert is_valid is False
    assert any("Jacobi symbol condition failed" in e or "Lucas" in e for e in errors)

def test_composite_factor_in_proof_rejected():
    """Reject certificate if a composite factor is falsely reported as prime."""
    payload = get_valid_payload()
    # Introduce composite factor 9
    payload["proofs"]["factors_of_center"]["9"] = 1
    payload["proofs"]["proof_upper_B"]["prime_factors"].append(9)
    if "odd_prime_factors" in payload["proofs"]["proof_lower_A"]:
        payload["proofs"]["proof_lower_A"]["odd_prime_factors"].append(9)
    is_valid, errors, _ = verify_phase6_certificate(payload)
    assert is_valid is False
    assert any("failed first-principles trial division primality" in e for e in errors)
