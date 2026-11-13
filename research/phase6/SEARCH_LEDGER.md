# Phase 6 Search Ledger and Campaign Coverage Manifest

**Document ID:** `PHASE6-LEDGER-001`  
**Date:** 2026-11-14T05:20:00+06:00  
**Phase:** Phase 6 (GITCSS)  
**Ledger Storage:** `data/phase6_candidates.jsonl` (17,682 entries)  
**Manifest Storage:** `data/phase6_coverage_manifest.json`

---

## 1. Campaign Execution Registry

| Campaign ID | Run ID | Target Interval $[p_{\min}, p_{\max}]$ | Mapped Center Interval $[m_{\min}, m_{\max}]$ | Centers Searched | Survivors | Dual PRPs | Certified Discoveries | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`smoke_test`** | `run_smoke_test_1794611462` | $[10^3, 10^4]$ | $[167, 1666]$ | 1,500 | 48 | 1 | 1 pair (4d) | `DISCOVERY_CERTIFIED` |
| **`pilot_general_discovery`** | `run_pilot_general_discovery_1794611484` | $[10^{15}, 10^{15} + 10^6]$ | $[1.666\times 10^{14}, 1.666\times 10^{14} + 1.66\times 10^5]$ | 166,667 | 5,340 | 1 | 1 pair (16d) | `DISCOVERY_CERTIFIED` |
| **`general_100d_campaign`** | `run_general_100d_campaign_1794611892` | $[10^{99}, 10^{99} + 3.14\times 10^6]$ | $[m_0, m_0 + 524,288)$ | 524,288 | 11,004 | 58 | 0 (factor limit) | `NO_NEW_PAIR_FOUND_IN_TESTED_RANGE` |
| **`pilot_350d_campaign`** | `run_pilot_350d_campaign_1794613686` | $[10^{349} + 1, 10^{349} + 6\times 10^5]$ | $[m_0, m_0 + 100,000)$ | 100,000 | 1,926 | 1 | 0 (factor limit) | `NO_NEW_PAIR_FOUND_IN_TESTED_RANGE` |
| **`unrestricted_350d_campaign`** | `run_unrestricted_350d_campaign_1794613703` | $[10^{349} + 1, 10^{349} + 6\times 10^6]$ | $[m_0, m_0 + 1,000,000)$ | 1,000,000 | 18,913 | 8 | 0 (factor limit) | `NO_NEW_PAIR_FOUND_IN_TESTED_RANGE` |

---

## 2. Detailed 350-Digit Segment Manifest (1,000,000 Centers)

The 350-digit campaign executed across four contiguous segments covering exactly 1,000,000 eligible centers starting at:
$$m_0 = \frac{10^{349} + 2}{6} = 16666\ldots6667 \text{ (349 digits)}$$

- **Segment 0:** $[m_0, m_0 + 262,144)$ — 5,038 survivors, 2 Dual PRPs, 8.72s
- **Segment 1:** $[m_0 + 262,144, m_0 + 524,288)$ — 4,958 survivors, 1 Dual PRP, 9.00s
- **Segment 2:** $[m_0 + 524,288, m_0 + 786,432)$ — 4,954 survivors, 3 Dual PRPs, 9.69s
- **Segment 3:** $[m_0 + 786,432, m_0 + 1,000,000)$ — 3,963 survivors, 2 Dual PRPs, 10.38s

### Contiguity Verification:
Executed: `python -m src.phase6.cli coverage`
Result: **PASS**. All segments are strictly contiguous with zero gaps and zero overlaps. Total centers: **1,000,000**.

---

## 3. Detailed 100-Digit Segment Manifest

The 100-digit general integer campaign executed over two contiguous segments of $S = 262,144$ elements starting at:
$$m_0 = \left\lceil \frac{10^{99} + 1}{6} \right\rceil = 166666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666667$$

### Segment 0:
- **Interval:** $[m_0, m_0 + 262,144) = [m_0, m_0 + 262,144)$
- **Actual $m$ Bounds:**
  - $m_{\text{start}} = 166666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666667$
  - $m_{\text{end}} = 166666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666928811$
- **Survivors from Sieve ($L=50,000$):** 5,531 (2.11%)
- **Dual PRP Hits:** 30 candidates passed 25-round Miller-Rabin
- **Proof Status:** Unproven due to 100-digit factor trial division limit
- **Elapsed Wall Time:** 19.70 seconds

### Segment 1:
- **Interval:** $[m_{\text{end\_0}}, m_{\text{end\_0}} + 262,144)$
- **Actual $m$ Bounds:**
  - $m_{\text{start}} = 166666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666928811$
  - $m_{\text{end}} = 166666666666666666666666666666666666666666666666666666666666666666666666666666666666666666667190955$
- **Survivors from Sieve ($L=50,000$):** 5,473 (2.09%)
- **Dual PRP Hits:** 28 candidates passed 25-round Miller-Rabin
- **Proof Status:** Unproven due to 100-digit factor trial division limit
- **Elapsed Wall Time:** 19.70 seconds

### Contiguity Verification:
Executed: `python -m src.phase6.cli coverage-audit`
Result: **PASS**. $m_{\text{end}}$ of Segment 0 equals $m_{\text{start}}$ of Segment 1. Zero gaps, zero overlaps.

---

## 3. Candidate Screening History in `data/phase6_candidates.jsonl`

- Total entries logged: **17,682 candidates**
- Total Dual PRP candidates identified: **102 candidate pairs**
- Breakdown of Dual PRPs:
  - 4-digit candidates: 1 (proven)
  - 16-digit candidates: 1 (proven)
  - 100-digit candidates: 58 (screened across segments 0 and 1, honest unproven status recorded)
  - Interrupted run exploratory entries: 42
