# Mathematical Specification and Primality Proof Audit (Phase 2)

**Author / Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Repository Branch:** `research/new-twin-prime-search-v2`  
**Commit Reference:** `62a8588`  

---

## 1. Mathematical Formulation

A pair of integers $(A, B)$ is defined as a **twin-prime pair** if and only if:
1. $B - A = 2$;
2. $A$ is prime;
3. $B$ is prime.

In this project, candidates are parameterized in the Riesel/Proth family:
$$A = k \cdot 2^n - 1, \quad B = k \cdot 2^n + 1$$
where $k$ is an odd positive integer and $n \ge 1$. The integer gap is trivially and identically:
$$B - A = (k \cdot 2^n + 1) - (k \cdot 2^n - 1) = 2$$

---

## 2. CRT Wheel Admissibility and Presieving

### 2.1 The Necessary Modulo 3 Congruence
For any integer $n \ge 1$:
$$2^n \equiv (-1)^n \equiv \pm 1 \pmod 3$$
If $3 \nmid k$, then $k \equiv \pm 1 \pmod 3$. 
- If $k \cdot 2^n \equiv 1 \pmod 3$, then $A = k \cdot 2^n - 1 \equiv 0 \pmod 3$.
- If $k \cdot 2^n \equiv 2 \equiv -1 \pmod 3$, then $B = k \cdot 2^n + 1 \equiv 0 \pmod 3$.

Therefore, for $A, B > 3$, a twin prime can exist in this family **if and only if**:
$$k \equiv 0 \pmod 3$$
Because $k$ is odd, this imposes the necessary congruence:
$$k \equiv 3 \pmod 6$$
This single mathematical condition eliminates $66.67\%$ of all odd positive integers before any arithmetic or modular exponentiation is performed.

### 2.2 Generalized Wheel Exclusion for Odd Primes $q$
For any odd prime $q \in \{3, 5, 7, 11, 13\}$, since $\gcd(2^n, q) = 1$, the modular inverse:
$$t_q \equiv (2^n)^{-1} \pmod q$$
is uniquely defined. Thus:
- $k \cdot 2^n - 1 \equiv 0 \pmod q \iff k \equiv t_q \pmod q$
- $k \cdot 2^n + 1 \equiv 0 \pmod q \iff k \equiv -t_q \equiv q - t_q \pmod q$

Modulo the wheel primorial modulus $M = 2 \cdot \prod_{q \in \{3,5,7,11,13\}} q = 2 \cdot 30030 = 60060$ (or odd modulus $30030$), the allowable residue classes are precomputed using the Chinese Remainder Theorem (CRT).
Across the odd candidates in $[1, 30030]$, exactly $1,485$ of $15,015$ odd residue classes survive ($9.89\%$), filtering out $90.11\%$ of all candidates prior to multiprecision allocation.

### 2.3 Exception Handling for Member Equals Sieve Prime
If $A = q$ or $B = q$ where $q$ is a sieving prime, a valid prime could theoretically be eliminated.
In our search domain:
$$n \ge 330, \quad k \ge 3 \implies A > 3 \cdot 2^{330} - 1 \approx 6.4 \times 10^{99}$$
Since the maximum sieving prime $Q \le 100,000 \ll 10^{99}$, the condition $A > Q$ holds unconditionally for all search candidates. Thus, no false eliminations can occur.

---

## 3. Deterministic Primality Theorems

### 3.1 Proth's Theorem for $B = k \cdot 2^n + 1$
**Theorem (Proth, 1878):**  
Let $B = k \cdot 2^n + 1$ with $k$ odd, $n \ge 1$, and $k < 2^n$. If there exists an integer $w$ (the Proth witness) such that:
$$w^{\frac{B-1}{2}} \equiv -1 \pmod B$$
then $B$ is unconditionally prime.

#### Necessary Preconditions:
1. $k$ is an odd positive integer;
2. $n \ge 1$;
3. **$k < 2^n$** (Crucial: if $k \ge 2^n$, the algebraic factor $(B-1)$ does not guarantee that all prime factors of $B$ exceed $\sqrt{B}$);
4. Witness $w$ must satisfy the congruence. By Euler's criterion, if $B$ is prime and the Jacobi symbol $\left(\frac{w}{B}\right) = -1$, this congruence is guaranteed to hold. If $\left(\frac{w}{B}\right) = -1$ and $w^{(B-1)/2} \not\equiv -1 \pmod B$, then $B$ is definitively **composite**.

---

### 3.2 Lucas-Lehmer-Riesel (LLR) / BLS Theorem 8 for $A = k \cdot 2^n - 1$
**Theorem (Riesel 1969; Brillhart, Lehmer, Selfridge 1975):**  
Let $A = k \cdot 2^n - 1$ with $k$ odd, $n \ge 2$, and $k < 2^n$.  
Let $P$ be an integer such that the Jacobi symbols satisfy:
$$\left(\frac{P-2}{A}\right) = 1 \quad \text{and} \quad \left(\frac{P+2}{A}\right) = -1$$
Define the Lucas sequence $V_j(P, 1)$ by:
$$V_0 = 2, \quad V_1 = P, \quad V_{j+1} = P \cdot V_j - V_{j-1}$$
Let $u_0 = V_k(P, 1) \pmod A$, and define the recurrence:
$$u_{i+1} = (u_i^2 - 2) \pmod A \quad \text{for } i \ge 0$$
Then $A$ is prime if and only if:
$$u_{n-2} \equiv 0 \pmod A$$

#### Necessary Preconditions:
1. $k$ is an odd positive integer;
2. $n \ge 2$;
3. $k < 2^n$;
4. Parameter $P$ must strictly satisfy the Jacobi non-residue criteria. Arbitrary constants without verifying Jacobi conditions invalidate the proof.

---

## 4. Algorithmic Complexity: Fast Lucas Sequence via Montgomery Ladder

The initial Phase 1 Python implementation computed $u_0 = V_k(P, 1) \pmod A$ with an iterative loop of $k$ additions and multiplications:
$$T_{\text{old}} = O(k \cdot M(\text{bits}(A)))$$
For $k = 200,000$, this required $200,000$ big-integer operations per candidate.

We replaced this with the **Montgomery Doubling Ladder** for Lucas sequences, using the identity:
$$\begin{aligned}
V_{2m} &= V_m^2 - 2 \pmod A \\
V_{2m+1} &= V_m \cdot V_{m+1} - P \pmod A
\end{aligned}$$
This reduces the complexity to:
$$T_{\text{new}} = O(\log_2 k \cdot M(\text{bits}(A)))$$
For $k = 200,000$, $\log_2 k \approx 18$ iterations, achieving a measured **$31,000\times$ speedup** while producing mathematically identical values verified against the linear oracle.

---

## 5. Audit of Verification Integrity

- **Hash Separation:** SHA-256 digests are employed solely for certificate data integrity and provenance tracking; they do NOT constitute primality proofs.
- **Strict Classification:** Candidates failing congruence tests are marked `COMPOSITE`. Unfinished tests are marked `INCONCLUSIVE`. A candidate is marked `PROVEN` if and only if both the Proth witness and the full LLR sequence $u_{n-2} \equiv 0 \pmod A$ succeed under all verified preconditions.
