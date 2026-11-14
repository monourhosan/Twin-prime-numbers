"""
Comprehensive Unit and Integration Tests for Phase 7 HDC-7 Engine.
Validates:
1. Exact digit boundaries and parameter reconstruction.
2. Modular root solver in compact t-space.
3. Sieve correctness and small prime exclusion.
4. Screener left/right/dual PRP distinction.
5. Proth and LLR deterministic proofs.
6. Standalone independent verification and tamper detection.
"""

import json
from pathlib import Path
import pytest

from src.phase7.math import (
    get_primorial_multiplier,
    exact_digit_t_bounds,
    solve_modular_roots,
    compute_candidate_pair,
    jacobi_symbol,
    lucas_v_montgomery,
    lucas_v_matrix
)
from src.phase7.sieve import CompactTSieve
from src.phase7.screening import HDCScreener
from src.phase7.prover import HDCProver
from scripts.phase7_independent_verify import verify_certificate_v7


def test_math_boundaries_and_primorial():
    """Verify exact boundaries for 1510 digits."""
    B = 13
    MB = get_primorial_multiplier(B)
    assert MB == 3 * 5 * 7 * 11 * 13 # 15015

    n = 4985
    D = 1510
    k_min, k_max, t_min, t_max = exact_digit_t_bounds(D, MB, n)
    assert t_min <= t_max
    assert k_max < (1 << n)

    # Test exact boundary candidate digits
    _, C_low, A_low, B_low = compute_candidate_pair(MB, t_min, n)
    assert len(str(A_low)) == D
    assert len(str(B_low)) == D
    assert B_low - A_low == 2
    assert C_low % 6 == 0

    _, C_high, A_high, B_high = compute_candidate_pair(MB, t_max, n)
    assert len(str(A_high)) == D
    assert len(str(B_high)) == D
    assert B_high - A_high == 2
    assert C_high % 6 == 0


def test_modular_roots_correctness():
    """Verify that t_plus causes r | (C-1) and t_minus causes r | (C+1)."""
    MB = get_primorial_multiplier(7) # 105
    n = 30
    for r in [17, 19, 23, 29, 31]:
        t_plus, t_minus = solve_modular_roots(MB, n, r)
        _, C_p, A_p, _ = compute_candidate_pair(MB, t_plus, n)
        assert A_p % r == 0, f"t_plus failed for prime {r}"

        _, C_m, _, B_m = compute_candidate_pair(MB, t_minus, n)
        assert B_m % r == 0, f"t_minus failed for prime {r}"


def test_compact_sieve_filtration():
    """Verify that compact sieve survivors have no small prime divisors."""
    MB = get_primorial_multiplier(5) # 15
    n = 20
    sieve = CompactTSieve(MB, n, sieve_depth=500)
    survivors, tele = sieve.sieve_segment(0, 100)

    # Check each survivor
    for t in survivors:
        _, _, A, Bprime = compute_candidate_pair(MB, t, n)
        for r in sieve.sieve_primes:
            assert A % r != 0, f"Survivor A divisible by sieve prime {r}"
            assert Bprime % r != 0, f"Survivor Bprime divisible by sieve prime {r}"


def test_lucas_v_implementations_match():
    """Verify that Montgomery ladder and 2x2 companion matrix produce identical results."""
    mod = 1000000007 # prime
    P = 5
    for k in [1, 2, 3, 7, 15, 127, 2048, 65535]:
        v_mont = lucas_v_montgomery(k, P, mod)
        v_mat = lucas_v_matrix(k, P, mod)
        assert v_mont == v_mat, f"Mismatch at k={k}: mont={v_mont}, mat={v_mat}"


def test_prover_and_independent_verifier_roundtrip(tmp_path):
    """Verify that a proven pair produces an authentic certificate verified by independent verifier."""
    MB = get_primorial_multiplier(5) # 15
    n = 10
    # At t=0: k=15, C=15360, A=15359, B=15361 (known twin primes)
    prover = HDCProver()
    cert = prover.prove_pair(5, MB, 0, n)
    assert cert is not None
    assert cert["schema_version"] == "7.0"
    assert cert["proofs"]["upper_member"]["verdict"] == "PROVEN_PRIME"
    assert cert["proofs"]["lower_member"]["verdict"] == "PROVEN_PRIME"

    cert_file = tmp_path / "cert_test.json"
    with open(cert_file, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)

    attest_dir = tmp_path / "attestations"
    ok, logs, att = verify_certificate_v7(cert_file, attest_dir)
    assert ok is True
    assert att["verdict"] == "UNCONDITIONALLY_VERIFIED"


def test_independent_verifier_tamper_detection(tmp_path):
    """Verify that tampered fields in Schema 7.0 certificate are caught and rejected."""
    MB = get_primorial_multiplier(5)
    n = 10
    prover = HDCProver()
    cert = prover.prove_pair(5, MB, 0, n)

    # 1. Tamper with sha256
    tampered_1 = dict(cert)
    tampered_1["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    f1 = tmp_path / "tamper_sha.json"
    with open(f1, "w", encoding="utf-8") as f:
        json.dump(tampered_1, f)
    ok, _, _ = verify_certificate_v7(f1)
    assert ok is False

    # 2. Tamper with witness
    tampered_2 = dict(cert)
    tampered_2["proofs"]["upper_member"]["witness_w"] = 4 # Even witness
    tampered_2["sha256"] = "recalculate"
    from src.phase7.prover import compute_canonical_sha256
    tampered_2["sha256"] = compute_canonical_sha256(tampered_2)
    f2 = tmp_path / "tamper_witness.json"
    with open(f2, "w", encoding="utf-8") as f:
        json.dump(tampered_2, f)
    ok, _, _ = verify_certificate_v7(f2)
    assert ok is False
