"""
Unit, property, and adversarial test suite for Phase 6 (QCP-6).
Tests family mathematics, modular roots, sieve concordance, proof engines,
independent verification, negative/adversarial certificate rejection, and ledger resumption.
"""

import math
import copy
import pytest
import gmpy2
from pathlib import Path

from src.phase6.families import MethodQFamily, MethodRFamily, is_prime_deterministic_u64, trial_factor_small_int
from src.phase6.polynomial_roots import tonelli_shanks, compute_method_q_forbidden_j
from src.phase6.sieve import QSieveReference, QSieveSegment, QSieveEvent
from src.phase6.screening import CandidateScreener
from src.phase6.proof import MethodQProofEngine, lucas_u_ladder, compute_canonical_sha256
from scripts.phase6_independent_verify import verify_certificate_file, lucas_u_matrix_independent


def test_family_mathematics_and_divisibility():
    """Verify that Method Q candidate generator produces valid twin candidates with 6 | C."""
    family = MethodQFamily.generate_fresh(target_pair_digits=30, seed=12345, h=3)
    assert family.S % 2 != 0, "S must be odd"
    assert family.S % 3 == 0, "S must be divisible by 3"

    for j in range(10):
        t = 2 * j + 1
        A, B, C = family.evaluate(t)
        assert B - A == 2, "B - A must be 2"
        assert C % 6 == 0, "Center C must be divisible by 6"
        assert A % 2 != 0 and B % 2 != 0, "A and B must be odd"
        assert A % 3 != 0 and B % 3 != 0, "A and B must not be divisible by 3"

        # Check size conditions
        F = family.S * t
        assert F * F > B, "F^2 > B size condition must hold strictly"
        assert (F - 1) * (F - 1) > A, "(F - 1)^2 > A size condition must hold strictly"


def test_tonelli_shanks_and_roots():
    """Verify Tonelli-Shanks square roots and modular root solving."""
    # Test on known primes
    for p in [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]:
        for n in range(1, p):
            if gmpy2.legendre(n, p) == 1:
                r = tonelli_shanks(n, p)
                assert r is not None
                assert (r * r) % p == n % p


def test_sieve_concordance_reference_vs_segment_vs_event():
    """Verify that Q-reference, Q-segment, and Q-event produce 100% identical survivor sets."""
    family = MethodQFamily(S_factors={3: 1, 7: 1}, h=3)
    sieve_limit = 200
    window_start = 0
    window_length = 500

    ref_engine = QSieveReference(family, sieve_limit=sieve_limit)
    seg_engine = QSieveSegment(family, sieve_limit=sieve_limit)
    event_engine = QSieveEvent(family, sieve_limit=sieve_limit, segment_size=100)

    surv_ref = ref_engine.sieve_window(window_start, window_start + window_length)
    surv_seg = seg_engine.sieve_segment(window_start, window_length)
    surv_event = event_engine.sieve_segment(window_start, window_length)

    assert surv_ref == surv_seg, "Q-segment does not match Q-reference"
    assert surv_ref == surv_event, "Q-event does not match Q-reference"


def test_lucas_ladder_concordance_with_companion_matrix():
    """Verify that producer binary ladder matches verifier companion matrix exponentiation."""
    import random
    rng = random.Random(999)
    for _ in range(25):
        k = rng.randint(2, 5000)
        P = rng.randint(3, 15)
        mod = rng.randint(50, 50000) | 1
        val_ladder = lucas_u_ladder(k, P, mod)
        val_matrix = lucas_u_matrix_independent(k, P, mod)
        assert val_ladder == val_matrix, f"Mismatch at k={k}, P={P}, mod={mod}: {val_ladder} != {val_matrix}"


def test_dual_bls_proof_engine_and_independent_verifier(tmp_path):
    """Test generating a certified proof for a small calibration candidate and verifying it."""
    family = MethodQFamily(S_factors={3: 1, 7: 1}, h=3)
    prover = MethodQProofEngine()

    # t = 5 produces A = 10709, B = 10711
    ok, cert, err = prover.prove_twin_pair(family, t=5, campaign_id="test_calibration")
    assert ok is True
    assert cert is not None
    assert err is None

    cert_file = tmp_path / "cert_test.json"
    import json
    with open(cert_file, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    # Independent verifier check
    v_ok, v_msg, att = verify_certificate_file(cert_file)
    assert v_ok is True
    assert att is not None
    assert att["verdict"] == "VERIFIED_UNCONDITIONAL_TWIN_PRIMES"


def test_adversarial_negative_certificate_rejections(tmp_path):
    """Adversarial testing: Tampered or invalid certificates must be strictly rejected by the independent verifier."""
    family = MethodQFamily(S_factors={3: 1, 7: 1}, h=3)
    prover = MethodQProofEngine()
    ok, valid_cert, _ = prover.prove_twin_pair(family, t=5, campaign_id="adversarial")
    assert ok is True

    import json

    # 1. Tamper prime A (make it composite)
    c1 = copy.deepcopy(valid_cert)
    c1["pair"]["lower_prime_A"] = str(int(c1["pair"]["lower_prime_A"]) + 2)
    c1["sha256"] = compute_canonical_sha256(c1)
    f1 = tmp_path / "c1_bad_A.json"
    f1.write_text(json.dumps(c1), encoding="utf-8")
    ok1, msg1, _ = verify_certificate_file(f1)
    assert ok1 is False, f"Should reject tampered A: {msg1}"

    # 2. Tamper SHA-256 hash
    c2 = copy.deepcopy(valid_cert)
    c2["sha256"] = "deadbeef" * 8
    f2 = tmp_path / "c2_bad_hash.json"
    f2.write_text(json.dumps(c2), encoding="utf-8")
    ok2, msg2, _ = verify_certificate_file(f2)
    assert ok2 is False, "Should reject bad SHA-256"

    # 3. Tamper factor decomposition
    c3 = copy.deepcopy(valid_cert)
    c3["factorization_F"]["factors"]["3"] = 2  # Change exponent of 3
    c3["sha256"] = compute_canonical_sha256(c3)
    f3 = tmp_path / "c3_bad_factors.json"
    f3.write_text(json.dumps(c3), encoding="utf-8")
    ok3, msg3, _ = verify_certificate_file(f3)
    assert ok3 is False, f"Should reject invalid factorization: {msg3}"

    # 4. Tamper Pocklington witness
    c4 = copy.deepcopy(valid_cert)
    c4["proofs"]["proof_upper_B"]["witnesses"]["3"] = 1  # 1 is invalid witness
    c4["sha256"] = compute_canonical_sha256(c4)
    f4 = tmp_path / "c4_bad_witness.json"
    f4.write_text(json.dumps(c4), encoding="utf-8")
    ok4, msg4, _ = verify_certificate_file(f4)
    assert ok4 is False, f"Should reject invalid witness: {msg4}"
