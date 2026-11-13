# Phase 5 Reproducibility Guide: Smooth-Center Certificate-Aware Search (SCCA)

This guide provides exact, tested commands to reproduce the Phase 5 baseline audit, controlled benchmarks, scientific discoveries, and first-principles independent verification.

---

## 1. System Requirements & Environment Setup

- **Operating System:** Windows 10/11, Linux, or macOS.
- **Python Version:** Python 3.10+ (tested on Python 3.12.10 AMD64).
- **Core Dependencies:**
  ```bash
  pip install gmpy2 sympy pytest
  ```
  *(Note: `gmpy2` provides accelerated GMP arithmetic; the engine will automatically fallback to pure Python if `gmpy2` is absent).*

---

## 2. Step-by-Step Reproduction Workflow

### Step 1: Run Full Repository Test Suite (Regression Guard)
Verify that all 80 unit and property tests across Phases 1–5 pass cleanly:
```bash
python -m pytest tests/ -v
```
*Expected Result:* 80 passed in < 10 seconds.

### Step 2: Run Baseline & Inventory Audit
Audit the local environment, CPU/GPU detection, and all 8 historical repository certificates:
```bash
python -m src.phase5 audit --repo .
```
*Expected Result:* Identifies 8 historical certificates, current repository record (1,509 digits), and confirms no regressions.

### Step 3: Run Controlled Algorithm Benchmark
Compare the Method S1 Segmented Filter against the CRT Wheel Walker, and benchmark proof timings:
```bash
python -m src.phase5 benchmark
```
*Expected Result:* Sieve rates > 1.5M cands/s (Segment) and > 7.0M cands/s (Wheel Walker); proof timings measured across digit bands.

### Step 4: Execute Fast Pilot Discovery (Smoke Test)
Run a bounded smoke campaign to discover and certify a small twin-prime pair:
```bash
python -m src.phase5 discover --config configs/phase5/smoke.json
```
*Expected Result:* Finds and proves twin pair `(453599, 453601)` in < 1 second.

### Step 5: Execute Scientific Discovery Campaign (59-Digit Band)
Search for and certify a multi-digit twin-prime pair:
```bash
python -m src.phase5 discover --config configs/phase5/scientific_55d.json
```
*Expected Result:* Discovers and certifies the 59-digit pair $A, B \approx 2.50 \times 10^{58}$ at $t = 877$.

### Step 6: Execute Intermediate Discovery Campaign (133-Digit Band)
Search for and certify a 133-digit twin-prime pair:
```bash
python -m src.phase5 discover --config configs/phase5/intermediate_133d.json
```
*Expected Result:* Discovers and certifies the 133-digit pair at $t = 9718$.

### Step 7: Inspect Search Ledger & Bandit Telemetry
Check work units, candidate progression, and UCB1 reward statistics:
```bash
python -m src.phase5 status
```

### Step 8: Standalone Independent Verification
Run the decoupled first-principles verifier (with ZERO imports from `src/`) on all generated certificates:
```bash
python scripts/phase5_independent_verify.py proofs/phase5/
```
*Expected Result:* `VERIFICATION SUCCESS` on all certificates with generated attestation JSON files in `proofs/phase5/attestations/`.

---

## 3. Command Reference Summary

| Task | Command |
|---|---|
| **Audit** | `python -m src.phase5 audit --repo .` |
| **Benchmark** | `python -m src.phase5 benchmark` |
| **Discover** | `python -m src.phase5 discover --config <config.json>` |
| **Status** | `python -m src.phase5 status` |
| **Verify (CLI)** | `python -m src.phase5 verify <path>` |
| **Verify (Independent)** | `python scripts/phase5_independent_verify.py <path>` |
| **Tests** | `python -m pytest tests/phase5/ -v` |
