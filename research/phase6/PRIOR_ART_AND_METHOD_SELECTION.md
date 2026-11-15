# Phase 6 Prior-Art Review and Method Selection (QCP-6 & Method R)

**Document ID:** `PHASE6-PRIOR-ART-003`  
**Date:** 2026-11-15T11:40:00+06:00  
**Phase:** Phase 6 (Method Q and Method R)  
**Authors:** Antigravity Autonomous Number Theory Research Engine  

---

## 1. Context and Problem Statement

Twin prime searches across computational number theory and prior phases of this repository have historically operated in special algebraic domains:
- **Phases 1–4 (CATS, CRT, HDRSS, ADRS-4):** Focused exclusively on the Proth/Riesel exponential family $p = k \cdot 2^n \pm 1$ with fixed small multipliers $k$ and varying exponents $n$. Primality testing used Proth's theorem on $B$ and the Lucas-Lehmer-Riesel (LLR) recurrence on $A$.
- **Phase 5 (SCCA):** Shifted to linear smooth centers $C = F \cdot t$, where $F = 2^{e_2} 3^{e_3} 5^{e_5} 7^{e_7}$ was a massive fixed smooth multiplier (e.g. 130+ digits) and $t$ was searched linearly.
- **Phase 6 Early GITCSS Attempt:** Attempted unstructured general integer centers $C = 6m$. Because $6m \pm 1$ has no prescribed algebraic factors, unconditional certification at $\ge 100$ digits required general-purpose ECPP (Primo or PARI/GP), which was blocked on Windows systems under Application Control policies.

**Method Q (QCP-6)** resolves this limitation by introducing a **quadratic co-factor family**:
$$x = S \cdot t, \qquad C = x(x - h), \qquad A = x^2 - hx - 1, \qquad B = x^2 - hx + 1$$
Here, the proven proof factor $F = x = S \cdot t$ grows dynamically with the candidate $t$, eliminating the need to construct a huge fixed smooth multiplier for every narrow interval, while maintaining $F > \sqrt{B}$ and $F - 1 > \sqrt{A}$.

---

## 2. Prior-Art Survey: Mathematical Foundations

| Theorem / Method | Canonical Reference | Role in Phase 6 | Prior Art Status | Existing in Repo? | What is NOT Novel |
|---|---|---|---|---|---|
| **Quadratic Modular Roots** | Tonelli (1891), Shanks (1973) | Solves $x^2 - hx \pm 1 \equiv 0 \pmod q$ for sieve forbidden residues | Standard classical algorithm | Used in number theory libraries | Root solving itself |
| **Segmented Sieve of Eratosthenes** | Bays & Hudson (1977), Sorenson (1998) | High-throughput bitset screening across $j$-blocks | Industry standard | Used in Phases 1–5 for $k$ and $t$ | Segmented array marking |
| **Pocklington Primality Theorem** | Pocklington (1914), BLS (1975) Thm 4 | Unconditional proof of upper member $B$ using factored $F \mid (B-1)$ | Foundational number theory | Used in Phase 5 on $B$ | Mathematical theorem |
| **Morrison Lucas Sequence Rank Test** | Morrison (1975), BLS (1975) Thm 17 | Unconditional proof of lower member $A$ using factored $F \mid (A+1)$ | Foundational number theory | Used in Phase 5 on $A$ | Mathematical theorem |
| **Quadratic Co-Factor Manifold (Method Q)** | Formulated in Phase 6 | Simultaneous algebraic factor $F = x$ dividing both $B-1$ and $A+1$ with $F > \sqrt{B}$ | **Novel Synthesis in Repository** | First introduced in Phase 6 | Sieve and BLS individually |

---

## 3. Algorithmic Differentiation vs Prior Phases

1. **Departure from Exponential Forms:**
   Unlike Phases 1–4, 7, and 8 which rely on $k \cdot 2^n \pm 1$, Phase 6 Method Q uses quadratic integer polynomials $x^2 - hx \pm 1$. The exponent of 2 does not dominate the candidate size; rather, the candidate size is governed by $x \approx \sqrt{B}$.
2. **Dynamic vs Fixed Smooth Multipliers:**
   Unlike Phase 5 SCCA which required a gigantic precomputed static smooth product $F$ (which restricted $t$ to small ranges before losing smooth dominance), Method Q uses an anchor $S$ and parameter $t$ where $x = S \cdot t$. Factorization of $x$ is trivial because $S$ is built from verified 64-bit primes and $t$ is small.
3. **Simultaneous Dual BLS Factor Alignment:**
   Because $B - 1 = x(x - h)$ and $A + 1 = x(x - h)$, both members share the *exact same* primary proof factor $F = x$. Since $x^2 > x^2 - hx + 1 = B > A$, both size conditions $F > \sqrt{B}$ and $(F-1)^2 > A$ are satisfied unconditionally for all $t \ge 1, h \ge 3$.

---

## 4. Evaluation of Method R (Direct Interval Search)

Method R parameterizes arbitrary centers as $C_j = C_0 + 6j$, with $A = C_j - 1$ and $B = C_j + 1$.
- **Sieve Efficiency:** Outstanding throughput ($>1.5 \times 10^7$ centers/sec) using two forbidden residues $j \equiv (\pm 1 - C_0) 6^{-1} \pmod q$.
- **Certification Bottleneck:** For arbitrary centers $C_0 + 6j$ at $\ge 100$ digits, $A - 1 = C_0 + 6j - 2$ and $B - 1 = C_0 + 6j$ possess no known algebraic factors. General integer factoring (GNFS/ECM) is completely infeasible within local compute budgets, and general ECPP engines (PARI/GP, Primo) are unavailable on the host environment due to Windows Application Control restrictions.
- **Role in Phase 6:** Method R is retained as an audited high-throughput screening engine and benchmark comparator, while Method Q is selected as the primary discovery and certification engine.
