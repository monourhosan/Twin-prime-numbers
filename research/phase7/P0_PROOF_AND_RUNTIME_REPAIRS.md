# Phase 7 P0 Proof and Reliability Repairs

**Date:** 2026-11-14  
**Author:** Google Antigravity (Mathematical Proof Auditor & Computational Number Theorist)  
**Status:** ALL P0 RELEASE BLOCKERS RESOLVED & VERIFIED  
**Regression Test Suite:** `tests/phase7/test_p0_repairs.py` (10/10 PASS)  
**Total Test Suite Status:** 169/169 PASS (100% green across entire repository)  

---

## 1. Executive Summary

Four critical defect clusters were audited, reproduced with failing test cases, and repaired in full accordance with mathematical rigor and operational safety:

1. **ECPP Verifier Soundness over Composite Moduli (`scripts/phase6b_ecpp_verify.py`):**
   - Repaired elliptic curve nonsingularity from naive `delta != 0 mod N` to exact unit discriminant $\gcd(4a^3 + 27b^2, N) = 1$.
   - Replaced flawed rounded-up bound $( \lfloor N^{1/4} \rfloor + 2 )^2$ (which rejected valid certificates) with exact integer evaluation of $q > (N^{1/4} + 1)^2$.
   - Implemented composite modulus detection during affine point addition (raising clean `CurveArithmeticException` when non-trivial factors are found, rather than crashing with unhandled `ValueError`).
   - Enforced exact integer Hasse-Weil interval check $(N + 1 - m)^2 \le 4N$.
   - Replaced weak $<10^7$ trial division leaf check with Jiang & Deng (2014) / Sinclair (2011) deterministic 7-base Miller-Rabin test for all $N < 2^{64}$.

2. **ECPP Producer End-to-End Adapter (`src/phase6/proof_router.py`):**
   - Replaced stub returning `ENGINE_AVAILABLE_NOT_EXECUTED` with a production-grade PARI/GP adapter.
   - Built a safe recursive parser for native PARI/GP vector format `[N, t, s, a, [x, y]]` without `eval()`.
   - Built an automated executable auditor: calculates binary SHA-256, queries version, and executes live smoke test on prime 17 and composite 15.
   - Accurately reports `BLOCKED_NO_APPROVED_ENGINE` on this Windows host where PARI/GP is absent, preventing unauthorized external downloads.

3. **Factorization Resource Bounds and Deterministic Primality (`src/phase6/proof_backend.py`):**
   - Replaced un-cancellable `ThreadPoolExecutor` (which leaked worker threads on timeout) with cooperative step-bounded trial division and bounded Pollard's rho that checks millisecond deadlines on every step.
   - Replaced probabilistic `gmpy2.is_prime(p, 25)` in `is_prime_factor` with the deterministic 7-base Miller-Rabin test for all $p < 2^{64}$.

4. **Candidate Space Counting and Ledger Bounds (`configs/phase6/stretch_1512d.json`):**
   - Resolved the counting discrepancy: $k \in [3, 150003)$ stepping by 6 ($k = 6t + 3$) contains exactly 25,000 eligible centers, not 50,000. All Phase 7 components use strict half-open integer intervals.

---

## 2. Defect Reproductions and Fixes

### 2.1 ECPP Nonsingularity over $\mathbb{Z}/N\mathbb{Z}$
- **Original Code:**
  ```python
  delta = (-16 * (4 * pow(self.a, 3, self.p) + 27 * pow(self.b, 2, self.p))) % self.p
  return delta != 0
  ```
- **Reproduction:** For $N = 35$, $a = 0$, $b = 5$:
  $$\Delta = -16 \cdot (0 + 27 \cdot 25) = -10800 \equiv 15 \pmod{35} \ne 0.$$
  The old verifier returned `True`, declaring the curve nonsingular even though $\gcd(4a^3 + 27b^2, 35) = 5 \ne 1$ (the curve is singular modulo 5).
- **Repair:**
  $$\gcd(4a^3 + 27b^2, N) = 1.$$
  Verified in `test_ecpp_non_unit_discriminant_rejected` (PASS).

### 2.2 Atkin-Morain Inequality Precision
- **Original Code:**
  ```python
  fourth_root = int(math.isqrt(math.isqrt(p))) + 1
  threshold = (fourth_root + 1) ** 2
  if q <= threshold: return False
  ```
- **Reproduction:** For $N = 101$, $(N^{1/4} + 1)^2 \approx 17.39$. The integer $q = 19$ satisfies $19 > 17.39$. The old code computed $\lfloor 101^{1/4} \rfloor + 1 = 4$, threshold $(4+1)^2 = 25$, and rejected valid $q = 19$.
- **Repair:** Exact integer algebra:
  $$q > (N^{1/4} + 1)^2 \iff q - 1 - \sqrt{N} > 2 N^{1/4} \iff ((q - 1)^2 + N)^2 > 4(q + 1)^2 N \quad (\text{for } (q-1)^2 > N).$$
  Verified in `test_ecpp_exact_atkin_morain_gk_condition` (PASS).

### 2.3 Factorization Resource Bounding
- **Original Code:**
  `ThreadPoolExecutor(max_workers=1)` with `future.result(timeout=...)` and non-waiting shutdown. Background threads continued to execute in C-loops indefinitely.
- **Repair:** Cooperative bounded algorithm with millisecond time checks inside every iteration and bounded Pollard rho steps (max 5,000 steps).
  Verified in `test_factor_timeout_no_lingering_threads` (PASS, completes in < 0.25s).

### 2.4 Deterministic 64-bit Primality
- **Implementation:** Jiang & Deng (2014) 7-base set:
  $$\{2, 325, 9375, 28178, 450775, 9780504, 1795265022\}.$$
  Verified against Carmichael numbers ($561, 1105, 1729, 2465, 2821, \dots$) in `test_deterministic_64bit_miller_rabin` (PASS).

---

## 3. Status of 350-Digit Pending PRPs and ECPP Engine

- **Host Engine Status:** Live check via `ProofRouter` confirmed `has_ecpp_engine() is False` (`pari_gp_path` absent from host PATH).
- **Guardrail Compliance:** Unauthorized external downloads or Windows security policy modifications are strictly prohibited.
- **Recovery Status:** The 8 pending 350-digit dual PRPs recorded in `data/phase6b_pending_pairs.jsonl` are preserved with status `PRP_PENDING_PROOF (BLOCKED_NO_APPROVED_ENGINE)`.
- **Alternative Special-Form Proof:** Centers of these 8 general integers lack large known factors ($F \ll \sqrt{N}$), so dual-BLS is mathematically inapplicable without GNFS or ECPP. They remain safely preserved until an authorized PARI/GP environment is made available.
