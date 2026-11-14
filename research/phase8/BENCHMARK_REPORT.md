# Phase 8 ADES-8 Performance and Benchmark Report

**Date:** 2026-11-14  
**Author:** Google Antigravity (Performance Engineering and Number-Theoretic Sieve Audit)  
**Host Environment:** Intel(R) Core(TM) i5-10210U CPU @ 1.60GHz (4C/8T), 12 GB RAM, Windows 11, Python 3.12.10, `gmpy2` 2.3.2  
**Target Search Band:** $D = 1,515$ decimal digits ($10^{1514}+1 \le C \le 10^{1515}-2$)  
**Raw Benchmark Data:** [`research/phase8/benchmarks_raw.csv`](benchmarks_raw.csv)

---

## 1. Executive Summary

Phase 8 introduced the **Adaptive Dual-axis Exponent Sieve (ADES-8)** architecture, evaluating a two-dimensional modular recurrence across adjacent exponent rows $n$ and parameter coordinates $t$.

### Key Findings
1. **Bitwise Exactness:** Variant A (1D fixed exponent), Variant B (2D direct recomputation), and Variant C (ADES-8 modular root recurrence) produced **100% identical survivor sets** (11,493 survivors out of 160,000 raw candidates).
2. **Kernel Speedup:** Variant C achieved **1,553,092 candidates/sec** (103.02 ms) versus Variant B's 664,013 cand/s (240.96 ms), demonstrating a **2.34x kernel speedup** solely by replacing logarithmic modular exponentiation with $O(1)$ row recurrence ($a_{n+1} = a_n \cdot 2^{-1} \bmod r$). Compared to the Phase 7 1D baseline (Variant A, 552,059 cand/s), the speedup is **2.81x**.
3. **Pipeline Bottleneck Identification:** While sieving throughput is very high (>1.55M cand/s), the dominant wall-clock cost in twin-prime search at $D=1,515$ digits is the first-stage Fermat PRP rejection test (37.97 ms per survivor). Sieve depth tuning ($S \ge 100,000$) reduces survivor density to $6.28\%$, maximizing end-to-end candidate throughput.

---

## 2. Kernel Microbenchmark Comparison

Tested over identical candidate space:
- Exponent block: $n \in [5000, 5015]$ ($H = 16$ rows)
- Parameter range: $t \in [20000, 30000]$ ($W = 10,000$ width per row)
- Total candidate centers: $N = 16 \times 10,000 = 160,000$
- Sieve limit: $S = 50,000$ primes ($5,131$ odd primes coprime to $M_{13}$)
- Primorial multiplier: $M_{13} = 15,015$ ($R = 13$)

| Implementation Variant | Description | Wall Time (ms) | Sieve Throughput (cand/s) | Bitwise Survivors | Speedup vs Ref |
|:---|:---|:---:|:---:|:---:|:---:|
| **Variant A** | HDC-7 1D Baseline (row-by-row) | 289.82 ms | 552,059 | 11,493 | 0.83x |
| **Variant B** | CPU Reference 2D (independent roots) | 240.96 ms | 664,013 | 11,493 | 1.00x |
| **Variant C** | **ADES-8 Recurrence 2D** ($a_{n+1} = a_n \cdot b \bmod r$) | **103.02 ms** | **1,553,092** | **11,493** | **2.34x** |

> **Conclusion:** The ADES-8 modular root recurrence is both mathematically rigorous and empirically superior, cutting sieve initialization and setup overhead by more than half.

---

## 3. Parameter Sensitivity and Sieve Scaling

### 3.1 Primorial Multiplier Cutoff ($R = 13, 31, 47, 97$)
Evaluated on an $8 \times 10,000$ tile ($80,000$ candidates) with $S = 50,000$:

| Primorial Cutoff $R$ | $M_R$ Bit Length | Primorial Gain $G(R)$ | Sieve Time (ms) | Survivors ($f(S)$) |
|:---:|:---:|:---:|:---:|:---:|
| **$R = 13$** | 14 bits | 3.3704 | 68.53 ms | 5,719 (7.15%) |
| **$R = 31$** | 37 bits | 5.3684 | 78.02 ms | 9,262 (11.58%) |
| **$R = 47$** | 59 bits | 6.5354 | 80.71 ms | 11,275 (14.09%) |
| **$R = 97$** | 120 bits | 8.7039 | 51.21 ms | 14,794 (18.49%) |

*Note:* Higher $R$ increases theoretical twin prime density $G(R)$, but also leaves more primes dividing $M$ un-sieved by the outer sieve (since primes $p \mid M$ cannot eliminate candidates mod $p$). For compact $t$-space searches with $k < 2^n$, $R = 13$ ($M = 15,015$) provides the ideal balance between compact integer size and low survivor density.

### 3.2 Tile Height Scaling ($H \in \{4, 8, 16, 32\}$)
Evaluated with $W = 10,000$ and $S = 50,000$:

| Height $H$ (Rows) | Total Candidates | Wall Time (ms) | Throughput (cand/s) |
|:---:|:---:|:---:|:---:|
| 4 | 40,000 | 30.88 ms | 1,295,521 |
| 8 | 80,000 | 51.10 ms | 1,565,582 |
| 16 | 160,000 | 100.49 ms | 1,592,257 |
| 32 | 320,000 | 191.88 ms | 1,667,717 |

*Note:* Throughput increases monotonically with tile height $H$ because the initial modular inverse setup at row 0 is amortized over more rows. $H = 16$ captures $>95\%$ of asymptotic throughput while maintaining low working memory.

### 3.3 Sieve Depth Scaling ($S \in \{20\text{k}, 50\text{k}, 100\text{k}, 250\text{k}\}$)
Evaluated on an $8 \times 10,000$ tile:

| Sieve Limit $S$ | Sieve Primes | Sieve Time (ms) | Survivors | Survivor Fraction $f(S)$ |
|:---:|:---:|:---:|:---:|:---:|
| 20,000 | 2,258 | 30.32 ms | 6,814 | 8.52% |
| 50,000 | 5,127 | 52.31 ms | 5,728 | 7.16% |
| 100,000 | 9,588 | 89.86 ms | 5,024 | 6.28% |
| 250,000 | 22,039 | 201.14 ms | 4,252 | 5.32% |

---

## 4. End-to-End Pipeline Latency at $D = 1,515$ Digits

Measured stage latencies on authentic 1,515-digit integers:

| Pipeline Stage | Operation Description | Measured Latency | Throughput |
|:---|:---|:---:|:---:|
| **Stage 0: 2D Sieve** | ADES-8 modular recurrence marking | 0.64 $\mu$s / cand | 1,553,000 cand/s |
| **Stage 1: Fermat PRP-A** | Fast Base-2 powmod on lower member $A = C - 1$ | 37.97 ms / test | 26.3 tests/s |
| **Stage 2: Fermat PRP-B** | Fast Base-2 powmod on upper member $B' = C + 1$ | 37.97 ms / test | 26.3 tests/s |
| **Stage 3: Miller-Rabin** | 25-round probabilistic confirmation | 28.77 ms / test | 34.8 tests/s |
| **Stage 4: Proth Proof** | Witness exponentiation $w^{(B'-1)/2} \equiv -1 \pmod{B'}$ | 29.11 ms / proof | 34.3 proofs/s |
| **Stage 5: LLR Proof** | 4,998 modular squarings $u \leftarrow (u^2 - 2) \pmod A$ | 31.00 ms / proof | 32.2 proofs/s |

### Optimization Impact
Because Stage 1 (Fermat PRP on $A$) rejects $\approx 99.7\%$ of sieve survivors, Stage 2 (Fermat PRP on $B'$) is executed on fewer than $0.3\%$ of survivors. Miller-Rabin and deterministic proofs (Stages 3–5) are executed exclusively on dual PRPs. The total deterministic certification time for both members combined is less than **70 milliseconds**.
