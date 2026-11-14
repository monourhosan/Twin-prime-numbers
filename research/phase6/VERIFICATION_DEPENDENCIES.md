# Phase 6 Verification Dependencies & Proof Strategy

**Date:** 14 November 2026  
**Auditor:** Antigravity Autonomous Research & Verification Agent  
**Focus:** Elliptic Curve Primality Proving (ECPP) & General Integer Verification  

---

## 1. The General Integer Primality Challenge

In earlier project phases, primality proving exploited algebraic factorizations of $N - 1$ or $N + 1$:
- **Phases 1–4:** $N \pm 1 = k \cdot 2^n$ (Proth and Riesel theorems factor completely into powers of 2).
- **Phase 5:** $N \pm 1 = F \cdot t$ (smooth center family, where $F$ is pre-factored by design).

In **Phase 6**, centers are general unrestricted integers:
\[
A = 6m - 1, \quad B = 6m + 1.
\]
For $m \approx 10^{349}$, $6m \pm 1$ are general 350-digit integers with no known algebraic factors.
To prove $A$ and $B$ prime unconditionally, BLS Theorem 4 or Theorem 17 require finding prime factors of $6m$ that multiply to $> \sqrt{N} \approx 10^{175}$.
Factoring general 350-digit integers into factors of size $10^{175}$ is completely intractable with existing general factoring algorithms (GNFS would require decades of compute).

**Conclusion:** The only computationally viable method for general 350–450-digit primality proving is **Elliptic Curve Primality Proving (ECPP)**.

---

## 2. Survey of Mature ECPP Tools

| Tool | Author / Maintainer | Version | License | Output Format | Platform Compatibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primo** | Marcel Martin | 4.3.3 | Freeware (Closed source) | Standard Primo certificate (`.out`) | Linux x86_64, Windows (GUI/CLI) |
| **Pari/GP** | PARI Group (Bordeaux) | 2.15+ | GNU GPLv2+ | `primecert` certificate | Linux, macOS, Windows |
| **FLINT** | William Hart et al. | 3.1+ | GNU LGPLv2.1+ | Fast C library | POSIX, MinGW |
| **SageMath** | Sage Community | 10.4+ | GNU GPLv2+ | ECPP Python/Cython wrapper | Linux, WSL |

---

## 3. Local Environment Blockers (`P6-BLOCKER-01`)

1. **Host Application Control Policies:**
   In restricted or sandboxed Windows environments, executing unsigned third-party native binaries (such as `primo.exe`) triggers Windows Defender / Application Control blockades.
2. **Pure Python ECPP Gap:**
   Neither Python's standard library nor pure-Python packages provide an ECPP certificate generator capable of completing 350-digit curve searches within practical local execution limits.
3. **Stand-down Policy:**
   Until an open-source, reproducible ECPP prover (such as Pari/GP or a verified C-extension) is integrated and whitelisted, all 350–450-digit candidates found by GITCSS screening **must remain categorized as `PRP_BOTH`**.
   Under **Non-Negotiable Rule 4**, no candidate may be promoted to `PROVEN_PRIME` or `VERIFIED_BOTH` without an independently verified proof artifact.
