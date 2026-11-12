# Prior Art, Theoretical Foundations, and Historical Context

**Author / Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  

---

## 1. The Twin Prime Conjecture and Asymptotics

A twin prime pair consists of primes $(p, p+2)$. The **Twin Prime Conjecture** asserts that there exist infinitely many primes $p$ such that $p+2$ is also prime. While landmark analytic advances by Yitang Zhang (2013), James Maynard (2015), and the Polymath8 project established finite bounded prime gaps ($\liminf_{n\to\infty} (p_{n+1} - p_n) \le 246$), the gap of 2 remains unproved.

According to the **First Hardy-Littlewood Conjecture** (1923), the number of twin primes $\pi_2(x) \le x$ obeys:
$$\pi_2(x) \sim 2 C_2 \int_2^x \frac{dt}{(\ln t)^2}$$
where $C_2 \approx 0.6601618158$ is the twin prime constant.

---

## 2. Specialized Search Families: $k \cdot 2^n \pm 1$

Searching for large twin primes among generic integers requires general-purpose primality proving algorithms such as the Adleman-Pomerance-Rumely (APR-CL) test or Elliptic Curve Primality Proving (ECPP), which scale as $O((\ln N)^{4+\epsilon})$.

By restricting candidates to the form:
$$A = k \cdot 2^n - 1, \quad B = k \cdot 2^n + 1$$
the factorization of $B - 1 = k \cdot 2^n$ and $A + 1 = k \cdot 2^n$ is fully known. This enables deterministic primality proving in $O(n \cdot M(\text{bits}(N)))$ using specialized algebraic number theory:

### 2.1 Proth's Theorem (1878)
François Proth published his test in 1878 for numbers of the form $B = k \cdot 2^n + 1$ with $k$ odd and $k < 2^n$. If an integer $w$ satisfies:
$$w^{\frac{B-1}{2}} \equiv -1 \pmod B$$
then $B$ is unconditionally prime.
- *Citation:* Proth, F. (1878). "Théorèmes sur les nombres premiers." *Comptes Rendus de l'Académie des Sciences Paris*, 87, 926.
- *Modern formulation:* Robinson, R. M. (1957). "A report on primes of the form $k \cdot 2^n + 1$ and on factors of Fermat numbers." *Proc. Amer. Math. Soc.*, 8(5), 849-855.

### 2.2 Lucas-Lehmer-Riesel (LLR) Test
Hans Riesel extended the Lucas-Lehmer test to numbers $A = k \cdot 2^n - 1$ in 1969.
- *Citation:* Riesel, H. (1969). "Lucasian Numbers." *Nordisk Tidskrift for Informationsbehandling (BIT)*, 9, 257–264.
- *General Proof Framework:* Brillhart, J., Lehmer, D. H., & Selfridge, J. L. (1975). "New Primality Criteria and Factorizations of $2^m \pm 1$." *Mathematics of Computation*, 29(130), 620–647.

---

## 3. Presieving, Wheels, and Prior Computational Implementations

To search regions containing billions of candidates efficiently, distributed projects use pre-filtering and wheel sieving:
- **TwinGen & NewPGen:** Established tools authored by Yves Gallot and Paul Jobling that pre-sieve twin candidates using modular linear forms and fast Fourier transform (FFT) multiplication.
- **PrimeGrid:** A distributed computing platform running LLR and Genefer clients.
  - PrimeGrid discovered the current **world-record twin-prime pair** on September 19, 2016:
    $$2,996,863,034,895 \times 2^{1,290,000} \pm 1 \quad (388,342\text{ decimal digits})$$
  - Discovered using the LLR software engine written by Jean Penné.

---

## 4. Distinction Between Algorithmic Engineering and Mathematical Novelty

The mathematical theorems (Proth, LLR, CRT, Lucas sequences) are established classical results. The contribution of this Phase 2 project lies in:
1. Deriving and integrating a self-contained, bounded-memory CRT wheel with streaming window sieving;
2. Implementing the Montgomery doubling ladder for $O(\log k)$ Lucas sequence initialization;
3. Enforcing full mathematical preconditions ($k < 2^n$, Jacobi symbol validation, strictly separate hash integrity from theorem proof);
4. Delivering verified, new-to-project discoveries scaling from the 34-digit baseline up to 159 decimal digits.
