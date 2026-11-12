# Phase 3 Reproducibility and Verification Manual

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Target Environment:** Windows 11 / Linux / macOS (Python 3.10+)  

---

## 1. System Requirements and Dependencies

```bash
python -m pip install numpy sympy matplotlib pytest
```
All Phase 3 tools execute under standard Python 3.10+ with pure Python and NumPy acceleration. No unpermitted native compilers or elevated privileges are required.

---

## 2. Step-by-Step Reproduction and Audit

### Step 1: Run the Phase 3 Baseline Audit
Validates all historical certificates and confirms mathematical integrity:
```bash
python -m src.phase3 audit --repo .
```

### Step 2: Execute the Automated Test Suite (29/29 Passing)
Run all 29 unit, property, and regression tests across Phase 1, Phase 2, and Phase 3:
```bash
python -m pytest -v tests/
```
Expected output: `29 passed in < 1.5s`.

### Step 3: Run Empirical Sieve Benchmarks
Benchmark S0 (baseline), S1 (vectorized segmented bitset), and S2 (hybrid):
```bash
python scripts/phase3_benchmark.py
```
Outputs are written to `runs/phase3/benchmarks/benchmark_comparison.json`.

### Step 4: Independent Strict Verification of Phase 3 Certificates
Verify all newly discovered 207-, 314-, and 507-digit certificates using the decoupled $2 \times 2$ matrix-powering auditor:
```bash
python scripts/phase3_independent_verify.py proofs/phase3/
```
Expected output:
```text
Independent Strict Verification of 3 certificates in proofs\phase3...
  [PASS] cert_k1183377_n1664.json
  [PASS] cert_k15993_n672.json
  [PASS] cert_k254697_n1024.json

[SUCCESS] All certificates passed independent strict verification!
```

You can also audit individual certificates:
```bash
python scripts/phase3_independent_verify.py proofs/phase3/cert_k254697_n1024.json
python scripts/phase3_independent_verify.py proofs/phase3/cert_k1183377_n1664.json
```

### Step 5: Check Cryptographic SHA-256 Manifest
```bash
Get-FileHash proofs/phase3/*.json -Algorithm SHA256
```
Compare against `proofs/phase3/sha256sums.txt`.

---

## 3. Launching or Resuming Search Campaigns

To run or resume progressive campaigns:

```bash
# Target >= 300 digits (n=1024)
python -m src.phase3 search --config configs/phase3/target_300.json --resume

# Stretch >= 500 digits (n=1664)
python -m src.phase3 search --config configs/phase3/stretch_500.json --resume

# Check active progress and live heartbeat
python -m src.phase3 status --campaign target_300

# Gracefully pause a running campaign
python -m src.phase3 pause --campaign target_300
```
All state is maintained in SQLite with Write-Ahead Logging in `runs/phase3/`.
