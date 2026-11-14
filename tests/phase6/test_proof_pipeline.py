"""
End-to-end tests for deterministic primality proof generation and independent attestation.
"""

from pathlib import Path
import tempfile
from src.phase6.proof_backend import DeterministicPairProver
from src.phase6.certificate_manifest import build_certificate_payload, save_certificate
from src.phase6.independent_verify import verify_file

def test_proof_and_independent_attestation():
    """Verify that DeterministicPairProver proves twin primes and independent verifier attests them."""
    prover = DeterministicPairProver()
    
    # Test m = 18 -> (107, 109)
    # 6*18 = 108 = 2^2 * 3^3
    proof = prover.prove_pair(18)
    assert proof is not None
    assert proof["status"] == "CERTIFIED_PRIMES"
    assert "proof_lower_A" in proof
    assert "proof_upper_B" in proof

    with tempfile.TemporaryDirectory() as tmp_dir:
        cert_dir = Path(tmp_dir) / "certificates"
        attest_dir = Path(tmp_dir) / "attestations"
        
        payload = build_certificate_payload(18, proof, "test_campaign")
        cert_path = save_certificate(payload, out_dir=cert_dir)
        assert cert_path.exists()

        # Run independent verification
        ok = verify_file(cert_path, attestation_dir=attest_dir)
        assert ok is True
        
        # Check attestation file was created
        attest_files = list(attest_dir.glob("attest_*.json"))
        assert len(attest_files) == 1
