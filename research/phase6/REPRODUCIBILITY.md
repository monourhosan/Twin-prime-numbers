# Phase 6 Reproducibility Guide: General-Integer Twin-Center Segmented Sieve (GITCSS)

**Document ID:** `PHASE6-REPRODUCIBILITY-001`  
**Date:** 2026-11-14T05:22:00+06:00  
**Phase:** Phase 6

---

## 1. Prerequisites and Environment Setup

- **Python Runtime:** Python 3.12 (standard 64-bit distribution)
- **Required Libraries:**
  ```bash
  pip install gmpy2 sympy pytest
  ```
- **Working Directory:** Local repository root `Twin-prime-numbers`.

---

## 2. Step-by-Step Reproduction Commands

### Step 1: Run the Full Test Suite
Verify that all 115 tests across Phases 1 through 6 pass without regressions:
```bash
python -m pytest
```

### Step 2: Run the Baseline and Historical Inventory Audit
Audits system environment and verifies the 48 historical certificates in `research/phase5_audit/historical_inventory.json`:
```bash
python -m src.phase6.cli audit
```

### Step 3: Run the Controlled Sieve and Screening Benchmarks
Generates `data/phase6_benchmarks.csv`, `runs/phase6/benchmarks/benchmark_results.json`, and `research/phase6/BENCHMARKS.md`:
```bash
python -m scripts.phase6_benchmarks
```

### Step 4: Run the Smoke Campaign
Validates end-to-end small-range sieving, screening, certification, and attestation:
```bash
python -m src.phase6.cli discover --config configs/phase6/smoke.json
```

### Step 5: Reproduce the General-Integer Twin-Prime Discovery
Executes the general-integer search in the $[10^{15}, 10^{15} + 10^6]$ interval, discovering and independently proving the 16-digit pair `(1000000000002371, 1000000000002373)`:
```bash
python -m src.phase6.cli discover --config configs/phase6/pilot_discovery.json
```

### Step 6: Run the 100-Digit Bounded Search Campaign
Sieves 524,288 general-integer centers (> 3.1 million integers) at 100 decimal digits:
```bash
python -m src.phase6.cli discover --config configs/phase6/general_100d.json --max-segments 2
```

### Step 7: Audit Search Interval Coverage for Gaps
Verifies that all completed segments in `data/phase6_coverage_manifest.json` are strictly contiguous with zero gaps or overlaps:
```bash
python -m src.phase6.cli coverage-audit
```

### Step 8: Run Independent First-Principles Verification on All Certificates
Validates all certificates in `proofs/phase6/certificates/` and generates machine-readable attestation artifacts:
```bash
python -m src.phase6.cli verify proofs/phase6/certificates/
```
