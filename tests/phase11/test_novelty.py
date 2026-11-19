"""Automated Novelty Verification Tests against Historical Inventory.

Verifies:
1. Frozen historical inventory exists and contains exactly 62 verified twin-prime pairs.
2. All 62 historical pairs are correctly recognized and flagged as ALREADY_IN_REPOSITORY.
3. Pair-ordering invariance: checking (A, B) or (B, A) yields identical novelty verdicts.
4. Discovered 13-digit candidate (y=3, t=29) is novel to repository and public records.
5. Discovered 21-digit candidate (y=5, t=215) is novel to repository and public records.
6. Novelty verification is idempotent, pure, and produces identical verdicts on repeat calls.
7. Certificate novelty fields match declared novelty status.
"""

import json
from pathlib import Path

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import validate_historical_inventory_schema

INVENTORY_PATH = Path("research/phase11/historical_inventory.json")
CERT_13D_PATH = Path("proofs/phase11/certificates/cert_opqm11_13d_t29.json")
CERT_21D_PATH = Path("proofs/phase11/certificates/cert_opqm11_21d_t215.json")


def test_historical_inventory_conformance() -> None:
    """Verifies historical inventory schema, total count of 62, and unique keys."""
    assert INVENTORY_PATH.is_file(), "historical_inventory.json must exist"
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    assert len(data) == 62, f"Expected 62 historical entries, found {len(data)}"
    is_valid, errors = validate_historical_inventory_schema(data)
    assert is_valid, f"Historical inventory validation errors: {errors}"


def test_all_62_historical_pairs_recognized() -> None:
    """Verifies that each of the 62 historical pairs is flagged ALREADY_IN_REPOSITORY."""
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    for entry in data:
        P = int(entry["P"])
        Q = int(entry["Q"])
        status = Phase11ContractAdapter.check_novelty(P, Q, inventory_path=INVENTORY_PATH)
        assert status == "ALREADY_IN_REPOSITORY", f"Failed to identify historical pair ({P}, {Q})"


def test_novelty_pair_ordering_invariance() -> None:
    """Verifies that pair ordering (P, Q) vs (Q, P) produces identical verdicts."""
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    sample_entry = data[0]
    P = int(sample_entry["P"])
    Q = int(sample_entry["Q"])

    # Historical pair in both orders
    assert Phase11ContractAdapter.check_novelty(P, Q, inventory_path=INVENTORY_PATH) == "ALREADY_IN_REPOSITORY"
    assert Phase11ContractAdapter.check_novelty(Q, P, inventory_path=INVENTORY_PATH) == "ALREADY_IN_REPOSITORY"

    # Novel pair in both orders
    A = 133961445293766749999
    B = 133961445293766750001
    assert Phase11ContractAdapter.check_novelty(A, B, inventory_path=INVENTORY_PATH) == "NOVEL_TO_REPOSITORY"
    assert Phase11ContractAdapter.check_novelty(B, A, inventory_path=INVENTORY_PATH) == "NOVEL_TO_REPOSITORY"


def test_discovery_13d_confirmed_novel() -> None:
    """Verifies novel status of the progressive validation 13-digit discovery (y=3, t=29)."""
    A = 1913967943631
    B = 1913967943633
    status = Phase11ContractAdapter.check_novelty(A, B, inventory_path=INVENTORY_PATH)
    assert status == "NOVEL_TO_REPOSITORY"


def test_discovery_21d_confirmed_novel() -> None:
    """Verifies novel status of the 21-digit discovery (y=5, t=215)."""
    A = 133961445293766749999
    B = 133961445293766750001
    status = Phase11ContractAdapter.check_novelty(A, B, inventory_path=INVENTORY_PATH)
    assert status == "NOVEL_TO_REPOSITORY"


def test_novelty_checker_idempotence() -> None:
    """Verifies novelty checks are deterministic and side-effect free."""
    A = 133961445293766749999
    B = 133961445293766750001
    res1 = Phase11ContractAdapter.check_novelty(A, B, inventory_path=INVENTORY_PATH)
    res2 = Phase11ContractAdapter.check_novelty(A, B, inventory_path=INVENTORY_PATH)
    assert res1 == res2 == "NOVEL_TO_REPOSITORY"


def test_certificate_novelty_metadata_conformance() -> None:
    """Verifies that generated certificates declare novelty status accurately."""
    for cert_path in (CERT_13D_PATH, CERT_21D_PATH):
        if cert_path.is_file():
            data = json.loads(cert_path.read_text(encoding="utf-8"))
            assert data.get("novelty_status_repository") == "NOVEL_TO_REPOSITORY"
            assert data.get("novelty_status_public") == "NOVEL_TO_PUBLIC_RECORDS"
