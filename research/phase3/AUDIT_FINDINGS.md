# Phase 3 Audit Findings and Corrective Action Plan

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Repository Branch:** `research/phase3-hdrss`  
**Base Commit Reference:** `531a3fc`  

---

## 1. Executive Audit Matrix

| Defect / Observation | Severity | Phase 2 Code Location | Status in Phase 3 | Resolution & Fix Plan |
| :--- | :--- | :--- | :--- | :--- |
| **1. Decimal transcription discrepancy** | High | `research/phase2/DISCOVERY_STATUS.md`<br>`README.md`<br>`FINDINGS.md` | **Fixed** | Replaced manual strings with exact canonical values computed directly from $k \cdot 2^n \pm 1$. Added automated regression tests. |
| **2. Nonfunctional Phase 2 CLI flags** | High | `src/phase2/cli.py` (L87–140) | **Confirmed** | Redesign `src/phase3/cli.py` with real enforcement of `--max-wall-hours`, `--workers`, `--resume`, `--mode`, and exact `--min-digits`. |
| **3. False coverage on early-stop windows** | Critical | `src/phase2/search_scheduler.py` (L86–109) | **Confirmed** | Refactor task state: work units are only `COMPLETED` when fully traversed. Early stops mark task `PARTIAL` with exact next $k$. |
| **4. Window sieve scalar candidate checking** | Medium | `src/phase2/window_sieve.py` (L65–80) | **Confirmed** | Implement Strategy S1 (vectorized dual-stride bitset) and Strategy S2 (hybrid stride + sparse modular check). |
| **5. Independent verifier imports engine code** | High | `src/phase2/independent_verifier.py` (L13–15) | **Confirmed** | Implement `scripts/phase3_independent_verify.py` completely decoupled, using 2x2 matrix powering for Lucas sequences. |
| **6. Wheel density documentation claim** | Medium | `research/phase2/MATH_AND_PROOF_AUDIT.md` | **Fixed** | Verified mathematically and experimentally that exactly 1,485 odd residues survive modulo 30,030 ($9.890\%$). Corrected all docs. |

---

## 2. Detailed Technical Audit

### 2.1 Decimal Transcription Discrepancy (Confirmed & Fixed)
- **Problem:** `research/phase2/DISCOVERY_STATUS.md` and related markdown files printed erroneous decimal strings for the three certified pairs.
- **Root Cause:** Manual transcription of numbers during initial exploratory search instead of programmatic serialization from canonical certificate JSONs.
- **Verification of Canonical Certificates:**
  The certificates themselves (`proofs/phase2/cert_k*.json`) contain the exact mathematical integers:
  - $k=12477, n=330$: `272903272931176397803957102877...47` (104 digits, SymPy `isprime` = True)
  - $k=126747, n=384$: `499408607937441105671873149557...51` (121 digits, SymPy `isprime` = True)
  - $k=61347, n=512$: `822528793078188504267567711564...11` (159 digits, SymPy `isprime` = True)
- **Action Taken:** Fixed all occurrences across all markdown files. Added regression tests in `tests/phase3/test_audit_regression.py`.

### 2.2 Phase 2 CLI Flag Nonfunctionality (Confirmed)
- **Problem:** In `src/phase2/cli.py`, `cmd_search` accepted `--max-minutes`, `--workers`, `--resume`, and `--mode`, but:
  - `--max-minutes`: Never checked during the search loop.
  - `--workers`: Hardcoded execution on a single process.
  - `--resume`: Boolean flag ignored; always restarted from $k=3$.
  - `--min-digits`: Dispatched only to $n \in \{330, 384, 512\}$ via an if/elif tree; higher targets could not be searched.
  - Hardcoded loop limit $k_{\max} = 500,000$.
- **Action Plan:** Implement `src/phase3/cli.py` with typed arguments, actual process pool execution, monotonic timer enforcement, and progressive open-ended range generators.

### 2.3 Early-Stop False Completed Window Ledger (Confirmed)
- **Problem:** `src/phase2/search_scheduler.py` broke out of the candidate loop when `len(discovered_certs) >= max_proven`, but subsequently executed `self.checkpoint_mgr.record_completed_window(task.task_id, ...)`. This recorded unsearched candidates as searched.
- **Action Plan:** A task ledger with granular states (`PENDING`, `CLAIMED`, `PARTIAL`, `COMPLETED`). If interrupted or stopped early, save `next_unprocessed_k` and mark `PARTIAL`.

### 2.4 Inefficient Window Sieve Hot Path (Confirmed)
- **Problem:** `src/phase2/window_sieve.py` enumerated wheel survivors into a Python list, then for each survivor $k$ and each prime $q$, computed $k \pmod q$.
- **Action Plan:**
  - **Strategy S1:** NumPy boolean array bitset with direct strided slice marking `alive[offset::q] = False`.
  - **Strategy S2:** Hybrid approach striding small primes ($q \le Q_{\text{stride}}$) and testing sparse survivors for $Q_{\text{stride}} < q \le Q_{\text{total}}$.

### 2.5 Independent Verifier Independence (Confirmed)
- **Problem:** `src/phase2/independent_verifier.py` directly imported `lucas_v_fast` and `validate_llr_preconditions` from `src.phase2`.
- **Action Plan:** Standalone verifier `scripts/phase3_independent_verify.py` with zero imports from `src.phase2` or `src.phase3`, implementing:
  - Binary $2 \times 2$ matrix exponentiation for Lucas sequence $V_k(P, 1) \pmod A$:
    $$\begin{pmatrix} V_{k+1} \\ V_k \end{pmatrix} = \begin{pmatrix} P & -1 \\ 1 & 0 \end{pmatrix}^k \begin{pmatrix} P \\ 2 \end{pmatrix} \pmod A$$
  - Standalone Jacobi symbol implementation;
  - Independent Proth and LLR theorem verifier with strict fail-closed behavior on corrupted inputs.

### 2.6 Wheel Modulus Survivor Count (Confirmed & Fixed)
- **Problem:** Historical notes cited 4,944 survivors.
- **Mathematical Fact:**
  Modulo $M = 30030 = 2 \times 3 \times 5 \times 7 \times 11 \times 13$, there are 15,015 odd residues.
  The condition $k \equiv 3 \pmod 6$ leaves $\frac{1}{3} \times 15015 = 5005$.
  Exclusions for $\{5, 7, 11, 13\}$ eliminate $\frac{2}{q}$ fractions:
  $$15015 \times \frac{1}{3} \times \frac{3}{5} \times \frac{5}{7} \times \frac{9}{11} \times \frac{11}{13} = 1485$$
- **Action Taken:** Corrected documentation to 1,485 ($9.890\%$).
