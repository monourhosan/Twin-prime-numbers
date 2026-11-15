# Phase 9: Exact Reproducibility Instructions

This document provides step-by-step instructions to reproduce the entire Phase 9 research, mathematical derivations, benchmarks, discovery campaign, and independent verification of the **364-digit twin-prime pair** on the **PACCM-9** manifold.

---

### 1. Environment & Prerequisites

- **Operating System:** Windows 10/11 64-bit
- **Python Version:** 3.12.x
- **GPU Hardware:** NVIDIA GeForce MX250 (Pascal architecture, `sm_61`, driver 582.78 or compatible)
- **Key Python Packages:**
  ```powershell
  python -m pip install gmpy2 sympy numpy pytest
  ```

---

### 2. Verify Baseline and Phase 9 Test Suite

Run the full repository test suite (236 passing tests across Phases 1 through 9):

```powershell
python -m pytest
```

To run Phase 9 tests specifically (including CPU/GPU differential equivalence, math properties, and tamper tests):

```powershell
python -m pytest tests/phase9/
```

---

### 3. Rebuild Authoritative Historical Inventory

To rebuild the inventory of all 59 pre-existing historical pairs across Phases 1 through 8:

```powershell
python scripts/phase9/build_full_historical_inventory.py
```
Output: `research/phase9/historical_inventory.json` (SHA-256: `6a77d23c1ab521efca099e05f1a58442bca322c0acfe1db61570216dc353d740`).

---

### 4. Reproduce NVIDIA GeForce MX250 Hardware Benchmarks

Execute the comparative CPU vs MX250 GPU benchmark over identical windows:

```powershell
python -m scripts.phase9.benchmark_phase9
```
Outputs:
- Markdown report: `research/phase9/BENCHMARKS.md`
- Raw metrics JSON: `data/phase9/benchmarks.json`

---

### 5. Reproduce Discovery Campaign Execution & Resumption

To execute the PACCM-9 discovery search campaign targeting $\ge 350$ decimal digits:

```powershell
python -m src.phase9.cli search --campaign-id phase9_primary_355d --anchor-y 283 --t-start 1 --t-end 50000 --sieve-depth 50000 --batch-size 5000
```

To resume from the verified checkpoint:

```powershell
python -m src.phase9.cli search --campaign-id phase9_primary_355d --anchor-y 283 --t-start 10003 --t-end 50000 --sieve-depth 50000
```

---

### 6. Independently Verify the Discovered 364-Digit Twin-Prime Pair

Run the standalone independent verifier (zero project imports):

```powershell
python scripts/phase9_independent_verify.py proofs/phase9/certificates/cert_paccm9_364d_t1129.json --attest-dir proofs/phase9/attestations
```

Expected output:
```text
Auditing Phase 9 certificate: cert_paccm9_364d_t1129.json...
  + Canonical Proof Payload SHA-256 verified: 62d13fd6011ec338f9324a0c9532bc90be297eb505a0f5ef0eebef349625b190
  + Difference B - A: 2
  + Exact decimal digits: 364
  + Pocklington BLS Theorem 4 primality unconditionally verified for upper member B
  + Morrison BLS Theorem 17 primality unconditionally verified for lower member A
  + Signed attestation written: .../proofs/phase9/attestations/attest_62d13fd6011ec338.json
  [PASS] cert_paccm9_364d_t1129.json unconditionally verified!
```
