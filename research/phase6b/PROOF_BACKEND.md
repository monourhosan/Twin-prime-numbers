# Phase 6B — Proof Router Architecture, ECPP Integration, and Verification Gates

**Document Version:** 1.0  
**Date:** 2026-11-14  
**Branch:** `research/phase6b-certification`  
**Compliance:** Strict Adherence to Mathematical Ground Truth and Host Environmental Boundaries

---

## 1. Hybrid Proof Architecture and Decision Matrix

The Phase 6B proof engine implements an intelligent proof router (`src/phase6/proof_router.py`) that evaluates candidate structural properties and dispatches to the most mathematically rigorous and computationally efficient theorem.

```
                              Candidate Pair (A, B)
                                      |
                 +--------------------+--------------------+
                 |                                         |
     k * 2^n +/- 1 (2^n > k)?                 General Center C = 6m
                 |                                         |
          [PROTH / LLR]                   Attempt Bounded Factoring of m
                 |                                         |
    +------------+------------+             +--------------+--------------+
    |                         |             |                             |
Upper (B): Proth          Lower (A): LLR    F > sqrt(N)?           F <= sqrt(N)
a^((B-1)/2) = -1 mod B    v_{n-2} = 0 mod A |                             |
                                     [DUAL-BLS]                   [GENERAL ECPP]
                                     Upper: BLS Thm 4 (Pocklington)  Goldwasser-Kilian-Atkin
                                     Lower: BLS Thm 17 (Morrison)    Elliptic Curve Chain
```

### Route Specifications:
1. **Route 1: Proth / LLR (`PROTH_LLR`)**
   - Applies to: Candidates of the algebraic form $k \cdot 2^n \pm 1$ with $2^n > k$.
   - Upper candidate $B = k \cdot 2^n + 1$: Proth's Theorem (quadratic non-residue witness $a^{(B-1)/2} \equiv -1 \pmod B$).
   - Lower candidate $A = k \cdot 2^n - 1$: Lucas-Lehmer-Riesel (LLR) Theorem ($v_{n-2} \equiv 0 \pmod A$ where $v_0 = V_k(P, 1)$).
   - Time Complexity: $O(n)$ modular multiplications. Proof generation completes in milliseconds even at 1,500+ digits.

2. **Route 2: Dual Classical BLS (`DUAL_CLASSICAL_BLS`)**
   - Applies to: Centers $C = 6m$ where complete or partial factorization yields factored part $F > \sqrt{N}$.
   - Upper candidate $B = 6m + 1$: Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington $N-1$).
   - Lower candidate $A = 6m - 1$: Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison $N+1$).
   - Pre-condition: Requires $F > \sqrt{N} + 1$. For general 350-digit integers, $F \le 10^6 \ll 10^{175}$, rendering this route mathematically inapplicable without general integer factorization (GNFS).

3. **Route 3: Elliptic Curve Primality Proving (`ECPP`)**
   - Applies to: General unrestricted integers where classical $N \pm 1$ factorizations are unavailable.
   - Theoretical Foundation: Goldwasser-Kilian (1986) and Atkin-Morain (1993) theorems.
   - Generates a certificate chain of curves $E(\mathbb{F}_p): y^2 = x^3 + ax + b$, group orders $m = |E(\mathbb{F}_p)|$, prime factors $q > (\sqrt[4]{p} + 1)^2$, and points $P = (x, y)$ satisfying $(m/q)P \neq \mathcal{O}$ and $mP = \mathcal{O} \pmod p$.
   - Recursively descends until $q < 10^7$ (terminal prime leaf).

---

## 2. Upstream Verification Gate and Issue #2723 Audit

In accordance with Phase 6B Section 3, an audit of PARI/GP upstream releases was conducted:

- **Upstream Defect Identified (PARI/GP Issue #2723):**
  In unpatched versions of PARI/GP prior to November 2026, `primecertisvalid` was subject to false positives under specific degenerate curve parameter conditions.
- **Upstream Fixes:**
  Addressed in permanent git commits `cb9aa6cb53` (dated 2026-10-29) and `d608e4e51d` (dated 2026-11-03).
- **Project Policy:**
  In adherence to scientific integrity, the project **never silently trusts `primecertisvalid` or any single black-box API**. All ECPP certificates must be independently validated by our separate, ground-up verifier `scripts/phase6b_ecpp_verify.py` which directly evaluates:
  1. Curve nonsingularity: $\Delta = -16(4a^3 + 27b^2) \not\equiv 0 \pmod p$.
  2. Point membership: $y^2 \equiv x^3 + ax + b \pmod p$.
  3. Hasse-Weil bound: $(\sqrt{p} - 1)^2 < m < (\sqrt{p} + 1)^2$.
  4. Atkin-Morain inequality: $q > (\sqrt[4]{p} + 1)^2$.
  5. Subgroup non-identity: $(m/q) \cdot P \neq \mathcal{O} \pmod p$.
  6. Group annihilation: $m \cdot P = \mathcal{O} \pmod p$.
  7. Downward recursion to proven small prime leaf.

---

## 3. Host Environment Audit and Explicit Blocker Record

An exhaustive inventory of host capabilities on the active system (Windows 11 AMD64, Intel i5-10210U) was conducted:

| Capability / Resource | Status | Verification Detail |
|---|---|---|
| Python 3.12.10 | **Available** | Verified in PATH; gmpy2 2.3.2 and SymPy 1.14.0 active. |
| PARI/GP (`gp.exe` / `pari.exe`) | **Absent** | Not present in PATH or user directories. |
| WSL (Windows Subsystem for Linux) | **Absent** | `wsl --status` reports command not found / not installed. |
| Winget PARI Package | **Unavailable** | Windows Package Manager contains no maintained PARI/GP distribution. |
| Windows Application Control | **Enforced** | Ad-hoc compiled binaries in `target/debug/build/` blocked by OS policy. |
| Execution Policy Directive | **Enforced** | Prompt directive strictly forbids downloading unsigned executables or running unreviewed scripts. |

### Blocker Declaration: `P6B-BLOCKER-01`
- **Blocker Code:** `P6B-BLOCKER-01`
- **Impacted Candidates:** The eight 350-digit probable twin-prime pairs in `data/phase6b_pending_pairs.jsonl`.
- **Reason:** Factoring the centers $m$ yields only small factors up to 6 digits, leaving 343+ digit composite cofactors. Classical BLS $N \pm 1$ proof requires $F > 10^{175}$ and is mathematically impossible without GNFS. Proving these candidates strictly requires general ECPP. However, no vetted ECPP engine is pre-installed on the host, and security boundaries prohibit unauthorized external executable downloads.
- **Candidate Classification:** All eight 350-digit pairs are verified 50-round Miller-Rabin + BPSW PRPs and remain classified as:
  ```json
  "proof_status": "PRP_PENDING_PROOF",
  "blocker_code": "P6B-BLOCKER-01"
  ```
- **Integrity Guarantee:** Zero false or unverified primality certificates have been generated. The codebase (`proof_router.py` and `scripts/phase6b_ecpp_verify.py`) stands fully implemented, tested, and ready to ingest ECPP proofs the moment an authorized PARI/GP engine becomes available.
