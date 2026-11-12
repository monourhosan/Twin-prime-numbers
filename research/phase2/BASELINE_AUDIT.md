# Baseline Audit and Integrity Report (Phase 2)

**Audit Date:** 2026-11-12  
**Target Repository:** https://github.com/monourhosan/Twin-prime-numbers  
**Audit Baseline Commit:** `62a858876ef4c34ff689b593fbcb2cf40e88ee92`  
**Dedicated Branch:** `research/new-twin-prime-search-v2`  
**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  

---

## 1. System and Environment Snapshot

* **Operating System:** Microsoft Windows 11 Enterprise / Pro [Version 10.0.26300-SP0] AMD64
* **Processor:** Intel64 Family 6 Model 142 Stepping 12, GenuineIntel (8 logical cores)
* **Python Runtime:** Python 3.12.10
* **Storage Available:** 75.78 GB free of 118.51 GB total
* **Security & Execution Constraints:** Windows Application Control (WDAC) restricts execution of newly built un-whitelisted binary executables in `target/debug/build/*.exe`. Execution of standard Python scripts, NumPy compiled C extensions, and SymPy is fully functional and permitted.

---

## 2. Frozen Baseline Inventory

All 35 pre-existing certificates in `proofs/` were scanned and recorded in an immutable inventory file:
* **Path:** `research/phase2/baseline_inventory.json`
* **Inventory SHA-256 Digest:** `b27e24a1ab320b9882e720e95a1336c1d768fa4c792383dfb245e383e2dcf554`
* **Total Pairs in Baseline:** 35 pairs (10 at $n=10$, 15 at $n=30$, 9 at $n=50$, 1 at $n=100$).
* **Largest Baseline Pair:** $4107 \times 2^{100} \pm 1$ (34 decimal digits).

All 35 certificates passed independent verification using `scripts/verify_certificate.py` with 100% pass rate.

---

## 3. Discrepancy Audit: The 34-Digit vs. 40-Digit Report Mismatch

### 3.1 The Defect
In the original project release (`FINDINGS.md`, `README.md`, and the paper appendix), the discovered pair for $k=4107, n=100$ was described as having 34 digits, but the text printed the following 40-digit integers:
* Printed $p$: `5205862110637458953584332604028295903027`
* Printed $p+2$: `5205862110637458953584332604028295903029`

### 3.2 Mathematical Fact-Checking
An independent recomputation confirms:
1. Exact arithmetic:
   $$4107 \times 2^{100} = 5206241015137338151946960064479232$$
   $$p = 4107 \times 2^{100} - 1 = 5206241015137338151946960064479231 \quad \text{(34 decimal digits)}$$
   $$p+2 = 4107 \times 2^{100} + 1 = 5206241015137338151946960064479233 \quad \text{(34 decimal digits)}$$
2. Primality:
   * Both 34-digit numbers are **provably prime** (certified by Proth witness $w=5$ and LLR parameter $P=5$).
   * The actual certificate file `proofs/cert_k4107_n100.json` already contained the **correct 34-digit integers** from generator output.
3. Compositeness of the printed 40-digit numbers:
   * `5205862110637458953584332604028295903027` is **composite** ($3^2 \times 578429123404162105953814733780921767003$).
   * `5205862110637458953584332604028295903029` is **composite** ($7 \times 79 \times 3581 \times 9444360091 \times \dots$).

### 3.3 Root Cause and Rectification
* **Root Cause:** A manual copy-paste / transcription error occurred during drafting of the markdown documentation, pasting numbers from an unrelated scratch test instead of reading from `proofs/cert_k4107_n100.json`.
* **Remediation:** 
  1. Updated `README.md`, `FINDINGS.md`, and `paper/twin_prime_search_paper.md` with the verified 34-digit integers.
  2. Implemented an automated regression test in `tests/phase2/test_regression.py` that parses all printed numerical values in markdown files and checks them against the structured JSON certificates and symbolic formulas.

---

## 4. Code Quality and Algorithmic Audit

| Component | Audit Observation | Severity | Action Taken in Phase 2 |
| :--- | :--- | :---: | :--- |
| **Proth Theorem Preconditions** | `src/cats/primality.py` only checked $k < 2^n$ when $n < 64$. For $n \ge 64$, arbitrary large $k$ was not checked against $2^n$. | Medium | Extended precondition check to arbitrary precision: $k < (1 \ll n)$ for all $n$. |
| **Proth Inconclusive vs. Composite** | If no witness with Jacobi symbol $-1$ was found, it returned `False`, which conflates "composite" with "inconclusive". | Medium | Distinguished `COMPOSITE_PROVEN`, `PRIME_PROVEN`, and `INCONCLUSIVE`. |
| **LLR Sequence $O(k)$ Initialization** | Lucas $V_k(P, 1)$ was computed via linear loop `for _ in range(1, k):`, requiring $O(k)$ big-integer operations. | High | Replaced with $O(\log k)$ binary Lucas doubling ladder (Montgomery ladder). |
| **LLR Hypothesis Verification** | In `llr_prove`, fallback $P=4$ was used without guaranteeing Jacobi conditions. | High | Enforced strict verification that $\left(\frac{P-2}{A}\right) = 1$ and $\left(\frac{P+2}{A}\right) = -1$. If no valid $P$ exists, classify as `INCONCLUSIVE`. |
| **Sieve Candidate Equals Divisor** | In `src/cats/sieve.py`, setting `alive[idx] = True` for $q = k 2^n \pm 1$ could resurrect candidates divisible by other primes. | Low | Sieve loop strictly eliminates candidates only when $k 2^n \mp 1 > q$, never resurrecting bits. |
| **Adaptive Sieve Depth** | Old ASD was a static formula of bit length, not empirical online optimization. | Low | Phase 2 engine implements real-time window calibration based on candidate throughput. |
