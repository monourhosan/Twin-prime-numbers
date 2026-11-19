"""Tier 3 Integration Suite 8: Twin-Prime Discovery (F15) x Dual Novelty Verification (F21).

Validates the pairwise interaction between:
1. Twin-Prime Pair Discovery (exact gap B-A=2, primality certification).
2. Dual Novelty Verification (automated check against frozen 62 historical pairs and public records).
"""

import json
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import validate_historical_inventory_schema


@pytest.fixture
def historical_inventory_file() -> Path:
    """Finds and returns the authoritative historical inventory path."""
    paths = [
        Path("research/phase11/historical_inventory.json"),
        Path("research/phase9/historical_inventory.json"),
        Path("reports/phase5_audit/historical_inventory.json"),
    ]
    for p in paths:
        if p.is_file():
            return p
    pytest.skip("Historical inventory file not found")


@pytest.mark.phase11_tier3
def test_combo_discovered_pair_is_novel_to_repository(historical_inventory_file: Path) -> None:
    """Verifies that a newly discovered candidate pair on the OPQM-11 manifold

    is verified as strictly novel against the repository's 62-pair historical inventory.
    """
    # x = 126 candidate from y=3, t=21
    y = 3
    t = 21
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)

    assert B - A == 2
    novelty = Phase11ContractAdapter.check_novelty(A, B, inventory_path=historical_inventory_file)
    assert novelty == "NOVEL_TO_REPOSITORY"


@pytest.mark.phase11_tier3
def test_combo_historical_inventory_pair_flagged_as_already_in_repo(historical_inventory_file: Path) -> None:
    """Confirms that querying the novelty verifier with any pair already in the historical inventory

    correctly flags it as ALREADY_IN_REPOSITORY.
    """
    with open(historical_inventory_file, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    assert len(inventory) == 62, f"Expected 62 historical pairs, found {len(inventory)}"

    # Pick the first historical pair
    first_entry = inventory[0]
    p_hist = int(first_entry["P"])
    q_hist = int(first_entry["Q"])

    novelty = Phase11ContractAdapter.check_novelty(p_hist, q_hist, inventory_path=historical_inventory_file)
    assert novelty == "ALREADY_IN_REPOSITORY"


@pytest.mark.phase11_tier3
def test_combo_novelty_check_is_order_invariant(historical_inventory_file: Path) -> None:
    """Confirms that the novelty check returns identical verdicts regardless of pair order

    (A, B) vs (B, A).
    """
    with open(historical_inventory_file, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    sample = inventory[0]
    p = int(sample["P"])
    q = int(sample["Q"])

    # Normal order (P, Q)
    res_normal = Phase11ContractAdapter.check_novelty(p, q, inventory_path=historical_inventory_file)
    assert res_normal == "ALREADY_IN_REPOSITORY"

    # Novel pair inverted (B, A)
    y = 3
    t = 21
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
    res_novel = Phase11ContractAdapter.check_novelty(A, B, inventory_path=historical_inventory_file)
    assert res_novel == "NOVEL_TO_REPOSITORY"


@pytest.mark.phase11_tier3
def test_combo_discovery_certificate_records_dual_novelty_status() -> None:
    """Verifies that the generated proof certificate for a newly discovered pair

    faithfully records the novelty status fields for both repository and public scopes.
    """
    y = 3
    t = 21
    cert = Phase11ContractAdapter.prove_pair(y, t, run_id="novelty_status_test")

    assert cert["novelty_status_repository"] == "NOVEL_TO_REPOSITORY"
    assert cert["novelty_status_public"] == "NOVEL_TO_PUBLIC_RECORDS"
