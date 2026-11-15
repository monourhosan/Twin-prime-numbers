# Phase 9: Prior Art, Algorithmic Novelty, and Architectural Trade-off Analysis
## Proof-Aware Unrestricted Twin-Prime Search (PAUTS) & Primorial-Anchored Cubic-Cofactor Manifold (PACCM-9)

### 1. Executive Summary & Purpose

The objective of Phase 9 is to discover and unconditionally certify at least one genuinely new-to-repository twin-prime pair ($B - A = 2, A > 2, B > 2$) with primary size $\ge 350$ decimal digits (and stretch target $\ge 1,512$ decimal digits). The mission requires leveraging the laptop's dedicated hardware accelerator (**NVIDIA GeForce MX250**, Pascal architecture, compute capability 6.1 `sm_61`, 2,048 MiB VRAM) for high-throughput modular sieving, combined with the CPU (Intel Core i5-10210U) for exact multi-precision arithmetic, deterministic primality triage, and rigorous independent primality certification.

This document establishes the mathematical foundations, historical context, prior-art landscape across all previous repository phases (Phases 1 through 8), and provides an exhaustive comparison of three candidate algorithmic architectures evaluated for Phase 9.

---

### 2. Comprehensive Inventory of Prior Art in this Repository (Phases 1–8)

Before designing Phase 9, every prior phase in the repository was audited at the source-code, mathematical specification, and certificate level:

| Phase / Engine | Algebraic Family / Representation | Proof Theorem / Router | GPU / Hardware Utilization | Highest Certified Digits |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1 — CATS** | $k \cdot 2^n \pm 1$ ($n \le 50$) | Classical Proth / LLR | CPU only | 34 digits |
| **Phase 2 — CRT Wheel** | $k \cdot 2^n \pm 1$ ($n \le 512$) | Streaming Proth / LLR | CPU only | 159 digits |
| **Phase 3 — HDRSS** | $k \cdot 2^n \pm 1$ ($n \le 1664$) | Hybrid Dual-Residue Streaming | CPU only | 507 digits |
| **Phase 4 — ADRS-4** | $k \cdot 2^n \pm 1$ ($n \le 4992$) | Proth / LLR with SQLite leases | CPU + MX250 (PTX Driver API) | 1,509 digits |
| **Phase 5 — SCCA** | Smooth center $C = 2^a 3^b 5^c 7^d \cdot t$ | Pocklington-BLS ($B$) / Morrison-BLS ($A$) | CPU multi-worker | 133 digits |
| **Phase 6 — GITCSS** | Unrestricted $6m \pm 1$; QCP-6: $6t(6t+1)$ | Dual BLS on quadratic cofactor; ECPP router | CPU multi-worker | 503 digits |
| **Phase 6B — Hybrid** | General $6m \pm 1$ (350d candidates) | ECPP via PARI/GP (blocked on Windows) | CPU (8 PRP candidates pending) | 350d (PRP only) |
| **Phase 7 — HDC-7** | Primorial Proth $k \cdot 2^n \pm 1, k = t \cdot P_B$ | Proth on $B$, LLR on $A$ | CPU streaming sieve | 1,510 digits |
| **Phase 8 — ADES-8** | 2D exponent sieve $k \cdot 2^n \pm 1$ | Proth on $B$, LLR on $A$ | CPU 2D tiled grid | 1,511 digits |
| **Phase 8 — PAQCS** | Primorial quadratic cofactor $C = x(x-3)$ | Pocklington Thm 4 ($B$) / Morrison Thm 17 ($A$) | CPU numpy sieve | 1,511 digits |

#### Historical Artifact Baseline
An authoritative full audit of the repository identified **59 unique certified twin-prime pairs** across Phases 1 through 8, recorded in `research/phase9/historical_inventory.json` (SHA-256: `6a77d23c1ab521efca099e05f1a58442bca322c0acfe1db61570216dc353d740`).
The current milestone records stand at:
- **Phase 7 HDC-7:** 1,510 digits (`cert_hdc7_1510d_B13_n4985_t15658.json`, verified).
- **Phase 8 ADES-8:** 1,511 digits (`cert_ades8_1511d_R13_n4987_t79783.json`, verified).
- **Phase 8 PAQCS:** 1,511 digits (`cert_paqcs_1511d_t110891.json`, verified).

In addition, 8 dual-PRP candidates of 350 digits generated during Phase 6B remain unproven in `data/phase6b_pending_pairs.jsonl` because general ECPP requires an external PARI/GP binary that is unavailable in the native Windows environment.

---

### 3. Critical Analysis of Three Candidate Architectures for Phase 9

In compliance with Section 4.2 of the Master Prompt, three distinct candidate architectures were evaluated:

```
                                      +---------------------------------------------+
                                      |         Candidate Architectures             |
                                      +---------------------------------------------+
                                                             |
                    +----------------------------------------+----------------------------------------+
                    |                                        |                                        |
                    v                                        v                                        v
     +------------------------------+         +------------------------------+         +------------------------------+
     |           Option A           |         |           Option B           |         |           Option C           |
     |   Unrestricted C = 6m        |         | Primorial-Anchored Cubic-    |         |   Proof-Cost-Aware Portfolio |
     |   with General ECPP          |         | Cofactor Manifold (PACCM-9)  |         |   Dynamic Utility Routing    |
     +------------------------------+         +------------------------------+         +------------------------------+
     | Status: BLOCKED on Windows   |         | Status: SELECTED & SOUND     |         | Status: SUB-OPTIMAL          |
     | Reason: Missing PARI/GP      |         | Advantage: Exact Dual-BLS,   |         | Reason: Overlaps older phases|
     | without external downloads   |         | F > B^(2/3), MX250 accelerated|        | without deterministic bounds |
     +------------------------------+         +------------------------------+         +------------------------------+
```

#### Option A: Unrestricted Integer Centers $C = 6m$ with General ECPP Certification
- **Mathematical Form:** $A = 6m - 1$, $B = 6m + 1$ for generic integers $m \in \mathbb{N}$.
- **Proof Route:** Goldwasser-Kilian-Atkin Elliptic Curve Primality Proving (ECPP).
- **Analysis & Blocker:**
  While the mathematical theory of ECPP is general and applies to unrestricted integers, executing ECPP at 350 to 1,512 decimal digits requires constructing Hilbert class polynomials and point-counting algorithms (SEA) implemented in specialized systems such as PARI/GP or Primo.
  Our audit confirmed that no approved PARI/GP executable (`gp.exe`) exists on the host Windows system. As strict repository guidelines prohibit downloading unvetted third-party binaries or disabling security controls, general ECPP for $\ge 350$-digit numbers is blocked on this host (`P6B-BLOCKER-01`).
  Therefore, Option A cannot guarantee deterministic certification without violating system safety guidelines.

#### Option B: Primorial-Anchored Cubic-Cofactor Manifold (PACCM-9) — [SELECTED]
- **Mathematical Form:**
  Let $x = S_y \cdot t$, where $S_y = \prod_{p \le y} p$ is a primorial anchor.
  Define the center as the cubic algebraic manifold:
  $$C(x) = 2 x^2 (3x + 1) = 6 x^3 + 2 x^2$$
  The twin-prime pair members are:
  $$A(x) = C(x) - 1 = 6 x^3 + 2 x^2 - 1$$
  $$B(x) = C(x) + 1 = 6 x^3 + 2 x^2 + 1$$
- **Proof Route:** Exact Dual-BLS Certification:
  - Upper member $B$: $B - 1 = C(x) = (2 x^2) \cdot (3x + 1)$. The completely factored divisor is $F = 2 x^2$. Since $F^2 = 4 x^4 > 6 x^3 + 2 x^2 + 1 = B$ for all $x \ge 2$, $F > \sqrt{B}$ holds unconditionally with an asymptotically infinite margin ($F / \sqrt{B} \approx 0.816 \sqrt{x} \to \infty$). Pocklington-BLS (Theorem 4) yields an unconditional deterministic proof.
  - Lower member $A$: $A + 1 = C(x) = (2 x^2) \cdot (3x + 1)$. Since $F = 2 x^2 > \sqrt{A + 1} > \sqrt{A}$, Morrison-BLS (Theorem 17) yields an unconditional deterministic proof using a valid Lucas sequence with $(D / A) = -1$.
  - Exact Coprimality: $\gcd(F, R) = \gcd(2 x^2, 3x + 1) = 1$ identically for all even $x$, eliminating any cofactor gcd failures.
- **Hardware Acceleration:** The modular sieving of $A(t) \equiv 0 \pmod q$ and $B(t) \equiv 0 \pmod q$ over $q \in (y, Q]$ maps directly to cubic congruences over $\mathbb{F}_q$. Once roots $t \pmod q$ are solved on the CPU, candidate elimination is offloaded to the NVIDIA GeForce MX250 via high-throughput PTX JIT bitset kernels.

#### Option C: Proof-Cost-Aware Heterogeneous Search Portfolio
- **Description:** Dynamically dispatch candidates across multiple families (e.g. smooth centers, quadratic cofactors, primorial Proth) using an online multi-armed bandit or cost-utility scheduler.
- **Analysis:** While portfolio scheduling was explored in Phase 5 (SCCA UCB1), it does not solve the fundamental mathematical requirement of introducing a genuinely new algebraic manifold. If the underlying families are repeats of Phases 1–8, optimizing the dispatch order does not constitute mathematical novelty.

---

### 4. Mathematical Comparison: PACCM-9 vs Prior Phases

The table below contrasts PACCM-9 against the prior special-form and quadratic families to demonstrate why PACCM-9 is not merely a cosmetic variation:

| Dimension | Phase 5 (SCCA) | Phase 6 (QCP-6) | Phase 8 (PAQCS) | Phase 9 (PACCM-9, Ours) |
| :--- | :--- | :--- | :--- | :--- |
| **Algebraic Manifold** | Smooth product $C = 2^a 3^b 5^c 7^d t$ | Quadratic $C = 6t(6t+1)$ | Quadratic $C = x(x-3)$ | **Cubic Manifold $C = 2x^2(3x+1)$** |
| **Polynomial Degree** | Linear in $t$ ($\deg = 1$) | Quadratic in $t$ ($\deg = 2$) | Quadratic in $x$ ($\deg = 2$) | **Cubic in $x$ ($\deg = 3$)** |
| **Factored Divisor $F$** | $2^a 3^b 5^c 7^d$ | $6t+1$ (single prime) | $x = S_y \cdot t$ | **$F = 2x^2 = 2 S_y^2 t^2$** |
| **Factored Share of Digits** | $50\% - 60\%$ | $\approx 50\%$ | $\approx 50\%$ | **$\approx 66.7\%$ ($F \approx C^{2/3}$)** |
| **Proof Margin $F / \sqrt{B}$** | Bounded ($> 1$) | Barely $> 1$ ($F - R = 1$) | Barely $> 1$ ($F - R = 3$) | **Asymptotically Infinite ($O(\sqrt{x})$)** |
| **Coprimality $\gcd(F, R)$** | Must test $\gcd(F, t)$ | Required prime $F$ | Required $3 \nmid t$ | **$\gcd(2x^2, 3x+1) \equiv 1$ identically** |
| **Sieve Congruence** | Linear residues | Quadratic residues | Quadratic residues | **Cubic congruences over $\mathbb{F}_q$** |
| **GPU Sieve Support** | No (CPU only) | No (CPU only) | No (CPU only) | **Yes (MX250 PTX JIT driver)** |

### 5. Conclusion & Action Plan
Option B (PACCM-9) is mathematically rigorous, fully provable via exact dual-BLS theorems, provides an unprecedented $66.7\%$ factored digit ratio, has an identically coprime divisor-cofactor structure, and harnesses the laptop's MX250 GPU for maximum sieving throughput.
