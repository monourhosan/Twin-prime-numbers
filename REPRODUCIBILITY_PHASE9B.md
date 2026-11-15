# Phase 9B Reproducibility Instructions

## Overview
This document provides exact, zero-ambiguity instructions to reproduce all Phase 9B audit verifications, campaign completions, stretch target searches, and Phase 10 mathematical validations.

---

### 1. Environment Setup

#### 1.1 Prerequisites
- Python 3.10, 3.11, or 3.12 (x86_64)
- (Optional for GPU acceleration): NVIDIA GPU supporting CUDA `sm_61` or higher with standard NVIDIA display driver (`nvcuda.dll` present on Windows or `libcuda.so` on Linux). If no GPU is detected, all CLI commands automatically fall back to the vectorized CPU sieve.

#### 1.2 Installation
```bash
git checkout research/phase9b-paccm-scaleup
pip install -r requirements.txt
```

---

### 2. Independent Verification of 364-Digit Discovery

To independently verify the 364-digit twin-prime discovery without importing any project modules:
```bash
python scripts/phase9_independent_verify.py proofs/phase9/certificates/cert_paccm9_364d_t1129.json
```
**Expected Output:**
```text
Auditing Phase 9 certificate: cert_paccm9_364d_t1129.json...
  + Canonical Proof Payload SHA-256 verified: 62d13fd6011ec338f9324a0c9532bc90be297eb505a0f5ef0eebef349625b190
  + Difference B - A: 2
  + Exact decimal digits: 364
  + Pocklington BLS Theorem 4 primality unconditionally verified for upper member B
  + Morrison BLS Theorem 17 primality unconditionally verified for lower member A
  [PASS] cert_paccm9_364d_t1129.json unconditionally verified!
```
**Expected Runtime:** ~0.42 seconds.

---

### 3. Automated Test Suite Execution (239 Tests)

Run the full pytest suite:
```bash
python -m pytest -v
```
**Expected Outcome:** `239 passed in ~25-30s`.

---

### 4. Completing the Primary Search Campaign ($t \in [1, 50000]$)

To resume from the saved checkpoint and search up to $t = 50000$:
```bash
python -m src.phase9.cli search --campaign-id phase9_primary_355d --anchor-y 283 --t-start 10003 --t-end 50000 --sieve-depth 50000 --batch-size 5000 --no-stop-on-first
```
**Expected Outcome:**
- Batches `[10003, 20003]`, `[20005, 30005]`, `[30007, 40007]`, `[40009, 49999]` executed.
- Total candidates sieved: 25,000.
- Checkpoint updated at `data/phase9/phase9_primary_355d_checkpoint.json` with `current_t: 50001`.

---

### 5. Reproducing the 1,512-Digit Stretch Target Searches

#### 5.1 Anchor $y = 1201$ Search ($t \in [1, 20000]$)
```bash
python -m src.phase9.cli search --campaign-id phase9_stretch_1512d_y1201 --anchor-y 1201 --t-start 1 --t-end 20000 --sieve-depth 50000 --batch-size 5000
```
- Sieve throughput: ~6.85 million cand/sec.
- 10,000 candidates evaluated (1,512 to 1,526 decimal digits).
- 4,247 survivors, 929 prime multipliers screened.
- 6 single-PRPs, 0 dual-PRPs.

#### 5.2 Anchor $y = 1193$ Search ($t \in [1, 10000]$)
```bash
python -m src.phase9.cli search --campaign-id phase9_stretch_1512d_y1193 --anchor-y 1193 --t-start 1 --t-end 10000 --sieve-depth 50000 --batch-size 5000
```
- 5,000 candidates evaluated.
- Note: Multiplier interval $t \in [1129, 2154]$ produces **exactly 1,512 decimal digits**.
- 2,158 survivors, 524 prime multipliers screened.
- 2 single-PRPs, 0 dual-PRPs.

---

### 6. Phase 10 Mathematical Validations

Execute unit tests verifying irreducibility, super-root dominance, coprimality, and dual-BLS proofs for all three Phase 10 candidate constructions:
```bash
python -m pytest tests/phase10/test_phase10_candidates.py -v
```
**Expected Outcome:** `3 passed in ~0.8s`.
