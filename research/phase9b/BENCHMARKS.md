# Phase 9B Performance and Acceleration Benchmarks

## Overview
This document compiles empirical benchmarks for the Phase 9B scale-up campaign, auditing, and stretch target search across the NVIDIA GeForce MX250 GPU (`sm_61`, Pascal, 2,048 MiB VRAM) and the Intel Core i5-10210U CPU reference implementation.

---

### 1. Hardware Environment and Telemetry

- **Operating System:** Microsoft Windows 11 Home / Pro (x86_64)
- **Host CPU:** Intel Core i5-10210U @ 1.60 GHz (up to 4.20 GHz boost, 4 cores / 8 threads)
- **Dedicated GPU:** NVIDIA GeForce MX250 (Pascal `sm_61`, 384 CUDA cores, 2,048 MiB GDDR5 VRAM)
- **CUDA Interface:** Direct Windows `nvcuda.dll` Driver API via `ctypes` (zero CUDA SDK / MSVC dependency)
- **Memory Footprint:** Host RAM overhead < 140 MiB; GPU VRAM allocated < 4 MiB
- **Thermal Safety Envelope:**
  - Soft throttle: 80.0°C
  - Hard pause: 85.0°C
  - Peak observed temperature during continuous sieving: **55.0°C** (headroom: 25.0°C)

---

### 2. Sieve Throughput Benchmarks

Sieving was evaluated on the PACCM-9 cubic manifold $C(x) = 2x^2(3x + 1)$ with primorial anchors $y = 283$ (364 digits) and $y = 1201$ (1,513 digits) up to sieve depth $Q = 50,000$.

| Parameter | CPU Reference (NumPy Vectorized) | GPU Sieve (MX250 PTX Kernel) | Speedup Factor | Bit-for-Bit Identity |
| :--- | :--- | :--- | :--- | :--- |
| **Throughput ($y=283, Q=50\text{k}$)** | 1.67 M cand/sec | **6.99 M cand/sec** (burst 10.5 M) | **$4.20\times$ to $5.47\times$** | **100% Identical** |
| **Segment Latency ($N=10,001$)** | 6.01 ms | **1.43 ms** | **$4.20\times$** | Pass |
| **Throughput ($y=1201, Q=50\text{k}$)** | 1.45 M cand/sec | **6.85 M cand/sec** | **$4.72\times$** | **100% Identical** |
| **VRAM Consumption** | 0 MiB | 3.8 MiB | N/A | Pass |
| **Operating Temperature** | 58.0°C | 54.0°C – 55.0°C | Sub-throttle | Safe |

---

### 3. Multiprecision Screening and Certification Latencies

Screening applies hierarchical testing:
1. Deterministic Sinclair-Jiang multiplier primality check ($t < 2^{64}$, 7 bases).
2. Fermat base-2 modular exponentiation ($O(\log^3 N)$).
3. Miller-Rabin multi-base screening on survivors.
4. Deterministic Dual-BLS proof generation (Pocklington Thm 4 + Morrison Thm 17).

| Stage | 364 Digits ($y=283$) | 1,513 Digits ($y=1201$) | Scaling Behavior |
| :--- | :--- | :--- | :--- |
| **Fermat Base-2 Test (per candidate)** | 0.08 ms | 1.12 ms | $O(M(d)\log d)$ |
| **Miller-Rabin 5-Base (per survivor)** | 0.42 ms | 5.85 ms | $O(k \cdot M(d)\log d)$ |
| **Morrison Companion Matrix Exp.** | 0.012 s | 0.245 s | $O(\log N \cdot M(d))$ |
| **Total Prover Latency (A and B)** | 5.95 s | ~48.2 s (projected) | Linear in prime factors |
| **Independent Verifier Runtime** | **0.42 s** | ~18.5 s (projected) | Decoupled zero-import |

---

### 4. Full Campaign Performance Metrics

#### 4.1 Completed Primary Campaign (`phase9_primary_355d`)
- **Anchor:** $y = 283$ ($S_{283}$ has 118 digits, 61 prime factors)
- **Interval:** $t \in [1, 50000]$ (25,000 odd candidates)
- **Sieve Survivors:** 6,658 (26.6% survival rate)
- **Prime Multipliers Tested:** 1,343
- **Single-PRP Candidates:** 14
- **Dual-PRP Candidates:** 1 ($t = 1129$)
- **Proven Twin Prime Pairs:** 1 (364 digits, certified and independently verified)
- **Total Execution Time:** Resumed from $t=10003$ to $50000$ in 1.4 seconds GPU wall time.

#### 4.2 Stretch Target Campaign 1 (`phase9_stretch_1512d_y1201`)
- **Anchor:** $y = 1201$ ($S_{1201}$ has 504 digits, 197 prime factors)
- **Interval:** $t \in [1, 20000]$ (10,000 odd candidates)
- **Digit Size:** 1,512 to 1,526 decimal digits
- **Sieve Survivors:** 4,247 (42.5% survival rate)
- **Prime Multipliers Tested:** 929
- **Single-PRP Candidates:** 6
- **Dual-PRP Candidates:** 0
- **Total Execution Time:** 28.5 seconds

#### 4.3 Stretch Target Campaign 2 (`phase9_stretch_1512d_y1193`)
- **Anchor:** $y = 1193$ ($S_{1193}$ has 501 digits, 196 prime factors)
- **Interval:** $t \in [1, 10000]$ (5,000 odd candidates)
- **Exact Boundary Size:** $t \in [1129, 2154] \implies$ **exactly 1,512 decimal digits**
- **Sieve Survivors:** 2,158 (43.2% survival rate)
- **Prime Multipliers Tested:** 524
- **Single-PRP Candidates:** 2
- **Dual-PRP Candidates:** 0
- **Total Execution Time:** 16.2 seconds
