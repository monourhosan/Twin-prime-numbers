# Phase 6 Mathematical Specification: General-Integer Twin-Center Segmented Sieve (GITCSS)

**Document ID:** `PHASE6-MATH-SPEC-001`  
**Date:** 2026-11-14T05:01:00+06:00  
**Phase:** Phase 6

---

## 1. Universal Parameterization of Twin Primes

### Theorem 1 (Universal Twin-Center Representation)
Let $(p, p+2)$ be a pair of positive integers. If $(p, p+2)$ is a twin-prime pair and $p > 3$, then there exists an integer $m \ge 1$ such that:
$$p = 6m - 1, \qquad p + 2 = 6m + 1$$

#### Proof:
1. Since $p$ is a prime strictly greater than 2, $p$ is odd. Consequently, $p+1$ is even: $2 \mid (p+1)$.
2. Consider the three consecutive integers $p, p+1, p+2$. In any three consecutive integers, exactly one is divisible by 3.
3. Since $p > 3$ and $p+2 > 3$ are both prime, neither $p$ nor $p+2$ can be divisible by 3.
4. Therefore, $3 \mid (p+1)$.
5. Since $\gcd(2, 3) = 1$ and both 2 and 3 divide $p+1$, their product $6 \mid (p+1)$.
6. Thus, there exists an integer $m \ge 1$ such that $p+1 = 6m$.
7. Solving for $p$ and $p+2$ yields:
   $$p = 6m - 1, \qquad p + 2 = 6m + 1 \quad \blacksquare$$

#### Exceptional Case:
For $p = 3$, $(p, p+2) = (3, 5)$. Here, $p+1 = 4$, which is not divisible by 6. The pair $(3, 5)$ is the unique twin-prime pair with $p \le 3$. All other twin-prime pairs satisfy $p = 6m - 1$ and $p+2 = 6m + 1$ for $m \ge 1$.

---

## 2. Exact Interval Mapping

Let $[p_{\min}, p_{\max}]$ be a specified search interval for the lower prime $p$.
The corresponding search interval for center index $m$, denoted $[m_{\min}, m_{\max}]$, is mapped using exact integer arithmetic:

$$m_{\min} = \left\lceil \frac{p_{\min} + 1}{6} \right\rceil = \left\lfloor \frac{p_{\min} + 1 + 5}{6} \right\rfloor$$
$$m_{\max} = \left\lfloor \frac{p_{\max} + 1}{6} \right\rfloor$$

#### Properties:
- For every integer $m \in [m_{\min}, m_{\max}]$, the candidate lower prime $A = 6m - 1$ satisfies $p_{\min} \le A \le p_{\max}$.
- The mapping is strictly monotonic and bijective from eligible center integers to twin candidate pairs.
- No floating-point division is used. In Python: `m_min = (p_min + 1 + 5) // 6` and `m_max = (p_max + 1) // 6`.

---

## 3. Modular Residue Sieve Mathematics

Let candidate pair $(A, B) = (6m - 1, 6m + 1)$ with center $C = 6m$.
Let $q \ge 5$ be an odd prime. Since $\gcd(6, q) = 1$, the modular inverse $6^{-1} \pmod q$ exists and is uniquely defined in $\{1, 2, \dots, q-1\}$.

### Lemma 1 (Forbidden Residues Modulo Sieve Primes)
For any prime $q \ge 5$:
1. $q \mid A \iff m \equiv 6^{-1} \pmod q$ (unless $A = q$, which occurs iff $m = (q+1)/6$).
2. $q \mid B \iff m \equiv -6^{-1} \equiv q - 6^{-1} \pmod q$ (unless $B = q$, which occurs iff $m = (q-1)/6$).

#### Proof:
1. $A \equiv 0 \pmod q \iff 6m - 1 \equiv 0 \pmod q \iff 6m \equiv 1 \pmod q$. Multiplying by $6^{-1} \pmod q$ gives $m \equiv 6^{-1} \pmod q$.
2. $B \equiv 0 \pmod q \iff 6m + 1 \equiv 0 \pmod q \iff 6m \equiv -1 \pmod q$. Multiplying by $6^{-1} \pmod q$ gives $m \equiv -6^{-1} \pmod q$. $\blacksquare$

### Lemma 2 (Distinctness of Forbidden Residues)
For any prime $q \ge 5$, the two forbidden residues are strictly distinct:
$$6^{-1} \not\equiv -6^{-1} \pmod q$$

#### Proof:
Suppose $6^{-1} \equiv -6^{-1} \pmod q$. Then $2 \cdot 6^{-1} \equiv 0 \pmod q \implies 2 \equiv 0 \pmod q$ or $6^{-1} \equiv 0 \pmod q$, which implies $q \mid 2$ or $q \mid 1$. Both are impossible since $q \ge 5$. Thus, the two residues are always distinct. $\blacksquare$

### Survivor Probability:
For each sieve prime $q \ge 5$, exactly 2 out of $q$ residue classes are eliminated. The fraction of admissible residues modulo $q$ is:
$$\sigma(q) = 1 - \frac{2}{q} = \frac{q - 2}{q}$$

For sieving up to bound $L$, the theoretical survivor fraction is:
$$\Pi(L) = \prod_{5 \le q \le L} \left(1 - \frac{2}{q}\right) \approx \frac{2 C_2}{(\ln L)^2}$$
where $C_2 = \prod_{p \ge 3} \left(1 - \frac{1}{(p-1)^2}\right) \approx 0.6601618158$ is the twin prime constant.

---

## 4. Wheel Factorization Architecture

To accelerate the sieve without computing modular residues for the smallest primes in every segment, we precompute a wheel over prime base $Q_W$:

$$W = \prod_{q \in Q_W} q$$

### Admissibility Condition:
A residue $r \in \{0, 1, \dots, W-1\}$ is wheel-admissible if and only if:
$$\forall q \in Q_W: \quad r \not\equiv 6^{-1} \pmod q \quad \text{and} \quad r \not\equiv -6^{-1} \pmod q$$

| Wheel Config | Modulus $W$ | Wheel Primes | Admissible Residues count | Survivor Fraction |
| :--- | :--- | :--- | :--- | :--- |
| **Wheel-5** | 5 | $\{5\}$ | 3 | 60.00% |
| **Wheel-5-7** | 35 | $\{5, 7\}$ | 15 | 42.86% |
| **Wheel-5-7-11** | 385 | $\{5, 7, 11\}$ | 135 | 35.06% |
| **Wheel-5-7-11-13** | 5005 | $\{5, 7, 11, 13\}$ | 1485 | 29.67% |

Using Wheel-5-7-11-13, **70.33% of candidate centers are eliminated instantly** upon segment allocation using a cyclic wheel lookup table, before touching a single non-wheel sieve prime.

---

## 5. Segmented Sieve Striding

For an arbitrary segment $m \in [m_{\text{base}}, m_{\text{base}} + S)$:
For each non-wheel sieve prime $q > \max(Q_W)$ with $q \le L$:
Let $r_1 = 6^{-1} \pmod q$ and $r_2 = (q - r_1) \pmod q$.
The first index $j_1 \in [0, q-1]$ in the segment where $m_{\text{base}} + j_1 \equiv r_1 \pmod q$ is:
$$j_1 = (r_1 - (m_{\text{base}} \bmod q)) \bmod q$$
Similarly, for $r_2$:
$$j_2 = (r_2 - (m_{\text{base}} \bmod q)) \bmod q$$

The elimination step marks all indices in the bitset:
$$\text{bitset}[j_1 + k \cdot q] = 0 \quad \text{for } 0 \le j_1 + k \cdot q < S$$
$$\text{bitset}[j_2 + k \cdot q] = 0 \quad \text{for } 0 \le j_2 + k \cdot q < S$$

This involves zero modular divisions within the inner loop and operates entirely through contiguous stride writes.

---

## 6. Deterministic Primality Proving Specification

For any surviving candidate pair $(A, B) = (6m - 1, 6m + 1)$ that passes Fermat base-2, 25-round Miller-Rabin, and Lucas probable-prime screening, primality must be proven deterministically.

### Center Factorization Symmetry
Notice that:
$$B - 1 = 6m = 2 \cdot 3 \cdot m$$
$$A + 1 = 6m = 2 \cdot 3 \cdot m$$

Let the prime factorization of center $m$ be:
$$m = \prod_{i=1}^k q_i^{e_i}$$
Then the complete prime factor set of $6m$ is $\mathcal{F} = \{2, 3\} \cup \{q_1, \dots, q_k\}$.

### 6.1 Theorem (Pocklington / BLS 1975 Theorem 4 for Upper Member $B$)
Let $B = 6m + 1$. The factored part of $B - 1$ is $F_B = 6m$.
Since $F_B = B - 1 > \sqrt{B}$ for all $B > 2$, $B - 1$ is 100% factored ($R_B = 1$).
If for each prime $q \in \mathcal{F}$, there exists an integer $a_q$ such that:
1. $a_q^{B - 1} \equiv 1 \pmod B$
2. $\gcd(a_q^{(B - 1) / q} - 1, B) = 1$

Then every prime factor $p$ of $B$ satisfies $p \equiv 1 \pmod{F_B}$.
Since $F_B = B - 1 > \sqrt{B}$, **$B$ is deterministically prime**.

### 6.2 Theorem (Morrison / BLS 1975 Theorem 17 for Lower Member $A$)
Let $A = 6m - 1$. The factored part of $A + 1$ is $F_A = 6m$.
Since $F_A = A + 1 > \sqrt{A}$ for all $A \ge 5$, $A + 1$ is 100% factored ($R_A = 1$).
Let $D = P^2 - 4$ be a discriminant with Jacobi symbol $\left(\frac{D}{A}\right) = -1$.
Let $U_k(P, 1)$ be the Lucas sequence defined by $U_0 = 0, U_1 = 1$, and $U_{k+1} = P U_k - U_{k-1}$.
If:
1. $U_{A + 1}(P, 1) \equiv 0 \pmod A$
2. For each prime $q \in \mathcal{F}$, $\gcd(U_{(A + 1) / q}(P, 1), A) = 1$

Then every prime factor $p$ of $A$ satisfies $p \equiv \pm 1 \pmod{F_A}$.
Since $F_A = A + 1 > \sqrt{A}$, **$A$ is deterministically prime**.

### 6.3 Prime Factor Trial Division Verification
Every prime factor $q \in \mathcal{F}$ must itself be proven prime. For factors $q \le 10^7$, primality is verified unconditionally via trial division by all primes $d \le \sqrt{q}$ from first principles.
