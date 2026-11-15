# Changelog & Regression Report: Phase 5 Integrity Repairs

**Audit Date:** 14 November 2026  
**Auditor:** Antigravity Autonomous Research & Verification Agent  
**Branch:** `audit/phase5-integrity-phase6-readiness`  

---

## 1. Summary of Code & Engine Modifications

### A. Independent Verification Gate (Defect P0-A)
- **Files Modified:** [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py), [`src/phase5/campaign.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/campaign.py)
- **Change:** Refactored discovery search pipelines to be strictly fail-closed. A candidate pair cannot be recorded in `storage.record_discovery` or returned in `discoveries` unless `scripts/phase5_independent_verify.py` completes with exit code 0, generates a valid attestation with `result: "PASS"`, and confirms matching SHA-256 and integer pair identities.
- **CLI Propagation:** `python -m src.phase5 verify` now propagates the verifier subprocess return code rather than returning success on failure.

### B. Canonical Pair Identity & Deduplication (Defect P0-B)
- **File Modified:** [`src/phase5/storage.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/storage.py)
- **Change:**
  - Standardized canonical pair identity to `twin-pair-v1:min(A, B):max(A, B)`.
  - Added `pair_id` column and index to SQLite `discoveries` table with safe backward-compatible migration.
  - Decoupled active candidate screening (`candidates` table) from novelty lookups, preventing self-contamination.
  - Fixed `is_known_discovery` to query `pair_id` in discoveries, eliminating invalid comparisons between pair hashes and certificate JSON SHA-256 digests.

### C. Verifier Empty-Directory Exit Behavior (Defect P0-C)
- **File Modified:** [`scripts/phase5_independent_verify.py`](file:///d:/project/Twin%20prime%20numbers/scripts/phase5_independent_verify.py)
- **Change:** When `target.is_dir()` contains no matching certificate files, the verifier prints an explicit error message and exits with code `2` (nonzero) instead of `0`. When target does not exist, exits with code `1`. Added `--attestation-dir` and `--overwrite` options to protect historical attestations.

### D. Campaign-Aware Status Command (Defect P1-D)
- **File Modified:** [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py)
- **Change:** Added `--db` and `--config` CLI flags to `python -m src.phase5 status`. Shows the resolved database path being read. If the DB does not exist, reports clearly without creating a blank database.

### E. Mathematical Audit Tooling (Defect P1-E)
- **File Modified:** [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py)
- **Change:** Enhanced `python -m src.phase5 audit` with `--strict` and `--report`. Invokes format-specific independent verifiers across all phases (Phase 1 through Phase 6), writing machine-readable JSON reports.

### F. Measured Work-Unit Counters (Defect P1-F)
- **File Modified:** [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py)
- **Change:** `execute_discovery_search` now returns measured telemetry (`survivors`, `dual_prp`, `proven`, `verified`). `run_discover` persists measured counts to `storage.complete_work_unit` rather than hardcoding zeros.

### G. Connection Leak & Windows File Locking
- **File Modified:** [`src/phase5/storage.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/storage.py)
- **Change:** Replaced unclosed connection handles with a safe context manager that commits and explicitly closes connections on exit, resolving Windows `PermissionError: [WinError 32]` during temp directory cleanups.

---

## 2. Regression Test Results (Before vs. After)

| Metric | Before Integrity Repair | After Integrity Repair |
| :--- | :--- | :--- |
| **Total Test Suite Count** | 118 tests | **144 tests** (+26 new tests) |
| **Total Test Passing Count** | 118 passed | **144 passed** (100.0%) |
| **Failures / Errors** | 0 | **0** |
| **Execution Duration** | 9.40s | **10.70s** |

### New Automated Regression Suites Added
1. [`tests/phase5/test_verification_gate.py`](file:///d:/project/Twin%20prime%20numbers/tests/phase5/test_verification_gate.py): 7 tests (missing verifier, exit code 1, FAIL attestation, missing attestation, timeout, digest mismatch, real tiny pair).
2. [`tests/phase5/test_novelty_identity.py`](file:///d:/project/Twin%20prime%20numbers/tests/phase5/test_novelty_identity.py): 5 tests (ordering, distinct digests, inventory exclusion, non-self-contamination, idempotent restart).
3. [`tests/phase5/test_verify_cli_failures.py`](file:///d:/project/Twin%20prime%20numbers/tests/phase5/test_verify_cli_failures.py): 6 tests (empty directory code 2, missing file code 1, mutation of gap, Morrison parameter, Pocklington witness, parameter t).
4. [`tests/phase5/test_audit_inventory.py`](file:///d:/project/Twin%20prime%20numbers/tests/phase5/test_audit_inventory.py): 2 tests (historical proof immutability, strict audit failure on unsupported/malformed cert).
5. [`tests/phase5/test_campaign_status.py`](file:///d:/project/Twin%20prime%20numbers/tests/phase5/test_campaign_status.py): 3 tests (custom DB path, nonexistent DB non-creation, multi-campaign isolation).
6. [`tests/phase5/test_resume_and_metrics.py`](file:///d:/project/Twin%20prime%20numbers/tests/phase5/test_resume_and_metrics.py): 3 tests (persisted telemetry measurements, interrupted resume, legacy schema migration).

---

## 3. Historical Proof Integrity

- Total historical artifacts audited: **60** (50 certificates, 10 attestations).
- Historical certificates verified by format verifiers: **50 / 50 PASS**.
- Byte modifications to historical artifacts: **0 bytes changed**.
