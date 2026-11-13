# Phase 6 GITCSS Engine: Controlled Empirical Benchmarks

## 1. System & Execution Profile

- **Host CPU:** Intel Core i5-10210U @ 1.60GHz (4 physical cores, 8 threads)
- **Memory:** 12.0 GB RAM (LPDDR3-2133)
- **Python / GMP:** Python 3.12.10, gmpy2 2.3.2 backed by GNU GMP 6.3.0
- **Engine:** GITCSS (General Integer Twin-Center Segmented Sieve)

## 2. Wheel Configuration Throughput

| Configuration | Wheel Modulus | Throughput (centers/s) | Survivor Rate | Latency (256K block) |
|---|---|---|---|---|
| `No_Wheel` | 1 | 8,553,799 | 3.21% | 30.65 ms |
| `Wheel_5` | 5 | 3,802,197 | 3.21% | 68.95 ms |
| `Wheel_5_7` | 35 | 8,668,439 | 3.21% | 30.24 ms |
| `Wheel_5_7_11` | 385 | 8,137,605 | 3.21% | 32.21 ms |
| `Wheel_5_7_11_13` | 5005 | 6,541,237 | 3.21% | 40.08 ms |

## 3. Sieve Limit Scaling

| Sieve Cutoff $Q$ | Throughput (centers/s) | Survivor Rate | Latency (256K block) |
|---|---|---|---|
| 1,000 | 10,886,831 | 4.91% | 24.08 ms |
| 5,000 | 10,367,693 | 3.21% | 25.28 ms |
| 20,000 | 10,607,320 | 3.21% | 24.71 ms |
| 50,000 | 5,320,485 | 3.21% | 49.27 ms |
| 100,000 | 6,239,607 | 3.21% | 42.01 ms |

## 4. Reference vs. Optimized Sieve Speedup

- **Reference Direct Divisibility:** 192,389 centers/s
- **Optimized GITCSS Bitset Wheel:** 1,749,934 centers/s
- **Measured Speedup:** **9.1x**
- **Mathematical Invariant:** Exact identity between reference and optimized survivor sets verified.

## 5. Candidate Screening Latency Across Digit Bands

| Scale | Median Latency ($\mu$s) | Throughput (screens/s) | Screening Rounds |
|---|---|---|---|
| **10 digits** | 7.30 $\mu$s | 136,986 | 25 MR + Fermat + BPSW |
| **50 digits** | 7.10 $\mu$s | 140,845 | 25 MR + Fermat + BPSW |
| **100 digits** | 7.80 $\mu$s | 128,205 | 25 MR + Fermat + BPSW |
| **350 digits** | 16.00 $\mu$s | 62,500 | 25 MR + Fermat + BPSW |
| **450 digits** | 20.30 $\mu$s | 49,261 | 25 MR + Fermat + BPSW |
