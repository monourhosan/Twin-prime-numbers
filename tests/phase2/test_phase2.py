"""
Automated Test Suite for Phase 2 Computational Number Theory Search Engine.
Covers:
- CRT wheel correctness vs naive enumeration
- Fast Lucas Montgomery ladder vs linear oracle
- Proth and LLR theorem preconditions and failure modes
- Cryptographic certificate integrity and tamper rejection
- Historical 34-digit discrepancy regression test
- Checkpoint atomic state recovery
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.phase2.candidate_wheel import CandidateWheel
from src.phase2.fast_lucas import lucas_v_fast
from src.phase2.proof_backend import (
    proth_prove, llr_prove, ProofStatus,
    validate_proth_preconditions, validate_llr_preconditions,
    jacobi_symbol
)
from src.phase2.certificate_v2 import TwinPrimeCertificateV2
from src.phase2.independent_verifier import verify_certificate_strict
from src.phase2.checkpoint import CheckpointManager
from src.phase2.window_sieve import WindowSieve

def linear_lucas(k: int, P: int, mod: int) -> int:
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod
    v0, v1 = 2, P % mod
    for _ in range(2, k + 1):
        v0, v1 = v1, (P * v1 - v0) % mod
    return v1

def test_crt_wheel_vs_naive():
    n = 100
    wheel = CandidateWheel(n=n, wheel_primes=[3, 5, 7])
    k_start = 3
    k_end = 2000
    survivors_wheel = wheel.enumerate_window(k_start, k_end)

    # Naive filter
    survivors_naive = []
    for k in range(k_start, k_end, 2):
        if k % 3 != 0:
            continue
        two_n = 1 << n
        a = k * two_n - 1
        b = k * two_n + 1
        if a % 5 == 0 or b % 5 == 0 or a % 7 == 0 or b % 7 == 0:
            continue
        survivors_naive.append(k)

    assert survivors_wheel == survivors_naive, "CRT wheel output must match naive enumeration exactly"

def test_fast_lucas_vs_linear_oracle():
    mod = 1000000007
    P = 4
    for k in [1, 2, 3, 5, 10, 42, 100, 500, 1024]:
        fast_val = lucas_v_fast(k, P, mod)
        lin_val = linear_lucas(k, P, mod)
        assert fast_val == lin_val, f"Mismatch at k={k}: fast={fast_val}, lin={lin_val}"

def test_proth_preconditions():
    # Valid: k=3, n=2, B=3*4+1=13 (prime)
    valid, msg = validate_proth_preconditions(3, 2, 13)
    assert valid, msg

    # Invalid: k >= 2^n (e.g., k=5, n=2, 2^n=4)
    valid, msg = validate_proth_preconditions(5, 2, 21)
    assert not valid
    assert "k < 2^n" in msg

    # Invalid: k even
    valid, msg = validate_proth_preconditions(4, 3, 33)
    assert not valid
    assert "odd" in msg

def test_llr_preconditions():
    # Valid: k=3, n=2, A=3*4-1=11 (prime)
    valid, msg = validate_llr_preconditions(3, 2, 11)
    assert valid, msg

    # Invalid: k >= 2^n
    valid, msg = validate_llr_preconditions(5, 2, 19)
    assert not valid
    assert "k < 2^n" in msg

    # Invalid: n < 2
    valid, msg = validate_llr_preconditions(3, 1, 5)
    assert not valid
    assert "n >= 2" in msg

def test_llr_jacobi_criterion():
    # Test Jacobi symbol properties
    assert jacobi_symbol(1, 11) == 1
    assert jacobi_symbol(3, 11) == 1
    assert jacobi_symbol(5, 11) == 1
    assert jacobi_symbol(2, 11) == -1

def test_verified_phase2_certificates():
    proof_dir = Path("proofs/phase2")
    certs = list(proof_dir.glob("cert_*.json"))
    assert len(certs) >= 3, f"Expected at least 3 Phase 2 certificates, found {len(certs)}"

    for c in certs:
        passed, msgs = verify_certificate_strict(c)
        assert passed, f"Certificate {c.name} failed verification: {msgs}"

def test_certificate_tamper_rejection():
    cert_path = Path("proofs/phase2/cert_k12477_n330.json")
    assert cert_path.exists()

    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Tamper with k
    tampered_data = json.loads(json.dumps(data))
    tampered_data["representation"]["k"] = 12479
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(tampered_data, tmp)
        tmp_path = Path(tmp.name)
    try:
        passed, msgs = verify_certificate_strict(tmp_path)
        assert not passed, "Tampered k must fail verification"
    finally:
        tmp_path.unlink()

    # 2. Tamper with witness
    tampered_data2 = json.loads(json.dumps(data))
    tampered_data2["proof_plus"]["witness"] = 2
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(tampered_data2, tmp)
        tmp_path = Path(tmp.name)
    try:
        passed, msgs = verify_certificate_strict(tmp_path)
        assert not passed, "Invalid witness must fail verification"
    finally:
        tmp_path.unlink()

def test_historical_discrepancy_regression():
    """
    Ensures README.md and FINDINGS.md do NOT contain the incorrect 40-digit
    composite strings for k=4107, n=100.
    """
    root = Path(__file__).resolve().parent.parent.parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    findings = (root / "FINDINGS.md").read_text(encoding="utf-8")

    composite_str = "5205862110637458953584332604028295903027"
    assert composite_str not in readme, "README.md must not contain the composite 40-digit string"
    assert composite_str not in findings, "FINDINGS.md must not contain the composite 40-digit string"

    # Must contain the exact correct 34-digit strings
    correct_minus = "5206241015137338151946960064479231"
    correct_plus = "5206241015137338151946960064479233"
    assert correct_minus in readme, "README.md must contain the correct 34-digit p_minus"
    assert correct_plus in readme, "README.md must contain the correct 34-digit p_plus"

    # Confirm math
    k, n = 4107, 100
    expected_minus = str(k * (1 << n) - 1)
    expected_plus = str(k * (1 << n) + 1)
    assert expected_minus == correct_minus
    assert expected_plus == correct_plus
    assert len(expected_minus) == 34

def test_checkpoint_atomic_recovery():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt = CheckpointManager(Path(tmp_dir), session_id="test_session")
        ckpt.record_completed_window("task_n384_k100_200", {"raw_tested": 50, "survivors": 2, "discovered": 0, "elapsed_sec": 0.1})

        # Reload from fresh instance
        ckpt2 = CheckpointManager(Path(tmp_dir))
        state = ckpt2.load()
        assert "task_n384_k100_200" in state["completed_windows"]
        assert state["stats"]["total_candidates_screened"] == 50
