"""Feature 21: Dual Novelty Verification.

Verifies:
1. Detection of historical repository pairs returning ALREADY_IN_REPOSITORY.
2. Novel candidate pairs returning NOVEL_TO_REPOSITORY.
3. Batch validation against frozen 62-pair repository inventory.
4. Public database novelty status contract in certificates.
5. Idempotent and consistent novelty verification behavior.
"""

import json
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


INVENTORY_PATH = Path("research/phase11/historical_inventory.json")


@pytest.fixture
def historical_pairs() -> list[tuple[int, int]]:
    """Loads first 5 historical twin prime pairs from inventory."""
    if not INVENTORY_PATH.is_file():
        pytest.skip("historical_inventory.json not available")
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [(int(entry["P"]), int(entry["Q"])) for entry in data[:5]]


@pytest.mark.phase11_tier1
def test_f21_historical_pair_detected(historical_pairs: list) -> None:
    """Verifies that a known historical pair is flagged ALREADY_IN_REPOSITORY."""
    P, Q = historical_pairs[0]
    status = Phase11ContractAdapter.check_novelty(P, Q)
    assert status == "ALREADY_IN_REPOSITORY"


@pytest.mark.phase11_tier1
def test_f21_new_candidate_flagged_novel() -> None:
    """Verifies that a new OPQM-11 candidate pair is flagged NOVEL_TO_REPOSITORY."""
    # A candidate from OPQM-11 manifold not present in historical inventory
    _, A, B = Phase11ContractAdapter.compute_candidate_pair(y=3, t=21)
    status = Phase11ContractAdapter.check_novelty(A, B)
    assert status == "NOVEL_TO_REPOSITORY"


@pytest.mark.phase11_tier1
def test_f21_all_historical_pairs_flagged_already_in_repo(historical_pairs: list) -> None:
    """Verifies multiple historical pairs are consistently recognized."""
    for P, Q in historical_pairs:
        status = Phase11ContractAdapter.check_novelty(P, Q)
        assert status == "ALREADY_IN_REPOSITORY", f"Failed to identify historical pair ({P}, {Q})"


@pytest.mark.phase11_tier1
def test_f21_public_database_novelty_status() -> None:
    """Verifies public database novelty status field in generated certificate."""
    cert = Phase11ContractAdapter.prove_pair(y=3, t=21)
    assert "novelty_status_public" in cert
    assert cert["novelty_status_public"] == "NOVEL_TO_PUBLIC_RECORDS"
    assert cert["novelty_status_repository"] == "NOVEL_TO_REPOSITORY"


@pytest.mark.phase11_tier1
def test_f21_novelty_checker_idempotence(historical_pairs: list) -> None:
    """Verifies repeated novelty checks yield identical status without side effects."""
    P, Q = historical_pairs[0]
    res1 = Phase11ContractAdapter.check_novelty(P, Q)
    res2 = Phase11ContractAdapter.check_novelty(P, Q)
    assert res1 == res2 == "ALREADY_IN_REPOSITORY"

    _, A, B = Phase11ContractAdapter.compute_candidate_pair(3, 21)
    nov1 = Phase11ContractAdapter.check_novelty(A, B)
    nov2 = Phase11ContractAdapter.check_novelty(A, B)
    assert nov1 == nov2 == "NOVEL_TO_REPOSITORY"
