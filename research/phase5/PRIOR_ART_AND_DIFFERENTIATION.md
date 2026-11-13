# Phase 5 Prior Art & Algorithmic Differentiation

**Date:** 2026-11-13  
**Authors:** Computational Number Theory & Algorithm Design Group (Antigravity Research)  
**Status:** Architecture Review Deliverable

---

## 1. Prior Art Foundations

The Smooth-Center Certificate-Aware Search (SCCA) engine synthesizes classical theorems from analytic and computational number theory into a modern streaming portfolio search:

1. **Brillhart, Lehmer, and Selfridge (BLS, 1975):**
   *Citation:* J. Brillhart, D. H. Lehmer, and J. L. Selfridge, *"New primality criteria and factorizations of $2^m \pm 1$"*, *Mathematics of Computation*, Vol. 29, No. 130, April 1975, pp. 620–647.
   *Used here:* Theorem 4 ($N-1$ Pocklington criterion) for unconditional certification of $B = C + 1$; Theorem 17 ($N+1$ Lucas criterion) for unconditional certification of $A = C - 1$.
2. **Morrison (1975):**
   *Citation:* M. A. Morrison, *"A note on primality testing using Lucas sequences"*, *Mathematics of Computation*, Vol. 29, No. 129, January 1975, pp. 181–182.
   *Used here:* Direct application of Lucas sequences to factorized $N+1$ bounds.
3. **Hardy & Littlewood (1923):**
   *Citation:* G. H. Hardy and J. E. Littlewood, *"Some problems of 'Partitio Numerorum'; III: On the expression of a number as a sum of primes"*, *Acta Mathematica*, 44 (1923), pp. 1–70.
   *Used here:* Asymptotic twin-prime constant $C_2 \approx 0.6601618$ and sieve survival density estimations.

---

## 2. Systematic Differentiation Across Repository Phases

The table below contrasts Phase 5 against all previous iterations in the repository:

| Dimension | Phase 1 (CATS) | Phase 2 (CRT Wheel) | Phase 3 (HDRSS) | Phase 4 (ADRS-4) | **Phase 5 (SCCA)** |
|---|---|---|---|---|---|
| **Center Representation** | $C = k \cdot 2^n$ ($n$ fixed) | $C = k \cdot 2^n$ ($k$ wheel) | $C = k \cdot 2^n$ ($k$ stream) | $C = (6t+3) \cdot 2^n$ | **$C = F \cdot t = 2^a \cdot 3^b \cdot 5^c \cdot 7^d \cdots t$** |
| **Factorization Structure** | Monolithic power of 2 ($2^n$) | Monolithic power of 2 ($2^n$) | Monolithic power of 2 ($2^n$) | Monolithic power of 2 ($2^n$) | **Multi-prime smooth product ($F_{odd}$ factored)** |
| **Sieve Search Domain** | Multiplier $k$ stride | Wheel mod $W$ on $k$ | Dual-residue bitset on $k$ | Compact parameter $t$ block | **Admissible classes $t \not\equiv \pm F^{-1} \pmod q$ ($q \nmid F$)** |
| **Upper Member Proof ($B$)** | Proth's theorem | Proth's theorem | Proth's theorem | Proth's theorem | **Pocklington / BLS 1975 Theorem 4 ($N-1$)** |
| **Lower Member Proof ($A$)** | LLR ($n-2$ squarings) | Fast Lucas ladder | Matrix Lucas LLR | LLR + Rodseth parameters | **Morrison / BLS 1975 Theorem 17 ($N+1$)** |
| **Algebraic Constraint** | $k < 2^n$ mandatory | $k < 2^n$ mandatory | $k < 2^n$ mandatory | $k < 2^n$ mandatory | **$F_{odd} > 2^a t$ (no fixed power-of-2 bound)** |
| **Scheduling Architecture** | Sequential batch | Static grid | Streaming worker | Work-unit SQLite WAL | **Multi-family Bandit UCB1 portfolio scheduler** |
| **Hardware Target** | CPU single-core | CPU multi-thread | CPU multi-thread | CPU + NVIDIA MX250 PTX | **Portable arbitrary-precision CPU (gmpy2/Py)** |
| **Certificate Schema** | Schema 1.0 (loose) | Schema 2.0 | Schema 3.0 | Schema 4.0 | **Schema 5.0 (Canonical SHA-256 + 2-sided proofs)** |

---

## 3. What Was Reused vs. What Was Replaced

### 3.1 Reused Infrastructure (with appropriate attribution)
1. **Durable WAL Ledger Pattern:** The transactional SQLite WAL architecture from Phase 4 was adapted to manage Phase 5 multi-family work units and candidate progression.
2. **First-Principles Matrix Verification:** The independent verification principle using $2 \times 2$ integer matrices was retained for the standalone checker, completely isolated from runtime search modules.

### 3.2 What Was Replaced and Why
1. **Replaced Proth / LLR Proof Engine:**
   - *Problem:* Proth and LLR strictly require the candidate form $k \cdot 2^n \pm 1$ with $k < 2^n$. This prevented searching smooth centers containing powers of 3, 5, 7, etc.
   - *Replacement:* Pocklington Theorem 4 ($N-1$) and Morrison Theorem 17 ($N+1$), which accept any known factored component $F_{odd} > \sqrt{N}$.
2. **Replaced Single-Family Sieve:**
   - *Problem:* Previous sieves hardcoded powers of 2 into modular residues.
   - *Replacement:* SCCA Method S1 calculates modular inverses $F^{-1} \pmod q$ for any arbitrary composite smooth center, eliminating residues $t \equiv \pm F^{-1} \pmod q$.
3. **Replaced Static Search Allocation:**
   - *Problem:* Hardcoded parameter ranges frequently hit barren density bands.
   - *Replacement:* Method S2 multi-family bandit scheduler (UCB1) balances exploratory allocations against high-yielding smooth families dynamically.
