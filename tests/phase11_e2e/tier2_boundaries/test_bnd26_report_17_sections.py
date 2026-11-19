"""Tier 2 Boundary Tests - Feature 26: 17-Section Final Research Report.

Verifies:
1. Missing section header detection (all 17 required sections).
2. Unexpanded placeholder text (TODO, TBD, [REPLACE]) rejection.
3. Cross-document data discrepancy detection with certificate JSON.
4. Broken markdown link and anchor reference detection.
5. Markdown table column syntax and alignment formatting.
"""

import re
import pytest
from pathlib import Path


REQUIRED_17_SECTION_HEADERS = [
    "1. Executive Summary",
    "2. Mathematical Formulation & Algebraic Manifold",
    "3. Candidate Method Analysis & Scoring",
    "4. Prior Art & Method Positioning",
    "5. Prototype Architecture & SymPy Oracle",
    "6. Arbitrary-Precision Engine & PTX Sieve",
    "7. CRT Inverse Pre-Filtering",
    "8. Checkpoint, Crash Recovery & Hardware Thermal Guards",
    "9. Multi-Tier Primality Screening Pipeline",
    "10. Deterministic Dual-BLS Certification System",
    "11. Morrison Lucas Singularity Guard Analysis",
    "12. Independent Standalone Verification",
    "13. Twin Prime Discovery Data & Provenance",
    "14. Dual Novelty Verification & Inventory Gating",
    "15. 13-Metric Comprehensive Performance Benchmarks",
    "16. Negative Results, Regimes & Lessons Learned",
    "17. Reproducibility Guide & Verification Package",
]


@pytest.mark.phase11_tier2
def test_bnd26_missing_section_header_detection() -> None:
    """Verifies that the report validator flags any missing section among the 17 required headers."""
    def audit_report_sections(markdown_text: str) -> tuple[bool, list[str]]:
        missing = []
        for header in REQUIRED_17_SECTION_HEADERS:
            # Check for header with ## prefix or plain title
            pattern = re.compile(rf"##\s+{re.escape(header)}", re.IGNORECASE)
            if not pattern.search(markdown_text):
                missing.append(header)
        return len(missing) == 0, missing

    # Incomplete report missing section 17
    incomplete_report = "\n".join([f"## {h}" for h in REQUIRED_17_SECTION_HEADERS[:-1]])
    ok, missing = audit_report_sections(incomplete_report)
    assert not ok
    assert missing == [REQUIRED_17_SECTION_HEADERS[-1]]

    # Complete report
    complete_report = "\n".join([f"## {h}\nContent of section." for h in REQUIRED_17_SECTION_HEADERS])
    ok_full, missing_full = audit_report_sections(complete_report)
    assert ok_full is True
    assert len(missing_full) == 0


@pytest.mark.phase11_tier2
def test_bnd26_unexpanded_placeholder_detection() -> None:
    """Verifies that placeholder strings such as TODO, TBD, [INSERT HERE] are flagged."""
    placeholder_pattern = re.compile(r"\b(TODO|TBD|FIXME|\[INSERT\s+[^\]]+\]|\[REPLACE\s+[^\]]+\])\b", re.IGNORECASE)

    sample_draft = """## 1. Executive Summary
This document outlines results.
TODO: Add final digit count.
Status: TBD.
"""
    matches = placeholder_pattern.findall(sample_draft)
    assert len(matches) == 2
    assert "TODO" in matches
    assert "TBD" in matches

    clean_text = "Executive summary is fully fleshed out with verified metrics."
    assert len(placeholder_pattern.findall(clean_text)) == 0


@pytest.mark.phase11_tier2
def test_bnd26_data_discrepancy_check() -> None:
    """Verifies that numeric claims in the report match certificate JSON values."""
    cert_data = {
        "lower_prime": "381107634767",
        "upper_prime": "381107634769",
        "digit_count": 12,
        "difference": 2,
    }

    def verify_report_consistency(report_text: str, cert: dict) -> list[str]:
        discrepancies = []
        # Check digit count
        if f"{cert['digit_count']} digits" not in report_text and f"{cert['digit_count']}-digit" not in report_text:
            discrepancies.append("Digit count mismatch")
        # Check difference
        if "gap of 2" not in report_text and "difference of 2" not in report_text:
            discrepancies.append("Twin gap mismatch")
        return discrepancies

    report_matching = "Discovered 12-digit twin prime pair with a verified difference of 2."
    report_bad = "Discovered 50-digit twin prime pair with a gap of 4."

    assert len(verify_report_consistency(report_matching, cert_data)) == 0
    assert len(verify_report_consistency(report_bad, cert_data)) == 2


@pytest.mark.phase11_tier2
def test_bnd26_broken_markdown_links() -> None:
    """Verifies that internal anchor links [text](#anchor) resolve to valid headers in the document."""
    sample_doc = """
# Phase 11 Final Report
[Jump to Math](#2-mathematical-formulation--algebraic-manifold)
[Jump to Broken](#broken-link-target)

## 2. Mathematical Formulation & Algebraic Manifold
Details here.
"""
    link_pattern = re.compile(r"\[([^\]]+)\]\(#([^\)]+)\)")
    header_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)

    raw_headers = header_pattern.findall(sample_doc)
    # Generate anchor slugs (lowercase, strip non-alphanumeric except hyphen, spaces to hyphens)
    anchors = set()
    for h in raw_headers:
        slug = re.sub(r"[^\w\s\-]", "", h.lower()).replace(" ", "-")
        anchors.add(slug)

    broken_links = []
    for text, link in link_pattern.findall(sample_doc):
        if link not in anchors:
            broken_links.append(link)

    assert "broken-link-target" in broken_links
    assert len(broken_links) == 1


@pytest.mark.phase11_tier2
def test_bnd26_table_syntax_formatting() -> None:
    """Verifies that markdown tables have consistent column counts across all rows."""
    def validate_markdown_table_formatting(table_markdown: str) -> tuple[bool, str]:
        lines = [line.strip() for line in table_markdown.strip().splitlines() if line.strip().startswith("|")]
        if len(lines) < 2:
            return False, "Table must have at least header and separator rows"

        col_count = len(lines[0].split("|"))
        for i, line in enumerate(lines[1:], start=2):
            if len(line.split("|")) != col_count:
                return False, f"Row {i} column count mismatch: {len(line.split('|'))} != {col_count}"
        return True, "OK"

    good_table = """
| Col 1 | Col 2 | Col 3 |
| :--- | :--- | :--- |
| A | B | C |
| D | E | F |
"""
    bad_table = """
| Col 1 | Col 2 | Col 3 |
| :--- | :--- | :--- |
| A | B |
"""

    ok_good, _ = validate_markdown_table_formatting(good_table)
    assert ok_good is True

    ok_bad, err_bad = validate_markdown_table_formatting(bad_table)
    assert not ok_bad
    assert "column count mismatch" in err_bad
