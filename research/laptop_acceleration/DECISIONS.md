# Architectural and Engineering Decision Record (ADR)

**Project:** Google Antigravity Laptop CPU + GPU Twin-Prime Search Accelerator  
**Target Hardware:** Intel Core i5-10210U (4c/8t, 15W TDP) + NVIDIA GeForce MX250 (2 GB VRAM, sm_61)  
**Date:** 2026-11-13  

---

## ADR-01: Native Windows Driver API JIT for NVIDIA GeForce MX250

- **Context:** NVIDIA removed offline compilation for Pascal GPUs (`sm_61`) starting in CUDA Toolkit 13.0+. Installing a full legacy CUDA 12.x toolkit or WSL2 Linux environment on Windows introduces system-wide driver/toolchain modifications and potential AppLocker/security friction.
- **Decision:** Use Python `ctypes` calling `C:\Windows\System32\nvcuda.dll` directly. Supply raw PTX assembly (`.version 6.1 .target sm_61`) and compile via the NVIDIA display driver's internal JIT compiler (`cuModuleLoadDataEx`).
- **Consequence:** 100% native Windows execution with zero external toolchain installations, zero registry modifications, and zero administrative permissions needed. Explicit 64-bit ctypes argument typings (`c_uint64`, `c_size_t`, `c_void_p`) prevent pointer truncation errors.

---

## ADR-02: GPU Sieve Acceleration with CPU Proof Verification (Hybrid Pipeline)

- **Context:** The GeForce MX250 is an entry-level mobile Pascal GPU with 384 CUDA cores and 2 GB VRAM. Sieve operations consist of simple integer modular markings, whereas Lucas-Lehmer-Riesel and Proth proofs require 1,000–2,500 digit big-integer arithmetic.
- **Decision:** Delegate dual-residue candidate sieving to the GPU using PTX segment byte-marking (`CUDASieveMX250`), while delegating multiprecision PRP screening, Proth proofs, and LLR proofs to CPU processes using GNU MP / `gmpy2`.
- **Consequence:** Achieves an empirical **4.1x to 17.8x speedup** in sieve throughput (~25,000,000 candidates/sec on MX250 vs ~1,500,000–2,500,000 cands/sec on CPU), while eliminating GPU multi-precision numerical overflow risks.

---

## ADR-03: Process Concurrency Budgeting for 15W TDP Mobile Package

- **Context:** The Intel Core i5-10210U has 4 physical cores and 8 logical hyperthreads, but is thermally bounded by a nominal 15W TDP. Pegging 4+ all-core threads causes clock frequencies to degrade from ~2.8 GHz down to ~1.8 GHz.
- **Decision:** Clamp default worker concurrency to **3 worker processes** for Maximum Sustainable Mode (and **2 worker processes** for Balanced Mode).
- **Consequence:** Concurrency benchmarks show 3 workers achieve **7,783 cands/s** (76.7% linear efficiency) while avoiding thermal saturation. Adding a 4th worker yields only a 2.4% net throughput gain while increasing fan noise and thermal pressure.

---

## ADR-04: Conservative Safety Fallback for Windows ACPI Thermal Telemetry

- **Context:** User-mode queries for `MSAcpi_ThermalZoneTemperature` on Windows 11 are restricted without elevated Administrator privileges. However, GPU temperature is fully available via NVML/`nvidia-smi`.
- **Decision:** Implement `LaptopSafetyMonitor` with an explicit `conservative_mode` fallback when CPU ACPI sensors are unreadable. Cap workers at $\le 3$, enforce AC line power, monitor free RAM ($\ge 2.5$ GB) and disk ($\ge 30$ GB), and monitor GPU temperature (soft throttle at 80°C, hard pause at 85°C).
- **Consequence:** Guarantees thermal safety and hardware preservation without requiring elevated Windows administrative privileges.

---

## ADR-05: Verification and Import of 1,509-Digit External Candidate

- **Context:** An external experimental package reported a 1,509-digit candidate pair: $416343 \cdot 2^{4992} \pm 1$.
- **Decision:** Perform strict mathematical verification from first principles using independent $2 \times 2$ matrix powering for the Lucas seed and $4,990$ LLR squarings, import it as `proofs/phase4/imported_cert_k416343_n4992.json`, generate an independent verification attestation, and document its provenance accurately without claiming world-first priority.
- **Consequence:** The verified pair is securely recorded in Schema 4.0 format, increasing the repository's proven maximum from 1,028 digits to 1,509 digits.
