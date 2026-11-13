# Phase 5 Baseline Audit & Prior-Art Inventory

**Audit Date:** 2026-11-13T18:30:00+06:00  
**Current Git Commit:** `c1e03b9f418b5e50c98e9d7dbe07152b3f2849d5`  
**Current Branch:** `research/phase5-scca`  
**Host Environment:** Windows 11 Build 26300 (AMD64), Intel Core i5-10210U (4c/8t, 15W TDP), NVIDIA GeForce MX250 (2 GB VRAM, sm_61)  
**Python Runtime:** Python 3.12.10 (tags/v3.12.10:0db05d2) with `gmpy2` 2.3.2 (GNU MP / MPIR backend)  

---

## 1. Baseline Test and Verification Record

Before modifying any source code or designing Phase 5 algorithms, the complete test suite and all historical proof certificates were executed:

### 1.1 Automated Test Suite
- **Command:** `python -m pytest tests/`
- **Result:** **64 passed in 8.20s** (100% pass rate).
- **Scope:**
  - `tests/phase2/`: 9 passed
  - `tests/phase3/`: 13 passed
  - `tests/phase4/`: 22 passed (math, config, sieves, storage recovery, proofs)
  - `tests/test_cats.py`: 10 passed
  - `tests/test_laptop_acceleration.py`: 10 passed (PTX JIT kernel, MX250 driver, thermal/power guardrails)

### 1.2 Historical Proof Certificates
- **Command:** `python scripts/phase4_independent_verify.py proofs/phase4 proofs/phase3 proofs/phase2`
- **Result:** **8 of 8 certificates passed** strict independent verification.

---

## 2. Project Deduplication Index (Existing Proof Inventory)

Every existing certified discovery in the repository was inventoried to prevent any accidental re-discovery or duplicate claim:

| Rank | Identifier / File | Family Representation | Decimal Digits | Mathematical Theorem | Independent Verification Status |
|---|---|---|---|---|---|
| **1 (Current Max)** | `imported_cert_k416343_n4992.json` | $k=416343, n=4992$ ($416343 \cdot 2^{4992} \pm 1$) | **1,509 digits** | Proth ($w=7$) + LLR ($P=3$) | **PASS** (`attest_7025c2a1baf9fa9d.json`) |
| **2** | `cert_k1836723_n3392.json` | $k=1836723, n=3392$ ($1836723 \cdot 2^{3392} \pm 1$) | **1,028 digits** | Proth ($w=13$) + LLR ($P=3$) | **PASS** (`attest_46a7116dc819e120.json`) |
| **3** | `cert_k1183377_n1664.json` | $k=1183377, n=1664$ ($1183377 \cdot 2^{1664} \pm 1$) | **507 digits** | Proth ($w=5$) + LLR ($P=5$) | **PASS** (Matrix Powering) |
| **4** | `cert_k254697_n1024.json` | $k=254697, n=1024$ ($254697 \cdot 2^{1024} \pm 1$) | **314 digits** | Proth ($w=5$) + LLR ($P=9$) | **PASS** (Matrix Powering) |
| **5** | `cert_k15993_n672.json` | $k=15993, n=672$ ($15993 \cdot 2^{672} \pm 1$) | **207 digits** | Proth ($w=7$) + LLR ($P=3$) | **PASS** (Matrix Powering) |
| **6** | `cert_k61347_n512.json` | $k=61347, n=512$ ($61347 \cdot 2^{512} \pm 1$) | **159 digits** | Proth ($w=5$) + LLR ($P=5$) | **PASS** (Montgomery Ladder) |
| **7** | `cert_k126747_n384.json` | $k=126747, n=384$ ($126747 \cdot 2^{384} \pm 1$) | **121 digits** | Proth ($w=5$) + LLR ($P=5$) | **PASS** (Montgomery Ladder) |
| **8** | `cert_k12477_n330.json` | $k=12477, n=330$ ($12477 \cdot 2^{330} \pm 1$) | **104 digits** | Proth ($w=17$) + LLR ($P=3$) | **PASS** (Montgomery Ladder) |

---

## 3. Prior-Method Inventory & Architectural Limitations

| Phase | Engine Name | Center / Family Form | Sieve Architecture | Proof Engine | Bottlenecks / Limitations |
|---|---|---|---|---|---|
| **Phase 1** | CATS | $k \cdot 2^n \pm 1$ | NumPy odd-$k$ stride | Pure Python Montgomery ladder | Single-threaded, high memory per candidate |
| **Phase 2** | CRT-Wheel | $k \cdot 2^n \pm 1$ | CRT wheel prefilter | Fast Lucas ladder | Memory bound on large wheel moduli |
| **Phase 3** | HDRSS | $k \cdot 2^n \pm 1$ | Hybrid dual-residue streaming | Decoupled $2 \times 2$ matrix Lucas | Fixed $k < 2^n$ Proth parameterization |
| **Phase 4** | ADRS-4 | $k \cdot 2^n \pm 1$ ($k=6t+3$) | Compact $t$-space block sieve + MX250 PTX | GMP `gmpy2` Proth + LLR | Exclusively restricted to the $k \cdot 2^n \pm 1$ single-power-of-2 template |

---

## 4. Why Phase 5 (SCCA) Is Fundamentally Distinct

All previous four phases (CATS, Phase 2, Phase 3, Phase 4) operated within the **rigid algebraic template**:
$$C = k \cdot 2^n, \quad A = k \cdot 2^n - 1, \quad B = k \cdot 2^n + 1$$
where $k$ was a monolithic multiplier and the only factored component was the power of 2 ($2^n$).

Phase 5 breaks out of this single-power-of-2 constraint:
1. **Mathematical Structure (Smooth Center $F$):**
   The center is structured with **multiple prime factors**:
   $$F = 2^a \cdot 3^b \cdot 5^c \cdot 7^d \cdots, \quad C(t) = F \cdot t$$
   Because $F$ contains multiples of 2 and 3 (and optionally 5, 7), $A(t) = F \cdot t - 1$ and $B(t) = F \cdot t + 1$ are guaranteed never divisible by any prime dividing $F$.
2. **Two-Sided Classical Theorem Duality:**
   Instead of using the specialized Proth ($k \cdot 2^n + 1$) and Riesel ($k \cdot 2^n - 1$) tests:
   - For $B(t) = F \cdot t + 1$: $B - 1 = F \cdot t$. Since the full prime factorization of $F$ is known, if $F > \sqrt{B}$ ($F^2 > B \iff F > t$), **Pocklington's Theorem / BLS Theorem 4 ($N-1$)** certifies $B$ prime unconditionally.
   - For $A(t) = F \cdot t - 1$: $A + 1 = F \cdot t$. Since $F$ is fully factored and $F > \sqrt{A}$, **Morrison / BLS Theorem 17 ($N+1$)** with generalized Lucas sequences certifies $A$ prime unconditionally.
3. **Algorithmic Search:**
   - **Method S1:** Certificate-first smooth-center CRT-class walker.
   - **Method S2:** Proof-cost-guided multi-family bandit scheduler.
   - **Method S3:** General center backup ($C = W \cdot m + r$).
