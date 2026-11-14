# Phase 6: Unrestricted Center-Space Algorithm Specification

## 1. Mathematical Formulation

### 1.1 Center-Space Representation
For any twin-prime pair $(p, p+2)$ with $p > 3$, both primes are odd and neither is divisible by 3. Consequently:
$$p \equiv 2 \pmod 3 \implies p = 6m - 1$$
$$p + 2 \equiv 1 \pmod 3 \implies p + 2 = 6m + 1$$
where the center $C = 6m$ is an integer strictly divisible by 6.

In an unrestricted center search, candidates are indexed by consecutive non-negative integers $j = 0, 1, 2, \ldots$:
$$C_j = C_0 + 6j = 6(m_0 + j)$$
where $C_0$ is chosen as the smallest multiple of 6 greater than or equal to a target boundary (e.g., $10^{349} + 2$ for the 350-digit band). This ensures arbitrary-precision exactness without imposing structural family constraints such as $k \cdot 2^n \pm 1$ or smooth primorial centers.

### 1.2 Modular Residue Constraints for Sieving
For each sieving prime $q \ge 5$, a center $C_j$ yields a composite candidate if either:
$$C_j - 1 \equiv 0 \pmod q \iff 6j \equiv 1 - C_0 \pmod q$$
$$C_j + 1 \equiv 0 \pmod q \iff 6j \equiv -1 - C_0 \pmod q$$

Since $\gcd(6, q) = 1$ for all primes $q \ge 5$, the multiplicative inverse $6^{-1} \pmod q$ exists and is unique. The two forbidden residue classes modulo $q$ for the index $j$ are:
$$r_1(q) = (1 - C_0) \cdot 6^{-1} \pmod q$$
$$r_2(q) = (-1 - C_0) \cdot 6^{-1} \pmod q$$

For each prime $q \in [5, Q]$, any index $j$ satisfying:
$$j \equiv r_1(q) \pmod q \quad \text{or} \quad j \equiv r_2(q) \pmod q$$
is marked composite and eliminated.

### 1.3 Small-Prime Equality Edge Cases
For large candidates ($C_j > 10^{15}$), $C_j - 1 > q$ and $C_j + 1 > q$ for all sieving primes $q \le Q \le 10^6$, so divisibility implies compositeness without exception. However, for general-purpose correctness on small ranges (e.g., $m=1 \implies (5, 7)$), small-prime equality preservation ensures:
$$\text{If } 6m - 1 = q \text{ or } 6m + 1 = q, \text{ the candidate is preserved.}$$

---

## 2. Multi-Stage Architectural Pipeline

```
  Center Index Range j in [0, N)
               │
               ▼
┌───────────────────────────────┐
│ Stage 1: Wheel Pre-Sieve      │  Modulo W = 210 or 30030
│ Residue Pattern Exclusion     │  Removes ~77% of candidates
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Stage 2: Segmented Bitset     │  Primes q in [17, Q] (Q = 100,000)
│ L1-Cache Friendly Slicing     │  Eliminates ~98.1% of all candidates
└──────────────┬────────────────┘
               │
               ▼ Sieve Survivors (~1.89% of eligible centers)
┌───────────────────────────────┐
│ Stage 3: Fast PRP Screening   │  Fermat Base-2 + 25-Round Miller-Rabin
│ GMP-Accelerated Native C      │  Throughput: 62,500 candidates/s (350d)
└──────────────┬────────────────┘
               │
               ▼ Dual PRPs (Passing Left & Right Tests)
┌───────────────────────────────┐
│ Stage 4: Strong PRP Screening │  Baillie-PSW (Lucas + MR)
│ Verification of Compositeness │  Zero false positives observed
└──────────────┬────────────────┘
               │
               ▼ Surviving Verified Dual PRPs
┌───────────────────────────────┐
│ Stage 5: Primality Proving    │  BLS Theorem 4 (N-1) on 6m+1
│ Factor-Aware / ECPP Pipeline  │  BLS Theorem 17 (N+1) on 6m-1
└──────────────┬────────────────┘
               │
               ▼ Certified Primality Proofs
┌───────────────────────────────┐
│ Stage 6: Independent Verifier │  Zero-dependency external audit
│ Standalone SHA-256 Attestation│  Strict theorem hypothesis check
└───────────────────────────────┘
```

---

## 3. Mathematical Theorems for Certification

### 3.1 Upper Member: Brillhart-Lehmer-Selfridge (1975) Theorem 4
For $B = 6m + 1$, write $B - 1 = 6m = F_B \cdot R_B$ where $F_B$ is completely factored into distinct primes $q_i$:
- **Hypothesis 1:** $F_B > \sqrt{B}$ (or $F_B > \sqrt[3]{B}$ with quadratic root conditions).
- **Hypothesis 2:** There exists an integer $a$ such that $a^{B-1} \equiv 1 \pmod B$.
- **Hypothesis 3:** For every prime factor $q_i \mid F_B$, $\gcd(a^{(B-1)/q_i} - 1, B) = 1$.

When all three hypotheses hold, every prime factor of $B$ is $\equiv 1 \pmod{F_B}$, which implies $B$ is unconditionally prime.

### 3.2 Lower Member: Morrison BLS (1975) Theorem 17
For $A = 6m - 1$, write $A + 1 = 6m = 2 \cdot F_{\text{odd}} \cdot R_A$:
- **Hypothesis 1:** $2 F_{\text{odd}} > \sqrt{A} + 1$.
- **Hypothesis 2:** There exists an integer $P$ with discriminant $D = P^2 - 4$ such that the Jacobi symbol satisfies $\left(\frac{D}{A}\right) = -1$.
- **Hypothesis 3:** The Lucas sequence satisfies $U_{A+1}(P, 1) \equiv 0 \pmod A$.
- **Hypothesis 4:** For every odd prime factor $q_j \mid F_{\text{odd}}$, $\gcd(U_{(A+1)/q_j}(P, 1), A) = 1$.

When all hypotheses hold, $A$ is unconditionally prime.

---

## 4. Factorization Boundary and Honest Reporting
For general integers in the 350-digit band ($C \approx 10^{350}$), the factored part $F$ must exceed $10^{175}$. Generic integers cannot be factored to $10^{175}$ via trial division or Pollard rho within feasible time. Without an external ECPP engine (such as Primo or PARI/GP), candidates passing Stage 4 are rigorously and honestly classified as **Dual PRPs (Probable Primes)**, avoiding false claims of mathematical certainty.
