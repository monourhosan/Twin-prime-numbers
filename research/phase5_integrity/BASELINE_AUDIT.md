# Baseline Audit Report: Phase 5 Integrity & Historical Artifacts

**Audit Date:** 14 November 2026  
**Auditor:** Antigravity Autonomous Research & Verification Agent  
**Repository:** `https://github.com/monourhosan/Twin-prime-numbers`  
**Base Commit Audited:** `c9d4619e780e861ba98f2773d3af86fe865df898`  
**Active Working Branch:** `audit/phase5-integrity-phase6-readiness`  

---

## 1. Environment & Hardware Inventory

- **Operating System:** Windows 11 Pro 64-bit (`win32`, MSC v.1943)
- **Python Version:** 3.12.10 (AMD64)
- **Core Computational Number Theory Dependencies:**
  - `gmpy2`: 2.3.2 (backed by GMP / MPFR / MPC)
  - `sympy`: 1.14.0
  - `pytest`: 9.2.0
  - `cargo`: 1.99.1
  - `rustc`: 1.99.1
- **Hardware Profile:**
  - Host CPU: Intel Core i7 (8 threads)
  - Dedicated Mobile Accelerator: NVIDIA GeForce MX250 (2GB VRAM, CUDA capability 6.1)
  - Memory: 16 GB DDR4

---

## 2. Baseline Test Suite Execution

A complete run of the test suite before applying integrity patches was executed:
```powershell
python -m pytest tests/ -v
```
**Observed Result:**
- **118 passed in 9.40s** (0 failed, 0 skipped).
- Covers tests across Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, laptop acceleration, and CATS engine.

---

## 3. Historical Artifact & Certificate Inventory (Phases 1–6)

All 60 historical proof JSON artifacts across `proofs/` were hashed (SHA-256) and verified for algebraic twin consistency ($B - A = 2, A > 2$):

| Phase | Certificates | Attestations | Prime Form / Family | Max Digit Record | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | 35 | 0 | $k \cdot 2^n \pm 1$ | 100 digits (`cert_k4107_n100.json`) | Valid algebraic twins ($B-A=2$) |
| **Phase 2** | 3 | 0 | $k \cdot 2^n \pm 1$ (Wheel/Sieve) | 156 digits (`cert_k61347_n512.json`) | Valid algebraic twins ($B-A=2$) |
| **Phase 3** | 3 | 0 | $k \cdot 2^n \pm 1$ (HDRSS) | 507 digits (`cert_k1183377_n1664.json`) | Valid algebraic twins ($B-A=2$) |
| **Phase 4** | 2 | 2 | $k \cdot 2^n \pm 1$ (ADRS / Proth-Riesel) | 1,509 digits (`imported_cert_k416343_n4992.json`) | Verified by `scripts/phase4_independent_verify.py` |
| **Phase 5** | 5 | 5 | $F \cdot t \pm 1$ (SCCA Smooth-Center) | 133 digits (`cert_scca_133d_...json`) | Verified by `scripts/phase5_independent_verify.py` |
| **Phase 6** | 2 | 3 | $6m \pm 1$ (GITCSS Unrestricted) | 16 digits (`cert_gitcss_m166666666667062_16d.json`) | Verified by `src/phase6/independent_verify.py` |
| **Total** | **50** | **10** | — | **1,509 digits** | **All 50 certs valid twins** |

An authoritative content-addressed catalog has been saved to:
[`research/phase5_integrity/HISTORICAL_CERTIFICATE_INVENTORY.json`](file:///d:/project/Twin%20prime%20numbers/research/phase5_integrity/HISTORICAL_CERTIFICATE_INVENTORY.json).

---

## 4. Baseline Verification Commands & Observed Results

1. **Phase 5 Standalone Verifier:**
   ```powershell
   python scripts/phase5_independent_verify.py proofs/phase5/
   ```
   *Result:* **5/5 PASS**, all 5 attestations preserved in `proofs/phase5/attestations/`.
2. **Phase 4 Standalone Verifier:**
   ```powershell
   python scripts/phase4_independent_verify.py proofs/phase4/
   ```
   *Result:* **2/2 PASS** (including the milestone 1,509-digit twin pair).
3. **Phase 3 Standalone Verifier:**
   ```powershell
   python scripts/phase3_independent_verify.py proofs/phase3/
   ```
   *Result:* **3/3 PASS**.
4. **Phase 2 Standalone Verifier:**
   ```powershell
   python scripts/phase2_verify.py proofs/phase2/cert_k12477_n330.json
   ```
   *Result:* **PASS**.
5. **Phase 1 Standalone Verifier:**
   ```powershell
   python scripts/verify_certificate.py proofs/cert_k15_n10.json
   ```
   *Result:* **PASS**.
6. **Phase 6 Standalone Verifier:**
   ```powershell
   python -m src.phase6.cli verify proofs/phase6/certificates
   ```
   *Result:* **2/2 PASS**.

---

## 5. Concise List of Reproducible Defects

1. **Defect P0-A: Independent Verification is Not an Acceptance Gate**
   - *Location:* [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L230-L257) and [`src/phase5/campaign.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/campaign.py#L288-L305).
   - *Issue:* `storage.record_discovery` and `discoveries.append(...)` occur even when the independent verifier fails, errors, times out, or is missing entirely. Unverified certificates are accepted and reported as discoveries.
2. **Defect P0-B: Self-Contaminated Novelty Checking & Digest Type Mismatch**
   - *Location:* [`src/phase5/storage.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/storage.py#L143-L151) and `is_known_discovery` at [L343-L350](file:///d:/project/Twin%20prime%20numbers/src/phase5/storage.py#L343-L350).
   - *Issue:* `is_known_discovery` queries the `candidates` table (where the candidate was just inserted as `PRP_BOTH`), making newly encountered pairs appear old. In addition, it executes `SELECT 1 FROM discoveries WHERE sha256 = ?` using the pair's canonical hash, comparing a pair identity hash against a certificate JSON content digest.
3. **Defect P0-C: Empty-Directory Verification Returns Success**
   - *Location:* [`scripts/phase5_independent_verify.py`](file:///d:/project/Twin%20prime%20numbers/scripts/phase5_independent_verify.py#L303-L305).
   - *Issue:* When `target.is_dir()` and no matching `cert_*.json` files exist, the script prints an informational message and exits with code `0`.
4. **Defect P1-D: Campaign Status Ignores CLI Configuration and Database Path**
   - *Location:* [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L378-L382).
   - *Issue:* `run_status` hardcodes `Path("runs/phase5/phase5_search.db")` and completely ignores custom config or database paths provided via CLI flags.
5. **Defect P1-E: Audit Command Checks Filename Metadata Without Mathematical Verification**
   - *Location:* [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L57-L109).
   - *Issue:* `run_audit` globs directory files, extracts digits metadata from JSON headers, and prints summaries without invoking independent proof verifiers or checking theorem conditions.
6. **Defect P1-F: SCCA Discovery Loop Fabricates Zero Counters for Completed Work Units**
   - *Location:* [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L332).
   - *Issue:* `storage.complete_work_unit(wu["work_unit_id"], survivors=0, dual_prp=0, proven=len(finds))` hardcodes `survivors=0` and `dual_prp=0`, corrupting telemetry and scheduler metrics.
7. **Defect P1-G: Attestation Preservation & Error Handling**
   - *Location:* [`scripts/phase5_independent_verify.py`](file:///d:/project/Twin%20prime%20numbers/scripts/phase5_independent_verify.py#L264-L282).
   - *Issue:* When invoked with overwrite or across repeated runs, existing PASS attestations could be modified or overwritten if corrupted inputs are provided.

---

## 6. Execution Status & Remaining Steps

- [x] Baseline git status, environment, and dependency audit recorded.
- [x] Historical proof catalog created (`HISTORICAL_CERTIFICATE_INVENTORY.json`) with all 60 proof/attestation artifacts.
- [x] Baseline verifiers run on historical certificates (100% PASS).
- [ ] Reproduce defects P0-A, P0-B, P0-C, P1-D, P1-E, P1-F in isolated tests (`DEFECT_REPRODUCTIONS.md`).
- [ ] Implement source code repairs in `src/phase5/`, `scripts/`.
- [ ] Add rigorous unit and regression tests in `tests/phase5/`.
- [ ] Re-run full test suite and verifiers to confirm zero regression.
- [ ] Deliver Phase 6 readiness study (`READINESS_ASSESSMENT.md`, `ARCHITECTURE_PLAN.md`, `VERIFICATION_DEPENDENCIES.md`).
