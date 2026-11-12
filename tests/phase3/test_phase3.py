"""
Comprehensive Automated Test Suite for Phase 3 (HDRSS).
Covers:
- Vectorized S1 and Hybrid S2 sieve mathematical equivalence
- Window invariance and boundary alignment
- Exact decimal digit checking and reconstruction
- Proth and LLR theorem preconditions and failure modes
- Independent 2x2 matrix powering Lucas verification vs Montgomery ladder
- Adversarial certificate mutation and tamper rejection
- Task continuation cursor and PARTIAL state recovery
- Regression prevention for all audited historical discrepancies
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.phase3.candidate_generator import Phase3Wheel
from src.phase3.segmented_sieve import SegmentedSieveS1
from src.phase3.hybrid_sieve import HybridSieveS2
from src.phase3.proof import (
    proth_prove, llr_prove, ProofStatus,
    validate_proth_preconditions, validate_llr_preconditions,
    lucas_v_montgomery, jacobi_symbol
)
from src.phase3.certificate import TwinPrimeCertificateV3
from src.phase3.storage import Phase3Storage
from scripts.phase3_independent_verify import (
    verify_certificate_file, lucas_v_matrix, standalone_jacobi
)

def test_wheel_counting_and_enumeration():
    wheel = Phase3Wheel(n=1024)
    assert len(wheel.allowed_residues) == 1485
    # Verify every allowed residue is odd and divisible by 3
    for r in wheel.allowed_residues:
        assert r % 2 == 1
        assert r % 3 == 0

def test_sieve_s1_vs_s2_equivalence():
    n = 672
    Q = 20_000
    k_start = 3
    k_end = 20_000

    s1 = SegmentedSieveS1(n=n, sieve_depth=Q)
    s2 = HybridSieveS2(n=n, sieve_depth=Q, stride_cutoff=5_000)

    surv1 = s1.sieve_window(k_start, k_end)
    surv2 = s2.sieve_window(k_start, k_end)

    assert sorted(surv1) == sorted(surv2), "S1 and S2 must yield identical candidate sets"

def test_sieve_window_invariance():
    n = 672
    Q = 10_000
    s1 = SegmentedSieveS1(n=n, sieve_depth=Q)

    # One monolithic window [3, 20003)
    monolithic = s1.sieve_window(3, 20003)

    # Two contiguous windows [3, 10003) and [10003, 20003)
    w1 = s1.sieve_window(3, 10003)
    w2 = s1.sieve_window(10003, 20003)
    combined = sorted(w1 + w2)

    assert monolithic == combined, "Sieve must be invariant under window partitioning"

def test_matrix_lucas_vs_montgomery_ladder():
    mod = 1000000007
    P = 5
    for k in [1, 2, 3, 7, 10, 42, 100, 500, 1024, 12477]:
        val_mont = lucas_v_montgomery(k, P, mod)
        val_matr = lucas_v_matrix(k, P, mod)
        assert val_mont == val_matr, f"Mismatch at k={k}: Montgomery={val_mont}, Matrix={val_matr}"

def test_proth_preconditions_rigor():
    # Valid
    valid, msg = validate_proth_preconditions(3, 2, 13)
    assert valid, msg

    # Invalid: k >= 2^n
    valid, msg = validate_proth_preconditions(5, 2, 21)
    assert not valid
    assert "k < 2^n" in msg

    # Invalid: k even
    valid, msg = validate_proth_preconditions(4, 2, 17)
    assert not valid

def test_llr_preconditions_rigor():
    # Valid
    valid, msg = validate_llr_preconditions(3, 2, 11)
    assert valid, msg

    # Invalid: k >= 2^n
    valid, msg = validate_llr_preconditions(5, 2, 19)
    assert not valid
    assert "k < 2^n" in msg

    # Invalid: n < 2
    valid, msg = validate_llr_preconditions(3, 1, 5)
    assert not valid

def test_independent_verifier_on_phase2_certificates():
    p2_dir = Path("proofs/phase2")
    certs = list(p2_dir.glob("*.json"))
    assert len(certs) >= 3, "Expected at least 3 Phase 2 certificates"

    for c in certs:
        passed, msgs = verify_certificate_file(c)
        assert passed, f"Certificate {c.name} failed independent verification: {msgs}"

def test_adversarial_certificate_mutation_rejection():
    cert_path = Path("proofs/phase2/cert_k12477_n330.json")
    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Tamper decimal digit
    tampered = json.loads(json.dumps(data))
    tampered["p_minus"] = str(int(tampered["p_minus"]) + 2)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(tampered, tmp)
        tmp_p = Path(tmp.name)
    try:
        passed, msgs = verify_certificate_file(tmp_p)
        assert not passed, "Tampered decimal digit must fail verification"
    finally:
        tmp_p.unlink()

    # 2. Tamper witness
    tampered2 = json.loads(json.dumps(data))
    tampered2["proof_plus"]["witness"] = 2
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(tampered2, tmp)
        tmp_p2 = Path(tmp.name)
    try:
        passed, msgs = verify_certificate_file(tmp_p2)
        assert not passed, "Invalid witness must fail verification"
    finally:
        tmp_p2.unlink()

def test_storage_task_partial_and_completed_semantics():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.sqlite"
        storage = Phase3Storage(db_path)
        storage.register_task("task_test_1", "camp1", 1024, 3, 10003)

        claimed = storage.claim_next_task("camp1", "worker_1")
        assert claimed is not None
        assert claimed["task_id"] == "task_test_1"

        # Update partial progress
        storage.update_task_progress("task_test_1", next_k=5003, is_completed=False, stats_delta={"raw_tested": 2500})
        status = storage.get_campaign_status("camp1")
        assert status["completed_tasks"] == 0
        assert status["partial_tasks"] == 1
        assert status["raw_tested"] == 2500

        # Complete task
        storage.update_task_progress("task_test_1", next_k=10003, is_completed=True, stats_delta={"raw_tested": 2500})
        status2 = storage.get_campaign_status("camp1")
        assert status2["completed_tasks"] == 1
        assert status2["partial_tasks"] == 0
        assert status2["raw_tested"] == 5000

def test_historical_discrepancy_regression_prevention():
    root = Path(__file__).resolve().parent.parent.parent
    old_composite_str = "5205862110637458953584332604028295903027"
    old_330_str = "27017684065910243176662483861875168819443588975317769532551460592962384976785160875323282245388052103167"
    old_512_str = "822557555627267597148560021677382218059881829631718134764024846747656910382276563777719630740954546452291566442654347781076949397669460505191261386121927376895"

    for md_file in [root / "README.md", root / "FINDINGS.md", root / "research/phase2/DISCOVERY_STATUS.md"]:
        if md_file.exists():
            text = md_file.read_text(encoding="utf-8")
            assert old_composite_str not in text
            assert old_330_str not in text
            assert old_512_str not in text

def test_storage_stale_claim_recovery():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_recovery.sqlite"
        storage = Phase3Storage(db_path)
        storage.register_task("task_crash_1", "camp_rec", 1024, 3, 10003)

        # Worker 1 claims task
        claimed = storage.claim_next_task("camp_rec", "worker_dead")
        assert claimed is not None
        assert claimed["task_id"] == "task_crash_1"

        # Under active lease (e.g. lease_timeout_sec=300), another worker gets None
        assert storage.claim_next_task("camp_rec", "worker_2", lease_timeout_sec=300.0) is None

        # When lease expires (simulated with lease_timeout_sec=-1.0), task is reclaimed!
        reclaimed = storage.claim_next_task("camp_rec", "worker_alive", lease_timeout_sec=-1.0)
        assert reclaimed is not None
        assert reclaimed["task_id"] == "task_crash_1"

def test_independent_verify_rejects_checksum_tamper():
    cert_path = Path("proofs/phase3/cert_k15993_n672.json")
    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Corrupt artifact_sha256
    tampered = json.loads(json.dumps(data))
    tampered["artifact_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(tampered, tmp)
        tmp_p = Path(tmp.name)
    try:
        passed, msgs = verify_certificate_file(tmp_p)
        assert not passed, "Tampered artifact_sha256 must fail verification"
        assert any("artifact_sha256 mismatch" in m for m in msgs)
    finally:
        tmp_p.unlink()

def test_cli_config_precedence():
    from src.phase3.cli import main
    from src.phase3.config import Phase3Config
    import subprocess
    import sys

    # Test that --config preserves values and is not overridden by default flags
    res = subprocess.run(
        [sys.executable, "-m", "src.phase3", "search", "--config", "configs/phase3/stretch_500.json", "--dry-run"],
        capture_output=True, text=True, check=True
    )
    assert "stretch_500" in res.stdout
    assert ">=500" in res.stdout
