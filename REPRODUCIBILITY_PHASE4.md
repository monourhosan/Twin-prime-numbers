# Phase 4 ADRS-4 Reproducibility Guide

This guide provides exact, deterministic commands to reproduce the Phase 4 audit, tests, benchmarks, independent verification, and search campaigns on any standard computer.

---

## 1. System Requirements & Environment Setup

- **Python Version:** 3.12+ (64-bit AMD64 recommended)
- **Key Dependencies:**
  ```bash
  pip install numpy sympy gmpy2 pytest matplotlib
  ```

---

## 2. Automated Test Suite

Run the full automated unit, differential, and regression test suite:

```bash
python -m pytest -q
```
Expected output:
```text
......................................................                   [100%]
54 passed in ~1.3s
```

---

## 3. Strict Independent Verification (Zero Internal Dependencies)

Audit all historical and newly discovered certificates from first principles:

```bash
# Verify Phase 4 primary 1,028-digit discovery:
python scripts/phase4_independent_verify.py proofs/phase4/

# Verify all Phase 2, Phase 3, and Phase 4 certificates:
python scripts/phase4_independent_verify.py proofs/phase4 proofs/phase3 proofs/phase2
```

The verifier uses pure Python standard library integer arithmetic with independent $2 \times 2$ matrix binary exponentiation for Lucas sequences and recalculates all canonical SHA-256 payload digests.

---

## 4. Empirical Benchmarking

To reproduce the benchmark comparison matrix across sieve engines, sieve depths, and arithmetic backends:

```bash
python scripts/phase4_benchmark_compare.py
```
Output data files are recorded to `runs/phase4/benchmarks/`.

To regenerate the paper figures:
```bash
python scripts/generate_phase4_plots.py
```
Figures are saved in `paper/phase4/figures/`.

---

## 5. Running the Phase 4 Search Campaign

### Dry Run (Validates configuration and displays interval mapping):
```bash
python -m src.phase4 search --config configs/phase4/target_1000.json --dry-run
```

### Live Local Execution:
```bash
# Via Python module:
python -m src.phase4 search --config configs/phase4/target_1000.json

# Or via PowerShell launcher:
powershell -ExecutionPolicy Bypass -File scripts/phase4_start.ps1 -Config configs/phase4/target_1000.json
```

### Inspect Operational Status:
```bash
python -m src.phase4 status --campaign target_1000
```

### Control Commands:
```bash
# Graceful pause (worker finishes current unit and pauses):
python -m src.phase4 pause --campaign target_1000

# Resume search:
python -m src.phase4 resume --campaign target_1000
python -m src.phase4 search --config configs/phase4/target_1000.json --resume

# Graceful stop:
python -m src.phase4 stop --campaign target_1000
```

### Continuous Coverage Audit:
```bash
python -m src.phase4 coverage-audit --campaign target_1000
```
Verifies interval continuity, gap-free boundaries, and completed task unions per exponent.
