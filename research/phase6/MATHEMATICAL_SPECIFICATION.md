# Phase 6 Mathematical Specification: Quadratic Co-Factor Proof Search (QCP-6)

**Document ID:** `PHASE6-MATH-SPEC-002`  
**Date:** 2026-11-14T11:38:00+06:00  
**Phase:** Phase 6 (Method Q and Method R)  
**Authors:** Antigravity Autonomous Number Theory Research Engine  

---

## 1. Universal Parameterization of Twin Primes

### Theorem 1 (Universal Twin-Center Representation)
Let $(p, p+2)$ be a pair of positive integers. If $(p, p+2)$ is a twin-prime pair and $p > 3$, then there exists an integer $m \ge 1$ such that:
$$p = 6m - 1, \qquad p + 2 = 6m + 1, \qquad C = \frac{p + (p+2)}{2} = 6m$$

#### Proof:
1. Since $p$ is a prime strictly greater than 2, $p$ is odd; hence $p+1$ is even, so $2 \mid (p+1)$.
2. Among the three consecutive integers $p, p+1, p+2$, exactly one is divisible by 3.
3. Since $p > 3$ and $p+2 > 3$ are prime, neither is divisible by 3. Hence $3 \mid (p+1)$.
4. Since $\gcd(2, 3) = 1$, $6 \mid (p+1)$. Setting $m = (p+1)/6 \in \mathbb{Z}^+$ yields $p = 6m - 1$ and $p+2 = 6m + 1$. $\blacksquare$

---

## 2. Method Q: Nonlinear Quadratic Co-Factor Family

### 2.1 Family Formulation
To avoid the requirement of constructing a fixed smooth multiplier for every narrow search interval (as in Phase 5), Method Q introduces a quadratic candidate generator whose known factored divisor grows dynamically with the candidate:

$$x = S \cdot t$$
$$C = x(x - h)$$
$$A = C - 1 = x^2 - hx - 1$$
$$B = C + 1 = x^2 - hx + 1$$

where:
1. $h$ is a small positive odd multiple of 3 (canonical primary choice: $h = 3$).
2. $S$ is an odd positive integer divisible by 3, with a fully known, verified prime factorization:
   $$S = 3 \prod_{i=1}^k p_i^{e_i}$$
3. $t$ is an odd positive integer ($t = 2j + 1$, $j \ge 0$) drawn from a bounded interval of machine-sized integers ($16 \le \text{bitlength}(t) \le 32$).
4. The candidate parameter satisfies $x > h + 2$.

### 2.2 Algebraic Divisibility by 6
#### Lemma 1
For any odd positive $S$ divisible by 3, odd positive $t$, and odd $h$, the integer center $C = x(x - h)$ is strictly divisible by 6.

#### Proof:
1. **Parity:** $S$ is odd and $t$ is odd $\implies x = S \cdot t$ is odd. Since $h$ is odd, the difference $x - h$ is even ($\text{odd} - \text{odd} = \text{even}$). The product $x(x - h)$ is the product of an odd and an even integer, hence $2 \mid C$.
2. **Divisibility by 3:** Since $3 \mid S$, $3 \mid x$, which implies $3 \mid x(x - h)$, so $3 \mid C$.
3. **Divisibility by 6:** Since $\gcd(2, 3) = 1$ and both divide $C$, $6 \mid C$. $\blacksquare$

Consequently, $A \equiv -1 \equiv 5 \pmod 6$ and $B \equiv +1 \pmod 6$. Neither member is divisible by 2 or 3.

---

## 3. Co-Factor Divisibility and Asymmetric Size Bounds

### 3.1 Upper Member $B$: Divisibility and Pocklington Bound
Observe that:
$$B - 1 = (x^2 - hx + 1) - 1 = x(x - h)$$
Setting the proof factor $F = x = S \cdot t$, we have $F \mid (B - 1)$ with cofactor $R = x - h$.

#### Lemma 2 (Pocklington Size Condition)
For $h \ge 3$ and $x > h + 2$, the proof factor $F = x$ satisfies $F^2 > B$.

#### Proof:
$$F^2 - B = x^2 - (x^2 - hx + 1) = hx - 1$$
Since $h \ge 3$ and $x > h + 2 \ge 5$:
$$hx - 1 \ge 3(5) - 1 = 14 > 0 \implies F^2 > B \quad \blacksquare$$

Since $F^2 > B$, we have $F > \sqrt{B}$.

### 3.2 Lower Member $A$: Divisibility and Morrison Lucas Bound
Observe that:
$$A + 1 = (x^2 - hx - 1) + 1 = x(x - h)$$
Setting the proof factor $F = x = S \cdot t$, we have $F \mid (A + 1)$ with cofactor $R = x - h$.

#### Lemma 3 (Morrison Lucas Size Condition)
For $h \ge 3$ and $x > 0$, the proof factor $F = x$ satisfies $(F - 1)^2 > A$.

#### Proof:
$$(F - 1)^2 - A = (x - 1)^2 - (x^2 - hx - 1) = (x^2 - 2x + 1) - (x^2 - hx - 1) = (h - 2)x + 2$$
Since $h \ge 3$, $h - 2 \ge 1$. Since $x > 0$:
$$(h - 2)x + 2 \ge x + 2 > 0 \implies (F - 1)^2 > A \quad \blacksquare$$

Since $(F - 1)^2 > A$, we have $F - 1 > \sqrt{A}$.

---

## 4. Unconditional Primality Theorems

### 4.1 Pocklington's Theorem for Upper Member $B$
#### Theorem 2 (Pocklington 1914 / BLS 1975 Theorem 4)
Let $N > 1$ be an odd integer, and let $N - 1 = F \cdot R$, where $F$ is fully factored into distinct prime factors $q_1, q_2, \dots, q_m$:
$$F = \prod_{i=1}^m q_i^{e_i}, \qquad e_i \ge 1$$
Suppose $F > \sqrt{N}$. If for each prime factor $q_i \mid F$ there exists an integer $a_i$ ($1 < a_i < N$) such that:
1. $a_i^{N - 1} \equiv 1 \pmod N$
2. $\gcd(a_i^{(N - 1)/q_i} - 1, N) = 1$

Then every prime divisor $p$ of $N$ satisfies:
$$p \equiv 1 \pmod{q_i^{e_i}} \quad \text{for all } i \in \{1, \dots, m\}$$
Consequently, $p \equiv 1 \pmod F$, so $p \ge F + 1 > \sqrt{N} + 1 > \sqrt{N}$. Since every prime divisor of $N$ strictly exceeds $\sqrt{N}$, $N$ must be prime. $\blacksquare$

### 4.2 Morrison's Rank-Based Lucas $N+1$ Theorem for Lower Member $A$
#### Definition (Lucas Sequence)
For integer parameters $P$ and $Q = 1$, with discriminant $D = P^2 - 4$, the Lucas sequence $U_k(P, 1)$ is defined by:
$$U_0 = 0, \quad U_1 = 1, \quad U_{k+2} = P \cdot U_{k+1} - U_k$$

#### Theorem 3 (Morrison 1975 / BLS 1975 Theorem 17)
Let $N > 1$ be an odd integer, and let $N + 1 = F \cdot R$, where $F$ is fully factored:
$$F = \prod_{i=1}^m q_i^{e_i}$$
Suppose $F - 1 > \sqrt{N}$ (i.e. $(F - 1)^2 > N$). Let $P \ge 3$ be an integer such that:
1. $\gcd(N, 2(P^2 - 4)) = 1$
2. The Jacobi symbol $\left(\frac{P^2 - 4}{N}\right) = -1$

If the Lucas sequence $U_k(P, 1)$ satisfies:
3. $U_{N + 1}(P, 1) \equiv 0 \pmod N$
4. $\gcd(U_{(N + 1)/q_i}(P, 1), N) = 1$ for every prime factor $q_i \mid F$

Then every prime divisor $p$ of $N$ satisfies:
$$p \equiv \left(\frac{D}{p}\right) \pmod F \implies p = k \cdot F \pm 1$$
Since $p$ is a prime divisor of $N > 1$, $k \ge 1$, which forces $p \ge F - 1 > \sqrt{N}$. Since every prime divisor of $N$ strictly exceeds $\sqrt{N}$, $N$ must be prime. $\blacksquare$

---

## 5. Quadratic Two-Polynomial Sieve Soundness

For each odd sieve prime $q \ge 5$ not dividing $S$, candidate indices $t$ where $q \mid A$ or $q \mid B$ are eliminated by solving the modular quadratic equations:

### 5.1 Roots of Member $A$
$$x^2 - hx - 1 \equiv 0 \pmod q$$
The discriminant is $D_A = h^2 + 4 \pmod q$ (for $h = 3$, $D_A = 13$).
- If Legendre symbol $\left(\frac{D_A}{q}\right) = +1$: two distinct roots $x \equiv (h \pm \sqrt{D_A}) \cdot 2^{-1} \pmod q$.
- If $q = 13$ ($D_A \equiv 0 \pmod{13}$): one repeated root $x \equiv h \cdot 2^{-1} = 3 \cdot 7 \equiv 8 \pmod{13}$.
- If $\left(\frac{D_A}{q}\right) = -1$: zero roots.

### 5.2 Roots of Member $B$
$$x^2 - hx + 1 \equiv 0 \pmod q$$
The discriminant is $D_B = h^2 - 4 \pmod q$ (for $h = 3$, $D_B = 5$).
- If Legendre symbol $\left(\frac{D_B}{q}\right) = +1$: two distinct roots $x \equiv (h \pm \sqrt{D_B}) \cdot 2^{-1} \pmod q$.
- If $q = 5$ ($D_B \equiv 0 \pmod 5$): one repeated root $x \equiv h \cdot 2^{-1} = 3 \cdot 3 \equiv 4 \pmod 5$.
- If $\left(\frac{D_B}{q}\right) = -1$: zero roots.

### 5.3 Root Disjointness
Subtracting the two equations yields:
$$(x^2 - hx + 1) - (x^2 - hx - 1) = 2 \equiv 0 \pmod q$$
For any odd prime $q \ge 3$, $2 \not\equiv 0 \pmod q$. Therefore, roots for $A$ and roots for $B$ are strictly disjoint.

### 5.4 Mapping from $x$ Roots to $j$ Index Residues
For each root $x_r \pmod q$:
$$t_r \equiv x_r \cdot S^{-1} \pmod q$$
Since $t = 2j + 1$:
$$2j \equiv (t_r - 1) \pmod q \implies j_r \equiv (t_r - 1) \cdot 2^{-1} \pmod q$$
This maps each root bijectively to a forbidden index residue $j \equiv j_r \pmod q$.

### 5.5 Absence of Equal-Prime Exceptions in Search Window
A root mark is invalid only if $A = q$ or $B = q$. For candidates in the primary band ($100 \le \text{digits} \le 200$), $A > 10^{99}$. Since the maximum sieve prime $Q_{\max} \le 10^7 \ll 10^{99}$, $A > Q_{\max}$ holds unconditionally across the entire search window. Hence, no candidate member can equal any sieve prime.

---

## 6. Bateman-Horn Density Model and Survivor Fractions

According to the Bateman-Horn conjecture, the density of twin primes in the sequence generated by two irreducible polynomials $f_1(t) = A(t)$ and $f_2(t) = B(t)$ of degree $d = 2$ is:
$$\pi_{f_1, f_2}(T) \sim \frac{C(f_1, f_2)}{(\deg f_1)(\deg f_2)} \int_2^T \frac{dt}{(\ln t)^2} = \frac{C(f_1, f_2)}{4} \int_2^T \frac{dt}{(\ln t)^2}$$
where the local correction factor $C(f_1, f_2)$ is given by the Euler product:
$$C(f_1, f_2) = \prod_{q \ge 3} \frac{1 - \rho(q)/q}{(1 - 1/q)^2}$$
and $\rho(q)$ is the number of solutions to $f_1(t) f_2(t) \equiv 0 \pmod q$.

For primes $q \nmid S$, $\rho(q) \in \{0, 1, 2, 4\}$ with asymptotic mean $\mathbb{E}[\rho(q)] = 2$.
Sieving to depth $Q_{\max} = 10^6$ reduces candidate volume by a factor of:
$$\mathcal{S}(Q_{\max}) = \prod_{5 \le q \le Q_{\max}} \left(1 - \frac{\rho(q)}{q}\right) \approx \frac{2 C_2}{(\ln Q_{\max})^2} \approx 0.007$$
yielding approximately 1 dual-PRP survivor per $\sim 280$ sieved candidates.
