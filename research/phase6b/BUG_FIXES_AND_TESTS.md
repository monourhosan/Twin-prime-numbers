# Phase 6B — Reliability Repairs, Algorithmic Audits, and Regression Suite

**Document Version:** 1.0  
**Date:** 2026-11-14  
**Branch:** `research/phase6b-certification`  
**Test Suite Status:** 156 / 156 Passing (`tests/phase6/test_phase6b_repairs.py` added)

---

## 1. Executive Summary of Repairs

In accordance with Phase 6B Section 4, a thorough mathematical and algorithmic audit of the Phase 6 codebase (`src/phase6/proof_backend.py`, `src/phase6/screening.py`, `src/phase6/campaign.py`, and `src/phase6/coverage.py`) was executed. Four critical reliability defects were identified, analyzed, repaired, and placed under automated regression tests:

1. **Proof Backend Timeout and Factorization Constraints (`proof_backend.py`):**
   - *Defect:* `factor_timeout_sec` was accepted as an argument in `DeterministicPairProver.__init__` but never passed to or enforced during factorization calls. Furthermore, `factorint` had all advanced factorization methods disabled (`use_ecm=False, use_pm1=False, use_rho=False`), and factor primality checking capped trial division at $10^7$, rejecting valid prime factors above $10^7$.
   - *Repair:* Factoring is now wrapped in `ThreadPoolExecutor` with strict timeout enforcement against `self.factor_timeout_sec`. Bounded Pollard rho and Pollard $p-1$ are enabled to extract small-to-medium factors rapidly. Prime factors are verified through `is_prime_factor(p)` which uses deterministic Miller-Rabin / BPSW for factors above $10^7$.

2. **Screening Pipeline Asymmetry and PRP Anomaly (`screening.py`):**
   - *Defect:* In `screen_candidate()`, the Fermat base-2 test on right candidate $B$ was executed before left candidate $A$ had completed Miller-Rabin. If $B$ failed Fermat base-2, the method returned with `is_left_prp=False` even though $A$ had successfully passed Fermat base-2! Furthermore, small-prime divisibility for $B$ aborted before $A$ was tested. This caused candidates where $A$ was prime/PRP but $B$ was composite to be marked `is_left_prp=False`.
   - *Impact on Historical Reports:* Explains why historical Phase 6 candidate reports observed an artificial equality between left PRPs and dual PRPs (the "8 == 8" anomaly).
   - *Repair:* Candidate screening is now strictly staged: Left member $A$ is completely screened (small prime, Fermat-2, Miller-Rabin). If $A$ passes, `is_left_prp = True` is permanently recorded regardless of $B$'s outcome. $B$ is then screened. If $B$ fails, the result correctly retains `is_left_prp = True, is_right_prp = False, is_dual_prp = False`.

3. **Campaign Premature Segment Completion on Discovery (`campaign.py` & `coverage.py`):**
   - *Defect:* In `GITCSSCampaign.run_bounded_search()`, when `stop_on_discovery=True` was triggered, the loop broke out of survivor screening at the discovered candidate $m_{\text{hit}}$. However, the post-loop code called `self.coverage.record_completed_segment(..., m_end=seg_end)`, marking the entire segment $[m_{\text{start}}, m_{\text{end}})$ as completed in SQLite and the JSON manifest. Unscreened survivors in $(m_{\text{hit}}, m_{\text{end}})$ were permanently skipped on resume!
   - *Repair:* When interrupted early on discovery, `campaign.py` now captures `seg_interrupted_at = m_val`. It records `m_end = seg_interrupted_at` with status `PARTIAL_DISCOVERY` in `CoverageManager`. Resumption picks up gap-free at $m_{\text{curr}} = seg\_interrupted\_at + 1$.

4. **Sieve Survival Rate "Flat 3.21%" Investigation (`segmented.py` vs Benchmark Scope):**
   - *Defect/Anomaly:* In Phase 6 benchmarks, survival rates appeared frozen at 8,402 / 262,144 (3.2051%) across $Q = 5,000$ to $100,000$.
   - *Root Cause Analysis:* Rigorous mathematical analysis revealed that the benchmark suite ran at `m_base = 1,000,000`. For $m \in [10^6, 1.26 \times 10^6]$, the candidate primes $N = 6m \pm 1$ are bounded by $N < 7.6 \times 10^6$. The square root bound is $\sqrt{N} < \sqrt{7.6 \times 10^6} \approx 2,751$.
   - By fundamental number theory, every composite number $N$ in that range has a prime factor $p \le \sqrt{N} \le 2,751$. Once $Q \ge 2,751$, all composite numbers in the window have already been eliminated! For $Q \ge 5,000$, no sieve prime $q \in [5,000, 100,000]$ can divide any surviving candidate unless the candidate equals $q$ itself (impossible since $N > 10^5$).
   - Therefore, at $m = 10^6$, the survivor count remains identically 8,402 for all $Q \ge 2,751$.
   - *Verification at Scale:* At 100d, 350d, and 1510d (where $Q \ll \sqrt{N}$), increasing $Q$ strictly and monotonically reduces survivor counts in accordance with Mertens' theorem (see benchmark table below).

---

## 2. Benchmark Evidence: Sieve Survival Scaling vs Digit Scale

Measurements over windows of 100,000 centers with wheel primes $\{5, 7, 11, 13\}$:

| Sieve Cutoff $Q$ | Sieve Primes | $m = 10^6$ (6 digits) | $m = 10^{99}$ (100 digits) | $m = 10^{349}$ (350 digits) | $m = 10^{1509}$ (1510 digits) |
|---|---|---|---|---|---|
| **$Q = 1,000$** | 162 | 4.906% (12,861/262k) | — | — | — |
| **$Q = 5,000$** | 663 | **3.205%** (8,402/262k) | 3.504% (3,504/100k) | 3.399% (3,399/100k) | 3.385% (3,385/100k) |
| **$Q = 10,000$** | 1,223 | **3.205%** (8,402/262k) | 3.019% (3,019/100k) | 2.932% (2,932/100k) | 2.881% (2,881/100k) |
| **$Q = 50,000$** | 5,127 | **3.205%** (8,402/262k) | 2.196% (2,196/100k) | 2.182% (2,182/100k) | 2.097% (2,097/100k) |
| **$Q = 100,000$** | 9,586 | **3.205%** (8,402/262k) | 1.948% (1,948/100k) | 1.960% (1,960/100k) | 1.839% (1,839/100k) |

**Conclusion:** At cryptographically large scales ($100\text{d}+$), the sieve behaves strictly as expected under Mertens' theorem, pruning the candidate space from $3.5\%$ down to $1.8\%$. At $m = 10^6$, saturation occurs strictly because $Q > \sqrt{N}$.

---

## 3. Automated Regression Suite (`tests/phase6/test_phase6b_repairs.py`)

Six dedicated tests verify all repaired pathways:
1. `test_factor_timeout_and_bounded_factoring`: Proves that a 200-digit RSA semiprime factorization aborts cleanly within 3.0s under a 0.5s timeout.
2. `test_is_prime_factor_validation`: Validates exact prime identification above $10^7$ and composite rejection.
3. `test_screening_left_prp_independent_from_right`: Validates that candidates with prime $A$ and composite $B$ are recorded with `is_left_prp=True` and `is_dual_prp=False`.
4. `test_campaign_early_break_does_not_falsely_complete_segment`: Proves that early break on discovery records the exact hit cursor and that resumption begins at $m_{\text{hit}} + 1$.
5. `test_sieve_survival_monotonicity_at_100d`: Enforces strict survival fraction monotonic decrease for $Q \in \{5k, 10k, 50k\}$.
6. `test_sieve_small_range_saturation_mechanism`: Verifies the mathematical saturation theorem for $m = 10^6$ between $Q=5k$ and $Q=100k$.
