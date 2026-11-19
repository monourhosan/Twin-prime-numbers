"""Tier 2 Boundary Tests - Feature 23: Negative Results & Bottleneck Log.

Verifies:
1. Rejection of empty or unsubstantiated negative results logs.
2. Rejection of unparameterized failure claims.
3. Contradiction detection between negative logs and discovery intervals.
4. Markdown tabular schema consistency.
5. Strict separation of algorithmic vs hardware failure categories.
"""

import pytest


REQUIRED_TABLE_COLUMNS = [
    "Parameter Regime",
    "Search Depth",
    "Observed Bottleneck",
    "Resolution / Lesson",
]


@pytest.mark.phase11_tier2
def test_bnd23_empty_negative_results_rejection() -> None:
    """Verifies that an empty or placeholder negative results document is rejected."""
    def validate_negative_results_content(text: str) -> tuple[bool, str]:
        if len(text.strip()) < 100:
            return False, "Negative results document is empty or too short"
        if "non-viable" not in text.lower() and "bottleneck" not in text.lower():
            return False, "Missing discussion of non-viable parameter regimes or bottlenecks"
        return True, "OK"

    # Empty document
    ok_empty, err_empty = validate_negative_results_content("")
    assert not ok_empty
    assert "too short" in err_empty

    # Compliant document
    compliant_doc = """# Negative Results & Bottleneck Log
## 1. Non-viable parameter regimes
Exploration of y=2 (not divisible by 6) and very large sieve depth led to computational bottleneck.
"""
    ok_good, _ = validate_negative_results_content(compliant_doc)
    assert ok_good is True


@pytest.mark.phase11_tier2
def test_bnd23_unparameterized_failure_claim_rejection() -> None:
    """Verifies that failure claims must include specific parameter assignments (y, t_range, depth)."""
    def validate_failure_claim(entry: dict) -> tuple[bool, list[str]]:
        required_fields = ["parameter_regime", "anchor_y", "t_range", "root_cause"]
        missing = [f for f in required_fields if f not in entry]
        return len(missing) == 0, missing

    # Unparameterized claim (e.g. "it failed for some large numbers")
    bad_claim = {"parameter_regime": "unspecified", "notes": "slow"}
    ok_bad, missing = validate_failure_claim(bad_claim)
    assert not ok_bad
    assert "anchor_y" in missing

    # Parameterized claim
    good_claim = {
        "parameter_regime": "y=7, t in [10^6, 10^7]",
        "anchor_y": 7,
        "t_range": [1000000, 10000000],
        "root_cause": "Lucas sequence computation exceeded wall-clock budget",
    }
    ok_good, _ = validate_failure_claim(good_claim)
    assert ok_good is True


@pytest.mark.phase11_tier2
def test_bnd23_contradiction_with_discovery_intervals() -> None:
    """Verifies that an interval documented as non-viable does not contradict an interval with a discovery."""
    discovery_intervals = [
        {"anchor_y": 3, "multiplier_t": 21, "outcome": "DISCOVERY_CONFIRMED"}
    ]

    def check_for_contradiction(negative_log_entry: dict, discoveries: list[dict]) -> bool:
        for d in discoveries:
            if d["anchor_y"] == negative_log_entry.get("anchor_y"):
                t_range = negative_log_entry.get("t_range", [0, 0])
                if t_range[0] <= d["multiplier_t"] <= t_range[1]:
                    if negative_log_entry.get("claimed_yield") == 0:
                        return True  # Contradiction!
        return False

    # Contradictory entry claiming t in [1, 50] had zero yield when t=21 was a discovery
    contradictory_entry = {
        "anchor_y": 3,
        "t_range": [1, 50],
        "claimed_yield": 0,
    }
    assert check_for_contradiction(contradictory_entry, discovery_intervals) is True

    # Non-contradictory entry in another range
    clean_entry = {
        "anchor_y": 3,
        "t_range": [100, 200],
        "claimed_yield": 0,
    }
    assert check_for_contradiction(clean_entry, discovery_intervals) is False


@pytest.mark.phase11_tier2
def test_bnd23_tabular_schema_consistency() -> None:
    """Verifies that markdown table rows have columns matching all required headers."""
    sample_table = """
| Parameter Regime | Search Depth | Observed Bottleneck | Resolution / Lesson |
| :--- | :--- | :--- | :--- |
| y=5, t in [1000, 2000] | 10000 | Memory pressure | Segment intervals |
| y=7, t in [5000, 6000] | 50000 | Slow proving | Prune with Fermat base-2 |
"""
    lines = [line.strip() for line in sample_table.strip().splitlines() if line.strip()]
    header_line = lines[0]
    headers = [col.strip() for col in header_line.split("|")[1:-1]]

    for req in REQUIRED_TABLE_COLUMNS:
        assert req in headers, f"Missing required table column: {req}"

    for row_line in lines[2:]:
        cols = [col.strip() for col in row_line.split("|")[1:-1]]
        assert len(cols) == len(headers), f"Row column count {len(cols)} != header count {len(headers)}"


@pytest.mark.phase11_tier2
def test_bnd23_failure_category_separation() -> None:
    """Verifies that entries strictly differentiate between algorithmic and hardware failure categories."""
    VALID_CATEGORIES = {"ALGORITHMIC_DENSITY", "ALGORITHMIC_FACTORING", "HARDWARE_THERMAL", "HARDWARE_OOM"}

    def validate_category(entry_category: str) -> bool:
        return entry_category in VALID_CATEGORIES

    assert validate_category("ALGORITHMIC_DENSITY") is True
    assert validate_category("HARDWARE_THERMAL") is True
    assert validate_category("RANDOM_CRASH") is False
    assert validate_category("UNKNOWN") is False
