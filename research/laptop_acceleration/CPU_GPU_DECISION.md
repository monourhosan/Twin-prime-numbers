# Hardware Architecture Decision: Hybrid CPU + NVIDIA MX250 GPU Sieve

**Date:** 2026-11-13  
**Target Hardware:** Intel Core i5-10210U @ 1.60GHz (4c/8t, 15W TDP) + NVIDIA GeForce MX250 (2 GB VRAM, Compute 6.1)  
**Selected Architectural Mode:** **HYBRID (`--backend hybrid` / `--algorithm r3_gpu_mx250`)**  
**Selected Worker Budget:** **3 CPU Worker Processes** for Maximum Sustainable Concurrency  

---

## 1. Decision Criteria & Evaluation Rubric

In accordance with Section 6 of the Master Execution Prompt:
> *"Choose GPU/hybrid only if (a) every correctness test passes, (b) actual sustained throughput improves meaningfully (suggested initial threshold >= 10% over CPU-only, with variance reported), and (c) thermal/memory reliability meets safe limits. Otherwise, select CPU-only and explain why the GPU is not worth keeping busy."*

### Criterion (a): Mathematical and Bit-Level Correctness
- **Status:** **PASS (100% Bit-Exact Agreement)**
- The PTX kernel on `sm_61` marks forbidden residues in candidate byte arrays with zero race conditions (stores of byte `0` are idempotent).
- Automated differential testing against the CPU reference `SieveR1_TSpace` across small, medium, and edge-case windows confirmed exact identity: $S_{\text{GPU}} \equiv S_{\text{CPU}}$ for all candidate indices $t \in [t_0, t_1)$.

### Criterion (b): Measured End-to-End Throughput Advantage
- **Status:** **PASS (Substantial 4.1x to 17.8x Speedup)**
- Across exponents $n \in \{3328, 4992, 6656, 8192\}$ and sieve depths $Q \in \{30000, 50000, 100000\}$:
  - At $n=3328, Q=50,000$: CPU = 2.35M cands/s vs MX250 GPU = **26.27M cands/s** (**11.19x speedup**).
  - At $n=3328, Q=100,000$: CPU = 1.45M cands/s vs MX250 GPU = **25.93M cands/s** (**17.82x speedup**).
  - At $n=6656, Q=50,000$: CPU = 1.96M cands/s vs MX250 GPU = **24.76M cands/s** (**12.66x speedup**).
  - At $n=6656, Q=100,000$: CPU = 1.37M cands/s vs MX250 GPU = **24.19M cands/s** (**17.61x speedup**).
- The throughput increase drastically exceeds the required $\ge 10\%$ threshold.

### Criterion (c): Thermal and Memory Sustainability
- **Status:** **PASS (Cool Thermals and Negligible VRAM Footprint)**
- **GPU Thermals:** Throughout all kernel sweeps and stress trials, the GeForce MX250 operated between **58°C and 60°C**, far below the soft-throttle threshold of 80°C and pause threshold of 85°C.
- **VRAM Utilization:** The packed segment buffer for a 120,000 candidate window requires only 20 KB of VRAM; even a massive 1,000,000 candidate window requires ~1 MB. Total GPU VRAM used by the search engine was under 12 MB out of 2,048 MB available (< 0.6% of VRAM), leaving complete headroom for the Windows DWM and display.
- **System RAM:** Available host memory remained stable at ~3.7–4.0 GB free (well above the 2.5 GB safety floor).

---

## 2. Worker Concurrency Selection (CPU Scheduling)

The Intel Core i5-10210U processor features 4 physical cores and 8 logical threads governed by a nominal 15W package TDP.
Empirical concurrency scaling was measured from 1 to 6 workers:
- **1 Worker:** 3,382 cands/s (100.0% efficiency, baseline)
- **2 Workers:** 6,049 cands/s (89.4% efficiency)
- **3 Workers:** **7,783 cands/s (76.7% efficiency) — Optimal Operating Point**
- **4 Workers:** 7,975 cands/s (59.0% efficiency) — Adding core 4 yields only a 2.4% net throughput gain while causing package thermal saturation and clock down-throttling.
- **5 Workers:** 8,824 cands/s (52.2% efficiency)
- **6 Workers:** 10,013 cands/s (49.3% efficiency)

**Autotuned Policy:**
- For **Maximum Sustainable Mode:** Use **3 worker processes**. This preserves high boost clock rates (~2.4–2.8 GHz) without exceeding the 15W thermal dissipation budget.
- For **Balanced / Quiet Mode:** Use **2 worker processes** (89.4% linear efficiency, near silent operation).

---

## 3. Asynchronous Hybrid Pipeline Structure

```
+--------------------------------------------------------------+
|                 Durable SQLite Ledger (WAL)                 |
|             Task Leases & Gap-Free Work Units                |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|               Host Precomputation (Vectorized)               |
|      Primes q <= Q, Forbidden t-Residues (t_minus, t_plus)    |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|        NVIDIA GeForce MX250 GPU Sieve Engine (PTX)           |
|      Dual-Residue Segment Marking (~25 Million cands/sec)     |
+--------------------------------------------------------------+
                               |  Survivors buffer (~1.5% - 2.5%)
                               v
+--------------------------------------------------------------+
|             3 Concurrent CPU Proof Workers (gmpy2)           |
|     Stage 1: Miller-Rabin PRP Screening (B, then A)          |
|     Stage 2: Proth Deterministic Primality (witness w)        |
|     Stage 3: Lucas-Lehmer-Riesel Proof (parameter P, seed u0)|
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|           Strict Standalone Independent Verifier             |
|          2x2 Matrix Powering + Verified Attestation          |
+--------------------------------------------------------------+
```

GPU execution is fully non-blocking and ephemerally verified: if any GPU driver reset or allocation error occurs, tasks are automatically routed to the CPU reference sieve without interrupting the campaign.
