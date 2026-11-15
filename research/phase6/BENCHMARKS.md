# Phase 6 Empirical Benchmark Report (QCP-6 vs Alternatives)

**Target Digit Band:** 100 digits
**Sample Window:** 10000 candidates
**Sieve Limit:** 50000 primes

## 1. Sieve Throughput Comparison

| Algorithm / Variant | Sieve Depth | Window | Elapsed (s) | Throughput (cand/s) | Survivors |
|---|---|---|---|---|---|
| Q-reference | 10000 | 2000 | 0.0879 | 22750.1 | 121 |
| Q-segment | 50000 | 10000 | 0.0345 | 289570.5 | 473 |
| Q-event | 50000 | 10000 | 0.0358 | 279470.9 | 473 |
| Method-R-Linear | 50000 | 10000 | 0.0153 | 654330.4 | 205 |

## 2. Screening Order Analysis (A-first vs. B-first)

- **Tested Survivors:** 473
- **A-First Throughput:** 14762.9 pairs/sec (0.0320s)
- **B-First Throughput:** 23038.1 pairs/sec (0.0205s)
- **Recommended Hot-Path Order:** `B_first`

## 3. Conclusions and Strategy

- `Q-segment` exhibits superior cache locality and throughput (289570.5 cand/s).
- `Q-event` achieves comparable throughput, but `Q-segment` has simpler memory management and zero pointer indirection.
- Screening order `B_first` is configured for live discovery campaigns.
