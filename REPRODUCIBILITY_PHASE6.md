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
# 1. Environment & Inventory Audit
python -m src.phase6.cli audit

# 2. Verify all 118 tests across Phases 1-6
python -m pytest tests/

# 3. Run controlled empirical benchmarks (wheel, sieve limit, reference vs optimized, screening scaling)
python -m src.phase6.cli benchmark

# 4. Discover and certify new general-integer twin-prime pair (16d)
python -m src.phase6.cli search --config configs/phase6/pilot_discovery.json

# 5. Execute 350-digit pilot campaign (100,000 eligible centers)
python -m src.phase6.cli search --config configs/phase6/pilot_350d.json --no-stop

# 6. Execute 350-digit unrestricted campaign (1,000,000 eligible centers)
python -m src.phase6.cli search --config configs/phase6/unrestricted_350d.json --no-stop --max-segments 4

# 7. Check campaign status and candidate ledger
python -m src.phase6.cli status

# 8. Audit segment coverage for zero gaps or overlaps
python -m src.phase6.cli coverage

# 9. Run decoupled independent verifier on proof certificates
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
