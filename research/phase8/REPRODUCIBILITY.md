# Phase 8 ADES-8 Reproducibility Guide

**Date:** 2026-11-14  
**Author:** Google Antigravity (Reproducibility & Verification Engineering)  
**Branch:** `research/phase8-adaptive-record`

---

## 1. Verified Software Environment

- **Operating System:** Windows 11 (AMD64 build 10.0.26300)
- **Python Version:** 3.12.10 (AMD64)
- **Required Libraries:**
  - `gmpy2 == 2.3.2` (multiprecision integer arithmetic & modular exponentiation)
  - `sympy == 1.14.0` (number-theoretic reference routines)
  - `pytest == 9.2.0` (automated testing framework)

To verify the Python environment from a fresh checkout:
```bash
python -c "import gmpy2, sympy, pytest; print('All required dependencies available!')"
```

---

## 2. Step-by-Step Reproduction Instructions

### Step 1: Run Full Regression Test Suite
Executes all 190 tests across Phases 1 through 8:
```bash
python -m pytest
```
*Expected Result:* `190 passed in ~12s` with zero failures.

### Step 2: Run Micro- and Macro-Benchmarks
Executes kernel comparison (Variant A vs B vs C), primorial parameter sweeps, scaling tests, and pipeline stage profiling:
```bash
python scripts/phase8_benchmarks.py
```
*Expected Result:*
- Variant C achieves $>1.5 \times 10^6$ candidates/sec ($>2.3\times$ speedup over Variant B).
- Raw CSV exported to `research/phase8/benchmarks_raw.csv`.

### Step 3: Run the Theoretical Search Planner
Displays exact integer bounds and Poisson yield models for $D = 1,511$ digits:
```bash
python -m src.phase8.cli plan --digit-band 1511 --R 13 --n-start 4985 --n-height 3
```

### Step 4: Execute the Discovery Campaign
Runs the deterministic 2D search campaign that discovered the record pair:
```bash
python -m src.phase8.cli search --config configs/phase8/search_1511d_dense2.json
```
*Expected Result:*
- Reaches hit at `tile_n4985_4987_t79313_89312` ($t = 79,783, n = 4,987$).
- Outputs `Campaign Result: SUCCESS_RECORD_PROVEN`.
- Writes certificate to `proofs/phase8/certificates/cert_ades8_1511d_R13_n4987_t79783.json`.

### Step 5: Execute Standalone Independent Verification
Verifies the certificate from scratch with zero internal repository imports:
```bash
python scripts/phase8_independent_verify.py proofs/phase8/certificates/cert_ades8_1511d_R13_n4987_t79783.json
```
*Expected Result:*
- Unconditional verification pass for both Proth ($w=19$) and LLR ($P=15, 4985$ squarings).
- Generates signed attestation in `proofs/phase8/attestations/attest_f29217cfe9267dd9.json`.

---

## 3. Cryptographic Artifact Checksums (SHA-256)

| Artifact File Path | SHA-256 Checksum |
|:---|:---|
| `proofs/phase8/certificates/cert_ades8_1511d_R13_n4987_t79783.json` | `f29217cfe9267dd9334534e76e5bc4b023918409eec95b1a8ebdd7ddfe855263` (canonical payload) |
| `proofs/phase8/attestations/attest_f29217cfe9267dd9.json` | Signed verification receipt |
| `configs/phase8/search_1511d_dense2.json` | Exact search campaign configuration |
| `scripts/phase8_independent_verify.py` | Decoupled independent verifier |
