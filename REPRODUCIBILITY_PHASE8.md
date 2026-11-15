# Phase 8 Reproducibility Guide: PAQCS (1,511-Digit Twin Prime Search)

## 1. Quick Verification (Instant First-Principles Audit)

To independently verify the newly discovered and unconditionally certified 1,511-digit twin prime pair without importing any search modules:

```bash
python scripts/phase8_paqcs_independent_verify.py proofs/phase8/certificates/cert_paqcs_1511d_t110891.json
```

Or using the CLI wrapper:

```bash
python scripts/phase8/independent_verify.py proofs/phase8/certificates/cert_paqcs_1511d_t110891.json
```

Expected output:
```
Auditing PAQCS certificate: cert_paqcs_1511d_t110891.json...
  + Canonical Proof Payload SHA-256 verified: cd5a4bafd77112bbc3130a0784ee648d4232b1e98d577c92637d44e85b812cbc
  + Exact decimal digits: 1511
  + Center C mod 6: 0
  + Difference B - A: 2
  + Distinct prime factors in x: 274
  + Pocklington BLS Theorem 4 primality unconditionally verified for upper member B
  + Morrison BLS Theorem 17 primality unconditionally verified for lower member A
  [PASS] cert_paqcs_1511d_t110891.json unconditionally verified!
```

---

## 2. Running Benchmarks

```bash
python scripts/phase8/benchmark.py
```

---

## 3. Re-running the Search Campaign

To resume or re-run the 1,511-digit search:

```bash
python -m src.phase8.paqcs_cli search --config configs/phase8/paqcs_primary_1511d.json
```

---

## 4. Full Automated Test Suite

To run all 217 unit, property, and regression tests across Phase 1 through Phase 8:

```bash
python -m pytest
```
