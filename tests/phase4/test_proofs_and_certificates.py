"""
Phase 4 Proofs, Certificates, and Adversarial Tamper Rejection Tests.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.phase4.proof import proth_prove, llr_prove, ProofStatus
from src.phase4.certificate import TwinPrimeCertificateV4
from scripts.phase4_independent_verify import verify_and_attest_file, verify_certificate_v4_payload

def test_phase3_pilot_pair_reproduction():
    # 207-digit pair: k=15993, n=672
    k = 15993
    n = 672
    A = k * (1 << n) - 1
    B = k * (1 << n) + 1

    # Proth prove
    st_p, w, _ = proth_prove(k, n, B, witness_pool=[3, 5, 7, 11])
    assert st_p == ProofStatus.PROVEN_PRIME
    assert w == 7

    # LLR prove
    st_l, p, u0, _ = llr_prove(k, n, A, parameter_pool=[3, 4, 5, 9])
    assert st_l == ProofStatus.PROVEN_PRIME
    assert p == 3
    assert u0 is not None

def test_certificate_v4_generation_and_attestation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cert = TwinPrimeCertificateV4(
            k=15993,
            n=672,
            proth_witness=7,
            llr_p=3,
            llr_u0=270838894130811022108280090769013578492992888741942177513886931585419711601717714216425046350402829577820567010889769249004635006870093560205507257528268531697657639878581981582224693267001859672485030467882,
            campaign_id="test_camp",
            task_id="task_pilot",
            config_sha256="0" * 64
        )
        cert_path = Path(tmp_dir) / "cert_test.json"
        attest_dir = Path(tmp_dir) / "attestations"
        digest = cert.save_payload_file(cert_path)
        assert len(digest) == 64

        # Run independent verifier and generate attestation
        passed, msgs, attest_path = verify_and_attest_file(cert_path, attest_dir)
        assert passed, f"Verification failed: {msgs}"
        assert attest_path is not None
        assert attest_path.exists()

        # Check attestation contents
        with open(attest_path, "r", encoding="utf-8") as f:
            att = json.load(f)
        assert att["schema_version"] == "4.0"
        assert att["verdict"] == "PASS"
        assert att["proof_payload_sha256"] == digest

def test_adversarial_v4_tamper_rejections():
    cert = TwinPrimeCertificateV4(
        k=15993,
        n=672,
        proth_witness=7,
        llr_p=3,
        llr_u0=270838894130811022108280090769013578492992888741942177513886931585419711601717714216425046350402829577820567010889769249004635006870093560205507257528268531697657639878581981582224693267001859672485030467882,
        campaign_id="test_camp",
        task_id="task_pilot",
        config_sha256="0" * 64
    )
    base_dict = cert.to_dict()

    # 1. Tamper decimal digit
    d1 = json.loads(json.dumps(base_dict))
    d1["pair"]["lower_decimal"] = str(int(d1["pair"]["lower_decimal"]) + 2)
    passed, msgs, _ = verify_certificate_v4_payload(d1)
    assert not passed
    assert any("lower_decimal arithmetic mismatch" in m for m in msgs)

    # 2. Tamper Proth witness
    d2 = json.loads(json.dumps(base_dict))
    d2["upper_proof"]["witness"] = "2"
    passed, msgs, _ = verify_certificate_v4_payload(d2)
    assert not passed
    assert any("Proth theorem failed" in m for m in msgs)

    # 3. Tamper LLR parameter P
    d3 = json.loads(json.dumps(base_dict))
    d3["lower_proof"]["P"] = "7"
    passed, msgs, _ = verify_certificate_v4_payload(d3)
    assert not passed
    assert any("Riesel Jacobi conditions failed" in m for m in msgs)

    # 4. Tamper initial u0
    d4 = json.loads(json.dumps(base_dict))
    d4["lower_proof"]["initial_Vk_mod_A"] = "123456789"
    passed, msgs, _ = verify_certificate_v4_payload(d4)
    assert not passed
    assert any("Initial u0 matrix recomputation mismatch" in m for m in msgs)
