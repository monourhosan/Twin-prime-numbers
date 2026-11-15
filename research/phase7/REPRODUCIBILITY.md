# Phase 7 Reproducibility Guide

**Date:** 2026-11-14  
**Author:** Google Antigravity (Computational Number Theory & Proof Audit Mission)  
**Branch:** `research/phase7-high-density`  

---

## 1. Environment & Prerequisites

- **Python:** Version $\ge 3.10$ (benchmarked on Python 3.12.10 64-bit AMD64).
- **Python Libraries:**
  - `gmpy2` ($\ge 2.1.0$, recommended for fast multiprecision arithmetic)
  - `pytest` ($\ge 8.0$, for test suite execution)
- **Host Hardware:** Minimum 4 GB RAM, x86_64 CPU (tested on Intel Core i5-10210U).
- **External Dependencies:** ZERO external binaries required for the HDC-7 special-form discovery and standalone independent verification.

---

## 2. Independent Verification of the 1,510-Digit Twin Prime

To verify the discovery from first principles without importing any search modules or using external packages:

```powershell
python scripts/phase7_independent_verify.py proofs/phase7/certificates/cert_hdc7_1510d_B13_n4985_t15658.json --attest-dir proofs/phase7/attestations
```

### Expected Output:
```
Auditing Phase 7 certificate: cert_hdc7_1510d_B13_n4985_t15658.json...
  + Canonical Proof Payload SHA-256 verified: 9e147e81b6d0879cd87edcb7cc577ba1e220519154901ed240de4319bb2ccc1e
  + Exact decimal digits: 1510
  + Center C mod 6: 0
  + Difference B - A: 2
  + Proth primality verified for upper member B' (witness w=23)
  + Riesel Jacobi conditions confirmed for lower member: (15-2/A)=1, (15+2/A)=-1
  + Initial u0 confirmed via independent 2x2 companion matrix powering
  + LLR recurrence sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
  + Attestation written to: attest_9e147e81b6d0879c.json
  [PASS] cert_hdc7_1510d_B13_n4985_t15658.json unconditionally verified!
```

---

## 3. Running Regression and Reliability Tests

Run the complete Phase 7 test suite (P0 repairs + HDC-7 engine tests):

```powershell
python -m pytest tests/phase7/ -v
```

Expected result: **16 passed in ~0.35s** (10 P0 regression tests + 6 HDC-7 unit tests).

Run the full repository test suite across all historical phases:

```powershell
python -m pytest
```

Expected result: **175 passed in ~13s** (100% PASS rate across Phases 2 through 7).

---

## 4. Re-running Empirical Benchmarks

To execute the multi-scale, multi-family benchmark suite comparing $B \in [3, 13, 31, 47]$:

```powershell
python scripts/phase7_benchmarks.py
```

Outputs will be generated at `research/phase7/benchmarks_raw.csv` and `research/phase7/BENCHMARKS.md`.

---

## 5. Resuming or Extending Search Campaigns

The primary campaign checkpoint is preserved at `data/phase7/hdc7_primary_1510d_checkpoint.json`.
To resume search across the remaining $61,594$ unsearched centers in this window starting from cursor $t = 15,659$:

```powershell
python -m src.phase7.cli search --config configs/phase7/production_1510d.json --max-centers 10000
```
