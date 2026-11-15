# Phase 6 Proof System Selection & Verification Architecture

**Document ID:** `PHASE6-PROOF-SELECT-001`  
**Date:** 2026-11-15T11:42:00+06:00  
**Phase:** Phase 6 (Method Q and Method R)  
**Authors:** Antigravity Autonomous Number Theory Research Engine  

---

## 1. Candidate Proof Systems Evaluated

| Proving System | Mathematical Basis | Certificate Format | Local Availability & Feasibility | Verdict |
|---|---|---|---|---|
| **Probable Prime (MR + BPSW)** | Fermat / Baillie-PSW | None (Boolean only) | Fully available via `gmpy2` / `sympy` | **Filter Only** (Disallowed as proof by mission brief) |
| **APR-CL** | Jacobi sums in cyclotomic fields | None standard / Large matrix logs | No standalone Python verifier; slow at 500+ digits | **Rejected** for primary pipeline |
| **ECPP (Goldwasser-Kilian-Atkin)** | Elliptic curve point counting & group orders | Downward recursive curve point chain | Host lacks trusted native `gp.exe` / `Primo` binary under Windows security policies | **Audited / Secondary** (Verifier implemented in `scripts/phase6b_ecpp_verify.py`) |
| **Pocklington (BLS Theorem 4)** | Order of units in $(\mathbb{Z}/B\mathbb{Z})^*$ with factored $F \mid (B-1)$ | Compact witness $a$, prime factors $q_i$, GCD checks | Native Python arbitrary precision; instantaneous verification | **Selected** for upper member $B$ |
| **Morrison (BLS Theorem 17)** | Rank of appearance in Lucas sequence with factored $F \mid (A+1)$ | Parameter $P$, discriminant $D$, companion matrix Lucas terms | Native Python arbitrary precision; companion matrix powering | **Selected** for lower member $A$ |

---

## 2. Mathematical Formalism of Selected Proof System

### 2.1 Upper Member: Brillhart-Lehmer-Selfridge (1975) Theorem 4
Let $B > 2$ be an odd integer with $B - 1 = F \cdot R$, where $F$ is completely factored into distinct primes:
$$F = \prod_{i=1}^k q_i^{e_i}$$
If:
1. $F > \sqrt{B}$ (Size Condition);
2. There exists an integer $a \ge 2$ such that $a^{B-1} \equiv 1 \pmod B$ (Fermat Condition);
3. For each prime divisor $q_i \mid F$:
   $$\gcd\left(a^{(B-1)/q_i} - 1, B\right) = 1 \quad \text{(Coprimality Condition)}$$
Then every prime factor of $B$ is $\equiv 1 \pmod F$, and since $F > \sqrt{B}$, $B$ is unconditionally prime.

### 2.2 Lower Member: Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison)
Let $A > 2$ be an odd integer with $A + 1 = F \cdot R'$, where $F$ is factored as above.
Let $U_n(P, Q)$ be the Lucas sequence with parameters $P \ge 3, Q = 1$, discriminant $D = P^2 - 4$.
If:
1. $\gcd(A, 2D) = 1$ and Jacobi symbol $\left(\frac{D}{A}\right) = -1$;
2. $(F - 1)^2 > A$ (Size Condition);
3. $U_{A+1}(P, 1) \equiv 0 \pmod A$ (Lucas Zero Congruence);
4. For each prime factor $q_i \mid F$:
   $$\gcd\left(U_{(A+1)/q_i}(P, 1), A\right) = 1 \quad \text{(Rank Maximality Condition)}$$
Then $A$ is unconditionally prime.

---

## 3. Structural Satisfaction in Method Q

In Method Q:
$$x = S \cdot t, \qquad A = x^2 - hx - 1, \qquad B = x^2 - hx + 1$$
$$B - 1 = x(x - h) \implies x \mid (B - 1)$$
$$A + 1 = x(x - h) \implies x \mid (A + 1)$$
Setting proof factor $F = x$:
- **Size on $B$:** Since $h \ge 3$ and $x > h$, $B = x^2 - hx + 1 < x^2$, which implies:
  $$F = x > \sqrt{B} \quad \text{strictly holds!}$$
- **Size on $A$:** Similarly, $A = x^2 - hx - 1 < (x-1)^2$ for $h \ge 3$, which implies:
  $$(F - 1)^2 = (x - 1)^2 > A \quad \text{strictly holds!}$$
- **Factorization:** $x = S \cdot t$. The anchor $S$ is composed of deterministic 64-bit primes $p_i$, each certified by deterministic 7-base Miller-Rabin with provably zero pseudoprimes below $2^{64}$. The parameter $t$ is factored completely by deterministic trial division. Thus, $F$ is 100% prime factored with full certificates of factor primality.

---

## 4. Decoupled Independent Verifier Architecture

The standalone verifier `scripts/phase6_independent_verify.py`:
1. **Zero External Imports:** Imports only `sys`, `json`, `math`, `hashlib`, `datetime`, `pathlib`. Absolutely no dependencies on `sympy`, `gmpy2`, or project source code.
2. **Companion Matrix Powering:** Computes $U_k(P, 1) \pmod A$ using binary exponentiation of the $2 \times 2$ matrix:
   $$\begin{pmatrix} P & -1 \\ 1 & 0 \end{pmatrix}^k \pmod A$$
3. **Jacobi Symbol:** Computed from first principles using quadratic reciprocity law without floating-point arithmetic.
4. **Canonical SHA-256 Digest:** Verifies the cryptographic hash of the JSON payload before issuing a signed attestation JSON artifact.
