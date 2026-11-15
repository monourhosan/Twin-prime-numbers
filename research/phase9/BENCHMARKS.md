# Phase 9: Hardware Sieve & End-to-End Benchmarks
## Comparative Evaluation: NVIDIA GeForce MX250 (`sm_61`) vs Intel Core i5-10210U CPU

### 1. Hardware & Software Configuration
- **GPU Accelerator:** NVIDIA GeForce MX250 (Pascal `sm_61`, 2,048 MiB VRAM, Driver 582.78, CUDA Driver API)
- **Host CPU:** Intel Core i5-10210U @ 1.60GHz (4 physical / 8 logical cores)
- **Host RAM:** 12.0 GB DDR4
- **Operating System:** Microsoft Windows 11 Home 64-bit
- **Python Environment:** Python 3.12.10, gmpy2 2.3.2, sympy 1.14.0, numpy 2.5.4
- **Sieve Target:** PACCM-9 Manifold ($x = S_{283} \cdot t, C = 2x^2(3x + 1)$), Sieve Depth $Q = 50000$ (4522 prime moduli)

---

### 2. Sieve Throughput & Latency Comparison
All benchmarks evaluated over identical, deterministic windows of odd multiplier space $t$.
Bit-for-bit exact survivor equivalence was strictly verified on every run.

| Window Description | Candidate Count | CPU Time (ms) | CPU Throughput | GPU Time (ms) | GPU Throughput | MX250 Speedup | GPU Temp | Survivor Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Small (10k)** | 5,001 | 9.37 ms | 533,915 c/s | 0.89 ms | 5,602,734 c/s | **10.49x** | 64.0°C | 28.4% |
| **Medium (30k)** | 15,001 | 11.02 ms | 1,361,413 c/s | 1.77 ms | 8,458,416 c/s | **6.21x** | 64.0°C | 28.7% |
| **Large (50k)** | 25,001 | 13.02 ms | 1,920,146 c/s | 2.38 ms | 10,506,535 c/s | **5.47x** | 64.0°C | 28.8% |

---

### 3. Key Observations & Hardware Performance Decision
1. **Bit-for-Bit Identity:** The NVIDIA GeForce MX250 GPU driver and PTX JIT kernel achieved **100% exact equality** of survivor sets with the CPU reference engine across all tested window sizes.
2. **Speedup Threshold Met:** The MX250 achieved measured speedups of **5.47x** over the optimized vectorized NumPy CPU implementation, comfortably exceeding the 10% threshold required by Section 7.4 of the Master Prompt.
3. **Thermal Stability:** Throughout sustained sieving of 50,000 candidates, GPU temperatures remained stable at 64.0°C (well below the 80°C soft throttle and 85°C pause limits).
4. **VRAM Footprint:** Device memory consumption was less than 4 MiB (< 0.2% of the 2,048 MiB capacity).
