# Phase 5 Reproducibility Guide: Smooth-Center Certificate-Aware Search (SCCA)

This guide provides exact, tested commands to reproduce the Phase 5 baseline audit, controlled benchmarks, scientific discoveries, fail-closed verification gates, and first-principles independent verification.

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
Verify that all 144 unit, property, and fault-injection tests across Phases 1–6 pass cleanly:
```bash
python -m pytest tests/ -v
```
*Expected Result:* **144 passed in ~10 seconds** (0 failed, 0 skipped).

### Step 2: Run Baseline & Independent Verification Audit
Audit the local environment, dependencies, and all 50 historical repository certificates across all phases:
```bash
python -m src.phase5 audit --repo . --strict --report research/phase5_integrity/AUDIT_REPORT.json
```
*Expected Result:* 
- Audits all 50 historical certificates with their respective format-specific verifiers.
- Confirms 50/50 VERIFIED, 0 failed, 0 malformed.
- Current repository maximum: 1,509 digits (`imported_cert_k416343_n4992.json`).

### Step 3: Run Controlled Algorithm Benchmark
Compare the Method S1 Segmented Filter against the CRT Wheel Walker, and benchmark proof timings:
```bash
python -m src.phase5 benchmark
```
*Expected Result:* Sieve rates > 1.5M cands/s (Segment) and > 7.0M cands/s (Wheel Walker); proof timings measured across digit bands.

### Step 4: Execute Fast Pilot Discovery (Smoke Test)
Run a bounded smoke campaign to discover and independently verify a small twin-prime pair:
```bash
python -m src.phase5 discover --config configs/phase5/smoke.json
```
*Expected Result:* Finds, certifies, and independently verifies twin pair `(453599, 453601)` in < 1 second. Only verified pairs are accepted into discoveries.

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
Check work units, candidate progression, and UCB1 reward statistics from any campaign database:
```bash
python -m src.phase5 status
python -m src.phase5 status --db runs/phase5/phase5_search.db
python -m src.phase5 status --config configs/phase5/smoke.json
```
*Expected Result:* Displays actual database path, measured work-unit telemetry (survivors, dual_prps), and accepted discoveries.

### Step 8: Standalone Independent Verification
Run the decoupled first-principles verifier (with ZERO imports from `src/`) on Phase 5 certificates:
```bash
python scripts/phase5_independent_verify.py proofs/phase5/
```
*Expected Result:* `VERIFICATION SUCCESS` on all 5 certificates; attestations preserved without overwriting historical records.

---

## 3. Command Reference Summary

| Task | Command |
|---|---|
| **Audit** | `python -m src.phase5 audit --repo . --strict --report research/phase5_integrity/AUDIT_REPORT.json` |
| **Benchmark** | `python -m src.phase5 benchmark` |
| **Discover** | `python -m src.phase5 discover --config <config.json>` |
| **Status** | `python -m src.phase5 status [--db <db_path>] [--config <config.json>]` |
| **Verify (CLI)** | `python -m src.phase5 verify <path>` |
| **Verify (Independent)** | `python scripts/phase5_independent_verify.py <path> [--attestation-dir <dir>]` |
| **Tests (Full Suite)** | `python -m pytest tests/ -v` |
| **Tests (Phase 5 Integrity)** | `python -m pytest tests/phase5/ -v` |
