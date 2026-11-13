# Phase 4 ADRS-4 vs Phase 5 SCCA Empirical Benchmark Report

**Date:** 2026-11-14T04:22:00+06:00  
**Phase:** Stage E Benchmark Comparison  
**Deliverable:** Fair Comparative Evaluation of Phase 4 and Phase 5 Search Architectures  

---

## 1. Executive Summary

We performed an end-to-end controlled comparative benchmark between **Phase 4 ADRS-4** (Fixed-Exponent $k \cdot 2^n \pm 1$ with Proth + LLR proofs) and **Phase 5 SCCA** (Smooth-Center $C = F \cdot t$ with Pocklington + Morrison proofs). 

Both engines were benchmarked on identical host hardware (Intel Core i5-10210U, gmpy2 2.3.2 enabled, single worker, identical memory and thermal environment) across three digit regimes:
- **100-digit scale** ($n=330$ vs $F \approx 10^{100}$)
- **500-digit scale** ($n=1664$ vs $F \approx 10^{500}$)
- **1,500-digit scale** ($n=4992$ vs $F \approx 10^{1510}$)

---

## 2. Benchmark Protocol & Controls

| Dimension | Phase 4 (ADRS-4) | Phase 5 (SCCA) | Control Note |
|---|---|---|---|
| Search Mathematical Domain | $C = k \cdot 2^n$, $k$ odd | $C = F \cdot t$, $t \in \mathbb{N}$ | Distinct algebraic spaces; comparison evaluates search architecture efficiency |
| Small Prime Pre-Sieve | Wheel streaming + $t$-space sieve | Segmented bitmask filter on $t \not\equiv \pm F^{-1} \pmod q$ | Evaluated at identical sieve depth $L = 50,000$ |
| Candidate Interval Span | 20,000 candidate window | 20,000 candidate window | Identical candidate volume per trial |
| Primality Proof (Upper) | Proth Theorem 1878 ($w^{(B-1)/2} \equiv -1 \pmod B$) | Pocklington / BLS Thm 4 ($a^{B-1} \equiv 1 \pmod B$, $\gcd=1$) | Both deterministic certificates |
| Primality Proof (Lower) | Lucas-Lehmer-Riesel / Rodseth ($S_{k+1} = S_k^2 - 2 \pmod A$) | Morrison / BLS Thm 17 ($U_{A+1} \equiv 0 \pmod A$, $\gcd=1$) | Both deterministic certificates |
| Big-Integer Engine | gmpy2 2.3.2 (GMP backend) | gmpy2 2.3.2 (GMP backend) | Exact arbitrary-precision arithmetic |
| Number of Repeated Trials | 5 trials (median reported) | 5 trials (median reported) | Minimizes OS scheduling jitter |

---

## 3. Empirical Results: Stage-by-Stage Breakdown

### 3.1 Sieve Throughput (Depth $L = 50,000$)

| Scale | Phase 4 Time (ms) | Phase 4 Rate (cands/s) | Phase 5 Time (ms) | Phase 5 Rate (cands/s) | SCCA Sieve Speedup |
|---|---|---|---|---|---|
| **100 digits** | 7.62 ms | 2,623,157 cands/s | **3.92 ms** | **5,103,864 cands/s** | **+1.95x** |
| **500 digits** | 7.96 ms | 2,512,468 cands/s | **3.92 ms** | **5,101,390 cands/s** | **+2.03x** |
| **1,500 digits** | 8.07 ms | 2,477,148 cands/s | **3.95 ms** | **5,065,600 cands/s** | **+2.05x** |

**Sieve Analysis:** SCCA's sieve throughput is consistently **~2x faster** than Phase 4's $t$-space sieve. In SCCA, the forbidden residue offsets $\pm F^{-1} \bmod q$ are precomputed once for the family smooth base $F$. Applying them to a candidate segment requires only two memory-strided bit-clearing slices per prime $q$, completely eliminating runtime modular reductions during the sieve loop.

### 3.2 Primality Proof Generation Latency (Pair $A$ & $B$)

| Scale | Phase 4 (Proth + LLR) | Phase 5 (Pocklington + Morrison) | Latency Ratio |
|---|---|---|---|
| **100 digits** | **0.51 ms** | 0.90 ms | Phase 4 is 1.76x faster |
| **500 digits** | **6.10 ms** | 27.51 ms | Phase 4 is 4.51x faster |
| **1,500 digits** | **118.02 ms** | 500.76 ms | Phase 4 is 4.24x faster |

**Proof Latency Analysis:**
- Phase 4's Proth + LLR proof is faster per pair at large digit scales. This is because:
  1. LLR evaluates $n - 2$ iterations of $S = S^2 - 2 \pmod A$ (a single scalar modular squaring per step).
  2. Morrison's Lucas sequence evaluation $U_{A+1}(\mathcal{P}, 1)$ operates via $2 \times 2$ companion matrix multiplication modulo $A$. Each matrix multiplication requires 4 modular multiplications, increasing the computational constant by roughly $4\times$.
  3. SCCA proofs must additionally evaluate $\gcd$ checks for every prime factor in $F_{odd}$ (e.g. factors 3 and 5).

---

## 4. End-to-End Search Pipeline Implications

1. **Where SCCA Excels:**
   - **Candidate Filtering Speed:** At 5.1 million candidates/second, SCCA's pre-sieve eliminates ~96.5% of candidates at nearly zero computational cost.
   - **Mathematical Flexibility:** SCCA is not restricted to fixed power-of-2 structures ($k \cdot 2^n \pm 1$). It allows exploring arbitrary smooth core compositions ($2^a 3^b 5^c \dots$).
2. **Where SCCA Incurs Cost:**
   - **Proof Burden:** When a dual-PRP survivor is identified, certifying a 1,510-digit pair takes ~500 ms in SCCA versus ~118 ms in Phase 4.
   - **Pipeline Optimization:** Because proof generation is ~4x slower, a strict multi-tier PRP filter (e.g. single-round base-2 Fermat screening followed by 25-round Miller-Rabin) is essential before launching full deterministic proofs. This ensures deterministic proofs are only attempted on true prime candidates.

---

## 5. Gate E Sign-Off

- [x] Controlled benchmark protocol executed across 100d, 500d, and 1500d scales.
- [x] Sieve throughput and proof latency measured independently.
- [x] Caveats and trade-offs between ADRS-4 and SCCA documented.
- [x] Raw telemetry persisted in machine-readable JSON at `research/phase5_benchmarks/raw/phase4_vs_phase5.json`.
- **GATE E STATUS: PASSED.** Ready to proceed to Stage F.
