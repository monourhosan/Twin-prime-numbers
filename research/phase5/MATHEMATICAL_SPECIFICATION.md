# Phase 5 Mathematical Specification: Smooth-Center Certificate-Aware Search (SCCA)

**Date:** 2026-11-13  
**Authors:** Computational Number Theory & Algorithm Design Group (Antigravity Research)  
**Status:** Canonical Reference Specification (Phase 5)

---

## 1. Algebraic Family Formulation

Let $F$ be a positive integer whose complete prime factorization is known:
$$F = 2^a \cdot \prod_{i=1}^m p_i^{e_i} = 2^a \cdot F_{odd}$$
where $p_i$ are distinct odd primes ($p_1 = 3, p_2 = 5, p_3 = 7, \dots$), exponents $a \ge 1$, $e_1 \ge 1$ (so $6 \mid F$), and $F_{odd} = \prod_{i=1}^m p_i^{e_i}$.

For any positive parameter $t \in \mathbb{Z}^+$, we define the exact center $C(t)$ and the twin-prime candidate pair $(A(t), B(t))$:
$$C(t) = F \cdot t$$
$$A(t) = C(t) - 1 = F \cdot t - 1$$
$$B(t) = C(t) + 1 = F \cdot t + 1$$

### 1.1 Fundamental Properties
1. **Gap Identity:**
   $$B(t) - A(t) = (F \cdot t + 1) - (F \cdot t - 1) = 2$$
   The difference is identically 2 for all $t$.
2. **Parity and Non-Triviality:**
   Since $a \ge 1$, $F$ is even, so $C(t)$ is even. Thus $A(t)$ and $B(t)$ are consecutive odd integers. For $t \ge 1$ and $F \ge 6$, $A(t) \ge 5 > 2$.
3. **Coprimality of Pair Members:**
   $$\gcd(A(t), B(t)) = \gcd(C - 1, C + 1) = \gcd(C - 1, (C + 1) - (C - 1)) = \gcd(C - 1, 2) = 1$$
   Since $C - 1$ is odd, $A(t)$ and $B(t)$ are strictly coprime.
4. **Small Prime Immunity:**
   For any prime factor $p$ dividing $F$:
   $$C(t) \equiv 0 \pmod p \implies A(t) \equiv -1 \pmod p \quad \text{and} \quad B(t) \equiv 1 \pmod p$$
   Therefore:
   $$\gcd(A(t), p) = 1 \quad \text{and} \quad \gcd(B(t), p) = 1 \quad (\forall p \mid F)$$
   Neither member of the pair is divisible by 2, 3, or any other prime factor included in $F$.

---

## 2. Deterministic Primality Theorem for Upper Member $B(t)$

### 2.1 Theorem Statement (Pocklington / BLS 1975 Theorem 4)
Let $N = B(t) = F \cdot t + 1$. Then $N - 1 = F \cdot t$, and $F_{odd}$ is a known factored divisor of $N - 1$.

**Theorem (Brillhart, Lehmer, Selfridge 1975, Theorem 4):**
Let $N$ be an odd integer, and let $N - 1 = F \cdot U$. Suppose the complete prime factorization of $F = \prod_{i=1}^m p_i^{e_i}$ is known.
If:
1. $F > \sqrt{N}$ (exact integer condition: $F^2 > N$).
2. For each prime factor $p_i \mid F$, there exists an integer $a_i$ such that:
   $$a_i^{N - 1} \equiv 1 \pmod N$$
   and
   $$\gcd\left(a_i^{(N - 1)/p_i} - 1, N\right) = 1$$
then every prime divisor $r$ of $N$ satisfies $r \equiv 1 \pmod F$.
Consequently, $N$ is unconditionally prime.

### 2.2 Proof of Correctness
Assume $N$ satisfies the hypotheses of Theorem 4.
Let $r$ be an arbitrary prime divisor of $N$. For each $i \in \{1, \dots, m\}$:
Since $r \mid N$, $a_i^{N-1} \equiv 1 \pmod r$.
Let $d$ be the order of $a_i$ in the multiplicative group $(\mathbb{Z}/r\mathbb{Z})^\times$.
Then $d \mid (N - 1)$.
Also, $\gcd(a_i^{(N-1)/p_i} - 1, N) = 1 \implies a_i^{(N-1)/p_i} \not\equiv 1 \pmod r$.
Thus, $d$ divides $N - 1$ but does not divide $(N - 1)/p_i$.
Hence, the highest power of $p_i$ dividing $N - 1$, namely $p_i^{e_i}$, must divide $d$.
Since $d \mid (r - 1)$ by Lagrange's theorem on $(\mathbb{Z}/r\mathbb{Z})^\times$, we have $p_i^{e_i} \mid (r - 1)$ for all $i$.
Since the $p_i$ are distinct primes, their product $F$ divides $r - 1$:
$$r \equiv 1 \pmod F \implies r \ge F + 1$$
If $N$ were composite, it would have at least two prime factors (counting multiplicity):
$$N \ge r_1 r_2 \ge (F + 1)^2 > F^2$$
However, hypothesis (1) specifies $F > \sqrt{N} \iff F^2 > N$.
This yields a contradiction: $N > F^2 \ge N$.
Therefore, $N$ cannot have two or more prime factors, and since $N > 1$, $N = B(t)$ is unconditionally prime. $\blacksquare$

---

## 3. Deterministic Primality Theorem for Lower Member $A(t)$

### 3.1 Theorem Statement (Morrison 1975 / BLS 1975 Theorem 17)
Let $N = A(t) = F \cdot t - 1$. Then $N + 1 = F \cdot t = 2^a \cdot F_{odd} \cdot t$.
Let $F_{odd} = \prod_{i=1}^m p_i^{e_i}$ with $p_i$ odd primes.

**Theorem (Morrison 1975; BLS 1975 Theorem 17):**
Let $N > 2$ be an odd integer, and let $F_{odd} \mid (N + 1)$ with $F_{odd}$ having known prime factors $p_1, \dots, p_m$.
Suppose:
1. **Size Condition:**
   $$F_{odd} > \sqrt{N} + 1 \quad (\text{exact integer check: } (F_{odd} - 1)^2 > N)$$
2. There exists an integer $P$ such that $D = P^2 - 4$ satisfies:
   $$\left(\frac{D}{N}\right) = -1 \quad (\text{Jacobi symbol})$$
3. The Lucas sequence $U_k(P, 1)$ satisfies:
   $$U_{N + 1}(P, 1) \equiv 0 \pmod N$$
4. For every prime factor $p_i \mid F_{odd}$:
   $$\gcd\left(U_{(N + 1)/p_i}(P, 1), N\right) = 1$$

Then every prime divisor $r$ of $N$ satisfies $r \equiv \pm 1 \pmod{F_{odd}}$.
Consequently, $N$ is unconditionally prime.

### 3.2 Proof of Correctness
Let $r$ be an arbitrary prime divisor of $N$.
In the quadratic extension $\mathbb{F}_{r^2} = \mathbb{F}_r[\sqrt{D}]$, the roots of the characteristic equation $x^2 - Px + 1 = 0$ are:
$$\alpha, \beta = \frac{P \pm \sqrt{D}}{2}, \quad \text{with } \alpha \beta = 1, \quad \alpha - \beta = \sqrt{D}$$
The Lucas sequence terms are given by:
$$U_k = \frac{\alpha^k - \beta^k}{\alpha - \beta}$$
The order of the multiplicative group of the norm-1 torus in $\mathbb{F}_{r^2}$ is $r - \left(\frac{D}{r}\right)$.
Condition (3) ensures that the rank of apparition $\omega(r)$ divides $N + 1$.
Condition (4) ensures that for each prime factor $p_i \mid F_{odd}$:
$$\gcd(U_{(N + 1)/p_i}, N) = 1 \implies U_{(N + 1)/p_i} \not\equiv 0 \pmod r$$
Hence $\omega(r)$ does not divide $(N + 1)/p_i$.
Therefore, $p_i^{e_i} \mid \omega(r)$ for every $i \in \{1, \dots, m\}$.
Since $\omega(r) \mid (r \pm 1)$, we have $F_{odd} \mid (r \pm 1)$, which implies:
$$r \equiv \pm 1 \pmod{F_{odd}} \implies r \ge F_{odd} - 1$$
If $N$ were composite, $N \ge r_1 r_2 \ge (F_{odd} - 1)^2$.
However, hypothesis (1) establishes $(F_{odd} - 1)^2 > N$.
Contradiction! Therefore, $N = A(t)$ is unconditionally prime. $\blacksquare$

### 3.3 The Factor-2 Rank of Apparition Singularity
A critical mathematical finding in this phase is why $q = 2$ cannot be included as a tested divisor in $U_{(N+1)/q}$ when $Q = 1$:
For any Lucas sequence with $Q = 1$ and Jacobi symbol $\left(\frac{D}{N}\right) = -1$:
$$\alpha^{N + 1} = 1 \implies (\alpha^{(N + 1)/2})^2 = 1 \implies \alpha^{(N + 1)/2} = \pm 1$$
Since $\alpha \beta = 1$, $\beta^{(N + 1)/2} = \alpha^{-(N + 1)/2} = \pm 1 = \alpha^{(N + 1)/2}$.
Therefore:
$$U_{(N + 1)/2} = \frac{\alpha^{(N + 1)/2} - \beta^{(N + 1)/2}}{\alpha - \beta} \equiv \frac{\pm 1 - (\pm 1)}{\alpha - \beta} \equiv 0 \pmod N$$
Thus $U_{(N + 1)/2} \equiv 0 \pmod N$ holds identically for ALL primes $N$.
Attempting to check $\gcd(U_{(N + 1)/2}, N) = 1$ will always fail since the GCD is $N$.
**Resolution:** By structuring $F = 2^a \cdot F_{odd}$ and enforcing the size bound on the odd part $F_{odd} > \sqrt{A} + 1$ (which corresponds to $F_{odd} > 2^a \cdot t$), Morrison's criterion is applied strictly across odd prime factors $p_i \mid F_{odd}$. This avoids the factor-2 singularity completely while maintaining 100% unconditional mathematical proof rigor.

---

## 4. Companion Matrix Arithmetic for Lucas Sequences

To guarantee deterministic, arbitrary-precision computation without numerical instability or floating-point approximations, $U_k(P, 1) \pmod N$ is computed via $2 \times 2$ matrix binary exponentiation.

Define the companion matrix $M \in \mathrm{GL}_2(\mathbb{Z}/N\mathbb{Z})$:
$$M = \begin{pmatrix} P & -1 \\ 1 & 0 \end{pmatrix} \pmod N$$

By induction on $k \ge 1$:
$$M \begin{pmatrix} U_k \\ U_{k-1} \end{pmatrix} = \begin{pmatrix} P U_k - U_{k-1} \\ U_k \end{pmatrix} = \begin{pmatrix} U_{k+1} \\ U_k \end{pmatrix}$$
Starting with $\begin{pmatrix} U_1 \\ U_0 \end{pmatrix} = \begin{pmatrix} 1 \\ 0 \end{pmatrix}$, we have:
$$M^k \begin{pmatrix} 1 \\ 0 \end{pmatrix} = \begin{pmatrix} U_{k+1} \\ U_k \end{pmatrix}$$
and
$$M^k = \begin{pmatrix} U_{k+1} & -U_k \\ U_k & -U_{k-1} \end{pmatrix} \pmod N$$

Hence:
$$U_k(P, 1) \pmod N = (M^k)_{1,0} \pmod N$$
Binary exponentiation computes $M^k \pmod N$ in exactly $\lfloor \log_2 k \rfloor$ matrix squarings and at most $\lfloor \log_2 k \rfloor$ matrix multiplications, with asymptotic complexity $O(M_{\mathrm{int}}(\log N) \cdot \log k)$.
