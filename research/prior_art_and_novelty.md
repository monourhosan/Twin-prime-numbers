# Prior Art Review and Novelty Audit

**Document Version:** 1.0.0  
**Research Date:** 2026-11-12  
**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Author:** Antigravity Research Group

---

## 1. Prior Art in Twin Prime Search and Verification

Large-scale twin prime searches have a storied history spanning over five decades of computational number theory.

### 1.1 Historical Sieving and Search Frameworks
1. **Classical Sieve of Eratosthenes & Wheel Factorization:**
   * Wheel factorization removes multiples of small primes (e.g., $2, 3, 5$) by precomputing coprimality wheels (Pritchard, 1981).
   * For twin primes, restricting candidate centers to multiples of 6 ($6r \pm 1$) represents a 2-3 wheel, which has been standard practice since the 19th century.
2. **Specialized Sieve Tools (NewPGen, TwinGen, PSIEVE, Cyclo):**
   * **NewPGen (Paul Jobling, 2001):** Widely used tool for generating sieve tables for linear forms $k \cdot b^n \pm 1$. Utilizes discrete logarithm techniques and fast assembly-optimized sieving.
   * **TwinGen (Yves Gallot, 2004):** Purpose-built sieve generator for twin and Sophie Germain primes of the form $k \cdot 2^n \pm 1$. Uses dual residue elimination.
   * **PRST (Proth and Riesel Sieve Tester by Roman Trunov, 2020–2026):** GPU- and multicore-accelerated tool using AVX-512 and OpenCL for sieving and PRP testing.
3. **Primality Proving Software (LLR, OpenPFGW, Primo):**
   * **LLR (Lucas-Lehmer-Riesel by Jean Penné):** Implementation of Proth's test and Lucas-Lehmer-Riesel test utilizing George Woltman's GMP/GWNUM FFT engine. LLR has powered the vast majority of PrimeGrid record discoveries.
   * **OpenPFGW (Chris Nash, Jim Fougeron et al.):** Fast probable prime tester for arbitrary expressions, utilizing fast Fourier transform (FFT) multiplication.
   * **Primo (Marcel Martin):** Implements Elliptic Curve Primality Proving (ECPP) providing independently verifiable certificates for general primes.

---

## 2. Distinction: Established Techniques vs. CATS Contributions

| Component | Status in Literature | CATS Design Status |
| :--- | :--- | :--- |
| Candidate filtering via $6r \pm 1$ | **Standard / Classical** (Known since Euler) | Adopted as necessary baseline for bounded mode. |
| Divisibility condition $k \equiv \pm a^{-1} \pmod q$ | **Established** (Riesel 1969, Gallot 2004) | Adopted; paired in unified bitset elimination. |
| Proth's Theorem ($k < 2^n$) | **Established** (Proth 1878) | Implemented deterministically for upper member. |
| BLS Theorem 4 ($N+1$ test) | **Established** (Brillhart, Lehmer, Selfridge 1975) | Implemented deterministically for lower member. |
| Dual-residue bitset memory layout | **Scattered / Ad-hoc** in specialized C/ASM tools | Unified native word-level Rust implementation with bitmask operations. |
| Adaptive Sieve-Depth (ASD) Calibration | **Heuristic / Manual tuning** in prior art | Formulated as an online cost-minimization function balancing sieve vs. PRP/proof runtime. |
| Certificate-Cost-Aware Pipeline (CCAP) | **Rarely integrated**; tools separate sieve from proof | Asymmetric early-exit ordering with automatic cryptographic JSON certificate serialization. |

---

## 3. The Proposed Algorithmic Variant: CATS

We designate our unified search and verification architecture as **CATS** (*Certificate-Aware Adaptive Twin-prime Sieve*).

### 3.1 Three Competing Candidate Improvements

To evaluate CATS rigorously, we define three specific algorithmic enhancements and subject them to an empirical ablation study:

1. **Improvement 1: Wheel-Aware Dual-Residue Bitset Sieve (DR-Sieve)**
   * *Mechanism:* Precomputes modular inverses $a^{-1} \pmod q$ for all $q \le Q$. Updates a tightly packed 64-bit integer array where both residue classes are eliminated in contiguous memory access patterns to maximize L1/L2 CPU cache residency.
   * *Ablation Baseline:* Standard sequential single-residue elimination.
2. **Improvement 2: Adaptive Sieve Depth (ASD)**
   * *Mechanism:* Dynamically selects the optimal sieve cutoff $Q^*(n)$ by profiling the marginal CPU cost per candidate eliminated versus the measured cost of big-integer probable-prime and certification tests for exponent $n$.
   * *Ablation Baseline:* Fixed arbitrary sieve depth (e.g., static $Q = 10^5$).
3. **Improvement 3: Certificate-Cost-Aware Pipeline (CCAP)**
   * *Mechanism:* Asymmetric verification ordering:
     1. Inexpensive Miller-Rabin 2-base PRP screen.
     2. Deterministic Proth test on $B = k \cdot 2^n + 1$ using minimal quadratic non-residue base ($a=3$ when $B \equiv 5 \pmod 8$ or via Jacobi symbol).
     3. Only if $B$ is proven prime, initiate the $N+1$ BLS test on $A = k \cdot 2^n - 1$.
     4. Serialize a self-contained, tamper-evident JSON certificate with SHA-256 verification hash.
   * *Ablation Baseline:* Unordered testing or attempting simultaneous dual PRP tests.

---

## 4. Formal Novelty Classification

* **Integrity Statement:** We do **not** claim a new mathematical theorem or discovery of a new class of primes.
* **Algorithmic Classification:** CATS is classified as a **“proposed algorithmic variant”** and an integrated software synthesis. Its novelty lies in:
  1. The automated online balancing of sieve depth against formal primality certificate generation costs;
  2. The end-to-end integration of dual-residue sieving with dual-member deterministic certification (Proth + BLS) emitting portable certificates.
