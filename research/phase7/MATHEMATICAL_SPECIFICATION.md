# Mathematical Specification: High-Density Primorial Proth/LLR Architecture (HDC-7)

**Author:** Google Antigravity (Computational Number Theory & Proof Audit Mission)  
**Date:** 2026-11-14  
**Target Milestone:** Exact Unconditional Proof of Fresh $\ge 1510$-Digit Twin Primes  

---

## 1. Research Hypothesis and Theoretical Motivation

The primary mission of Phase 7 is to discover and unconditionally certify at least one fresh twin-prime pair $P, Q$ with $\ge 1,510$ decimal digits per member ($Q - P = 2$).

### The Core Problem in General Integer Search at 1,510 Digits
At 1,510 digits ($\approx 10^{1509}$), general unrestricted integers have no known algebraic factorization. The Hardy-Littlewood asymptotic density of twin primes for centers $C \equiv 0 \pmod 6$ is:
$$\rho_6(C) \approx \frac{12 C_2}{(\ln C)^2} \approx \frac{12 \cdot 0.6601618}{(1509 \cdot \ln 10)^2} \approx \frac{7.9219}{(3474.6)^2} \approx 6.56 \times 10^{-7}.$$
Furthermore, general integers require Elliptic Curve Primality Proving (ECPP), which takes tens of minutes to hours per candidate member on consumer hardware and is blocked by local engine availability.

### The HDC-7 Solution
The HDC-7 (High-Density Certificate-Aware) architecture resolves both bottlenecks simultaneously:
1. **Algebraic Special Form:** Couples centers $C = k \cdot 2^n$ with $k < 2^n$, enabling $O(n \cdot M(n))$ deterministic, unconditional primality proofs via Proth's Theorem for $B' = C + 1$ and the Lucas-Lehmer-Riesel (LLR) Theorem for $A = C - 1$.
2. **Primorial Multiplier Conditioning:** Embeds an odd primorial multiplier $M_B = \prod_{3 \le p \le B} p$ into the multiplier $k = M_B(2t + 1)$. This guarantees that neither $A$ nor $B'$ can be divisible by any prime $p \le B$, conditioning out composite factors before sieving even starts.

---

## 2. Parameterization and Exact Boundaries

### 2.1 Multiplier and Candidate Formulation
Let $B \ge 3$ be an odd integer bound. The odd primorial multiplier is defined as:
$$M_B = \prod_{\substack{3 \le p \le B \\ p \text{ prime}}} p.$$

For integer index $t \ge 0$:
$$k = M_B \cdot (2t + 1).$$
Candidate center:
$$C = k \cdot 2^n = M_B \cdot (2t + 1) \cdot 2^n.$$
Candidate twin pair:
$$A = C - 1 = k \cdot 2^n - 1, \qquad B' = C + 1 = k \cdot 2^n + 1.$$

### 2.2 Divisibility Exclusion Lemma
**Lemma 1:** *For any prime $p \le B$, $p \nmid A$ and $p \nmid B'$.*
*Proof:*
- For $p = 2$: $C = k \cdot 2^n$ with $n \ge 2$, so $C \equiv 0 \pmod 2$. Thus $A \equiv -1 \equiv 1 \pmod 2$ and $B' \equiv 1 \pmod 2$. Both are odd integers coprime to 2.
- For an odd prime $p \le B$: $p \mid M_B$, which implies $p \mid k$ and $p \mid C$. Thus $A = C - 1 \equiv -1 \pmod p \not\equiv 0 \pmod p$, and $B' = C + 1 \equiv 1 \pmod p \not\equiv 0 \pmod p$.
- For $D \ge 1510$, $A > B \ge p$. Hence $A$ and $B'$ cannot equal $p$. Therefore $\gcd(A, p) = 1$ and $\gcd(B', p) = 1$. $\blacksquare$

### 2.3 Exact Integer Digit Bounding
To guarantee that both members have **exactly** $D$ decimal digits without floating-point edge inaccuracies:
$$10^{D-1} \le A < B' < 10^D.$$
Since $A = C - 1$ and $B' = C + 1$, the exact integer condition is:
$$10^{D-1} + 1 \le C \le 10^D - 2.$$

Given $C = k \cdot 2^n$, the allowable $k$ interval is:
$$k_{min} = \left\lceil \frac{10^{D-1} + 1}{2^n} \right\rceil, \qquad k_{max} = \min\left( \left\lfloor \frac{10^D - 2}{2^n} \right\rfloor, 2^n - 1 \right).$$

For $k = M_B(2t + 1)$, let $odd_{min}$ be the smallest odd integer $\ge \lceil k_{min} / M_B \rceil$, and $odd_{max}$ be the largest odd integer $\le \lfloor k_{max} / M_B \rfloor$.
The exact half-open search interval for index $t$ is:
$$t \in [t_{min}, t_{max} + 1), \quad \text{where } t_{min} = \frac{odd_{min} - 1}{2}, \quad t_{max} = \frac{odd_{max} - 1}{2}.$$

---

## 3. First-Principles Derivation of Modular Roots in Compact $t$-Space

Let $r$ be a sieve prime such that $r \nmid 2 M_B$ (i.e. $r > B$). We find all indices $t$ such that $r \mid A$ or $r \mid B'$.

### 3.1 Lower Candidate $A = C - 1 \equiv 0 \pmod r$
$$M_B(2t + 1) 2^n \equiv 1 \pmod r.$$
Let $\alpha = (M_B \cdot 2^n) \bmod r$. Since $r \nmid 2 M_B$, $\gcd(\alpha, r) = 1$. Thus $u = \alpha^{-1} \pmod r$ exists uniquely.
$$2t + 1 \equiv u \pmod r \implies 2t \equiv u - 1 \pmod r \implies t \equiv (u - 1) \cdot 2^{-1} \pmod r.$$
We define the root:
$$t_{plus} = ((u - 1) \cdot 2^{-1}) \bmod r.$$
When $t \equiv t_{plus} \pmod r$, $C \equiv 1 \pmod r$, so $A = C - 1$ is divisible by $r$.

### 3.2 Upper Candidate $B' = C + 1 \equiv 0 \pmod r$
$$M_B(2t + 1) 2^n \equiv -1 \pmod r \implies 2t + 1 \equiv -u \pmod r \implies 2t \equiv -u - 1 \pmod r.$$
We define the root:
$$t_{minus} = ((-u - 1) \cdot 2^{-1}) \bmod r.$$
When $t \equiv t_{minus} \pmod r$, $C \equiv -1 \pmod r$, so $B' = C + 1$ is divisible by $r$.

### 3.3 Sieve Strategy
In compact $t$-space:
- A bitset of length $L = t_{max} - t_{min} + 1$ represents candidate indices $t \in [t_{min}, t_{max}]$.
- For each sieve prime $r \in (B, S_{depth}]$, calculate $t_{plus}$ and $t_{minus}$.
- Strike out all $t \equiv t_{plus} \pmod r$ and $t \equiv t_{minus} \pmod r$.
- Survivors of this segmented sieve are coprime to all primes $\le S_{depth}$.

---

## 4. Primality Proof Theorems

### 4.1 Proth's Theorem (1878) for $B' = k \cdot 2^n + 1$
**Theorem 1:** *Let $B' = k \cdot 2^n + 1$ with $k$ odd and $k < 2^n$. If there exists an integer $w$ such that:*
$$w^{(B' - 1)/2} \equiv -1 \pmod{B'},$$
*then $B'$ is unconditionally prime.*

*Proof:*
Let $p$ be any prime divisor of $B'$. Then $w^{(B'-1)/2} \equiv -1 \pmod p$.
Squaring gives $w^{B'-1} \equiv 1 \pmod p$.
Thus, the multiplicative order of $w$ modulo $p$, denoted $d = \text{ord}_p(w)$, divides $B' - 1 = k \cdot 2^n$, but does not divide $(B' - 1)/2 = k \cdot 2^{n-1}$.
This implies that $2^n$ divides $d$.
Since $d \mid (p - 1)$ by Fermat's Little Theorem, $2^n \mid (p - 1)$, which implies $p \ge 2^n + 1$.
If $B'$ were composite, it would have at least two prime factors (or one prime factor $\ge \sqrt{B'}$).
Since each prime factor $p > 2^n$, the product of any two prime factors would satisfy:
$$B' \ge p_1 p_2 \ge (2^n + 1)^2 > 2^{2n} + 2^{n+1} + 1.$$
However, $B' = k \cdot 2^n + 1 < 2^n \cdot 2^n + 1 = 2^{2n} + 1$ because $k < 2^n$.
This contradiction proves that $B'$ cannot be composite. Hence $B'$ is prime. $\blacksquare$

### 4.2 Lucas-Lehmer-Riesel (LLR) Theorem (1969, 1994) for $A = k \cdot 2^n - 1$
**Theorem 2 (Riesel 1969, Rödseth 1994):** *Let $A = k \cdot 2^n - 1$ with $k$ odd, $k < 2^n$, and $n \ge 2$. Let $P \in \mathbb{Z}^+$ such that the Jacobi symbols satisfy:*
$$\left(\frac{P - 2}{A}\right) = 1 \quad \text{and} \quad \left(\frac{P + 2}{A}\right) = -1.$$
*Define the sequence:*
$$u_0 = V_k(P, 1) \bmod A, \qquad u_{j+1} = (u_j^2 - 2) \bmod A.$$
*Then $A$ is unconditionally prime if and only if:*
$$u_{n-2} \equiv 0 \pmod A.$$

*Proof:*
See Riesel (1969) and Rödseth (1994, Math. Comp. 63). The condition $(\frac{P-2}{A}) = 1, (\frac{P+2}{A}) = -1$ guarantees that the associated quadratic order $\mathcal{O}_D$ (with $D = P^2 - 4$) has Frobenius trace and splitting behavior ensuring that $u_{n-2} \equiv 0 \pmod A$ forces every prime divisor $p$ of $A$ to satisfy $p \equiv \pm 1 \pmod{2^n}$. Since $k < 2^n$, $A < 2^{2n}$, so $A$ cannot be the product of two such divisors. Hence $A$ is prime. $\blacksquare$

### 4.3 Deterministic Leaf Primality (Jiang & Deng 2014)
**Theorem 3:** *For any integer $N < 2^{64}$, if $N$ passes the Miller-Rabin test for all 7 prime bases:*
$$\mathcal{B} = \{2, 325, 9375, 28178, 450775, 9780504, 1795265022\},$$
*then $N$ is unconditionally prime.*
*Reference:* Jiang & Deng, "Strong pseudoprimes to the first eight prime bases", Math. Comp. 83 (2014).

---

## 5. Hardy-Littlewood Density Model

The conditional density of twin primes among integers $C = M_B(2t + 1) 2^n$ is modeled by:
$$\rho_{\text{HDC-7}}(B, C) \approx \rho_6(C) \times \prod_{\substack{5 \le p \le B \\ p \text{ prime}}} \frac{p}{p - 2},$$
where $\rho_6(C) = \frac{12 C_2}{(\ln C)^2}$.

| $B$ | $M_B$ | Theoretical Gain $\prod \frac{p}{p-2}$ |
|:---:|:---:|:---:|
| 3 (Baseline) | 3 | $1.000\times$ |
| 13 | 15,015 | $3.370\times$ |
| 31 | 100,280,245,065 | $5.127\times$ |
| 47 | 307,444,891,294,245,705 | $6.079\times$ |
| 97 | $2.30 \times 10^{36}$ | $7.828\times$ |

---

## 6. Novelty and Independence Protocol

1. **Exact Representation Reconstruction:** Every discovery is defined by canonical $(B, M_B, t, k, n)$, allowing exact bit-for-bit reconstruction of $C$, $A$, and $B'$.
2. **Deterministic Cryptographic Digest:** Canonical JSON representation hashed with SHA-256.
3. **Double-Independent Verification:**
   - Primary search engine generates the certificate with witnesses $(w, P, u_0)$.
   - Completely standalone independent verifier (`scripts/phase7_independent_verify.py`), with zero imports from `src/`, recalculates the Proth congruence, independent $2 \times 2$ matrix powering for $u_0$, and the full LLR recurrence, outputting a cryptographically bound attestation file.
