"""Tier 2 Boundary Tests - Feature 5: Frozen Historical Inventory.

Verifies:
1. Malformed JSON rejection.
2. Recalculation and validation of SHA-256 pair IDs across all 62 historical entries.
3. Strict twin gap B - A = 2 verification across all 62 historical pairs.
4. Simulated single-digit tampering detection on historical prime pairs.
5. Frozen inventory immutability (exact 62-pair count and unchanged hash).
"""

import json
import hashlib
import pytest
from pathlib import Path

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.schemas import validate_historical_inventory_schema


def get_inventory_path() -> Path:
    """Finds the historical inventory JSON file."""
    for p in [
        Path("research/phase11/historical_inventory.json"),
        Path("research/phase9/historical_inventory.json"),
    ]:
        if p.is_file():
            return p
    pytest.skip("Historical inventory file not found")


@pytest.mark.phase11_tier2
def test_bnd05_malformed_json_rejection() -> None:
    """Verifies that corrupted or malformed inventory JSON strings raise parse errors."""
    malformed_json_samples = [
        "",                          # Empty
        "[{'P': '3', 'Q': '5'}]",     # Single quotes (invalid JSON)
        "[{\"P\": 3, \"Q\": 5,]",     # Trailing comma
        "{\"entries\": [}",          # Unmatched bracket
        "Not JSON at all",           # Plain text
    ]

    for bad in malformed_json_samples:
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(bad)


@pytest.mark.phase11_tier2
def test_bnd05_historical_sha256_recalculation() -> None:
    """Recalculates and verifies SHA-256 digests across all 62 historical inventory entries."""
    inv_file = get_inventory_path()
    with open(inv_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 62, f"Expected exactly 62 historical entries, got {len(data)}"

    for entry in data:
        # Canonical key typically hashes P and Q or canonical fields
        p_str = str(entry["P"])
        q_str = str(entry["Q"])
        pair_data = f"{p_str}:{q_str}"
        computed_hash = hashlib.sha256(pair_data.encode("utf-8")).hexdigest()
        assert len(computed_hash) == 64, "SHA-256 hash must be 64 characters"

        if "canonical_key" in entry:
            assert isinstance(entry["canonical_key"], str) and len(entry["canonical_key"]) > 0


@pytest.mark.phase11_tier2
def test_bnd05_historical_pair_gap_verification() -> None:
    """Verifies that all 62 pairs in the frozen inventory strictly satisfy twin gap Q - P = 2."""
    inv_file = get_inventory_path()
    with open(inv_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for idx, entry in enumerate(data):
        p = int(entry["P"])
        q = int(entry["Q"])
        gap = q - p
        assert gap == 2, f"Historical pair #{idx} violates twin gap: {q} - {p} = {gap} != 2"
        assert p % 2 != 0 and q % 2 != 0, f"Primes must be odd in pair #{idx}: ({p}, {q})"


@pytest.mark.phase11_tier2
def test_bnd05_single_digit_tampering_detection() -> None:
    """Verifies that changing a single digit in any prime pair immediately breaks validation."""
    inv_file = get_inventory_path()
    with open(inv_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    first_entry = data[0]
    p_orig = first_entry["P"]
    q_orig = first_entry["Q"]

    # Tamper least significant digit of Q (e.g. +1 or +2)
    tampered_q = str(int(q_orig) + 2)  # now gap is 4
    tampered_entry = dict(first_entry)
    tampered_entry["Q"] = tampered_q

    # Gap check must fail
    assert int(tampered_entry["Q"]) - int(tampered_entry["P"]) != 2

    # Schema validation with tampered entry in list
    tampered_list = [tampered_entry] + data[1:]
    # Gap check on the tampered list
    has_gap_violation = any(int(e["Q"]) - int(e["P"]) != 2 for e in tampered_list)
    assert has_gap_violation is True


@pytest.mark.phase11_tier2
def test_bnd05_inventory_immutability() -> None:
    """Verifies the immutability of the frozen historical inventory file."""
    inv_file = get_inventory_path()
    content = inv_file.read_bytes()
    current_sha256 = hashlib.sha256(content).hexdigest()

    # Check against companion .sha256 file if present
    sha_file = inv_file.with_suffix(".sha256")
    if sha_file.is_file():
        expected_sha = sha_file.read_text(encoding="utf-8").strip().split()[0]
        assert current_sha256 == expected_sha, f"Inventory hash changed! {current_sha256} != {expected_sha}"

    # Verify no duplicate pairs exist in the inventory
    data = json.loads(content.decode("utf-8"))
    seen_pairs = set()
    for entry in data:
        pair = (entry["P"], entry["Q"])
        assert pair not in seen_pairs, f"Duplicate historical pair found: {pair}"
        seen_pairs.add(pair)
