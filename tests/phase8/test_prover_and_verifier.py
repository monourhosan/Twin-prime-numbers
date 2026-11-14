"""
Tests for Phase 8 Prover and Independent Verifier.
"""

import os
import json
import tempfile
import pytest

from src.phase8.prover import ADES8Prover, compute_canonical_sha256
from src.phase8.math import get_primorial_multiplier, compute_candidate_pair
from scripts.phase8_independent_verify import verify_certificate


def test_prover_and_verifier_roundtrip_small():
    """
    Tests small candidate pair with known prime status.
    For R=3, M=3:
    Let t = 0 -> k = 3*(1) = 3.
    For n = 3: C = 3 * 2^3 = 24.
    A = 23, B' = 25 (25 is composite, so Proth must reject it!).
    """
    prover = ADES8Prover()
    # Upper member 25 = 5^2, Proth should reject
    ok_B, w, msg, _ = prover.prove_proth_upper(3, 3, 25)
    assert ok_B is False


def test_prover_llr_known_prime():
    """
    Test LLR on known Riesel prime:
    A = 3 * 2^3 - 1 = 23.
    k=3, n=3.
    """
    prover = ADES8Prover()
    ok_A, P, u0, msg, _ = prover.prove_llr_lower(3, 3, 23)
    assert ok_A is True
    assert msg.startswith("PROVEN_PRIME")


def test_prover_proth_known_prime():
    """
    Test Proth on known Proth prime:
    B' = 3 * 2^2 + 1 = 13.
    k=3, n=2.
    """
    prover = ADES8Prover()
    ok_B, w, msg, _ = prover.prove_proth_upper(3, 2, 13)
    assert ok_B is True
    assert msg.startswith("PROVEN_PRIME")


def test_independent_verifier_tamper_detection():
    """
    Verifies that the independent verifier rejects tampered certificates fail-closed.
    """
    # Create valid dummy certificate structure
    # For k=3, n=3: A=23 (LLR), B'=25 is composite, but let's test tamper rejection on valid Phase 7 structure adapted to 8.0
    R = 13
    M = 15015
    prover = ADES8Prover()

    # Create a small valid test certificate using small proven pair:
    # Say, k=15, n=6: C = 15 * 64 = 960. A=959, B=961 (both composite).
    # Instead, let's adapt a verified certificate from phase7 to 8.0 schema for tamper testing:
    with open("proofs/phase7/certificates/cert_hdc7_1510d_B13_n4985_t15658.json", "r", encoding="utf-8") as f:
        p7_data = json.load(f)

    # Convert to schema 8.0
    cert_8 = {
        "schema_version": "8.0",
        "campaign_id": "test_campaign",
        "discovery_type": "CERTIFIED_FRESH_RECORD",
        "representation": {
            "family": "primorial_constrained_proth_llr_2d",
            "R_primorial": p7_data["representation"]["B_primorial"],
            "M_R": p7_data["representation"]["M_B"],
            "t": p7_data["representation"]["t"],
            "k": p7_data["representation"]["k"],
            "n": p7_data["representation"]["n"]
        },
        "pair": p7_data["pair"],
        "proofs": p7_data["proofs"],
        "search_evidence": p7_data["search_evidence"]
    }
    cert_8["sha256"] = compute_canonical_sha256(cert_8)

    with tempfile.TemporaryDirectory() as tmpdir:
        cert_path = os.path.join(tmpdir, "cert_test.json")
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert_8, f, indent=2)

        # Baseline verify: must pass
        assert verify_certificate(cert_path) is True

        # Tamper 1: Wrong SHA-256
        cert_tamper_sha = dict(cert_8)
        cert_tamper_sha["sha256"] = "0" * 64
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert_tamper_sha, f, indent=2)
        assert verify_certificate(cert_path) is False

        # Tamper 2: Tampered lower prime integer
        cert_tamper_lower = dict(cert_8)
        cert_tamper_lower["pair"] = dict(cert_8["pair"])
        cert_tamper_lower["pair"]["lower_decimal"] = str(int(cert_8["pair"]["lower_decimal"]) + 2)
        cert_tamper_lower["sha256"] = compute_canonical_sha256(cert_tamper_lower)
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert_tamper_lower, f, indent=2)
        assert verify_certificate(cert_path) is False

        # Tamper 3: Tampered witness w = 4 (quadratic residue, guaranteed 4^((B-1)/2) == +1 != -1)
        cert_tamper_w = dict(cert_8)
        cert_tamper_w["proofs"] = dict(cert_8["proofs"])
        cert_tamper_w["proofs"]["upper_member"] = dict(cert_8["proofs"]["upper_member"])
        cert_tamper_w["proofs"]["upper_member"]["witness_w"] = 4
        cert_tamper_w["sha256"] = compute_canonical_sha256(cert_tamper_w)
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert_tamper_w, f, indent=2)
        assert verify_certificate(cert_path) is False

        # Tamper 4: Invalid schema version
        cert_tamper_schema = dict(cert_8)
        cert_tamper_schema["schema_version"] = "99.0"
        cert_tamper_schema["sha256"] = compute_canonical_sha256(cert_tamper_schema)
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert_tamper_schema, f, indent=2)
        assert verify_certificate(cert_path) is False
