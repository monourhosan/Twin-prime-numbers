# Phase 6 Prior-Art Review and Algorithmic Differentiation (QCP-6 & Method R)

**Document ID:** `PHASE6-PRIOR-ART-002`  
**Date:** 2026-11-14T11:39:00+06:00  
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
| **Quadratic Modular Roots** | Tonelli (1891), Shanks (1973) | Solves $x^2 - hx \pm 1 \equiv 0 \pmod q$ | Classical number theory (1891, 1973) | Used only for linear congruences in prior phases | Tonelli-Shanks algorithm and modular square roots are classical mathematics. |
| **Pocklington Primality Criterion** | Pocklington (1914); Brillhart, Lehmer, Selfridge (1975) Theorem 4 | Proves upper member $B = x^2 - hx + 1$ unconditionally using $F = x > \sqrt{B}$ | Classical primality criterion (1914, 1975) | Used in Phase 1 and Phase 5 | BLS Theorem 4 is a published, standard theorem; not a new result. |
| **Morrison Rank-Based Lucas $N+1$ Proof** | Morrison (1975), *Math. Comp.* 29, 181–182; BLS (1975) Theorem 17 | Proves lower member $A = x^2 - hx - 1$ unconditionally using $F - 1 > \sqrt{A}$ | Published standard theorem (1975) | Morrison sequence used in Phase 5 for smooth centers | Morrison's rank theorem and Lucas sequence divisibility are published classical mathematics. |
| **Bateman-Horn Heuristic** | Bateman & Horn (1962), *Math. Comp.* 16, 363–367 | Predicts candidate survivor rates for polynomial systems $f_1(t), f_2(t)$ | Published standard heuristic (1962) | Heuristic formulas used informally in Phase 4/5 | Bateman-Horn conjecture is well-known prior art; does not supply a deterministic proof. |
| **Segmented Sieve of Eratosthenes** | Bays & Hudson (1977); Sorenson (1998) | Packs candidate status into cache-sized bitset segments in $j$-space | Standard algorithmic technique | Used in Phase 1 (Rust) and Phase 5 (Python bitset) | Bitset segmentation is a standard software engineering technique. |
| **Dual BLS Primality Coupling** | Selfridge et al. (1975) | Proves both $A$ and $B$ using single factored kernel $x(x - h)$ | Known algebraic identity | Used in Phase 5 for $F \cdot t$ | Algebraic coupling of $N-1$ and $N+1$ is known in twin-prime literature. |

---

## 3. Algorithmic Differentiation: Method Q vs. Prior Phases

| Architectural Dimension | Phase 4 (ADRS-4) | Phase 5 (SCCA) | Prior Phase 6 (GITCSS) | **Phase 6 Method Q (QCP-6)** |
|---|---|---|---|---|
| **Candidate Form** | $k \cdot 2^n \pm 1$ | $F \cdot t \pm 1$ | $6m \pm 1$ | **$x(x - h) \pm 1$, $x = S \cdot t$** |
| **Parameter Space** | Exponent $n$ (linear/exponential) | Multiplier $t$ (linear on fixed $F$) | Center index $m$ (linear) | **Index $t$ in quadratic polynomials** |
| **Factorization Mechanism** | Exponential factor $2^n$ | Pre-generated massive smooth $F$ | Unfactored arbitrary $6m$ | **$S$ pre-factored proven primes, $t$ factored by trial division** |
| **Root Structure per Prime $q$** | Linear modular inverse | Linear modular inverse | Fixed residue classes $\pm 6^{-1}$ | **Quadratic roots ($D_A = 13, D_B = 5$) with $\rho(q) \in \{0, 1, 2, 4\}$** |
| **Proof Scalability** | Unbounded (LLR/Proth) | Requires new smooth $F$ per band | Blocked (requires ECPP) | **Scales smoothly with modest $t$ and factored anchor $S$** |
| **Independent Verification** | Python LLR check | Zero-dependency Morrison/Pocklington | Blocked by missing ECPP tool | **Zero-dependency 2x2 companion matrix Lucas check + Pocklington** |

---

## 4. Method R (General Integer Windows + ECPP Fallback)

Method R serves as the independent alternative route:
1. Picks a random anchor $C_0 \equiv 0 \pmod 6$ from OS randomness and logs the seed/manifest before searching.
2. Scans consecutive disjoint windows $C = C_0 + 6j$.
3. Uses dual-offset linear sieve: $j \equiv (\pm 1 - C_0) \cdot 6^{-1} \pmod q$.
4. Screens candidates with Miller-Rabin / BPSW PRP.
5. Certification requirement: Requires general ECPP certificates (`primecert`).
   - **Current Status in Windows Environment:** Because PARI/GP and Primo are blocked or unavailable on this system, Method R cannot emit certified primality proofs. As directed by the prompt, candidates from Method R are treated as `PRP_BOTH` only and never promoted to certified discoveries. Method Q is the designated primary discovery path.
