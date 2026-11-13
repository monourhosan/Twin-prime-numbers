# Phase 6 Reproducibility Guide: General-Integer Twin-Center Segmented Sieve (GITCSS)

**Phase:** Phase 6  
**Method:** Universal representation $p = 6m - 1, p+2 = 6m + 1$, wheel-compressed segmented sieve, tiered probable-prime screening, and dual Morrison/Pocklington classical primality proofs.

---

## 1. Environment & Prerequisites

- **Python Runtime:** Python 3.12 (64-bit)
- **Dependencies:** `gmpy2`, `sympy`, `pytest`
- **Installation:**
  ```bash
  pip install gmpy2 sympy pytest
  ```

---

## 2. One-Line Reproduction Pipeline

To reproduce all Phase 6 research deliverables, tests, benchmarks, discoveries, and independent attestations:

```bash
# 1. Verify 115 tests across Phases 1-6
python -m pytest

# 2. Run controlled benchmarks
python -m scripts.phase6_benchmarks

# 3. Discover and certify new general-integer twin-prime pair
python -m src.phase6.cli discover --config configs/phase6/pilot_discovery.json

# 4. Execute 100-digit bounded general-integer search
python -m src.phase6.cli discover --config configs/phase6/general_100d.json --max-segments 2

# 5. Audit segment coverage for zero gaps
python -m src.phase6.cli coverage-audit

# 6. Run decoupled independent verifier on proof certificates
python -m src.phase6.cli verify proofs/phase6/certificates/
```

---

## 3. Authoritative Discovery Details

- **Lower Prime $A$:** `1000000000002371` (16 decimal digits)
- **Upper Prime $B$:** `1000000000002373` (16 decimal digits)
- **Difference:** $B - A = 2$
- **Certificate:** `proofs/phase6/certificates/cert_gitcss_m166666666667062_16d.json`
- **Canonical SHA-256:** `1f2d443508c19ee0650c239183998ccf4eba9bf265dc031b90dba66140c6b727`
- **Attestation:** `proofs/phase6/attestations/attest_6c0b671d46a457d1.json`
- **Novelty:** `NEW_TO_REPOSITORY` (first general-integer twin-prime discovery in repository history).
