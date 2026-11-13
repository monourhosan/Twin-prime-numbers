# Phase 5 Performance & Verification Benchmarks

**Benchmark Environment:**  
- **Host CPU:** Intel Core i5-10210U @ 1.60GHz (4 physical cores, 8 threads, 15W TDP)  
- **Host RAM:** 11.85 GB Available  
- **Operating System:** Windows 11 Build 26300 (AMD64)  
- **Python:** 3.12.10 (AMD64) with `gmpy2` 2.3.2  
- **Audit Date:** 2026-11-13  

---

## 1. Candidate Sieve Engine Throughput (Method S1)

Measured on interval length $\Delta t = 20,000$ with smooth-center family $F = 2^3 \cdot 3^4 \cdot 5^2 \cdot 7^1 = 113,400$ and sieve prime limit $L_{\mathrm{sieve}} = 50,000$:

| Sieve Implementation | Elapsed Time (ms) | Raw Throughput (cands/s) | Sieve Survivors | Survival Rate (%) | Notes |
|---|---|---|---|---|---|
| **Method S1: Segmented Bit/Byte Filter** | **12.62 ms** | **1,584,740 cands/s** | **896** | **4.48%** | Compact memory footprint, optimal for large prime tables |
| **Method S1: CRT Wheel Walker ($W=2431$)** | **2.75 ms** | **7,265,017 cands/s** | **12,213** | **61.07%** | Enumerate-only admissible residues ($q \in \{11, 13, 17\}$) |

### Algorithmic Trade-off:
- The CRT Wheel Walker achieves $7.26\times 10^6$ candidates/sec because it avoids scanning eliminated slots, but only filters small wheel primes ($W = 2431$).
- The Segmented Bit Filter eliminates primes up to 50,000, reducing the survivor density from 61.1% down to 4.48% (a $13.6\times$ reduction in expensive downstream PRP tests).
- **Optimal Pipeline:** In Phase 5 production, the Segmented Bit Filter is used to screen to 50,000, minimizing big-integer construction.

---

## 2. Deterministic Primality Proving Throughput Across Digit Bands

Measured end-to-end execution time for both Pocklington (Upper $B$) and Morrison (Lower $A$) proofs:

| Digit Band | Exact Integer Digits | Family Exponents | Prover Time (ms) | Breakdown: Pocklington | Breakdown: Morrison Matrix Pow |
|---|---|---|---|---|---|
| **Small** | 18 digits | $2^1 \cdot 3^{20} \cdot 5^{10}$ | 0.32 ms | 0.08 ms | 0.24 ms |
| **Pilot** | 43 digits | $2^1 \cdot 3^{50} \cdot 5^{25}$ | 0.45 ms | 0.11 ms | 0.34 ms |
| **Discovery 1** | **59 digits** | $2^3 \cdot 3^{60} \cdot 5^{25} \cdot 7^{10}$ | **0.88 ms** | **0.18 ms** | **0.70 ms** |
| **Intermediate** | 84 digits | $2^1 \cdot 3^{100} \cdot 5^{50}$ | 2.46 ms | 0.42 ms | 2.04 ms |
| **Discovery 2** | **133 digits** | $2^3 \cdot 3^{150} \cdot 5^{50} \cdot 7^{25}$ | **4.15 ms** | **0.65 ms** | **3.50 ms** |
| **Scientific** | 365 digits | $2^3 \cdot 3^{400} \cdot 5^{150} \cdot 7^{80}$ | 22.80 ms | 3.10 ms | 19.70 ms |
| **Stretch** | 1,562 digits | $2^1 \cdot 3^{2100} \cdot 5^{800}$ | 285.50 ms | 29.80 ms | 255.70 ms |

### Key Performance Findings:
- Proving a 59-digit pair takes under 1 millisecond.
- Proving a 133-digit pair takes 4.15 milliseconds.
- Proving a 1,562-digit pair takes 0.28 seconds using GMP-backed binary matrix powering.
- Proof generation is computationally efficient once a dual PRP candidate is located.

---

## 3. Method S2 Multi-Family Portfolio Scheduling Comparison

Controlled experiment over 10 work units ($\Delta t = 2,500$ per unit, total candidate parameter slots = 25,000) under identical random seeds across three smooth-center families ($F_1, F_2, F_3$):

| Scheduling Policy | Exploration Strategy | Work Units Dispatched | Dual PRPs Located | Certified Pairs | Wall Clock (s) | Effective Discovery Efficiency |
|---|---|---|---|---|---|---|
| **Bandit UCB1** | $c = 1.414$, min-quota = 2 | 10 | 2 | 2 | 0.95 s | **2.11 pairs / wall-sec** |
| **Round-Robin** | Cyclic sequence ($F_1 \to F_2 \to F_3$) | 10 | 2 | 2 | 1.12 s | **1.78 pairs / wall-sec** |
| **Static Priority** | Fixed $F_1$ dominance | 10 | 2 | 2 | 1.08 s | **1.85 pairs / wall-sec** |

### Observations:
- Bandit UCB1 successfully satisfies its minimum exploration quotas across all families before allocating additional work units to high-yielding parameter bands.
- Online reward tracking correctly weighs dual PRPs and successful certificates, preventing compute starvation.
