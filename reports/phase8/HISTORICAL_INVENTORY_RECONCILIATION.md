# Historical Inventory Reconciliation Report

**Date:** 15 November 2026  
**Auditor:** Antigravity (Google DeepMind)  
**Branch:** `research/phase8-primorial-qcp-scaleup`  
**Base Commit:** `a07237b`  

---

## 1. Discrepancy Reconciliation

### 1.1 Certificate Totals: 48 vs 58
- The top-level `README.md` badge historically advertised **48 certificates**.
- That count represented the state at the conclusion of **Phase 5 (SCCA)**:
  - Phase 1 (CATS Baseline): 35 certificates
  - Phase 2 (Wheeled Lucas): 3 certificates (104d, 121d, 159d)
  - Phase 3 (HDRSS): 3 certificates (207d, 314d, 507d)
  - Phase 4 (ADRS): 2 certificates (1,028d, 1,509d imported)
  - Phase 5 (SCCA): 5 certificates (6d, 12d, 12d, 59d, 133d)
  - **Phase 1--5 Subtotal:** $35 + 3 + 3 + 2 + 5 = \mathbf{48}$ certificates.
- Subsequent phases produced additional unconditionally proven certificates:
  - Phase 6 (GITCSS & QCP-6): 8 certificates (4d, 16d, 107d, 108d, 108d, 110d, 502d, 503d)
  - Phase 7 (HDC-7 Primorial): 1 certificate (1,510d)
  - Phase 8 (ADES-8 Historical): 1 certificate (1,511d)
- **Current Total Real Proof Certificates in Repository:** **58**.

### 1.2 Certificates vs. Attestations
- Some documentation colloquially counted proof artifacts without separating certificates from attestations.
- In the repository today:
  - **Proof Certificates (`cert_*.json`):** 58 files
  - **Verification Attestations (`attest_*.json`):** 18 files
  - **Combined JSON artifacts:** 76 files.
- Attestations are independent verification receipts; they must never be conflated with mathematical certificates.

### 1.3 Test Count Progression: 80 -> 144 -> 191 -> 208
- Phase 5 baseline: 80 tests.
- Phase 6 additions: expanded to 144 tests.
- Phase 7 and Phase 8 additions: expanded to 191 tests.
- Phase 8 Gate A verifier hardening (`tests/phase7/test_adversarial_v7.py`): added 17 mutation test cases.
- **Current Repository Test Suite:** **208 passed in 25.33s** (100% pass rate).

### 1.4 ECPP Readiness vs Special Proof Families
- `research/phase6/READINESS_ASSESSMENT.md` correctly identified that proving generic, unstructured integers $C = 6m$ in the 100d+ realm is blocked on Windows due to App Control preventing execution of unvetted binaries like `ecpp.exe` or `gp.exe`.
- QCP-6 (Phase 6) and PAQCS (Phase 8) deliberately bypass this obstacle by structuring the search over quadratic cofactors $C = x(x - h)$. Because $x$ divides both $A+1$ and $B-1$, both members can be proven deterministically using Pocklington (Theorem 4) and Morrison (Theorem 17) BLS criteria whenever $x$ is fully factored and $x^2 > \max(A, B)$.

---

## 2. Definitive Inventory by Phase and Method

| Phase | Method | Schema | Certificates | Attestations | Digits Range | Primary Theorems |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | CATS (Proth/Lucas) | 1.0 | 35 | 0 | 5 -- 34 | Proth / Lucas $V_k$ |
| **Phase 2** | Streaming Sieve / CRT | 2.0 | 3 | 0 | 104, 121, 159 | Proth Theorem |
| **Phase 3** | HDRSS Dense Exponent | 3.0 | 3 | 0 | 207, 314, 507 | Proth / Lucas Matrix |
| **Phase 4** | ADRS Two-Tier | 4.0 | 2 | 2 | 1028, 1509 | Proth / Riesel LLR |
| **Phase 5** | SCCA Smooth-Center | 5.0 | 5 | 5 | 6, 12, 12, 59, 133 | Pocklington / Morrison BLS |
| **Phase 6** | GITCSS / QCP-6 | 6.0 | 8 | 9 | 4, 16, 107, 108, 108, 110, 502, 503 | Pocklington / Morrison BLS |
| **Phase 7** | HDC-7 Primorial Proth/LLR | 7.0 | 1 | 1 | 1510 | Proth / LLR ($w=23, P=15$) |
| **Phase 8** | ADES-8 (Pre-PAQCS) | 8.0 | 1 | 1 | 1511 | Proth / LLR ($w=19, P=15$) |
| **Total** | -- | -- | **58** | **18** | **4 -- 1511** | -- |

All 58 historical certificates have been verified for integrity against their baseline digests.
