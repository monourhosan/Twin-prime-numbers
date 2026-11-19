# Phase 11 Reproducibility Instructions: OPQM-CRT Hybrid Manifold

## Overview
This document provides exact, zero-ambiguity step-by-step instructions to reproduce all Phase 11 mathematical verifications, independent certificate validations, regression test passes, search campaign executions, checkpoint resumptions, and empirical benchmark suites.

---

### 1. Environment & Prerequisites

#### 1.1 Hardware Specifications
- **Host CPU:** x86_64 processor supporting AVX2 and BMI2 (e.g., Intel Core i5-10210U @ 1.60GHz or higher).
- **Host Memory:** $\ge 8$ GB physical RAM ($\ge 2.5$ GB available).
- **Dedicated GPU (Optional):** NVIDIA GPU supporting Compute Capability 6.1+ (sm_61 or higher, e.g. GeForce MX250) with driver $\ge 582.78$. Sieve routines automatically fall back to CPU AVX2 if no CUDA GPU is detected.
- **Operating System:** Windows 10/11 (PowerShell / Command Prompt) or Linux (Bash).

#### 1.2 Software Toolchain & Dependencies
- **Python:** 3.12 (AMD64)
- **Rustc / Cargo:** 1.99.1+ (for auxiliary systems crates)
- **Core Python Packages:** `gmpy2 >= 2.3.2`, `sympy >= 1.14.0`, `numpy >= 2.5.4`, `pytest >= 9.2.0`, `psutil >= 7.0.0`

#### 1.3 Installation Commands

##### Windows (PowerShell)
```powershell
# Ensure working directory is repository root
cd "d:\project\Twin prime numbers"
python -m pip install -r requirements.txt
python -c "import gmpy2, sympy, numpy, pytest, psutil; print('All dependencies successfully imported!')"
```

##### Linux / macOS (Bash)
```bash
# Ensure working directory is repository root
cd /path/to/repository
python3 -m pip install -r requirements.txt
python3 -c "import gmpy2, sympy, numpy, pytest, psutil; print('All dependencies successfully imported!')"
```

---

### 2. One-Command Master Verification (Regression Suite)

Execute the complete repository test suite:

```bash
python -m pytest tests -q
```

**Expected Outcome:**
```text
646 passed in 31.63s
```
*Verification Invariant:* Exactly 646 passed, 0 failed, 0 errors across all 239 baseline historical tests, 334 Phase 11 E2E tests, and 73 Phase 11 unit/property tests.

To run only the Phase 11 test suite:
```bash
python -m pytest tests/phase11 tests/phase11_e2e -v
```

---

### 3. Independent First-Principles Verification of Discovered Pairs

Verify the authentic discovery certificates using the standalone, zero-dependency independent verifier (`scripts/phase11/phase11_independent_verify.py`):

#### 3.1 13-Digit Twin-Prime Pair ($x = 174$, $y = 3, t = 29$)

```bash
python scripts/phase11/phase11_independent_verify.py proofs/phase11/certificates/cert_opqm11_13d_t29.json
```

**Expected Console Output:**
```text
Auditing Phase 11 certificate: proofs/phase11/certificates/cert_opqm11_13d_t29.json...
  + Canonical Payload SHA-256 verified: a6dfe07bc54e0d81a5b3bccfbe66510fe77ed63b63d34a8d616b63c615b780df
  + Twin gap verified: B - A = 2
  + Exact decimal digits: 13
  + Parity & mod 6 congruence verified: C = 0 mod 6
  + Divisor-cofactor coprimality verified: gcd(F, R) = 1
  + Pocklington size condition verified: F^2 > B
  + Pocklington BLS Theorem 4 primality unconditionally verified for upper member B
  + Morrison size condition verified: (F_odd - 1)^2 > A
  + Jacobi non-residue symbol verified: (21 / A) = -1
  + Full-period Lucas zero congruence verified: U_{A+1}(5, 1) = 0 mod A
  + Morrison Odd Divisor Singularity Guard verified: factor 2 excluded, all odd factor GCDs == 1
  + Morrison BLS Theorem 17 primality unconditionally verified for lower member A
  Verdict: UNCONDITIONALLY_VERIFIED (BLS Theorems 4 & 17)
  [PASS] cert_opqm11_13d_t29.json unconditionally verified!
```
**Expected Exit Code:** 0

#### 3.2 21-Digit Twin-Prime Pair ($x = 6450$, $y = 5, t = 215$)

```bash
python scripts/phase11/phase11_independent_verify.py proofs/phase11/certificates/cert_opqm11_21d_t215.json
```

**Expected Console Output:**
```text
Auditing Phase 11 certificate: proofs/phase11/certificates/cert_opqm11_21d_t215.json...
  + Canonical Payload SHA-256 verified: 88e2252187b01694b3c885e6e8b521a940ec1ed71249b2d0779ef19ad91b155a
  + Twin gap verified: B - A = 2
  + Exact decimal digits: 21
  + Parity & mod 6 congruence verified: C = 0 mod 6
  + Divisor-cofactor coprimality verified: gcd(F, R) = 1
  + Pocklington size condition verified: F^2 > B
  + Pocklington BLS Theorem 4 primality unconditionally verified for upper member B
  + Morrison size condition verified: (F_odd - 1)^2 > A
  + Jacobi non-residue symbol verified: (77 / A) = -1
  + Full-period Lucas zero congruence verified: U_{A+1}(9, 1) = 0 mod A
  + Morrison Odd Divisor Singularity Guard verified: factor 2 excluded, all odd factor GCDs == 1
  + Morrison BLS Theorem 17 primality unconditionally verified for lower member A
  Verdict: UNCONDITIONALLY_VERIFIED (BLS Theorems 4 & 17)
  [PASS] cert_opqm11_21d_t215.json unconditionally verified!
```
**Expected Exit Code:** 0

---

### 4. Automated Novelty Verification Against Historical Inventory

Execute the novelty verification test suite:

```bash
python -m pytest tests/phase11/test_novelty.py -v
```

**Expected Outcome:**
- Confirms `research/phase11/historical_inventory.json` contains exactly 62 historical discovery records with SHA-256 `5e52545f2093b176b78d802323ede8df3968306a8bb7f68b97b2e232f09c0d87`.
- Confirms all 62 historical pairs are flagged `ALREADY_IN_REPOSITORY`.
- Confirms both the 13-digit and 21-digit discoveries are flagged `NOVEL_TO_REPOSITORY` in both `(A, B)` and `(B, A)` orderings.

---

### 5. Checkpoint Resumption & Search Campaign Reproduction

The staged search campaign framework (`src/phase11/campaign.py` and `scripts/phase11/run_campaign.py`) supports bounded work units, atomic JSON checkpointing, crash recovery, and hardware thermal guards:

#### 5.1 Stage 1 Sanity Run ($y = 3, t \in [1, 50]$)
```bash
python scripts/phase11/run_campaign.py --stage sanity
```
- Evaluates 50 candidates; identifies 8 sieve survivors.
- Saves atomic JSON checkpoint at `runs/phase11/stage1_sanity_checkpoint.json`.

#### 5.2 Stage 4 Discovery Run ($y = 3, t \in [25, 35]$)
```bash
python scripts/phase11/run_campaign.py --stage discovery --anchor-y 3 --t-start 25 --t-end 35 --prime-limit 1000
```
- Discovers 13-digit twin-prime pair at $t = 29$:
  - Lower: `1913967943631`
  - Upper: `1913967943633`
- Saves checkpoint at `runs/phase11/stage4_discovery_y3_t25_35_checkpoint.json`.

#### 5.3 Stage 4 Discovery Run ($y = 5, t \in [210, 220]$)
```bash
python scripts/phase11/run_campaign.py --stage discovery --anchor-y 5 --t-start 210 --t-end 220 --prime-limit 1000
```
- Discovers 21-digit twin-prime pair at $t = 215$:
  - Lower: `133961445293766749999`
  - Upper: `133961445293766750001`
- Saves checkpoint at `runs/phase11/stage4_discovery_y5_t210_220_checkpoint.json`.

#### 5.4 Checkpoint Resumption Verification
To verify seamless crash recovery without duplicating work units:
```bash
python scripts/phase11/run_campaign.py --stage discovery --anchor-y 3 --t-start 25 --t-end 35 --resume
```
- Loads `stage4_discovery_y3_t25_35_checkpoint.json`, reports `current_t: 35`, and exits cleanly without duplicating computations.

---

### 6. Standardized 13-Metric Benchmark Suite Reproduction

Run the empirical benchmark harness to measure and export all 13 metrics:

```bash
python scripts/phase11/benchmark.py --quick
```

Or run the comprehensive benchmark:
```bash
python scripts/phase11/benchmark.py
```

**Expected Artifacts Generated:**
- Machine-readable JSON: `data/phase11/benchmarks.json`
- Standardized CSV: `research/phase11/benchmarks_raw.csv`
- Comparative Markdown table: `research/phase11/BENCHMARKS.md`

All 13 metrics are validated strictly positive (> 0) and host RAM consumption is verified $\le 4,096$ MB.
