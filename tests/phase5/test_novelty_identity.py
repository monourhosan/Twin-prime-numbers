"""
Regression tests for Phase 5 Canonical Identity and Novelty Pipeline (P0-B).
Verifies:
- Stable canonical pair ID across representations: twin-pair-v1:<decimal A>:<decimal B>.
- Distinct digests: pair_id vs certificate sha256.
- Candidate absent from pre-run inventory then inserted as PRP remains NEW_TO_REPO_ONLY.
- Candidate in pre-run inventory yields ALREADY_IN_REPOSITORY.
- Re-encounter of same pair is idempotent and stable.
"""

import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from src.phase5.storage import Phase5Storage

def test_canonical_pair_key_and_id_ordering():
    """Verify pair identity is order-independent and domain-separated."""
    A = 1000000000002371
    B = 1000000000002373
    
    key_ab = Phase5Storage.canonical_pair_key(A, B)
    key_ba = Phase5Storage.canonical_pair_key(B, A)
    assert key_ab == key_ba == f"twin-pair-v1:{A}:{B}"
    
    id_ab = Phase5Storage.canonical_pair_id(A, B)
    id_ba = Phase5Storage.canonical_pair_id(B, A)
    assert id_ab == id_ba
    expected_hash = hashlib.sha256(f"twin-pair-v1:{A}:{B}".encode("utf-8")).hexdigest()
    assert id_ab == expected_hash

def test_pair_id_distinct_from_certificate_sha256():
    """Scenario 14: Certificate metadata variations do not alter pair identity."""
    A = 1019
    B = 1021
    pair_id = Phase5Storage.canonical_pair_id(A, B)
    
    # Mock two different certificates for the exact same pair
    cert1 = {
        "schema_version": "5.0",
        "lower_decimal": str(A),
        "upper_decimal": str(B),
        "metadata": "run_1"
    }
    cert2 = {
        "schema_version": "5.0",
        "lower_decimal": str(A),
        "upper_decimal": str(B),
        "metadata": "run_2_different_timestamp"
    }
    
    sha1 = hashlib.sha256(json.dumps(cert1, sort_keys=True).encode("utf-8")).hexdigest()
    sha2 = hashlib.sha256(json.dumps(cert2, sort_keys=True).encode("utf-8")).hexdigest()
    
    assert sha1 != sha2
    assert pair_id != sha1
    assert pair_id != sha2
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Phase5Storage(db_path)
        
        # is_known_discovery must operate on pair_id, never confusing sha256
        assert not storage.is_known_discovery(pair_id)
        storage.record_discovery("fam", 1, 4, A, B, "c1.json", sha1, "NEW_TO_REPO_ONLY", pair_id=pair_id)
        assert storage.is_known_discovery(pair_id)

def test_candidate_in_pre_run_inventory():
    """Scenario 11: Candidate already in historical baseline -> ALREADY_IN_REPOSITORY."""
    A = 1000000000002371
    B = 1000000000002373
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        
        inv_path = tmp_path / "hist_inv.json"
        with open(inv_path, "w") as f:
            json.dump([{
                "canonical_pair_key": f"twin-pair-v1:{A}:{B}",
                "pair_id": storage.canonical_pair_id(A, B),
                "A": str(A),
                "B": str(B)
            }], f)
            
        status = storage.check_novelty(A, B, historical_inventory_path=inv_path)
        assert status in ("ALREADY_IN_REPOSITORY", "ALREADY_IN_HISTORICAL_INVENTORY")

def test_candidate_inserted_as_prp_not_self_contaminated():
    """Scenario 12: Candidate absent from inventory, inserted as PRP, remains NEW_TO_REPO_ONLY."""
    A = 1019
    B = 1021
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        
        inv_path = tmp_path / "hist_inv.json"
        with open(inv_path, "w") as f:
            json.dump([], f)
            
        pair_id = storage.canonical_pair_id(A, B)
        # Simulate PRP recording in candidates table
        storage.record_candidate("smoke", 1, A, B, 4, "PRP_BOTH", pair_id)
        
        # check_novelty must NOT be self-contaminated by the candidates table
        status = storage.check_novelty(A, B, historical_inventory_path=inv_path)
        assert status in ("NEW_TO_REPO_ONLY", "NEW_TO_REPOSITORY")

def test_re_encounter_is_idempotent():
    """Scenario 13: Re-encounter of same candidate produces DUPLICATE_IN_CURRENT_RUN after discovery."""
    A = 1019
    B = 1021
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test.db"
        storage = Phase5Storage(db_path)
        
        inv_path = tmp_path / "hist_inv.json"
        with open(inv_path, "w") as f:
            json.dump([], f)
            
        pair_id = storage.canonical_pair_id(A, B)
        
        # First encounter
        status1 = storage.check_novelty(A, B, historical_inventory_path=inv_path)
        assert status1 in ("NEW_TO_REPO_ONLY", "NEW_TO_REPOSITORY")
        
        # Record discovery
        storage.record_discovery("smoke", 1, 4, A, B, "c.json", "sha_dummy", status1, pair_id=pair_id)
        
        # Re-encounter
        status2 = storage.check_novelty(A, B, historical_inventory_path=inv_path)
        assert status2 == "DUPLICATE_IN_CURRENT_RUN"
