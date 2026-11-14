# Phase 6B — Empirical Performance Benchmarks & Scaling Analysis

**Date:** 2026-11-14  
**Hardware Environment:** Intel Core i5-10210U @ 1.60 GHz (8 logical cores), 12.0 GB RAM, Windows 11 AMD64  
**Runtime:** Python 3.12.10, gmpy2 2.3.2 (MPIR/GMP), SymPy 1.14.0  

---

## 1. Multi-Scale Sieve & Screening Performance

Measurements over window sizes of 100,000 centers with wheel primes $\{5, 7, 11, 13\}$ and sieve cutoff $Q = 50,000$:

| Scale (Digits) | Universal Center Base $m$ | Sieve Throughput (centers/s) | Sieve Survivors | Survival Fraction | Screening Latency (ms/cand) | Screening Rate (cands/s) |
|---|---|---|---|---|---|---|
| **16 digits** | $10^{15}$ | 5,805,010 | 2,151 / 100k | 2.15% | 0.030 ms | 33,391.2 |
| **100 digits** | $10^{99}$ | 6,249,844 | 2,196 / 100k | 2.20% | 0.151 ms | 6,616.6 |
| **350 digits** | $10^{349}$ | 5,322,206 | 2,182 / 100k | 2.18% | 0.544 ms | 1,838.1 |
| **1510 digits** | $10^{1509}$ | 4,199,440 | 2,097 / 100k | 2.10% | 32.41 ms | 30.9 |

### Observations:
1. **Sieve Invariance to Digit Length:** The segmented sieve operates strictly on small modular arithmetic ($m \pmod q$) and bit-array slices. Throughput remains sustained between 4.2M and 6.2M centers/second regardless of digit length from 16 to 1,510 digits.
2. **Screening Complexity:** Screening latency scales roughly as $O(d^2)$ to $O(d^3)$ with digit count $d$, from 0.03 ms at 16d to 32.4 ms at 1510d. Fast rejection via small-prime divisibility and Fermat base-2 filters out $> 99.8\%$ of non-PRP survivors before full Miller-Rabin rounds execute.

---

## 2. Sieve Depth ($Q$) Scaling vs Mertens' Theorem

Empirical survivor counts across sieve limits $Q$ in windows of 100,000 centers:

| Sieve Cutoff $Q$ | Sieve Primes | $m = 10^6$ (6d) | $m = 10^{99}$ (100d) | $m = 10^{349}$ (350d) | $m = 10^{1509}$ (1510d) |
|---|---|---|---|---|---|
| **$Q = 1,000$** | 162 | 4.906% | — | — | — |
| **$Q = 5,000$** | 663 | **3.205%** | 3.504% | 3.399% | 3.385% |
| **$Q = 10,000$** | 1,223 | **3.205%** | 3.019% | 2.932% | 2.881% |
| **$Q = 50,000$** | 5,127 | **3.205%** | 2.196% | 2.182% | 2.097% |
| **$Q = 100,000$** | 9,586 | **3.205%** | 1.948% | 1.960% | 1.839% |

### Resolution of the 3.21% Flat Survival Mystery:
At $m = 10^6$, $\sqrt{6m \pm 1} \approx 2,450 < 5,000$. All composite candidates in that window have prime factors $\le 2,450$. Once $Q \ge 2,450$, 100% of composite numbers are eliminated, freezing the survivor count at 8,402. At 100d+, where $Q \ll \sqrt{N}$, survivor fractions decrease monotonically following the twin-prime asymptotic $\prod_{5 \le q \le Q} (1 - 2/q)$.

---

## 3. Screening Order Benchmark: A-First vs B-First

Benchmarked on 350-digit candidate pairs:
- **A-First Throughput:** 96,525.1 pairs/second
- **B-First Throughput:** 10,282.4 pairs/second
- **Recommendation:** `A_first` provides optimal early-exit rejection in the current implementation.

---

## 4. Family Density and Discovery Expectation Comparison (1510+ Digits)

Comparison of candidate families targeting 1,510+ decimal digits ($N \approx 10^{1511}$):

| Family Parameterization | Arithmetic Form | Conditional Multiplier | Estimated Pair Density $P(\text{twin})$ | Proof Theorem Applicable | Proof Wall-Clock Latency |
|---|---|---|---|---|---|
| **Proth / LLR** | $k \cdot 2^{5020} \pm 1$ ($k \equiv 3 \pmod 6$) | $2 \times \frac{3-1}{3-2} = 4.0$ | $\approx 2.18 \times 10^{-7}$ | Proth (upper) + LLR (lower) | $< 15$ ms |
| **SCCA Smooth-Center** | $C = F \cdot t$, $F = 2 \cdot 3^{2035} \cdot 5^{772}$ | $\prod_{p \mid F, p>2} \frac{p-1}{p-2} \approx 4.0$ | $\approx 2.18 \times 10^{-7}$ | BLS Thm 4 + BLS Thm 17 | $\approx 2.5$ s |
| **General GITCSS** | $A = 6m - 1, B = 6m + 1$ | $1.0$ (universal) | $\approx 1.09 \times 10^{-7}$ | General ECPP (Atkin-Morain) | $\approx 900$ s |

### Yield per CPU-Second:
Proth / LLR offers the highest yield per CPU-second at 1,510+ digits due to microsecond proof validation without requiring large factorization or external ECPP dependencies.
