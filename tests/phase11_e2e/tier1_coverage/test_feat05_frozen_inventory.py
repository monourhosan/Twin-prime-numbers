"""Feature 5: Frozen Historical Inventory Verification.

Verifies:
1. historical_inventory.json exists in research/phase11/historical_inventory.json.
2. Exactly 62 historical discovery records are catalogued.
3. All canonical fields are present in every inventory record.
4. All 62 referenced certificate JSON files exist on disk in proofs/.
5. Zero duplicate pairs exist, and all pairs satisfy Q - P == 2.
"""

import json
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import INVENTORY_ENTRY_REQUIRED_FIELDS


INVENTORY_PATH = Path("research/phase11/historical_inventory.json")


@pytest.mark.phase11_tier1
def test_f05_inventory_file_exists() -> None:
    """Verifies historical_inventory.json exists and is valid JSON."""
    if not INVENTORY_PATH.is_file():
        if Phase11ContractAdapter.get_mode() == "LIVE":
            pytest.fail(f"LIVE mode mandates {INVENTORY_PATH}")
        pytest.skip(f"{INVENTORY_PATH} not yet available")

    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)


@pytest.mark.phase11_tier1
def test_f05_exact_62_pairs_recorded() -> None:
    """Verifies that exactly 62 historical twin prime discoveries are catalogued."""
    if not INVENTORY_PATH.is_file():
        pytest.skip(f"{INVENTORY_PATH} not yet available")

    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 62, f"Expected exactly 62 historical pairs, found {len(data)}"


@pytest.mark.phase11_tier1
def test_f05_required_canonical_fields_present() -> None:
    """Verifies all required canonical fields are populated in every record."""
    if not INVENTORY_PATH.is_file():
        pytest.skip(f"{INVENTORY_PATH} not yet available")

    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, entry in enumerate(data):
        for field in INVENTORY_ENTRY_REQUIRED_FIELDS:
            assert field in entry, f"Missing field '{field}' in record {i}"
            assert entry[field] is not None, f"Null field '{field}' in record {i}"


@pytest.mark.phase11_tier1
def test_f05_all_referenced_certificates_exist() -> None:
    """Verifies that all 62 referenced certificate files exist on disk."""
    if not INVENTORY_PATH.is_file():
        pytest.skip(f"{INVENTORY_PATH} not yet available")

    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing = []
    for entry in data:
        cert_path = Path(entry["certificate_path"])
        if not cert_path.is_file():
            missing.append(str(cert_path))

    assert len(missing) == 0, f"Missing {len(missing)} certificate files: {missing[:5]}"


@pytest.mark.phase11_tier1
def test_f05_zero_duplicate_pairs() -> None:
    """Verifies zero duplicate pairs and valid twin prime gap Q - P = 2 across all 62 records."""
    if not INVENTORY_PATH.is_file():
        pytest.skip(f"{INVENTORY_PATH} not yet available")

    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen_pairs = set()
    for entry in data:
        P = int(entry["P"])
        Q = int(entry["Q"])
        pair = (P, Q)
        assert pair not in seen_pairs, f"Duplicate pair detected: {pair}"
        seen_pairs.add(pair)
        assert Q - P == 2, f"Invalid twin gap in record {entry.get('canonical_key')}: {Q - P} != 2"
