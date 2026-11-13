"""
Reproduction and Regression Test Suite for Phase 5 Issues:
1. Novelty detection and insertion ordering (Issue 3.1)
2. UCB1 cumulative reward mean and bounded accounting (Issue 3.2)
3. Checkpoint restoration and --resume interval continuity (Issue 3.3)
4. Audit CLI and certificate-hash reconciliation (Issue 3.4)
"""

import os
import json
import time
import pytest
from pathlib import Path

from src.phase5.candidates import SmoothCenterFamily, TwinPairCandidate
from src.phase5.storage import Phase5Storage
from src.phase5.scheduler import MultiFamilyScheduler, SCCAProfile, SchedulingPolicy

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

@pytest.fixture
def temp_db(tmp_path):
    return tmp_path / "test_phase5_repair.db"

@pytest.fixture
def temp_storage(temp_db):
    return Phase5Storage(temp_db)

# ---------------------------------------------------------------------------
# Issue 3.1: Novelty detection and insertion ordering
# ---------------------------------------------------------------------------

def test_novelty_pipeline_and_canonicalization(temp_storage, tmp_path):
    """
    Validates explicit novelty pipeline:
    - Canonical key is invariant to pair order (min(P, Q), max(P, Q)).
    - Invalid gap != 2 is rejected as INVALID_PAIR.
    - Historical pairs are classified as ALREADY_IN_HISTORICAL_INVENTORY.
    - New pair is classified as NEW_TO_REPOSITORY before insertion.
    - Subsequent occurrence in current run is classified as DUPLICATE_IN_CURRENT_RUN.
    """
    # Create a small mock historical inventory
    hist_inv_path = tmp_path / "mock_hist_inventory.json"
    hist_data = [
        {
            "canonical_key": "1000000000061:1000000000063",
            "P": "1000000000061",
            "Q": "1000000000063",
            "digits_P": 13,
            "digits_Q": 13,
            "raw_sha256": "mockhash123"
        }
    ]
    with open(hist_inv_path, "w", encoding="utf-8") as f:
        json.dump(hist_data, f)

    # 1. Test canonicalization & gap validation
    cand_A = 1000000000061
    cand_B = 1000000000063
    # Check reversed order produces exact same key
    assert temp_storage.canonical_key(cand_A, cand_B) == temp_storage.canonical_key(cand_B, cand_A)
    assert temp_storage.canonical_key(cand_A, cand_B) == f"{cand_A}:{cand_B}"

    # 2. Check historical novelty lookup before insertion
    status_hist = temp_storage.check_novelty(cand_A, cand_B, historical_inventory_path=hist_inv_path)
    assert status_hist == "ALREADY_IN_HISTORICAL_INVENTORY"

    # 3. Check genuinely new candidate
    new_A = 2000000000079
    new_B = 2000000000081
    status_new = temp_storage.check_novelty(new_A, new_B, historical_inventory_path=hist_inv_path)
    assert status_new == "NEW_TO_REPOSITORY"

    # 4. Check invalid pair
    status_invalid = temp_storage.check_novelty(new_A, new_A + 4, historical_inventory_path=hist_inv_path)
    assert status_invalid == "INVALID_PAIR"

    # 5. Insertion ordering: record candidate, then re-check novelty
    temp_storage.record_candidate(
        family_id="fam_test",
        t=10,
        A=new_A,
        B=new_B,
        digits=len(str(new_A)),
        status="PROVEN_BOTH",
        canonical_hash=temp_storage.canonical_hash(new_A, new_B)
    )

    # Now that it's in the current run's database, checking again must report duplicate
    status_dup = temp_storage.check_novelty(new_A, new_B, historical_inventory_path=hist_inv_path)
    assert status_dup == "DUPLICATE_IN_CURRENT_RUN"

# ---------------------------------------------------------------------------
# Issue 3.2: UCB1 scheduler and reward accounting
# ---------------------------------------------------------------------------

def test_ucb1_uses_cumulative_mean_not_last_reward(temp_storage):
    """
    Validates that UCB1 uses the cumulative empirical mean (cumulative_reward / pulls),
    not the most-recent reward.
    """
    profiles = [
        SCCAProfile(family_id="fam_alpha", exponents={2: 1, 3: 2}, t_batch_size=100),
        SCCAProfile(family_id="fam_beta", exponents={2: 1, 3: 3}, t_batch_size=100),
    ]
    scheduler = MultiFamilyScheduler(
        storage=temp_storage,
        profiles=profiles,
        policy=SchedulingPolicy.BANDIT_UCB1,
        min_exploration_pulls=1,
        ucb_c=0.0 # Zero exploration bonus to isolate empirical mean
    )

    # Initial pulls: 1 each
    # fam_alpha pull 1: reward = 0.8
    temp_storage.update_bandit_stats("fam_alpha", elapsed_sec=1.0, survivors=8, dual_prp=0, proven=0, reward=0.8)
    # fam_beta pull 1: reward = 0.4
    temp_storage.update_bandit_stats("fam_beta", elapsed_sec=1.0, survivors=4, dual_prp=0, proven=0, reward=0.4)

    # fam_alpha pull 2: reward = 0.2 -> cumulative = 1.0, mean = 0.5
    temp_storage.update_bandit_stats("fam_alpha", elapsed_sec=1.0, survivors=2, dual_prp=0, proven=0, reward=0.2)
    # fam_beta pull 2: reward = 0.4 -> cumulative = 0.8, mean = 0.4
    temp_storage.update_bandit_stats("fam_beta", elapsed_sec=1.0, survivors=4, dual_prp=0, proven=0, reward=0.4)

    stats = temp_storage.get_bandit_stats()
    assert stats["fam_alpha"]["pulls"] == 2
    assert abs(stats["fam_alpha"]["cumulative_reward"] - 1.0) < 1e-6
    assert abs(stats["fam_alpha"]["mean_reward"] - 0.5) < 1e-6

    assert stats["fam_beta"]["pulls"] == 2
    assert abs(stats["fam_beta"]["cumulative_reward"] - 0.8) < 1e-6
    assert abs(stats["fam_beta"]["mean_reward"] - 0.4) < 1e-6

    # fam_alpha has mean 0.5, fam_beta has mean 0.4.
    # But fam_alpha's LAST reward was 0.2, whereas fam_beta's LAST reward was 0.4!
    # If using cumulative mean, fam_alpha (0.5) MUST WIN over fam_beta (0.4).
    # If using last_reward (bug), fam_beta (0.4) would incorrectly win!
    prof, rationale = scheduler.select_next_profile()
    assert prof.family_id == "fam_alpha", f"Expected fam_alpha (mean 0.5) to beat fam_beta (mean 0.4), got {prof.family_id}"

def test_ucb1_deterministic_tie_breaking(temp_storage):
    """Verifies that ties between equal arms are broken deterministically by family_id."""
    profiles = [
        SCCAProfile(family_id="fam_z", exponents={2: 1, 3: 2}, t_batch_size=100),
        SCCAProfile(family_id="fam_a", exponents={2: 1, 3: 3}, t_batch_size=100),
    ]
    scheduler = MultiFamilyScheduler(
        storage=temp_storage,
        profiles=profiles,
        policy=SchedulingPolicy.BANDIT_UCB1,
        min_exploration_pulls=1,
        ucb_c=1.414
    )
    # Both arms have 1 pull with identical reward 0.5
    temp_storage.update_bandit_stats("fam_z", elapsed_sec=1.0, survivors=5, dual_prp=0, proven=0, reward=0.5)
    temp_storage.update_bandit_stats("fam_a", elapsed_sec=1.0, survivors=5, dual_prp=0, proven=0, reward=0.5)

    prof, _ = scheduler.select_next_profile()
    # Lexicographically earlier "fam_a" must win tie deterministically
    assert prof.family_id == "fam_a"

# ---------------------------------------------------------------------------
# Issue 3.3: Checkpointing and --resume
# ---------------------------------------------------------------------------

def test_resume_restores_next_search_interval(temp_storage):
    """
    Validates that resuming a search restores the next unprocessed t index
    per family rather than restarting from t=1.
    """
    prof = SCCAProfile(family_id="fam_resume", exponents={2: 1, 3: 2}, t_batch_size=1000)
    scheduler = MultiFamilyScheduler(
        storage=temp_storage,
        profiles=[prof],
        policy=SchedulingPolicy.ROUND_ROBIN
    )

    # Dispense two units: [1, 1001), [1001, 2001)
    wu1 = scheduler.dispense_work_unit()
    assert wu1["t_start"] == 1
    assert wu1["t_end"] == 1001
    temp_storage.complete_work_unit(wu1["work_unit_id"], survivors=10, dual_prp=0, proven=0)

    wu2 = scheduler.dispense_work_unit()
    assert wu2["t_start"] == 1001
    assert wu2["t_end"] == 2001
    temp_storage.complete_work_unit(wu2["work_unit_id"], survivors=12, dual_prp=0, proven=0)

    # Now simulate process restart: instantiate a NEW scheduler pointing to the same storage
    # When resume=True is requested, it must continue from t=2001, NOT t=1
    resumed_scheduler = MultiFamilyScheduler(
        storage=temp_storage,
        profiles=[prof],
        policy=SchedulingPolicy.ROUND_ROBIN,
        resume=True
    )
    wu_resumed = resumed_scheduler.dispense_work_unit()
    assert wu_resumed["t_start"] == 2001, f"Expected resumed t_start=2001, got {wu_resumed['t_start']}"
    assert wu_resumed["t_end"] == 3001

# ---------------------------------------------------------------------------
# Issue 3.4: Documentation and certificate-hash reconciliation
# ---------------------------------------------------------------------------

def test_historical_inventory_reconciliation():
    """
    Validates that the frozen historical inventory accurately reflects the actual
    filesystem proof files and matches its recorded SHA-256 checksum.
    """
    inv_path = REPO_ROOT / "research" / "phase5_audit" / "historical_inventory.json"
    sha_path = REPO_ROOT / "research" / "phase5_audit" / "historical_inventory.sha256"
    assert inv_path.exists(), "Historical inventory JSON missing"
    assert sha_path.exists(), "Historical inventory SHA-256 missing"

    import hashlib
    raw_hash = hashlib.sha256(inv_path.read_bytes()).hexdigest()
    with open(sha_path, "r", encoding="utf-8") as f:
        stored_hash = f.read().split()[0]
    assert raw_hash == stored_hash, f"Historical inventory checksum mismatch: {raw_hash} != {stored_hash}"

    with open(inv_path, "r", encoding="utf-8") as f:
        inv = json.load(f)

    # Must contain all 48 certificates across Phases 1-5
    assert len(inv) == 48, f"Expected 48 historical certificates, got {len(inv)}"

    # Check that maximum recorded digits is 1509
    max_d = max(r["digits_P"] for r in inv)
    assert max_d == 1509, f"Expected max historical digits 1509, got {max_d}"
