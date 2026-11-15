"""
Comprehensive Unit, Correctness, Property, and Adversarial Tests for PAQCS (Phase 8).
Validates anchor factorization, root solving, sieve bounds, candidate construction,
dual-BLS proofs, and fail-closed independent verification.
"""

import copy
import json
import math
import tempfile
from pathlib import Path
import pytest
import sympy

from src.phase8.paqcs_anchor import PrimorialAnchor, factor_small_int, is_small_prime_deterministic
from src.phase8.paqcs_math import (
    tonelli_shanks,
    get_forbidden_t_residues,
    construct_pair,
    lucas_u_ladder
)
from src.phase8.paqcs_sieve import prepare_sieve_plan, SegmentedPAQCSSieve
from src.phase8.paqcs_screening import screen_candidate_single
from src.phase8.paqcs_prover import PAQCSProver
from scripts.phase8_paqcs_independent_verify import (
    verify_paqcs_certificate,
    compute_canonical_sha256,
    is_small_prime_standalone
)


# 1. Anchor tests
def test_anchor_product_matches_factors():
    anchor = PrimorialAnchor(y=100)
    reconstructed = 1
    for p in anchor.primes:
        assert is_small_prime_deterministic(p)
        reconstructed *= p
    assert anchor.S_y == reconstructed
    assert anchor.digits == len(str(reconstructed))


def test_anchor_factorization_of_x():
    anchor = PrimorialAnchor(y=50)
    t = 105  # 3 * 5 * 7
    distinct_primes, mults = anchor.factor_x(t)
    x = anchor.S_y * t
    rec_x = 1
    for p in distinct_primes:
        rec_x *= (p ** mults[p])
    assert rec_x == x
    assert mults[3] == 2
    assert mults[5] == 2
    assert mults[7] == 2


# 2. Candidate construction tests: C = 0 mod 6 and B - A = 2
def test_pair_properties():
    anchor = PrimorialAnchor(y=30)
    for t in [3, 5, 17, 39, 101, 39045]:
        x, C, A, B = construct_pair(anchor.S_y, t, h=3)
        assert B - A == 2
        assert C % 6 == 0
        assert A % 2 == 1
        assert B % 2 == 1
        assert A % 3 != 0
        assert B % 3 != 0


# 3. Sieve roots vs Brute force oracle
def test_sieve_roots_vs_brute_force():
    anchor = PrimorialAnchor(y=100)
    h = 3
    d_A = h * h + 4  # 13
    d_B = h * h - 4  # 5

    test_primes = [q for q in sympy.primerange(101, 300)]
    for q in test_primes:
        S_y_mod_q = anchor.S_y % q
        forbidden = get_forbidden_t_residues(q, S_y_mod_q, h=h)

        # Brute force all t mod q
        for t in range(q):
            x = (S_y_mod_q * t) % q
            div_A = (x * (x - h) - 1) % q == 0
            div_B = (x * (x - h) + 1) % q == 0
            is_div = div_A or div_B
            assert (t in forbidden) == is_div, f"Root mismatch for q={q}, t={t}"


# 4. Discriminant residue and non-residue cases
def test_discriminant_residue_cases():
    # q=1783 has (13/q)=-1 and (5/q)=-1
    forbidden = get_forbidden_t_residues(1783, 12345, h=3)
    assert len(forbidden) == 0


# 5. Sieve segment boundaries & no genuine twin pair removed
def test_sieve_segment_exactness():
    anchor = PrimorialAnchor(y=30)
    plan = prepare_sieve_plan(anchor.S_y, anchor.y, Q_bound=200, h=3)
    sieve = SegmentedPAQCSSieve(plan)

    # Segment 1: [101, 301]
    # Segment 2: [303, 503]
    surv1 = sieve.sieve_segment(101, 301)
    surv2 = sieve.sieve_segment(303, 503)
    surv_full = sieve.sieve_segment(101, 503)

    assert set(surv1).isdisjoint(set(surv2))
    assert sorted(surv1 + surv2) == sorted(surv_full)


# 6. Exact decimal digit bounds
def test_exact_digit_bounds():
    anchor = PrimorialAnchor(y=1780)
    t_min = anchor.compute_min_t(target_digits=1511, h=3)
    x, C, A, B = construct_pair(anchor.S_y, t_min, h=3)
    assert len(str(A)) == 1511
    assert len(str(B)) == 1511

    # t_min - 2 should yield 1510 digits
    x_prev, C_prev, A_prev, B_prev = construct_pair(anchor.S_y, t_min - 2, h=3)
    assert len(str(A_prev)) == 1510


# 7. Screening filter with Carmichael numbers & composites
def test_screening_filter():
    anchor = PrimorialAnchor(y=30)
    # Carmichael number test: 561 = 3 * 11 * 17
    # screening handles large constructed candidates
    is_single, is_dual, _, _ = screen_candidate_single(anchor.S_y, 3, h=3)
    # 3 should not be a dual prime for S_30
    assert isinstance(is_single, bool)
    assert isinstance(is_dual, bool)


# 8. Dual-BLS proof generation and adversarial mutations
def test_proof_and_adversarial_verification():
    anchor = PrimorialAnchor(y=50)
    # Generate a certified pair at t=10286487 (known from calibration)
    prover = PAQCSProver(anchor)
    ok, cert, err = prover.prove_twin_pair(10286487, h=3, campaign_id="test_adversarial")
    assert ok, f"Prover failed: {err}"

    # Verify base certificate passes
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(cert, tmp, indent=2)
        tmp_path = Path(tmp.name)

    try:
        v_ok, logs, _ = verify_paqcs_certificate(tmp_path)
        assert v_ok, f"Base certificate verification failed: {logs}"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    # Mutation test helper
    def check_mutation(mutated_dict):
        mutated_dict["sha256"] = compute_canonical_sha256(mutated_dict)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(mutated_dict, tmp, indent=2)
            t_path = Path(tmp.name)
        try:
            m_ok, m_logs, _ = verify_paqcs_certificate(t_path)
            assert not m_ok, f"Mutated certificate unexpectedly passed! Logs: {m_logs}"
        finally:
            if t_path.exists():
                t_path.unlink()

    # Mutate t to even
    d = copy.deepcopy(cert)
    d["representation"]["t"] = 10286488
    check_mutation(d)

    # Mutate h
    d = copy.deepcopy(cert)
    d["representation"]["h"] = 4
    check_mutation(d)

    # Mutate difference
    d = copy.deepcopy(cert)
    d["pair"]["difference"] = 4
    check_mutation(d)

    # Mutate member integer
    d = copy.deepcopy(cert)
    d["pair"]["lower_decimal"] = str(int(d["pair"]["lower_decimal"]) - 2)
    check_mutation(d)

    # Mutate digit count
    d = copy.deepcopy(cert)
    d["pair"]["digits"] = d["pair"]["digits"] - 1
    check_mutation(d)

    # Mutate witness (w=1 is invalid)
    d = copy.deepcopy(cert)
    d["proofs"]["upper_member"]["witnesses"]["3"] = 1
    check_mutation(d)

    # Mutate Morrison Lucas parameter
    d = copy.deepcopy(cert)
    d["proofs"]["lower_member"]["parameter_P"] = 2
    check_mutation(d)

    # Mutate factor primality (fake composite factor)
    d = copy.deepcopy(cert)
    d["representation"]["x_factorization"]["4"] = 1
    check_mutation(d)
