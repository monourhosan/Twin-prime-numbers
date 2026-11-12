# Phase 2 Reproducibility and Audit Guide

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Target Environment:** Windows / Linux / macOS (Python 3.10+)  

---

## 1. System Environment and Dependencies

All experiments and discoveries reported in Phase 2 were computed and audited on:
- **Operating System:** Windows 11 Home x86_64
- **Python Version:** Python 3.12.10
- **Primary Dependencies:** `numpy`, `sympy`, `pytest`, `matplotlib`
- **Git Commit:** `62a8588` (on branch `research/new-twin-prime-search-v2`)

To install required dependencies:
```bash
pip install numpy sympy pytest matplotlib
```

---

## 2. Step-by-Step Verification and Audit

### Step 1: Run the Baseline Audit and Discrepancy Check
Verify the frozen baseline inventory (35 certificates, SHA-256 `b27e24a1ab320b9882e720e95a1336c1d768fa4c792383dfb245e383e2dcf554`) and confirm that the historical transcription error in `README.md` is resolved:
```bash
python -m src.phase2 audit --repo . --write-report research/phase2/BASELINE_AUDIT.md
```

### Step 2: Run the Automated Test Suite
Execute all 19 unit, regression, and fault injection tests:
```bash
python -m pytest -v tests/
```
Expected output: `19 passed in < 1.0s`.

### Step 3: Run the Benchmarks and Ablations
Reproduce the Lucas sequence comparison, CRT wheel elimination percentages, and sieve depth trade-offs:
```bash
python scripts/phase2_benchmark.py
```
Outputs are written to `runs/phase2/benchmark_results.json` and `runs/phase2/benchmark_results.csv`.

### Step 4: Strict Independent Verification of Discovered Pairs
Verify all newly discovered pairs in `proofs/phase2/` without trusting the generator:
```bash
python scripts/phase2_verify.py proofs/phase2/
```
Expected output:
```text
Auditing 3 certificates in proofs\phase2...
  [PASS] cert_k12477_n330.json
  [PASS] cert_k126747_n384.json
  [PASS] cert_k61347_n512.json

[SUCCESS] All Phase 2 certificates passed strict independent audit!
```

You can also audit individual certificates:
```bash
python scripts/phase2_verify.py proofs/phase2/cert_k12477_n330.json
python scripts/phase2_verify.py proofs/phase2/cert_k126747_n384.json
python scripts/phase2_verify.py proofs/phase2/cert_k61347_n512.json
```

### Step 5: Check Cryptographic SHA-256 Manifest
Ensure certificate payload integrity:
```bash
Get-FileHash proofs/phase2/*.json -Algorithm SHA256
```
Compare against `proofs/phase2/sha256sums.txt`.

---

## 3. Resuming or Continuing the Search Campaign

To resume search for further pairs:
```bash
# Search for >= 100 digit pairs (n >= 330)
python -m src.phase2 search --min-digits 100 --checkpoint-dir runs/phase2 --resume

# Inspect current progress and status
python -m src.phase2 status --checkpoint-dir runs/phase2
```
All progress is saved atomically in `runs/phase2/checkpoint_state.json`. Safe to interrupt via `Ctrl+C` at any time.
