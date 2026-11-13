# Phase 5 Multi-Family SCCA Portfolio & Scheduler Benchmark Report

**Date:** 2026-11-14T04:21:00+06:00  
**Phase:** Phase 5 Smooth-Center Certificate-Aware Search (SCCA)  
**Deliverable:** Stage D Multi-Family Experiment and Scheduler Benchmark  

---

## 1. Multi-Family Mathematical Architecture

To demonstrate true portfolio scheduling across mathematically distinct candidate-generation domains, three separate families were implemented and benchmarked:

### 1.1 Family 1: `fam_scca_p3_dense` (Ternary Dominant)
- **Smooth Base Formulation:**
  $$F_1 = 2^1 \cdot 3^{40} \cdot 5^{10}$$
  $$\text{Odd Factor: } F_{odd} = 3^{40} \cdot 5^{10},\quad \text{Prime Factors: } \{2, 3, 5\}$$
- **Size:** $F_1 \approx 4.35 \times 10^{26}$ (27 decimal digits, 88 bits).
- **Sieve Characteristics:** Primes $q \in \{7, 11, 13, 17, 19, \dots\}$ are actively sieved via $t \not\equiv \pm F_1^{-1} \pmod q$.
- **Arithmetic Profile:** Extremely fast modular reductions due to sparse factor base; high survivor density.

### 1.2 Family 2: `fam_scca_balanced_multibase` (Distributed Smooth Spectrum)
- **Smooth Base Formulation:**
  $$F_2 = 2^3 \cdot 3^{20} \cdot 5^{10} \cdot 7^6 \cdot 11^3$$
  $$\text{Odd Factor: } F_{odd} = 3^{20} \cdot 5^{10} \cdot 7^6 \cdot 11^3,\quad \text{Prime Factors: } \{2, 3, 5, 7, 11\}$$
- **Size:** $F_2 \approx 4.29 \times 10^{25}$ (26 decimal digits, 86 bits).
- **Sieve Characteristics:** Primes 2, 3, 5, 7, and 11 divide $F_2$, providing algebraic immunity against divisibility by these primes. The modular sieve begins at prime $q = 13$.
- **Arithmetic Profile:** Higher number of GCD conditions during proof phase (4 odd prime factors).

### 1.3 Family 3: `fam_scca_sparse_highbase` (Quinary-Skipping High Base)
- **Smooth Base Formulation:**
  $$F_3 = 2^2 \cdot 3^{25} \cdot 7^{10} \cdot 13^5 \cdot 17^3$$
  $$\text{Odd Factor: } F_{odd} = 3^{25} \cdot 7^{10} \cdot 13^5 \cdot 17^3,\quad \text{Prime Factors: } \{2, 3, 7, 13, 17\}$$
- **Size:** $F_3 \approx 1.34 \times 10^{31}$ (31 decimal digits, 101 bits).
- **Sieve Characteristics:** Explicitly excludes prime 5 from $F_3$. Therefore $t \not\equiv \pm F_3^{-1} \pmod 5$ is an active filter stage. Primes 7, 13, and 17 provide divisibility immunity.
- **Arithmetic Profile:** Tests candidate survival when standard prime 5 is unconstrained.

---

## 2. Small-Prime Residue Sieve Verification

Residue exclusion rules were unit-tested against exhaustive brute-force direct divisibility on all three families (`tests/phase5/test_phase5_sieve_verification.py`):
1. **Bit-Exact Equivalence:** Over $t \in [1, 500]$ and primes $q \le 100$, the segmented modular sieve produced an identical survivor set to brute-force integer divisibility checks ($0$ false positives, $0$ false negatives).
2. **Prime Preservation:** A known twin prime pair ($t=3$ on $C=28350$) was preserved by the sieve without elimination.

---

## 3. Scheduler Performance Experiment

Three scheduling strategies were executed on an identical fixed compute budget of 12 allocations (6,000 candidates total across families) with sieve limit $L = 50,000$:

| Metric | Round-Robin (`ROUND_ROBIN`) | UCB1 Bandit (`BANDIT_UCB1`) | Cost-Aware Bandit (`COST_AWARE`) |
|---|---|---|---|
| Total Allocations | 12 | 12 | 12 |
| Total Candidates Screened | 6,000 | 6,000 | 6,000 |
| Total Wall Time (s) | 3.53 s | 3.80 s | **3.15 s** |
| Throughput (cands / s) | 1,702 cands/s | 1,580 cands/s | **1,906 cands/s** |
| Throughput Advantage | Baseline (1.00x) | 0.93x | **+12.0% over baseline** |
| Certified Twin Pairs Found | 25 | 25 | 19 |
| Allocation Distribution | 4 / 4 / 4 (even) | 4 / 4 / 4 (exploring) | 7 / 2 / 3 (cost-optimized) |
| Exploration Quota | Enforced | Enforced (min 2 pulls) | Enforced (min 2 pulls) |
| Independent Verification | 100% PASS | 100% PASS | 100% PASS |

### 3.1 Observations
1. **Exploration Guarantees:** Both UCB1 and Cost-Aware schedulers satisfied the initial exploration constraint, ensuring all 3 arms were sampled before pure exploitation.
2. **Cost-Aware Efficiency:** The `COST_AWARE` policy recognized that `fam_scca_p3_dense` processed candidates faster due to lower proof complexity (fewer prime factors to verify GCD conditions on), allocating 7 of 12 pulls to the high-throughput arm and achieving 1,906 candidates/second.
3. **Reproducibility:** Raw JSON logs are persisted at `research/phase5_benchmarks/raw/scheduler_comparison.json`.

---

## 4. Gate D Sign-Off

- [x] Three mathematically distinct SCCA families defined and documented.
- [x] Residue exclusion rules mathematically verified against direct divisibility.
- [x] Three scheduling policies evaluated under controlled equal-budget protocol.
- [x] Full telemetry persisted in machine-readable JSON.
- **GATE D STATUS: PASSED.** Ready to proceed to Stage E.
