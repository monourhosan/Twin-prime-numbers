# Hardware Diagnostics and Runtime Environment Report

**Host:** Windows 11 (Version 10.0.26300, AMD64)  
**Date Evaluated:** 2026-11-12T23:50:00+06:00  
**Machine Profile ID:** `i5-10210u-mx250-12gb`

---

## 1. Physical and Logical Hardware Audit

| Component | Specification | Measurement / State | Implications for Search Engine |
|---|---|---|---|
| **CPU Model** | Intel Core i5-10210U @ 1.60GHz | 4 physical cores, 8 logical threads, 6 MB SmartCache | Laptop U-series processor with nominal 15W TDP. Pegging 8 logical threads rapidly causes clock degradation to base frequency. Optimal concurrency is 2–3 worker processes. |
| **System Memory** | 12.0 GB Physical (11.85 GB usable) | 4.07 GB available, 7.78 GB used (65% load), 21.35 GB pagefile | Ample memory for multiple concurrent workers, but large sieve allocations must be bounded to stay within 1.0 GB total project footprint. |
| **Dedicated GPU** | NVIDIA GeForce MX250 | 2,048 MB total VRAM (1,667 MB free, 303 MB used), 59°C, 15% util | Pascal family GPU with Compute Capability **6.1** (`sm_61`). Full driver API accessible via `nvcuda.dll`. Fast integer parallel marking. |
| **Integrated GPU** | Intel UHD Graphics | Shared system memory | Dedicated to display rendering and desktop compositing; excluded from compute scheduling to preserve shared memory bandwidth. |
| **Storage (C:)** | NVMe / SSD | **335.12 GB free** (475.83 GB total) | System drive with vast headroom. Well above 30 GB safety threshold. |
| **Storage (D:)** | NVMe / SSD | **75.77 GB free** (118.51 GB total) | Project working drive with ample free capacity for SQLite WAL logs and checkpoints. |
| **Power Source** | AC Line Adapter | **ONLINE (Plugged In)**, Battery at 59% | Complies with AC power requirement for continuous high-performance computation. |

---

## 2. Toolchain and Computational Libraries

- **Python Runtime:** Python 3.12.10 (64-bit AMD64).
- **GMP / gmpy2:** `gmpy2` version 2.3.2 installed and functional. Accelerated C-level multiprecision modular exponentiation and Miller-Rabin tests confirmed active.
- **Scientific Stack:** `numpy` 2.5.4, `scipy` 1.18.1, `sympy` 1.14.0.
- **C/C++ Compiler:** Microsoft Visual C++ 2026 Community compiler (`cl.exe` version 14.52.37025) installed in `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.52.37025\bin\Hostx64\x64\cl.exe`.
- **NVIDIA Driver & CUDA Environment:**
  - Driver Version: `582.78`
  - CUDA Driver API: `C:\Windows\System32\nvcuda.dll` verified functional (`cuInit(0)` returns 0).
  - Runtime Compilation: NVIDIA driver built-in PTX JIT compiler verified functional for `sm_61`.
  - CUDA Toolkit (Standalone): Not installed; WSL2 is not installed.
  - Architecture Target: Direct execution of `.version 6.1 .target sm_61` PTX via Driver API provides 100% native hardware access with zero external toolchain dependencies.

---

## 3. Thermal and Safety Monitoring Feasibility

1. **GPU Thermal Telemetry:** Fully operational via `nvidia-smi` and NVML queries. Reports temperature (57–59°C idle/light load), memory usage, and GPU utilization in real time.
2. **CPU Thermal Telemetry:** Windows standard user queries for `MSAcpi_ThermalZoneTemperature` return restricted access (requires elevated administrator privilege). As mandated by prompt Section 1 and Section 7, the system engages **`conservative_mode`**:
   - Caps worker count at $\le 3$ processes (instead of 8).
   - Injects periodic yield delays to prevent thermal saturation.
   - Requires continuous AC power and aborts on battery operation.
3. **Memory and Disk Guardrails:**
   - Active memory monitor checks available RAM before admitting work units (pause threshold: $< 2.5$ GB available).
   - Disk monitor ensures $> 30$ GB free space on both C: and D: drives.
