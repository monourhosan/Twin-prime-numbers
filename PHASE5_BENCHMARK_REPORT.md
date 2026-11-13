# Phase 5 Comprehensive Benchmark Report

**Repository:** https://github.com/monourhosan/Twin-prime-numbers  
**Mission Phase:** Phase 5 SCCA (Smooth-Center Certificate-Aware Search)  
**Date:** 2026-11-14T04:27:00+06:00  

---

## 1. Benchmarking Environment

| Specification | Details |
|---|---|
| Processor | Intel(R) Core(TM) i5-10210U CPU @ 1.60GHz (4 physical cores, 8 threads) |
| Memory | 11.85 GB physical RAM (12 GB visible) |
| Operating System | Microsoft Windows 11 Home 64-bit |
| Python Version | Python 3.12.10 (AMD64) |
| Big-Integer Backend | gmpy2 2.3.2 (backed by GMP arbitrary-precision C arithmetic) |
| Computer Algebra Oracle | SymPy 1.14.0 |
| Baseline Sieve Limits | $L = 50,000$ (comparative benchmarks) and $L = 500,000$ (production search) |

---

## 2. Multi-Family Portfolio & Scheduler Comparison

### 2.1 Family Search Space Definitions
Three mathematically distinct candidate-generation families were configured and benchmarked under identical hardware constraints:
1. **`fam_scca_p3_dense`:** $F_1 = 2^1 \cdot 3^{40} \cdot 5^{10}$ (~27 digits, smooth base $\{2, 3, 5\}$).
2. **`fam_scca_balanced_multibase`:** $F_2 = 2^3 \cdot 3^{20} \cdot 5^{10} \cdot 7^6 \cdot 11^3$ (~26 digits, smooth base $\{2, 3, 5, 7, 11\}$).
3. **`fam_scca_sparse_highbase`:** $F_3 = 2^2 \cdot 3^{25} \cdot 7^{10} \cdot 13^5 \cdot 17^3$ (~31 digits, smooth base $\{2, 3, 7, 13, 17\}$).

### 2.2 Controlled Policy Results (Equal Budget of 6,000 Candidates)

| Metric | Round-Robin (`ROUND_ROBIN`) | UCB1 Bandit (`BANDIT_UCB1`) | Cost-Aware Bandit (`COST_AWARE`) |
|---|---|---|---|
| Candidates Screened | 6,000 | 6,000 | 6,000 |
| Wall-Clock Time | 3.53 s | 3.80 s | **3.15 s** |
| Throughput | 1,702 cands/s | 1,580 cands/s | **1,906 cands/s (+12.0%)** |
| Arm Allocation Ratio | 4 / 4 / 4 (Uniform) | 4 / 4 / 4 (Exploration) | 7 / 2 / 3 (Exploited fast arm) |
| Certified Twin Pairs | 25 | 25 | 19 |
| Independent Verification | 100% PASS | 100% PASS | 100% PASS |

**Analysis:** Cost-aware scheduling correctly preferred the ternary-dominant family `fam_scca_p3_dense` because its smaller prime base allowed faster GCD verification, boosting search throughput by +12.0% over round-robin.

---

## 3. Comparative Benchmark: Phase 4 ADRS-4 vs Phase 5 SCCA

A controlled head-to-head comparison was executed across three digit bands under identical hardware and gmpy2 acceleration:

### 3.1 Pre-Sieve Throughput ($L = 50,000$, Window = 20,000 Candidates)

| Candidate Scale | Phase 4 ADRS-4 (cands/s) | Phase 5 SCCA (cands/s) | SCCA Advantage |
|---|---|---|---|
| **100 decimal digits** | 2,623,157 cands/s | **5,103,864 cands/s** | **+1.95x** |
| **500 decimal digits** | 2,512,468 cands/s | **5,101,390 cands/s** | **+2.03x** |
| **1,500 decimal digits** | 2,477,148 cands/s | **5,065,600 cands/s** | **+2.05x** |

**Observation:** SCCA's pre-sieve delivers >5 million candidates/second across all digit scales, approximately double the speed of Phase 4's $t$-space sieve. This speedup is achieved because the forbidden residue classes $\pm F^{-1} \pmod q$ are invariant across the entire family and precomputed once, reducing sieving to direct memory strides without runtime arithmetic.

### 3.2 Primality Proof Generation Latency (Pair $A$ and $B$)

| Candidate Scale | Phase 4 Proth + LLR (ms) | Phase 5 Pocklington + Morrison (ms) | Ratio |
|---|---|---|---|
| **100 decimal digits** | **0.51 ms** | 0.90 ms | 1.76x |
| **500 decimal digits** | **6.10 ms** | 27.51 ms | 4.51x |
| **1,500 decimal digits** | **118.02 ms** | 500.76 ms | 4.24x |

**Observation:** Phase 4's LLR proof is faster than Phase 5's Morrison proof at 1,500 digits because LLR uses scalar squaring ($S_{k+1} = S_k^2 - 2 \pmod A$), whereas Morrison requires $2 \times 2$ companion matrix powering ($4\times$ modular multiplications per binary step) and GCD checks for each factor in $F_{odd}$.

---

## 4. Pipeline Design Trade-Offs

1. **Sieve Superiority:** SCCA provides a 2x faster pre-sieve, eliminating ~96.5% of candidates at $L=50,000$ and ~97.5% at $L=500,000$.
2. **Proof Prudence:** Because Morrison proofs take ~500 ms at 1,510 digits, the pipeline must employ aggressive multi-tier PRP filtering (single-round base-2 Fermat screening followed by 25-round Miller-Rabin) to ensure deterministic proofs are only launched for genuine prime survivors.

---

## 5. Limitations & Statistical Caveats

- Bandits were evaluated on a controlled sample of 12 allocations. For production searches over millions of candidates, reward non-stationarity will require rolling or discounted UCB policies.
- Sieve depth beyond $L = 1,000,000$ exhibits diminishing returns due to L1/L2 cache pressure on laptop hardware.
- Raw machine-readable benchmark telemetry is preserved at:
  - `research/phase5_benchmarks/raw/scheduler_comparison.json`
  - `research/phase5_benchmarks/raw/phase4_vs_phase5.json`
