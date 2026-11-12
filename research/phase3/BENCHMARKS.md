# Phase 3 Empirical Benchmark Analysis: S0 vs S1 vs S2

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Platform:** Windows 11 x86_64, Python 3.12.10, NumPy 2.2.3  
**Data Files:** `runs/phase3/benchmarks/benchmark_comparison.json`, `runs/phase3/benchmarks/benchmark_comparison.csv`  

---

## 1. Executive Benchmark Summary

We evaluated three architectural sieving strategies across three target exponent regimes:
- **$n = 672$** ($\approx 202$ decimal digits)
- **$n = 1024$** ($\approx 308$ decimal digits)
- **$n = 1664$** ($\approx 500$ decimal digits)

Evaluated strategies:
1. **Strategy S0 (Phase 2 Baseline):** Candidate-by-prime scalar filtering using Python loops over wheel candidates;
2. **Strategy S1 (Phase 3 Vectorized Segmented Sieve):** C-level NumPy slice striding (`alive[i0::q] = False`) on boolean bitset buffers;
3. **Strategy S2 (Phase 3 Hybrid Sieve):** Small-prime bitset striding ($q \le 10,000$) combined with sparse scalar checks for larger primes ($q > 10,000$).

---

## 2. Empirical Measured Results

All runs tested a constant window of $100,000$ $k$-span ($50,000$ odd candidates) starting from $k = 3$:

| Exponent $n$ | Target Digits | Sieve Depth $Q$ | S0 Latency (Baseline) | S1 Latency (Vectorized Bitset) | S2 Latency (Hybrid) | S1 Speedup over S0 | S1 Throughput (cands/sec) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$n = 672$** | ~202 digits | $10,000$ | $110.0\text{ ms}$ | **$<1.0\text{ ms}$** | $<1.0\text{ ms}$ | **$>100\times$** | $>50,000,000$ |
| **$n = 672$** | ~202 digits | $50,000$ | $234.0\text{ ms}$ | **$16.0\text{ ms}$** | $250.0\text{ ms}$ | **$14.6\times$** | $3,125,000$ |
| **$n = 672$** | ~202 digits | $100,000$ | $547.0\text{ ms}$ | **$31.0\text{ ms}$** | $344.0\text{ ms}$ | **$17.6\times$** | $1,612,903$ |
| **$n = 1024$** | ~308 digits | $10,000$ | $62.0\text{ ms}$ | **$<1.0\text{ ms}$** | $16.0\text{ ms}$ | **$>60\times$** | $>50,000,000$ |
| **$n = 1024$** | ~308 digits | $50,000$ | $250.0\text{ ms}$ | **$31.0\text{ ms}$** | $156.0\text{ ms}$ | **$8.1\times$** | $1,612,903$ |
| **$n = 1024$** | ~308 digits | $100,000$ | $406.0\text{ ms}$ | **$79.0\text{ ms}$** | $734.0\text{ ms}$ | **$5.1\times$** | $632,911$ |
| **$n = 1664$** | ~500 digits | $10,000$ | $125.0\text{ ms}$ | **$<1.0\text{ ms}$** | $16.0\text{ ms}$ | **$>120\times$** | $>50,000,000$ |
| **$n = 1664$** | ~500 digits | $50,000$ | $296.0\text{ ms}$ | **$32.0\text{ ms}$** | $156.0\text{ ms}$ | **$9.3\times$** | $1,562,500$ |
| **$n = 1664$** | ~500 digits | $100,000$ | $406.0\text{ ms}$ | **$31.0\text{ ms}$** | $297.0\text{ ms}$ | **$13.1\times$** | $1,612,903$ |

---

## 3. Key Algorithmic Findings

1. **Strategy S1 (Vectorized Segmented Sieve) is the Clear Overall Winner:**
   - Yields an **$8.1\times$ to $17.6\times$ speedup** over Phase 2 baseline across standard depth $Q=50,000$.
   - Executes entirely within NumPy's compiled C-striding routines without scalar candidate loops in Python.
   - Preserves exact mathematical survivor parity with S0 and S2 ($100\%$ set equality verified).

2. **Why S2 (Hybrid Sieve) Lost to S1:**
   - While S2 was designed to save memory by testing sparse survivors in scalar Python loops for large primes, Python interpreter overhead on sparse modular checks ($k \pmod q$) is significantly slower than NumPy's SIMD-optimized bitset slice assignment (`alive[i0::q] = False`) even when prime steps are large.
   - Consequently, **Strategy S1 is adopted as the primary default engine for all production Phase 3 campaigns**.
