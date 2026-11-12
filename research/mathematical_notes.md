# Mathematical Foundations of Twin Prime Search and Verification

**Document Version:** 1.0.0  
**Research Date:** 2026-11-12  
**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Author:** Antigravity Research Group

---

## 1. Fundamental Definitions

### Definition 1.1 (Prime and Composite Numbers)
An integer $p \in \mathbb{Z}_{\ge 2}$ is called *prime* if its only positive divisors are $1$ and $p$. Otherwise, $p$ is called *composite*. The set of all prime numbers is denoted by $\mathbb{P}$.

### Definition 1.2 (Twin Primes)
A pair $(p, p+2)$ of integers is called a *twin-prime pair* if both $p \in \mathbb{P}$ and $p+2 \in \mathbb{P}$. The lower member is $p$, the upper member is $p+2$, and the *center* is $m = p+1$.

---

## 2. Necessary Congruence Structures and Center Divisibility

### Theorem 2.1 (Center Divisibility by 6)
Every twin-prime pair $(p, p+2)$ except $(3,5)$ satisfies:
$$p \equiv 5 \pmod 6, \quad p+2 \equiv 1 \pmod 6, \quad \text{and} \quad m = p+1 \equiv 0 \pmod 6$$
Equivalently, all twin primes other than $(3,5)$ can be written in the form:
$$(6r - 1, 6r + 1) \quad \text{for some } r \in \mathbb{Z}^+$$

#### Proof:
Let $p > 3$ be an odd prime. Since $p$ is coprime to $2$ and $3$, its residue modulo $6$ cannot be $0, 2, 3$, or $4$.
Hence, $p \equiv 1 \pmod 6$ or $p \equiv 5 \pmod 6$.
* If $p \equiv 1 \pmod 6$, then $p+2 \equiv 3 \pmod 6$. This implies $3 \mid (p+2)$. Since $p > 3$, $p+2 > 5$, so $p+2$ is composite and cannot be prime.
* If $p \equiv 5 \pmod 6$, then $p+2 \equiv 7 \equiv 1 \pmod 6$, which is coprime to both $2$ and $3$.
Thus, for $(p, p+2)$ to be twin primes with $p > 3$, we must have $p \equiv 5 \equiv -1 \pmod 6$ and $p+2 \equiv 1 \pmod 6$.
The center $m = p+1 = 6r - 1 + 1 = 6r$, which is divisible by $6$. $\blacksquare$

> **Caveat (Necessary vs. Sufficient):** Theorem 2.1 is only a necessary condition. For example, $r=4 \implies (23, 25)$, where $25 = 5^2$ is composite; $r=6 \implies (35, 37)$, where $35 = 5 \times 7$ is composite. Hence, sieving or testing is required to eliminate composite candidates.

---

## 3. Modular Elimination Theory (The Dual-Residue Sieve)

### 3.1 Bounded-Range Dual Sieve Modulo $q$

Let $q$ be an odd prime, $q \ge 5$. Since $\gcd(6, q) = 1$, the multiplicative inverse $6^{-1} \pmod q$ exists and is unique.

#### Lemma 3.1 (Residue Exclusion for General Twins)
For a candidate pair $(6r - 1, 6r + 1)$ and an odd prime $q \ge 5$:
1. $6r - 1 \equiv 0 \pmod q \iff r \equiv 6^{-1} \pmod q$
2. $6r + 1 \equiv 0 \pmod q \iff r \equiv -6^{-1} \pmod q$

#### Proof:
$6r \mp 1 \equiv 0 \pmod q \iff 6r \equiv \pm 1 \pmod q$. Multiplying by $6^{-1} \pmod q$ gives $r \equiv \pm 6^{-1} \pmod q$. $\blacksquare$

#### Corollary 3.1 (Soundness and Completeness of Bounded Sieve)
Let $r \in \mathbb{Z}^+$ such that $6r - 1 > q$. Then $(6r - 1)(6r + 1)$ has $q$ as a proper divisor if and only if:
$$r \equiv 6^{-1} \pmod q \quad \text{or} \quad r \equiv -6^{-1} \pmod q$$
By marking candidate indices $r$ that fall into these two arithmetic progressions, exactly those pairs with a member divisible by $q$ are eliminated. No valid twin prime pair with $p > q$ is ever removed.

---

### 3.2 Structured Twin Primes: Form $k \cdot 2^n \pm 1$

Consider the candidate family:
$$A = k \cdot 2^n - 1, \quad B = k \cdot 2^n + 1, \quad k \text{ odd}, \ n \ge 1$$

#### Lemma 3.2 (Dual Modular Inversion for Exponent $n$)
Let $q$ be an odd prime divisor. Since $\gcd(2^n, q) = 1$, let $a \equiv 2^n \pmod q$. Then $a^{-1} \pmod q$ exists and is unique.
1. $q \mid (k \cdot 2^n - 1) \iff k \equiv a^{-1} \pmod q$
2. $q \mid (k \cdot 2^n + 1) \iff k \equiv -a^{-1} \pmod q$

#### Proof:
$k \cdot 2^n \mp 1 \equiv 0 \pmod q \iff k \cdot a \equiv \pm 1 \pmod q \iff k \equiv \pm a^{-1} \pmod q$. $\blacksquare$

#### Definition 3.3 (Dual Forbidden Residue Pair)
For a fixed exponent $n$ and sieve prime $q$:
$$u_1(q, n) = (2^n \pmod q)^{-1} \bmod q, \quad u_2(q, n) = (q - u_1(q, n)) \bmod q$$
Any odd integer $k$ satisfying $k \equiv u_1 \pmod q$ or $k \equiv u_2 \pmod q$ generates a composite member and can be eliminated with zero multiprecision arithmetic.

---

## 4. Probable-Prime Testing vs. Mathematical Primality Proofs

### 4.1 Probable-Prime Tests (PRP)
A candidate $N$ is a *probable prime* base $a$ if it satisfies a necessary condition for primality, such as:
* **Fermat PRP:** $a^{N-1} \equiv 1 \pmod N$.
* **Miller-Rabin Strong PRP:** Writing $N-1 = 2^s d$ with $d$ odd, either $a^d \equiv 1 \pmod N$ or $a^{2^r d} \equiv -1 \pmod N$ for some $0 \le r < s$.
* **Baillie-PSW:** A combination of base-2 Miller-Rabin and a strong Lucas test. While no counterexample is known, it has not been mathematically proven that no composite passes Baillie-PSW for arbitrary $N$.

> **Rule:** Passing a PRP test classifies a number as a **probable prime**, never a **mathematically certified prime**.

---

### 4.2 Deterministic Primality Certification

To claim mathematical certainty, we utilize constructive theorems where the structure of $N \pm 1$ provides a certificate.

#### Theorem 4.1 (Proth's Theorem, 1878)
Let $B = k \cdot 2^n + 1$, where $k$ is an odd positive integer and $k < 2^n$.
If there exists an integer $a$ such that:
$$a^{\frac{B-1}{2}} \equiv -1 \pmod B$$
then $B$ is prime.

#### Proof:
Squaring the congruence yields:
$$a^{B-1} = \left(a^{\frac{B-1}{2}}\right)^2 \equiv (-1)^2 \equiv 1 \pmod B$$
Let $q$ be any prime divisor of $B$. In the multiplicative group $(\mathbb{Z}/q\mathbb{Z})^\times$, the order of $a \pmod q$, denoted $d = \operatorname{ord}_q(a)$, divides $B-1 = k \cdot 2^n$.
However, $a^{\frac{B-1}{2}} \equiv -1 \pmod q$, which means $a^{\frac{B-1}{2}} \not\equiv 1 \pmod q$.
Therefore, $d$ does not divide $\frac{B-1}{2} = k \cdot 2^{n-1}$.
This implies that the highest power of 2 dividing $d$ must be $2^n$.
Consequently, $2^n \mid d$. By Lagrange's theorem, $d \mid (q - 1)$, which implies:
$$q - 1 \ge d \ge 2^n \implies q \ge 2^n + 1$$
If $B$ were composite, it would possess at least one prime factor $q \le \sqrt{B}$.
However, using the condition $k < 2^n$:
$$\sqrt{B} = \sqrt{k \cdot 2^n + 1} < \sqrt{2^n \cdot 2^n + 1} = \sqrt{2^{2n} + 1} < 2^n + 1$$
Thus, any prime factor $q$ would satisfy $q < 2^n + 1$, directly contradicting $q \ge 2^n + 1$.
Therefore, $B$ cannot have any prime factor $\le \sqrt{B}$, and $B$ is prime. $\blacksquare$

#### Theorem 4.2 (Brillhart-Lehmer-Selfridge Theorem 4, 1975 / Pocklington $N+1$)
Let $A = k \cdot 2^n - 1$ with $k$ odd and $k < 2^n$.
Note that $A + 1 = k \cdot 2^n$. The completely factored part of $A + 1$ is $F = 2^n$.
Since $k < 2^n$, we have $F^2 = 2^{2n} = 2^n \cdot 2^n > k \cdot 2^n > A$, so $F > \sqrt{A}$.
If there exists an integer $a$ and a prime factor $p$ of $F$ (here $p = 2$) such that:
1. $a^{A+1} \equiv 1 \pmod A$, and
2. $\gcd\left(a^{\frac{A+1}{2}} - 1, A\right) = 1$
(or equivalently, the Lucas sequence $V_{\frac{A+1}{2}} \equiv 0 \pmod A$ with appropriate discriminant $D$),
then every prime factor $q$ of $A$ satisfies $q \equiv \pm 1 \pmod{2^n}$.
Since $2^n > \sqrt{A}$, $A$ must be prime.

#### Corollary 4.3 (Complete Structured Twin-Prime Certification)
Whenever $k < 2^n$, both members of the twin pair:
$$A = k \cdot 2^n - 1 \quad \text{and} \quad B = k \cdot 2^n + 1$$
can be proven prime in deterministic polynomial time $O(n^3)$ without factoring arbitrary integers!
* $B$ is certified via Proth's witness $a_B$.
* $A$ is certified via BLS witness $a_A$.
The certificate consists of the tuple $(k, n, a_B, a_A)$ and can be verified by any independent verifier in milliseconds.

---

## 5. Asymptotic Density and Sieve Tuning Heuristics

### 5.1 Hardy-Littlewood Density Heuristic
Conjecturally, the number of twin primes $\le x$ satisfies:
$$\pi_2(x) \sim 2 C_2 \int_2^x \frac{dt}{(\ln t)^2}, \quad C_2 = \prod_{p \ge 3}\left(1 - \frac{1}{(p-1)^2}\right) \approx 0.6601618158$$

### 5.2 Survival Rate After Sieve Depth $Q$
For each odd prime $q \le Q$, the dual residue sieve eliminates $2$ out of $q$ residue classes.
By Mertens' third theorem, the probability of a candidate surviving sieving up to prime $Q$ is:
$$\mathcal{S}(Q) = \prod_{3 \le q \le Q} \left(1 - \frac{2}{q}\right) \approx \frac{C_2}{(\ln Q)^2}$$

### 5.3 Optimal Sieve Depth Tradeoff
Let $C_{\text{sieve}}(Q)$ be the cost of sieving $K$ candidates up to prime $Q$:
$$C_{\text{sieve}}(Q) \approx K \sum_{q \le Q} \frac{2}{q} \approx 2 K \ln(\ln Q)$$
Let $C_{\text{PRP}}(n)$ be the cost of a strong PRP / Proth test on an $n$-bit integer:
$$C_{\text{PRP}}(n) \approx \gamma \cdot n^2 \log n$$
The total expected computation cost per candidate is:
$$T(Q) = C_{\text{sieve}}(Q) + \mathcal{S}(Q) \cdot C_{\text{PRP}}(n)$$
Minimizing $T(Q)$ with respect to $Q$ yields the optimal sieve depth $Q^*$:
$$\frac{d}{dQ} T(Q) = 0 \implies Q^* \approx \Theta(C_{\text{PRP}}(n) \cdot \ln n)$$
This theoretical relationship informs the Adaptive Sieve Depth scheduler in CATS.
