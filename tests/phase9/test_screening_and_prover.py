"""
Unit and regression tests for Candidate Screening, Prover, and Independent Verifier.
Includes adversarial tamper resistance tests.
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.phase9.anchor import PrimorialAnchor
from src.phase9.screening import screen_candidate_t, CandidateStatus
from src.phase9.prover import PACCM9Prover
from scripts.phase9_independent_verify import verify_paccm9_certificate


@pytest.fixture(scope="module")
def smoke_cert():
    anchor = PrimorialAnchor(y=5) # primes 2, 3, 5 => S_5 = 30
    prover = PACCM9Prover(anchor)
    # t=13 gives twin prime pair A=356218199, B=356218201
    cert = prover.prove_pair(t=13, campaign_id="test_prover")
    assert cert is not None
    return cert


def test_screening_rejection():
    anchor = PrimorialAnchor(y=5)
    # Composite multiplier t=9 should be rejected
    status, _ = screen_candidate_t(anchor.S_y, t=9, require_prime_t=True)
    assert status == CandidateStatus.COMPOSITE


def test_screening_success():
    anchor = PrimorialAnchor(y=5)
    status, pair = screen_candidate_t(anchor.S_y, t=13, require_prime_t=True)
    assert status == CandidateStatus.DUAL_PRP
    assert pair is not None
    C, A, B = pair
    assert B - A == 2


def test_prover_and_independent_verifier_pass(smoke_cert):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(smoke_cert, tf, indent=2)
        tmp_path = Path(tf.name)

    try:
        ok, logs, att = verify_paccm9_certificate(tmp_path)
        assert ok is True
        assert att["verdict"] == "UNCONDITIONALLY_VERIFIED"
    finally:
        tmp_path.unlink()


def test_adversarial_tamper_hash(smoke_cert):
    tampered = dict(smoke_cert)
    tampered["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(tampered, tf, indent=2)
        tmp_path = Path(tf.name)

    try:
        ok, logs, _ = verify_paccm9_certificate(tmp_path)
        assert ok is False
        assert any("SHA-256 mismatch" in l for l in logs)
    finally:
        tmp_path.unlink()


def test_adversarial_tamper_gap(smoke_cert):
    from src.phase9.prover import compute_canonical_sha256
    tampered = dict(smoke_cert)
    # Alter upper member B so difference is 4 instead of 2
    tampered["pair"] = dict(tampered["pair"])
    orig_B = int(tampered["pair"]["upper_decimal"])
    tampered["pair"]["upper_decimal"] = str(orig_B + 2)
    tampered["sha256"] = compute_canonical_sha256(tampered)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(tampered, tf, indent=2)
        tmp_path = Path(tf.name)

    try:
        ok, logs, _ = verify_paccm9_certificate(tmp_path)
        assert ok is False
    finally:
        tmp_path.unlink()


def test_adversarial_tamper_witness(smoke_cert):
    from src.phase9.prover import compute_canonical_sha256
    tampered = json.loads(json.dumps(smoke_cert))
    # Replace valid witness for factor 3 with 1 (invalid witness)
    tampered["proofs"]["upper_member"]["witnesses"]["3"] = 1
    tampered["sha256"] = compute_canonical_sha256(tampered)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(tampered, tf, indent=2)
        tmp_path = Path(tf.name)

    try:
        ok, logs, _ = verify_paccm9_certificate(tmp_path)
        assert ok is False
    finally:
        tmp_path.unlink()
