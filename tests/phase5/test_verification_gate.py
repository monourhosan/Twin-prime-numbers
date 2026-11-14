"""
Regression tests for Phase 5 Fail-Closed Verification Acceptance Gate (P0-A).
Verifies that no candidate can be accepted or recorded into discoveries unless
the independent verifier runs, produces a valid attestation with result PASS,
and confirms exact certificate SHA-256 and integer pair identities.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from src.phase5.candidates import SmoothCenterFamily
from src.phase5.cli import execute_discovery_search
from src.phase5.storage import Phase5Storage
from src.phase5.scheduler import SCCAProfile

def test_missing_verifier_blocks_acceptance():
    """Scenario 1: Verifier executable missing -> candidate is NOT accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)
        
        # Monkeypatch verifier script path to nonexistent
        orig_script = Path("scripts/phase5_independent_verify.py")
        missing_script = tmp_path / "nonexistent_verifier.py"
        
        import src.phase5.cli as cli
        old_parent = cli.Path.__file__ if hasattr(cli.Path, "__file__") else None
        
        # We can temporarily rename or mock subprocess.run in execute_discovery_search
        real_run = subprocess.run
        def mock_missing_run(*args, **kwargs):
            raise FileNotFoundError("Mock verifier script missing")

        try:
            subprocess.run = mock_missing_run
            res = execute_discovery_search(
                storage=storage,
                profile=prof,
                t_start=4,
                t_end=5,
                output_dir=tmp_path / "proofs",
                historical_inventory_path=None,
                verbose=False
            )
            # Must NOT accept
            assert len(res["discoveries"]) == 0
            assert res["metrics"]["failed_verification"] > 0
            assert res["metrics"]["verified"] == 0
            with storage._get_connection() as conn:
                discs = conn.execute("SELECT * FROM discoveries").fetchall()
                assert len(discs) == 0
                cands = conn.execute("SELECT status FROM candidates").fetchall()
                assert any(c["status"] == "VERIFICATION_FAILED" for c in cands)
        finally:
            subprocess.run = real_run

def test_verifier_exit_code_1_blocks_acceptance():
    """Scenario 2: Verifier returns code 1 -> NOT accepted, no success counter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)

        real_run = subprocess.run
        def mock_fail_run(*args, **kwargs):
            class MockRes:
                returncode = 1
                stderr = "Mock verification failure"
                stdout = ""
            return MockRes()

        try:
            subprocess.run = mock_fail_run
            res = execute_discovery_search(
                storage=storage,
                profile=prof,
                t_start=4,
                t_end=5,
                output_dir=tmp_path / "proofs",
                historical_inventory_path=None,
                verbose=False
            )
            assert len(res["discoveries"]) == 0
            assert res["metrics"]["verified"] == 0
            with storage._get_connection() as conn:
                discs = conn.execute("SELECT * FROM discoveries").fetchall()
                assert len(discs) == 0
        finally:
            subprocess.run = real_run

def test_verifier_attestation_fail_blocks_acceptance():
    """Scenario 3: Verifier returns code 0 but attestation reports FAIL -> NOT accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)

        real_run = subprocess.run
        def mock_attest_fail(cmd, *args, **kwargs):
            cert_file = Path(cmd[2])
            with open(cert_file) as f:
                cdata = json.load(f)
            att_dir = cert_file.parent / "attestations"
            att_dir.mkdir(parents=True, exist_ok=True)
            att_path = att_dir / f"attest_{cdata['sha256'][:16]}.json"
            with open(att_path, "w") as f:
                json.dump({
                    "result": "FAIL",
                    "target_sha256": cdata["sha256"],
                    "target_certificate": cert_file.name
                }, f)
            class MockRes:
                returncode = 0
                stdout = ""
                stderr = ""
            return MockRes()

        try:
            subprocess.run = mock_attest_fail
            res = execute_discovery_search(
                storage=storage,
                profile=prof,
                t_start=4,
                t_end=5,
                output_dir=tmp_path / "proofs",
                historical_inventory_path=None,
                verbose=False
            )
            assert len(res["discoveries"]) == 0
            assert res["metrics"]["verified"] == 0
        finally:
            subprocess.run = real_run

def test_verifier_no_attestation_blocks_acceptance():
    """Scenario 4: Verifier returns code 0 but produces no attestation file -> NOT accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)

        real_run = subprocess.run
        def mock_no_attest(*args, **kwargs):
            class MockRes:
                returncode = 0
                stdout = ""
                stderr = ""
            return MockRes()

        try:
            subprocess.run = mock_no_attest
            res = execute_discovery_search(
                storage=storage,
                profile=prof,
                t_start=4,
                t_end=5,
                output_dir=tmp_path / "proofs",
                historical_inventory_path=None,
                verbose=False
            )
            assert len(res["discoveries"]) == 0
            assert res["metrics"]["verified"] == 0
        finally:
            subprocess.run = real_run

def test_verifier_timeout_blocks_acceptance():
    """Scenario 5: Verifier subprocess timeout -> NOT accepted, diagnostic status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)

        real_run = subprocess.run
        def mock_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["mock"], timeout=60.0)

        try:
            subprocess.run = mock_timeout
            res = execute_discovery_search(
                storage=storage,
                profile=prof,
                t_start=4,
                t_end=5,
                output_dir=tmp_path / "proofs",
                historical_inventory_path=None,
                verbose=False
            )
            assert len(res["discoveries"]) == 0
            assert res["metrics"]["failed_verification"] > 0
        finally:
            subprocess.run = real_run

def test_attestation_mismatch_blocks_acceptance():
    """Scenario 6: Attestation references a different SHA-256 digest -> NOT accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)

        real_run = subprocess.run
        def mock_mismatch(cmd, *args, **kwargs):
            cert_file = Path(cmd[2])
            with open(cert_file) as f:
                cdata = json.load(f)
            att_dir = cert_file.parent / "attestations"
            att_dir.mkdir(parents=True, exist_ok=True)
            att_path = att_dir / f"attest_{cdata['sha256'][:16]}.json"
            with open(att_path, "w") as f:
                json.dump({
                    "result": "PASS",
                    "target_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "target_certificate": cert_file.name
                }, f)
            class MockRes:
                returncode = 0
                stdout = ""
                stderr = ""
            return MockRes()

        try:
            subprocess.run = mock_mismatch
            res = execute_discovery_search(
                storage=storage,
                profile=prof,
                t_start=4,
                t_end=5,
                output_dir=tmp_path / "proofs",
                historical_inventory_path=None,
                verbose=False
            )
            assert len(res["discoveries"]) == 0
        finally:
            subprocess.run = real_run

def test_real_tiny_pair_passes_all_gates():
    """Positive test: Real tiny twin pair (t=4 in smoke family) passes all gates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        fam = SmoothCenterFamily({2: 3, 3: 4, 5: 2, 7: 1}, family_id="smoke")
        prof = SCCAProfile(family_id="smoke", exponents={2: 3, 3: 4, 5: 2, 7: 1}, t_batch_size=10, sieve_limit=100)

        res = execute_discovery_search(
            storage=storage,
            profile=prof,
            t_start=4,
            t_end=5,
            output_dir=tmp_path / "proofs",
            historical_inventory_path=None,
            verbose=False
        )
        assert len(res["discoveries"]) == 1
        assert res["metrics"]["verified"] == 1
        find = res["discoveries"][0]
        assert Path(find["cert_path"]).exists()
        assert Path(find["attestation_path"]).exists()
        with open(find["attestation_path"]) as af:
            att = json.load(af)
            assert att["result"] == "PASS"
            assert att["target_sha256"] == find["sha256"]
        with storage._get_connection() as conn:
            discs = conn.execute("SELECT * FROM discoveries").fetchall()
            assert len(discs) == 1
            assert discs[0]["sha256"] == find["sha256"]
            assert discs[0]["pair_id"] == find["pair_id"]
