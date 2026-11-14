# ADES-8 Algorithm Specification: Adaptive Dual-Axis Exponent Sieve and Independent Proof Routing

**Version:** 8.0.0  
**Date:** 2026-11-14  
**Author:** Google Antigravity (Computational Number Theory & Proof Engineering Mission)  
**Target Class:** Primorial-constrained Proth-Riesel twin prime pairs $(p, q) = (C - 1, C + 1)$ with $C = k \cdot 2^n$

---

## 1. Candidate Family and Exact Number-Theoretic Constraints

We search for twin prime pairs within the structured primorial family:
$$M_R = \prod_{\substack{3 \le p \le R \\ p \text{ prime}}} p$$
$$k = M_R \cdot (2t + 1), \quad t \in \mathbb{N}_0$$
$$C = k \cdot 2^n = M_R \cdot (2t + 1) \cdot 2^n$$
$$p = C - 1, \quad q = C + 1$$

### Invariant Preconditions
1. **Odd $k$:** Because $M_R$ is a product of odd primes and $2t + 1$ is odd, $k$ is strictly odd for all $t \ge 0$.
2. **Proth / Riesel Condition:** We strictly enforce $k < 2^n$ (which implies $2t + 1 < \frac{2^n}{M_R}$). This satisfies the standard theorem precondition for both Proth's Theorem on $q$ and the Lucas-Lehmer-Riesel Theorem on $p$.
3. **Divisibility by 6:** Because $3 \mid M_R$ and $2 \mid 2^n$ ($n \ge 1$), $C \equiv 0 \pmod 6$. Consequently, $p \equiv 5 \pmod 6$ and $q \equiv 1 \pmod 6$, satisfying the necessary condition for twin primes $>3$.
4. **Small Factor Elimination:** For every prime $r \mid M_R$, $C \equiv 0 \pmod r$, so $p \equiv -1 \pmod r$ and $q \equiv +1 \pmod r$. Therefore, neither member is divisible by any prime $r \le R$.
5. **Exact Digit Band Bounds:** For target decimal digits $D$, we enforce:
   $$10^{D-1} + 1 \le C \le 10^D - 2$$
   which guarantees that both $p = C - 1$ and $q = C + 1$ have **exactly $D$ decimal digits**.

---

## 2. Two-Dimensional Sieve and Modular Recurrence

Let $r$ be an odd sieve prime coprime to $M_R$ ($r > R$).

### 2.1 Direct Modular Roots
We seek parameter offsets $t \pmod r$ such that $r \mid (C - 1)$ or $r \mid (C + 1)$:
$$C = M_R (2t + 1) 2^n \equiv (2t + 1) \alpha_n^{-1} \pmod r$$
where $\alpha_n \equiv (M_R \cdot 2^n)^{-1} \pmod r$.

- For $p = C - 1 \equiv 0 \pmod r$:
  $$(2t + 1) \alpha_n^{-1} \equiv 1 \pmod r \iff 2t + 1 \equiv \alpha_n \pmod r \iff t \equiv (\alpha_n - 1) \cdot 2^{-1} \pmod r$$
- For $q = C + 1 \equiv 0 \pmod r$:
  $$(2t + 1) \alpha_n^{-1} \equiv -1 \pmod r \iff 2t + 1 \equiv -\alpha_n \pmod r \iff t \equiv (-\alpha_n - 1) \cdot 2^{-1} \pmod r$$

Let $b_r \equiv 2^{-1} \pmod r$. The roots are:
$$t_{\text{minus}} \equiv ((\alpha_n - 1) \cdot b_r) \pmod r$$
$$t_{\text{plus}} \equiv ((-\alpha_n - 1) \cdot b_r) \pmod r$$

### 2.2 Row-to-Row Modular Recurrence
In fixed-exponent sieves (e.g. ADRS-4, HDC-7), $\alpha_n$ is recomputed for every $(r, n)$ using modular exponentiation ($O(\log n)$ operations).
In ADES-8, we observe:
$$\alpha_{n+1} \equiv (M_R \cdot 2^{n+1})^{-1} \equiv (M_R \cdot 2^n \cdot 2)^{-1} \equiv \alpha_n \cdot 2^{-1} \equiv (\alpha_n \cdot b_r) \pmod r$$

Thus, across an exponent tile $n \in [n_{\text{start}}, n_{\text{start}} + H - 1]$:
1. $\alpha_{n_{\text{start}}}$ is computed once for each sieve prime $r$.
2. For each subsequent row $n + 1$, $\alpha_{n+1}$ is obtained in **exactly one multiplication and reduction** in $\mathbb{Z}/r\mathbb{Z}$.
3. For $H = 16$ rows and $S = 100,000$, this eliminates $15 \times 9,588 \approx 143,820$ multi-precision modular exponentiations per tile.

---

## 3. Staged Screening Cascade

Candidates that survive the 2D sieve are evaluated through a cost-optimized multi-tier filter:

```
[2D Sieve Survivor (n, t)]
          |
          v
[Stage 1: Base-2 Fermat PRP on A = C - 1]
    --> Rejects ~99.7% of survivors in ~38 ms
          |
          v (Only ~0.3% reach Stage 2)
[Stage 2: Base-2 Fermat PRP on B' = C + 1]
    --> Rejects remaining non-twin composites
          |
          v
[Stage 3: Multi-Round Miller-Rabin (25 rounds)]
    --> Confirms Dual Probable Prime (Dual PRP)
          |
          v
[Stage 4: Deterministic Primality Prover]
```

---

## 4. Deterministic Primality Proof Routing

### 4.1 Upper Member $B' = k \cdot 2^n + 1$ (Proth's Theorem)
**Theorem (Proth, 1878):**  
Let $B' = k \cdot 2^n + 1$ with $k$ odd and $0 < k < 2^n$. If there exists an integer $w$ such that:
$$w^{\frac{B' - 1}{2}} \equiv -1 \pmod{B'}$$
then $B'$ is unconditionally prime.

*Proof Search Policy:* Test small prime witnesses $w \in \{3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47\}$. If $\left(\frac{w}{B'}\right) = -1$, Euler's criterion guarantees $w^{(B'-1)/2} \equiv -1 \pmod{B'}$ for prime $B'$.

### 4.2 Lower Member $A = k \cdot 2^n - 1$ (Lucas-Lehmer-Riesel Theorem)
**Theorem (Riesel 1969, Rodseth 1994):**  
Let $A = k \cdot 2^n - 1$ with $k$ odd, $k < 2^n$, and $n \ge 2$. Let $P$ be an integer such that the Jacobi symbols satisfy:
$$\left(\frac{P - 2}{A}\right) = 1 \quad \text{and} \quad \left(\frac{P + 2}{A}\right) = -1$$
Define the Lucas sequence $V_k(P, 1)$ with $u_0 = V_k(P, 1) \bmod A$, and the recurrence:
$$u_{m+1} \equiv u_m^2 - 2 \pmod A$$
Then $A$ is prime if and only if $u_{n-2} \equiv 0 \pmod A$.

*Initial Value Computation:* $u_0 = V_k(P, 1) \bmod A$ is computed in the prover using the Montgomery binary ladder:
$$V_{2m} = V_m^2 - 2 \pmod A, \quad V_{2m+1} = V_m V_{m+1} - P \pmod A$$
and independently verified using $2 \times 2$ companion matrix powering:
$$\begin{pmatrix} V_k \\ V_{k-1} \end{pmatrix} \equiv \begin{pmatrix} P & -1 \\ 1 & 0 \end{pmatrix}^{k-1} \begin{pmatrix} P \\ 2 \end{pmatrix} \pmod A$$

---

## 5. Schema 8.0 Cryptographic Certificate Structure

All discoveries produce a canonical JSON certificate containing:
- `schema_version`: `"8.0"`
- `campaign_id`: Campaign identifier
- `discovery_type`: `"CERTIFIED_FRESH_RECORD"` (if $D \ge 1,511$)
- `representation`: Parameters $R$, $M_R$, $t$, $k$, $n$
- `pair`: Decimal strings of $C$, $A$, $B'$, exact digit count $D$, and difference 2
- `proofs`:
  - `lower_member`: Theorem, parameter $P$, Jacobi symbols, $u_0$, LLR rounds $n-2$, final residue 0, prover time
  - `upper_member`: Theorem, witness $w$, congruence verification, prover time
- `search_evidence`: Sieve depth, screener configuration, UTC timestamps
- `sha256`: SHA-256 digest of canonical compact JSON representation excluding the `sha256` key.

---

## 6. Decoupled Independent Verifier Specification

The independent verifier `scripts/phase8_independent_verify.py` is completely decoupled with **zero repository imports**:
- Reconstructs $M_R$, $k$, $C$, $A$, $B'$ from integers.
- Re-computes and checks canonical SHA-256 digest.
- Verifies $B' - A == 2$, $C \equiv 0 \pmod 6$, and digit count $\ge 1,511$.
- Evaluates Proth witness congruence.
- Evaluates Jacobi conditions, companion matrix powering for $u_0$, and $n-2$ LLR squarings.
- Emits signed attestation JSON: `proofs/phase8/attestations/attest_<sha16>.json`.
- Fail-closed: any tampered field or failed congruence terminates with non-zero exit code.
