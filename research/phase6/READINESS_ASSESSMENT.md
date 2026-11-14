# Phase 6 Design Readiness Assessment & Feasibility Study

**Assessment Date:** 14 November 2026  
**Auditor:** Antigravity Autonomous Research & Verification Agent  
**Scope:** Architecture assessment for Unrestricted Twin-Prime Center Search ($C = 6m$)  
**Verdict:** **CONDITIONAL GO (Blocker: ECPP Engine Deployment on Windows)**  

---

## 1. Study Questions & Definitive Answers

### Q1: Which Phase 1–5 components can safely be reused now that Phase 5's accounting and verification gates are repaired?
- **Safe for Direct Reuse:**
  - `Phase5Storage` / SQLite WAL connection manager with strict commit-close semantics, canonical pair identity (`twin-pair-v1:min:max`), and pre-run historical inventory baseline checks.
  - Multi-tier PRP screening infrastructure (`gmpy2.is_prime` Miller–Rabin with $\ge 25$ rounds).
  - Standalone verifier architecture: JSON Schema format validation, canonical JSON SHA-256 byte digest hashing, and fail-closed exit code contracts.
  - SCCA/CRT segment bitset array structures.
- **Excluded from Reuse:**
  - Phase 5 Pocklington and Morrison proof backends (`prove_pocklington_upper`, `prove_morrison_lower`), because unrestricted centers $6m$ do not have smooth, structured factorizations of $6m \pm 1$.

### Q2: Can candidate identity, audit manifest, and proof acceptance mechanisms be made phase-independent?
- **Yes.** The domain-separated canonical tuple encoding:
  \[
  \text{canonical\_pair\_key}(A, B) = \text{twin-pair-v1}:\min(A, B):\max(A, B)
  \]
  and its SHA-256 digest `pair_id` are purely algebraic and completely independent of prime generation family ($k \cdot 2^n \pm 1$, $F \cdot t \pm 1$, or general $6m \pm 1$). The unified audit manifest format in `HISTORICAL_CERTIFICATE_INVENTORY.json` already catalogs all 6 phases under this identical identity schema.

### Q3: What mature general-purpose prime proving tool can emit usable proof artifacts for 350–450-digit candidates?
- **Tool:** **Primo** (Marcel Martin) or **Pari/GP (`primecert`) / FLINT / SageMath ECPP**.
  - *Primo:* Gold standard for Elliptic Curve Primality Proving (ECPP), emitting human-readable and machine-parseable certificates. Free for research use, version 4.3.3.
  - *Pari/GP:* Open source (GPLv2+), supports ECPP certificate generation and validation via `primecert()`.
- **Limitation in Current Environment:** Primo is a closed-source binary, blocked by Windows Application Control policies in sandboxed environments. Python lacks a pure-standard-library ECPP certificate generator for 350–450-digit integers.

### Q4: Can a separate established verifier consume those certificates, and how will its result be bound to the exact integer?
- **Yes.** Primo certificates can be independently consumed by open-source verifiers such as `primov` or Python-based elliptic curve point-addition verifiers that check the Weierstrass curve parameters, point order, and down-step prime factor conditions. The certificate digest binds directly to the decimal string of $A$ and $B$.

### Q5: How will memory, CPU, and wall-clock budgets be enforced without assuming old laptop/GPU availability?
- **Segmented Bitset Sieve:** Sieve segments of $L = 500,000$ to $1,000,000$ center indices fit in $< 1 \text{ MB}$ of L3 CPU cache, requiring minimal RAM and zero GPU dependencies.
- **Worker Timeouts:** Bounded work units with explicit `time_budget_seconds` and signal-based cooperative pauses (`.pause` file).

### Q6: What should the pilot size, segment size, and resume format be, subject to actual benchmarks?
- **Pilot Size:** 100,000 eligible centers at $10^{349}$.
- **Production Segment Size:** 250,000 centers per slice.
- **Resume Format:** Atomic JSON / SQLite interval manifests recording contiguous completed ranges $[m_{\text{start}}, m_{\text{end}}]$ with zero gaps.

### Q7: Is Phase 6's unrestricted-center search technically different from the project's Phase 2 CRT wheel search?
- **Search Domain:**
  - Phase 2: Restrictive Proth/Riesel family $p = k \cdot 2^n \pm 1$, searching for exponent $n$ with fixed $k$.
  - Phase 6: General integer center sequence $C = 6m$, exploring all integers across the continuum $p \in [10^{349}, 10^{350}]$.
- **Indexing & Residues:**
  - Phase 2: Wheel on exponent $n$ modulo small primes.
  - Phase 6: General Integer Twin-Center Segmented Sieve (GITCSS) with forbidden residues $m \equiv \pm 6^{-1} \pmod q$ for every sieving prime $q \ge 5$.
- **Proof Method:**
  - Phase 2: Proth's theorem (for $B$) and Lucas–Lehmer–Riesel (for $A$).
  - Phase 6: General ECPP (or BLS Theorem 4/17 only when coupled center factorization is tractable).

### Q8: What evidence is necessary to label a 350–450-digit pair `NEW_TO_REPO_ONLY` vs. worldwide novelty?
- **`NEW_TO_REPO_ONLY`:** Authenticated proof that the pair is absent from `HISTORICAL_CERTIFICATE_INVENTORY.json` and all prior project databases.
- **Worldwide Novelty:** Cross-referencing against the Prime Pages Twin Prime Records database (maintained by Chris Caldwell) and the Top5000 prime list. Currently, the world-record twin prime exceeds 388,342 digits, but general unrestricted twin primes at 350–450 digits are sparsely cataloged.

### Q9: What blockers make a full-scale Phase 6 search premature?
- **Blocker P6-B1 (Critical):** Lack of a verified, whitelisted, local ECPP certificate generator capable of running under Windows without trigger-blocking by host security policies.
- **Scientific Integrity Mandate:** Dual PRPs found at 350–450 digits **must never be reported as proven primes**; they must remain honestly classified as `PRP_BOTH` / `UNPROVEN_DUE_TO_FACTORIZATION_LIMIT` until unconditional ECPP certificates are verified.

---

## 2. Comparison Matrix: Phases 2–5 vs. Phase 6

| Dimension | Phase 2 (Wheel) | Phase 3 (HDRSS) | Phase 4 (ADRS) | Phase 5 (SCCA) | Phase 6 (GITCSS) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Center Form** | $k \cdot 2^n$ | $k \cdot 2^n$ | $k \cdot 2^n$ | $F \cdot t$ (smooth) | $6m$ (unrestricted) |
| **Digit Record** | 159 digits | 507 digits | 1,509 digits | 133 digits | 350–450 digits |
| **Sieve Method** | Wheel 30/210 | Depth-350k HDRSS | Bucket + GPU PTX | Segmented SCCA | GITCSS bitset |
| **Proof on Upper** | Proth Theorem | Proth Theorem | Proth Theorem | Pocklington (BLS 4) | ECPP / General BLS |
| **Proof on Lower** | LLR Test | LLR Test | LLR Test | Morrison (BLS 17) | ECPP / General BLS |
| **Factoring Need** | Trivial ($2^n$) | Trivial ($2^n$) | Trivial ($2^n$) | Pre-factored $F$ | Unfactored general $6m$ |
| **Proof Tool** | In-tree Python | In-tree Python | In-tree Python | Standalone Python | **External ECPP (Blocked)** |

---

## 3. Definitive Readiness Verdict

### **Verdict: CONDITIONAL GO**
- **Passed Gates:**
  1. All 144 unit and regression tests pass with zero errors.
  2. Fail-closed verification gate implemented and proven by fault injection (P0-A).
  3. Novelty checking decoupled from active candidate tables (P0-B).
  4. Verifier empty-directory exit code fixed (P0-C).
  5. 100% of historical certificates (50/50) verified and preserved byte-for-byte.
  6. Phase 5 59d and 133d discoveries independently validated.
- **Open Blocker:**
  - **`P6-BLOCKER-01`**: Absence of automated, whitelisted ECPP proof generation in this Windows environment.
- **Next Permitted Step:**
  - Sieve and dual-PRP screening campaigns at 350 digits are **APPROVED** for heuristic mathematical density studies, provided all candidates are strictly recorded as `PRP_BOTH` and **never claimed as proven twin primes**.
  - Unconditional certificate generation at $\ge 350$ digits remains **HOLD** pending deployment of a verified ECPP solver.
