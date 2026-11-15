# Phase 9: Mathematical Specification
## The Primorial-Anchored Cubic-Cofactor Manifold (PACCM-9) & Dual-BLS Certification Engine

### 1. Algebraic Definition of the Manifold

Let $y \ge 3$ be an anchor prime limit, and let the primorial anchor $S_y$ be defined as the square-free product of all primes up to $y$:
$$S_y = \prod_{p \le y, \, p \text{ prime}} p = 2 \cdot 3 \cdot 5 \cdot 7 \cdots y$$

Let $t \in \mathbb{N}$ be an odd positive integer coprime to $S_y$ (and preferably prime to maintain an exact, minimal factorization).
Define the parameterized coordinate:
$$x(t) = S_y \cdot t$$

Define the even center $C(x)$ as the canonical cubic algebraic manifold:
$$C(x) = 2 x^2 (3x + 1) = 6 x^3 + 2 x^2$$

The associated candidate twin-prime pair $(A(x), B(x))$ is defined symmetrically around $C(x)$:
$$A(x) = C(x) - 1 = 6 x^3 + 2 x^2 - 1$$
$$B(x) = C(x) + 1 = 6 x^3 + 2 x^2 + 1$$

---

### 2. Fundamental Algebraic and Number-Theoretic Properties

#### Theorem 2.1 (Exact Twin Gap)
For all $x \in \mathbb{R}$:
$$B(x) - A(x) = (C(x) + 1) - (C(x) - 1) = 2$$
The arithmetic gap between upper and lower candidates is identically two.

#### Theorem 2.2 (Universal Center Divisibility and Parity)
For all $y \ge 3$ and all $t \in \mathbb{N}$:
1. $6 \mid S_y$, since $2 \mid S_y$ and $3 \mid S_y$.
2. $6 \mid x$, which implies $x \equiv 0 \pmod 2$ and $x \equiv 0 \pmod 3$.
3. $C(x) = 6 x^3 + 2 x^2 \equiv 2(0)^2 \equiv 0 \pmod 3$, and $C(x)$ is even.
4. Consequently, $C(x) \equiv 0 \pmod 6$.
5. Therefore:
   $$A(x) \equiv -1 \equiv 5 \pmod 6, \qquad B(x) \equiv 1 \pmod 6$$
   Both $A(x)$ and $B(x)$ are strictly odd and not divisible by 2 or 3.

#### Theorem 2.3 (Primorial Anchor Divisibility Immunity)
Let $p$ be any prime such that $p \le y$.
Then by construction, $p \mid S_y$, so $x \equiv 0 \pmod p$.
Substituting into $A(x)$ and $B(x)$:
$$A(x) = 6 x^3 + 2 x^2 - 1 \equiv 6(0)^3 + 2(0)^2 - 1 \equiv -1 \pmod p$$
$$B(x) = 6 x^3 + 2 x^2 + 1 \equiv 6(0)^3 + 2(0)^2 + 1 \equiv +1 \pmod p$$
Since $\pm 1 \not\equiv 0 \pmod p$ for any prime $p$, it follows that:
$$\gcd(A(x), p) = 1 \quad \text{and} \quad \gcd(B(x), p) = 1 \quad \forall p \le y$$
**Corollary:** The candidate pair $(A(x), B(x))$ possesses no prime factors $\le y$. All primes up to $y$ are eliminated a priori without any modular divisions or sieving operations.

#### Theorem 2.4 (Polynomial Irreducibility over $\mathbb{Q}$)
The polynomials $P_-(x) = 6 x^3 + 2 x^2 - 1$ and $P_+(x) = 6 x^3 + 2 x^2 + 1$ are irreducible over the field of rational numbers $\mathbb{Q}$.
*Proof:*
By the Rational Root Theorem, any rational root $x = r/s$ in lowest terms of $6 x^3 + 2 x^2 \pm 1 = 0$ must satisfy $r \mid \pm 1 \implies r \in \{\pm 1\}$, and $s \mid 6 \implies s \in \{1, 2, 3, 6\}$.
Testing the candidate roots $x \in \{\pm 1, \pm 1/2, \pm 1/3, \pm 1/6\}$:
- For $P_-(x) = 6 x^3 + 2 x^2 - 1$:
  $P_-(1) = 7 \ne 0$, $P_-(-1) = -5 \ne 0$
  $P_-(1/2) = 6/8 + 2/4 - 1 = 1/4 \ne 0$, $P_-(-1/2) = -6/8 + 2/4 - 1 = -5/4 \ne 0$
  $P_-(1/3) = 6/27 + 2/9 - 1 = -5/9 \ne 0$, $P_-(-1/3) = -6/27 + 2/9 - 1 = -1 \ne 0$
  $P_-(1/6) = 6/216 + 2/36 - 1 = -11/12 \ne 0$, $P_-(-1/6) = -6/216 + 2/36 - 1 = -35/36 \ne 0$
- For $P_+(x) = 6 x^3 + 2 x^2 + 1$:
  $P_+(1) = 9 \ne 0$, $P_+(-1) = -3 \ne 0$
  $P_+(1/2) = 9/4 \ne 0$, $P_+(-1/2) = 3/4 \ne 0$
  $P_+(1/3) = 13/9 \ne 0$, $P_+(-1/3) = 1 \ne 0$
  $P_+(1/6) = 13/12 \ne 0$, $P_+(-1/6) = 37/36 \ne 0$
Since neither polynomial has a rational root and both are of degree 3, both $P_-(x)$ and $P_+(x)$ are strictly irreducible over $\mathbb{Q}$. Hence, they cannot factor into lower-degree integer polynomials and can generate infinitely many primes under Schinzel's Hypothesis H and the Bateman-Horn Conjecture. $\blacksquare$

---

### 3. Divisor Structure and Exact Dual-BLS Certification Theorems

Both members share the exact same algebraic relationship to the center $C(x)$:
$$B - 1 = C(x) = (2 x^2) \cdot (3x + 1)$$
$$A + 1 = C(x) = (2 x^2) \cdot (3x + 1)$$

Let the completely factored divisor $F$ and the cofactor $R$ be defined as:
$$F = 2 x^2 = 2 \cdot S_y^2 \cdot t^2, \qquad R = 3x + 1$$

#### Theorem 3.1 (Exact Coprimality $\gcd(F, R) = 1$)
For all $y \ge 3$ and all $t \in \mathbb{N}$:
$$\gcd(F, R) = \gcd(2 x^2, 3x + 1) = 1$$
*Proof:*
Let $g = \gcd(x, 3x + 1)$. Then $g \mid x \implies g \mid 3x$. Since $g \mid (3x + 1)$, it follows that $g \mid ((3x + 1) - 3x) = 1$, so $g = 1$. Thus $\gcd(x, 3x + 1) = 1$, which implies $\gcd(x^2, 3x + 1) = 1$.
Furthermore, since $2 \mid S_y$, $x$ is even, which means $3x + 1$ is odd:
$$3x + 1 \equiv 3(0) + 1 \equiv 1 \pmod 2 \implies \gcd(2, 3x + 1) = 1$$
Since $\gcd(2, 3x + 1) = 1$ and $\gcd(x^2, 3x + 1) = 1$, by Euclid's Lemma:
$$\gcd(2 x^2, 3x + 1) = 1 \quad \blacksquare$$

#### Theorem 3.2 (Super-Root Dominance Condition $F > \sqrt{B} > \sqrt{A}$)
For all $x \ge 2$:
$$F^2 > B > A$$
*Proof:*
$$F^2 - B = (2 x^2)^2 - (6 x^3 + 2 x^2 + 1) = 4 x^4 - 6 x^3 - 2 x^2 - 1$$
Let $f(x) = 4 x^4 - 6 x^3 - 2 x^2 - 1$.
For $x = 2$: $f(2) = 4(16) - 6(8) - 2(4) - 1 = 64 - 48 - 8 - 1 = 7 > 0$.
The derivative $f'(x) = 16 x^3 - 18 x^2 - 4 x = 2x(8x^2 - 9x - 2)$.
For $x \ge 2$, $8x^2 - 9x - 2 \ge 8(4) - 18 - 2 = 12 > 0$, so $f(x)$ is strictly increasing for all $x \ge 2$.
Therefore:
$$F^2 > B \iff F > \sqrt{B}$$
Since $B = A + 2 > A$, it also follows that:
$$F > \sqrt{B} > \sqrt{A + 1} > \sqrt{A} \quad \blacksquare$$

**Asymptotic Ratio:**
$$\lim_{x \to \infty} \frac{F}{\sqrt{B}} = \lim_{x \to \infty} \frac{2 x^2}{\sqrt{6 x^3 + 2 x^2 + 1}} = \lim_{x \to \infty} \frac{2}{\sqrt{6}} x^{1/2} = \infty$$
At $D = 350$ digits ($x \approx 10^{117}$):
$\log_{10}(F) \approx 234$ digits, while $\log_{10}(\sqrt{B}) \approx 175$ digits.
The factored portion $F$ exceeds $\sqrt{B}$ by **59 orders of magnitude** ($10^{59}$).

#### Theorem 3.3 (Unconditional Primality of Upper Member $B$)
Let $B = F \cdot R + 1$, where $F = 2 x^2$, $\gcd(F, R) = 1$, and $F > \sqrt{B}$.
Let $q_1, q_2, \dots, q_k$ be all distinct prime factors of $F$.
If for each $q_i$ there exists an integer witness $a_i \in \{2, 3, \dots, B-1\}$ such that:
1. $a_i^{B - 1} \equiv 1 \pmod B$
2. $\gcd(a_i^{(B - 1) / q_i} - 1, B) = 1$
Then $B$ is unconditionally **PRIME** by Brillhart-Lehmer-Selfridge (1975, Theorem 4).

#### Theorem 3.4 (Unconditional Primality of Lower Member $A$)
Let $A = F \cdot R - 1$, where $F = 2 x^2$, $\gcd(F, R) = 1$, and $F > \sqrt{A + 1}$.
Let $D$ be a non-square integer such that the Jacobi symbol $(D / A) = -1$.
Let the Lucas sequence $U_k(P, Q)$ be defined with parameter $Q = 1$ and $P$ chosen such that $P^2 - 4 = D$.
If:
1. $U_{A + 1} \equiv 0 \pmod A$
2. $\gcd(U_{(A + 1) / q_i}, A) = 1$ for all distinct prime factors $q_i \mid F$
Then every prime factor $p$ of $A$ satisfies $p \equiv \pm 1 \pmod F$.
Since $F > \sqrt{A + 1} > \sqrt{A}$, $A$ is unconditionally **PRIME** by Brillhart-Lehmer-Selfridge (1975, Theorem 17 / Morrison-BLS).

---

### 4. Modular Sieve Theory for PACCM-9 on GPU

For primes $q > y$, a candidate multiplier $t$ produces a composite member if either $A(t) \equiv 0 \pmod q$ or $B(t) \equiv 0 \pmod q$.
Substituting $x \equiv S_y \cdot t \pmod q$:

#### Congruence for Upper Member $B$:
$$6 (S_y t)^3 + 2 (S_y t)^2 + 1 \equiv 0 \pmod q$$
Let $x \equiv S_y t \pmod q$. Since $q > y$, $\gcd(6, q) = 1$ and $\gcd(S_y, q) = 1$.
The cubic congruence over $\mathbb{F}_q$:
$$6 x^3 + 2 x^2 + 1 \equiv 0 \pmod q$$
has at most 3 distinct roots $\{r_{B, 1}, r_{B, 2}, \dots\} \subset \mathbb{F}_q$.

#### Congruence for Lower Member $A$:
$$6 (S_y t)^3 + 2 (S_y t)^2 - 1 \equiv 0 \pmod q$$
$$6 x^3 + 2 x^2 - 1 \equiv 0 \pmod q$$
has at most 3 distinct roots $\{r_{A, 1}, r_{A, 2}, \dots\} \subset \mathbb{F}_q$.

#### Forbidden Residue Classes for Multiplier $t$:
For each root $r \in \{r_{A, j}\} \cup \{r_{B, j}\}$:
$$t \equiv r \cdot S_y^{-1} \pmod q$$
Let $\mathcal{R}_q \subset \mathbb{F}_q$ denote the union of all forbidden $t$-residues modulo $q$.
On average, by the Chebotarev density theorem applied to Galois groups of degree 3 polynomials, an irreducible cubic has on average 1 root in $\mathbb{F}_q$. Thus:
$$|\mathcal{R}_q| \approx 1 + 1 = 2 \text{ roots per prime } q$$
For each $r \in \mathcal{R}_q$, the GPU marks all indices $t = r + k \cdot q$ in parallel.

---

### 5. Expected-Yield Model (Hardy-Littlewood with Primorial Boost)

By the Hardy-Littlewood twin-prime conjecture, the raw twin-prime density for integers near $X$ is:
$$\pi_2(X) \sim 2 C_2 \frac{X}{(\ln X)^2}, \qquad C_2 \approx 0.6601618158$$

Because our candidates are constrained to $x = S_y \cdot t$, they possess zero prime factors $\le y$.
The local factor at prime $p$ for generic integers is $(1 - 2/p)$.
Because our construction eliminates divisibility by all $p \le y$, the twin-prime probability is amplified by the **primorial singular series enhancement factor**:
$$E(y) = \prod_{3 \le p \le y} \left(1 - \frac{2}{p}\right)^{-1} = \prod_{3 \le p \le y} \frac{p}{p - 2}$$

For our primary 350-digit campaign ($y = 283$):
- Number of odd primes $\le 283$: 60 primes.
- Enhancement factor: $E(283) \approx 39.58\times$.
- Target size: $X \approx 10^{355} \implies \ln X \approx 817.4$.
- Boosted twin-prime probability per eligible candidate:
  $$P_{\text{twin}}(t) \approx \frac{2 C_2}{(\ln X)^2} \cdot E(y) \approx \frac{1.3203}{(817.4)^2} \cdot 39.58 \approx 7.82 \times 10^{-5}$$
- Expected candidates per twin prime:
  $$\mathbb{E}[\text{candidates}] \approx \frac{1}{7.82 \times 10^{-5}} \approx 12,786$$
- For a planned search campaign of $N = 50,000$ candidates:
  $$\mathbb{E}[\text{twins}] \approx 50,000 \times 7.82 \times 10^{-5} \approx 3.91 \text{ pairs}$$
  The Poisson probability of finding at least one twin-prime pair is:
  $$P(\text{discovery} \ge 1) = 1 - e^{-3.91} \approx 98.0\%$$
