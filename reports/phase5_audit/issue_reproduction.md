# Phase 5 Issue Reproduction & Engineering Repair Audit

**Date:** 2026-11-14T04:15:00+06:00  
**Phase:** Phase 5 SCCA (Smooth-Center Certificate-Aware Search)  
**Deliverable:** Stage B Issue Reproduction and Repairs  

---

## 1. Executive Summary

Four critical engineering and accounting issues were identified in the Phase 5 baseline codebase during mathematical research review. All four issues were successfully reproduced using failing regression tests (`tests/phase5/test_phase5_repairs_regression.py`), and verified against the initial checkout. Rigorous fixes were then implemented in `src/phase5/storage.py`, `src/phase5/scheduler.py`, and `src/phase5/cli.py`. All 85 unit, integration, and regression tests now pass with 100% success.

---

## 2. Issue 3.1: Novelty Detection and Insertion Ordering

### 2.1 Reported Risk
In the candidate discovery pipeline, a candidate was inserted into the database table prior to checking its novelty. Because the novelty lookup queried the candidates table for the candidate's canonical hash, the query observed the newly inserted row and classified genuinely new pairs as already existing. Furthermore, historical repository records were not queried.

### 2.2 Reproduction & Root Cause
- **Location:** `src/phase5/cli.py` (lines 172–183) and `src/phase5/storage.py` (`is_known_discovery`).
- **Mechanism:**
  1. `storage.record_candidate(..., status="PROVEN_BOTH", canonical_hash=cand.canonical_hash())` was called at line 172.
  2. `is_known = storage.is_known_discovery(cand.canonical_hash())` was called at line 181.
  3. `is_known_discovery` executed `SELECT 1 FROM candidates WHERE canonical_hash = ?`.
  4. The candidate was guaranteed to be present because of line 172. Consequently, `is_known` returned `True` for every candidate, setting `novelty_status = "ALREADY_IN_PROJECT"`.
  5. The frozen historical inventory of 48 earlier certificates was completely ignored.

### 2.3 Implementation Fix
- Added `Phase5Storage.canonical_key(A, B)` returning `f"{min(A,B)}:{max(A,B)}"`.
- Added `Phase5Storage.check_novelty(A, B, historical_inventory_path)` implementing an explicit multi-stage pipeline:
  1. Validates gap is exactly 2 ($B - A = 2$), odd parity, and $A > 2$.
  2. Looks up canonical key in `historical_inventory.json` (classifying as `ALREADY_IN_HISTORICAL_INVENTORY`).
  3. Queries current run database for prior occurrences (classifying as `DUPLICATE_IN_CURRENT_RUN`).
  4. Only if absent from both, classifies as `NEW_TO_REPOSITORY`.
- In `src/phase5/cli.py`, `check_novelty` is now evaluated **before** recording candidate state or executing primality proofs.

### 2.4 Verification
Tested via `test_novelty_pipeline_and_canonicalization` in `test_phase5_repairs_regression.py`.

---

## 3. Issue 3.2: UCB1 Scheduler and Reward Accounting

### 2.1 Reported Risk
The multi-family portfolio scheduler used the single most-recent reward `last_reward` as if it were the empirical mean reward, violating the theoretical formulation of UCB1. Additionally, the reward was unbounded, tie-breaking was non-deterministic, and cost-aware scheduling was absent.

### 3.2 Reproduction & Root Cause
- **Location:** `src/phase5/scheduler.py` (lines 100–104) and `src/phase5/storage.py` (`bandit_stats` schema).
- **Mechanism:**
  - Table `bandit_stats` only stored `last_reward REAL` with no tracking of cumulative reward or mean reward.
  - In `select_next_profile()`, `avg_reward = f_stat["last_reward"]`.
  - When an arm received high reward in pull 1 and lower reward in pull 2, pull 1 was completely forgotten, causing erratic exploitation of noisy fluctuations.
  - Reward calculation `(survivors * 0.1 + dual_prp * 10 + proven * 1000) / elapsed` was unbounded and could exceed $10^6$, invalidating the logarithmic regret bounds of UCB1 which assume $r \in [0, 1]$.

### 3.3 Implementation Fix
- Updated `bandit_stats` schema in `storage.py` to store `cumulative_reward` and `mean_reward`.
- Added `compute_bounded_reward(survivors, batch_size, dual_prp, proven, elapsed_sec)` mapping rewards strictly into $[0.0, 1.0]$:
  $$R = 0.1 \cdot \min\left(1, \frac{\text{survivors}}{\text{batch\_size}}\right) + 0.4 \cdot \min(1, \text{dual\_prp}) + 0.5 \cdot \min(1, \text{proven})$$
- In `MultiFamilyScheduler.select_next_profile()`, UCB1 now uses:
  $$\text{Score}_i = \hat{\mu}_i + c \sqrt{\frac{\ln(\sum N_j)}{N_i}}$$
  where $\hat{\mu}_i = \frac{\text{cumulative\_reward}_i}{N_i}$.
- Ties are broken deterministically by sorting on `(-score, family_id)`.
- Added `COST_AWARE` scheduling policy normalizing reward by elapsed compute time.

### 3.4 Verification
Tested via `test_ucb1_uses_cumulative_mean_not_last_reward` and `test_ucb1_deterministic_tie_breaking`.

---

## 4. Issue 3.3: Checkpointing and `--resume`

### 4.1 Reported Risk
The CLI accepted the `--resume` argument, but search position and scheduler state were never restored, causing restarted campaigns to re-search from $t=1$ and duplicate work.

### 4.2 Reproduction & Root Cause
- **Location:** `src/phase5/cli.py` (`run_discover`) and `src/phase5/scheduler.py`.
- **Mechanism:**
  - `p_disc.add_argument("--resume", ...)` was defined, but `args.resume` was never referenced in `run_discover`.
  - `MultiFamilyScheduler.next_t_by_family` unconditionally initialized to `{fid: 1}`.
  - On restart, new work units were registered starting at $t=1$, repeating previously searched intervals.

### 4.3 Implementation Fix
- Added `storage.get_max_t_for_family(family_id)` returning $\max(t_{end})$ from existing work units.
- Updated `MultiFamilyScheduler.__init__` to accept `resume: bool`. When `resume=True`, `next_t_by_family[fid]` is initialized to $\max(t_{end})$ if $>0$.
- Passed `args.resume` from CLI to `MultiFamilyScheduler`.

### 4.4 Verification
Tested via `test_resume_restores_next_search_interval`.

---

## 5. Issue 3.4: Documentation and Certificate-Hash Reconciliation

### 5.1 Reported Risk
Historical proof audits ignored Phase 1 certificates due to hardcoded directory paths, and lacked raw byte SHA-256 verification against disk assets.

### 5.2 Reproduction & Root Cause
- **Location:** `src/phase5/cli.py` (`run_audit`).
- **Mechanism:**
  - `proof_dirs` looked for Phase 1 in `proofs/phase1`, whereas Phase 1 certificates resided directly under `proofs/`. Consequently, only 13 of 48 historical certificates were counted.
  - Phase 2 certificates used `digits_p_minus`, but audit checked `digits_lower`, displaying 0 digits.

### 5.3 Implementation Fix
- Built standalone script `scripts/build_historical_inventory.py` computing byte-exact SHA-256 hashes for all 48 certificates across Phases 1–5.
- Fixed `run_audit` in `cli.py` to correctly scan top-level `proofs/` and parse all schema variants.
- Verified all 48 certificates exist, differ by 2, and have valid proofs.

### 5.4 Verification
Tested via `test_historical_inventory_reconciliation` and `python -m src.phase5.cli audit`.

---

## 6. Gate B Sign-Off

- [x] All 4 reported issues reproduced via failing tests.
- [x] Corrective implementations verified with exact integer arithmetic.
- [x] Full regression test suite passes (85/85 tests).
- **GATE B STATUS: PASSED.** Ready to proceed to Stage C.
