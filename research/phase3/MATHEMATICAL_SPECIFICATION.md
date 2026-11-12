# Phase 3 Mathematical Specification: HDRSS Architecture and Primality Proof Standards

**Author / Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Target Search Regimes:** $\ge 200$, $\ge 300$, and $\ge 500$ decimal digits  

---

## 1. Candidate Family and Structural Invariants

A candidate twin pair $(A, B)$ is parameterized in the Riesel/Proth family:
$$A = k \cdot 2^n - 1, \qquad B = k \cdot 2^n + 1$$
subject to the following invariants:
1. $k \in \mathbb{N}$ is positive and odd ($k \equiv 1 \pmod 2$);
2. $n \ge 2$;
3. $k < 2^n$ (strict inequality required for Proth and LLR theorem completeness);
4. $A > 3$;
5. Difference identity: $B - A = 2$ identically.

### 1.1 Necessary Modulo 3 Admissibility
For $n \ge 1$:
$$2^n \equiv (-1)^n \equiv \begin{cases} 1 \pmod 3 & \text{if } n \text{ is even} \\ 2 \equiv -1 \pmod 3 & \text{if } n \text{ is odd} \end{cases}$$
If $3 \nmid k$, then $k \in \{1, 2\} \pmod 3$.
- If $k \cdot 2^n \equiv 1 \pmod 3$, then $A = k \cdot 2^n - 1 \equiv 0 \pmod 3$, so $3 \mid A$.
- If $k \cdot 2^n \equiv 2 \equiv -1 \pmod 3$, then $B = k \cdot 2^n + 1 \equiv 0 \pmod 3$, so $3 \mid B$.

Because $A > 3$, a twin prime can exist if and only if:
$$k \equiv 0 \pmod 3$$
Since $k$ is odd, this is equivalent to the linear form:
$$k \equiv 3 \pmod 6 \iff k = 6t + 3, \quad t \ge 0$$

---

## 2. CRT Wheel Construction and Counting

Consider the wheel primorial modulus formed by the first five odd primes:
$$M_{\text{odd}} = 3 \times 5 \times 7 \times 11 \times 13 = 15,015$$
$$M = 2 \times M_{\text{odd}} = 30,030$$

The total number of odd integers in $[1, M)$ is:
$$N_{\text{odd}} = \frac{M}{2} = 15,015$$

For each odd prime $q \in \{3, 5, 7, 11, 13\}$, since $\gcd(2^n, q) = 1$, the inverse $a^{-1} = (2^n)^{-1} \pmod q$ exists and is unique.
- Divisibility $q \mid A \iff k \equiv a^{-1} \pmod q$;
- Divisibility $q \mid B \iff k \equiv -a^{-1} \pmod q$.

For $q = 3$, $k \equiv 0 \pmod 3$ leaves $1$ surviving residue out of $3$.
For $q \in \{5, 7, 11, 13\}$, $a^{-1} \not\equiv -a^{-1} \pmod q$, so exactly $2$ residue classes modulo $q$ are forbidden.
By the Chinese Remainder Theorem, the fraction of surviving residue classes is:
$$\sigma = \left(\frac{1}{3}\right) \times \left(1 - \frac{2}{5}\right) \times \left(1 - \frac{2}{7}\right) \times \left(1 - \frac{2}{11}\right) \times \left(1 - \frac{2}{13}\right) = \frac{1}{3} \times \frac{3}{5} \times \frac{5}{7} \times \frac{9}{11} \times \frac{11}{13} = \frac{1485}{15015} \approx 0.098901$$

The exact number of surviving odd residues modulo $30,030$ is therefore:
$$\text{Survivors} = 15,015 \times \sigma = 1,485$$
This eliminates $90.11\%$ of candidates before sieve array allocation.

---

## 3. Segmented Sieve Mathematics (Strategy S1 and S2)

Let a search window be defined on candidate indices $t$ where $k = 6t + 3$ for $t \in [t_{\text{start}}, t_{\text{end}})$.
Let array size be $L = t_{\text{end}} - t_{\text{start}}$, indexed by $i = t - t_{\text{start}} \in [0, L)$.

For an odd sieve prime $q \notin \{2, 3\}$:
We require $k \not\equiv \pm a^{-1} \pmod q$, where $a \equiv 2^n \pmod q$.
Let $r \in \{a^{-1} \pmod q, -a^{-1} \pmod q\}$.
The congruence $k = 6t + 3 \equiv r \pmod q$ gives:
$$6t \equiv r - 3 \pmod q \implies t \equiv 6^{-1} (r - 3) \pmod q$$
Let $t_0 \equiv 6^{-1} (r - 3) \pmod q$ with $0 \le t_0 < q$.
The first index $i_0 \ge 0$ in the window $[t_{\text{start}}, t_{\text{end}})$ matching this progression is:
$$i_0 = (t_0 - t_{\text{start}}) \bmod q$$

### 3.1 Vectorized Strided Marking (Strategy S1)
For all primes $q \le Q_{\text{sieve}}$, we mark the NumPy boolean bitset array:
```python
alive[i0_minus :: q] = False
alive[i0_plus :: q] = False
```
This executes via high-speed C-level vector strides without Python loop overhead per candidate.

### 3.2 Hybrid Small-Prime Striding + Sparse Filtering (Strategy S2)
For larger primes $Q_{\text{stride}} < q \le Q_{\text{total}}$:
Bitset density becomes sparse after small-prime filtering ($< 1\%$ survivors). We extract the surviving indices $i$ and test $6(t_{\text{start}} + i) + 3 \pmod q$ directly in scalar modular arithmetic, avoiding memory cache misses from striding huge primes across large buffers.

---

## 4. Deterministic Primality Theorems and Independent Proofs

### 4.1 Proth's Theorem for $B = k \cdot 2^n + 1$
**Theorem (Proth 1878):**  
Let $B = k \cdot 2^n + 1$ with $k$ odd, $n \ge 1$, and $k < 2^n$. If there exists an integer $w$ such that:
$$w^{\frac{B-1}{2}} \equiv -1 \pmod B$$
then $B$ is unconditionally prime.

*Proof sketch:* If $p \mid B$ is prime, $w^{B-1} \equiv 1 \pmod p$ while $w^{(B-1)/2} \equiv -1 \pmod p$. Hence the order of $w \pmod p$ divides $B - 1 = k \cdot 2^n$ but does not divide $k \cdot 2^{n-1}$. Thus $2^n \mid \text{ord}_p(w)$, implying $p \equiv 1 \pmod{2^n}$, so $p \ge 2^n + 1$. If $B$ were composite, its smallest prime factor would satisfy $p \le \sqrt{B} = \sqrt{k \cdot 2^n + 1} < \sqrt{2^{2n} + 1} < 2^n + 1$ (since $k < 2^n$). This contradiction establishes that $B$ is prime.

### 4.2 Lucas-Lehmer-Riesel (LLR) Theorem for $A = k \cdot 2^n - 1$
**Theorem (Riesel 1969; BLS 1975 Theorem 8):**  
Let $A = k \cdot 2^n - 1$ with $k$ odd, $n \ge 2$, and $k < 2^n$. Let $P$ be an integer such that the Jacobi symbols satisfy:
$$\left(\frac{P-2}{A}\right) = +1 \quad \text{and} \quad \left(\frac{P+2}{A}\right) = -1$$
Define the Lucas sequence $V_j(P, 1)$ by $V_0 = 2, V_1 = P, V_{j+1} = P V_j - V_{j-1}$.
Let $u_0 = V_k(P, 1) \pmod A$, and iterate:
$$u_{i+1} = (u_i^2 - 2) \pmod A \quad \text{for } 0 \le i < n - 2$$
Then $A$ is prime if and only if $u_{n-2} \equiv 0 \pmod A$.

---

## 5. Independent Lucas Sequence Evaluation via $2 \times 2$ Matrix Powering

To ensure absolute independence between the search engine and the verifier:
The search engine computes $V_k(P, 1) \pmod A$ using the Montgomery doubling ladder:
$$\begin{aligned}
V_{2m} &= V_m^2 - 2 \pmod A \\
V_{2m+1} &= V_m V_{m+1} - P \pmod A
\end{aligned}$$

The independent verifier (`scripts/phase3_independent_verify.py`) computes $V_k(P, 1) \pmod A$ via a completely different algorithm: **Binary Matrix Exponentiation**:
$$\begin{pmatrix} V_{k+1} \\ V_k \end{pmatrix} = \begin{pmatrix} P & -1 \\ 1 & 0 \end{pmatrix}^k \begin{pmatrix} P \\ 2 \end{pmatrix} \pmod A$$
Because the mathematical code paths, data structures, and arithmetic algorithms are distinct, any implementation bug in the Montgomery ladder cannot be masked by the verifier.
