# PAQCS Proof System Specification (Phase 8)

**Date:** 15 November 2026  
**Author:** Antigravity (Google DeepMind)  
**Status:** Mathematical Formulation & Verification Standard  

---

## 1. Mathematical Foundation

PAQCS primality certification relies on two classical theorems of Brillhart, Lehmer, and Selfridge (1975), applied symmetrically to the pair $(A, B)$:

$$A = x(x - 3) - 1, \quad B = x(x - 3) + 1$$
$$F = x = S_y \cdot t$$

---

## 2. Upper Member $B$: Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington $N-1$)

### Theorem Statement:
Let $N$ be an odd integer, and let $N - 1 = F \cdot R$, where $F = \prod_{i=1}^k q_i^{e_i}$ is completely factored into known distinct primes $q_i$.
If:
1. $F^2 > N$, and
2. For each prime factor $q_i \mid F$, there exists an integer $a_i$ such that:
   $$a_i^{N-1} \equiv 1 \pmod N$$
   $$\gcd\left(a_i^{(N-1)/q_i} - 1, N\right) = 1$$

Then every prime factor of $N$ is $\equiv 1 \pmod F$. Because $F^2 > N$, $N$ cannot have two prime factors $\ge F+1$, and thus **$N$ is unconditionally prime**.

### Application to $B$:
- $N = B = x^2 - 3x + 1$.
- $N - 1 = x(x - 3) = F \cdot (x - 3)$, where $F = x$.
- $F^2 - N = x^2 - (x^2 - 3x + 1) = 3x - 1 > 0$ for all $x \ge 1$.
- Size condition $F^2 > B$ holds unconditionally.
- Prime factors of $F$: the 274 primes of $S_{1780}$ plus prime factors of $t$.
- For each factor $q \mid x$, a witness base $a \in \{2, 3, 5, 7, \dots\}$ is deterministically found satisfying the Fermat and gcd conditions.

---

## 3. Lower Member $A$: Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison $N+1$ Lucas Rank)

### Theorem Statement:
Let $N$ be an odd integer, and let $N + 1 = F \cdot R$, where $F = \prod_{i=1}^k q_i^{e_i}$ is completely factored into known distinct primes $q_i$.
Let $P, Q$ be integers with $Q = 1$, discriminant $D = P^2 - 4$, satisfying:
1. $\gcd(N, 2D) = 1$
2. Jacobi symbol $\left(\frac{D}{N}\right) = -1$
3. $(F - 1)^2 > N$
4. Lucas sequence rank conditions:
   $$U_{N+1}(P, 1) \equiv 0 \pmod N$$
   $$\gcd\left(U_{(N+1)/q_i}(P, 1), N\right) = 1 \quad \text{for all } q_i \mid F$$

Then every prime factor of $N$ is $\equiv \pm 1 \pmod F$. Since $(F - 1)^2 > N$, **$N$ is unconditionally prime**.

### Application to $A$:
- $N = A = x^2 - 3x - 1$.
- $N + 1 = x(x - 3) = F \cdot (x - 3)$, where $F = x$.
- $(F - 1)^2 - N = (x - 1)^2 - (x^2 - 3x - 1) = x + 2 > 0$ for all $x > 0$.
- Size condition $(F - 1)^2 > A$ holds unconditionally.
- $P$ is searched deterministically starting from $P = 3$. For $t = 110,891$, $P = 30$ ($D = 896$) satisfies all conditions.
- Binary ladder Lucas evaluation computes $U_{(A+1)/q_i}(P, 1) \pmod A$ and verifies $\gcd = 1$ for all 274 prime factors.

---

## 4. Verification and Attestation Protocol

Independent verification is executed by `scripts/phase8_paqcs_independent_verify.py` with zero project imports:
1. Validates canonical JSON SHA-256 payload digest.
2. Independently validates deterministic primality of every prime in $S_{1780}$ and $t$ using trial division.
3. Reconstructs $S_y, x, C, A, B$ exactly and confirms $B - A = 2$, $C \equiv 0 \pmod 6$, and digit counts.
4. Independently re-computes Pocklington exponentiations and gcds.
5. Independently re-computes Morrison Lucas terms and gcds using a standalone binary ladder.
6. Emits an attestation file `attest_<sha256[:16]>.json` recording unconditional verification.
