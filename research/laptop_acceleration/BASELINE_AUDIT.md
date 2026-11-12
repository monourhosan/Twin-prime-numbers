# Phase 4 Baseline Code and Security Audit: Laptop CPU + GPU Acceleration

**Audit Date:** 2026-11-12T22:30:00+06:00  
**Target Hardware:** Intel Core i5-10210U (4 cores / 8 threads, 15W TDP) + NVIDIA GeForce MX250 (2 GB VRAM, Pascal sm_61)  
**Host Environment:** Windows 11 Build 26300, 64-bit AMD64, 11.85 GB RAM (4.07 GB available)  
**Initial Commit:** `6b74b5df62` (branch `research/laptop-mx250-acceleration`)  
**Python Runtime:** Python 3.12.10 (tags/v3.12.10:0db05d2, Feb 4 2025)

---

## 1. Executive Summary

A comprehensive architectural and mathematical audit of the `Twin-prime-numbers` repository was conducted before implementing hardware optimizations.
The existing mathematical algorithms, SQLite transaction semantics, and certificate formats are rigorously designed and fully reproducible.

All **54 existing automated unit and regression tests** passed with zero errors (`pytest 9.2.0` executed in 1.42s). All **7 historical certified discoveries** (covering Phase 2, Phase 3, and Phase 4 up to 1,028 digits) passed strict independent verification. Furthermore, the external 1,509-digit candidate ($416343 \cdot 2^{4992} \pm 1$) was independently verified from first principles and imported into Schema 4.0 format with an independent attestation.

---

## 2. Test Execution and Verification Record

### 2.1 Automated Unit and Property Tests
Executed command:
```powershell
python -m pytest tests/
```
Output:
- `tests/phase2/test_phase2.py`: 9 passed
- `tests/phase3/test_phase3.py`: 13 passed
- `tests/phase4/test_config.py`: 4 passed
- `tests/phase4/test_math.py`: 7 passed
- `tests/phase4/test_proofs_and_certificates.py`: 3 passed
- `tests/phase4/test_sieves.py`: 4 passed
- `tests/phase4/test_storage_recovery.py`: 4 passed
- `tests/test_cats.py`: 10 passed
**Total: 54 passed in 1.42 seconds.**

### 2.2 Historical Proof Independent Verification
Executed command:
```powershell
python scripts/phase4_independent_verify.py proofs/phase4 proofs/phase3 proofs/phase2
```
Results:
1. `proofs/phase4/cert_k1836723_n3392.json` (1,028 digits): **PASS**
   - Proth witness $w=13$, congruence $13^{(B-1)/2} \equiv -1 \pmod B$.
   - LLR parameter $P=3$, Jacobi conditions $(1/A)=1, (5/A)=-1$. Initial $u_0$ recomputed via independent $2 \times 2$ matrix powering; final residue $u_{3390} \equiv 0 \pmod A$.
   - Payload SHA-256: `46a7116dc819e1202807c498f31a62f3e7100f586b1c9267c207216296026a41`
2. `proofs/phase3/cert_k1183377_n1664.json` (507 digits): **PASS**
3. `proofs/phase3/cert_k254697_n1024.json` (314 digits): **PASS**
4. `proofs/phase3/cert_k15993_n672.json` (207 digits): **PASS**
5. `proofs/phase2/cert_k61347_n512.json` (159 digits): **PASS**
6. `proofs/phase2/cert_k126747_n384.json` (121 digits): **PASS**
7. `proofs/phase2/cert_k12477_n330.json` (104 digits): **PASS**

### 2.3 Verification and Import of 1,509-digit Candidate
The candidate provided in `discovery_k416343_n4992_certificate.json` was audited:
- Representation: $k = 416343$, $n = 4992$.
- Lower member $A = 416343 \cdot 2^{4992} - 1$ (1,509 decimal digits).
- Upper member $B = 416343 \cdot 2^{4992} + 1$ (1,509 decimal digits).
- Gap: $B - A = 2$.
- Upper primality: Proth witness $w = 7$, $7^{(B-1)/2} \equiv -1 \pmod B$ confirmed.
- Lower primality: LLR parameter $P = 3$, $(1/A) = 1, (5/A) = -1$. Initial $u_0$ evaluated via independent $2 \times 2$ matrix binary exponentiation; $u_{4990} \equiv 0 \pmod A$ verified after 4,990 squaring rounds.
- Converted to Schema 4.0 at [imported_cert_k416343_n4992.json](file:///d:/project/Twin%20prime%20numbers/proofs/phase4/imported_cert_k416343_n4992.json).
- Attestation generated at [attest_7025c2a1baf9fa9d.json](file:///d:/project/Twin%20prime%20numbers/proofs/phase4/attestations/attest_7025c2a1baf9fa9d.json).
- SHA-256 digest: `7025c2a1baf9fa9da4d03baf61fd400a693d98d2e3399a8bce6403701e3eda66`.

---

## 3. Detailed Component Audit

| File | Lines | Function / Responsibility | Audit Findings & Optimizations |
|---|---|---|---|
| [backend.py](file:///d:/project/Twin%20prime%20numbers/src/phase4/backend.py#L1-L99) | 1–99 | Multiprecision wrapper for `gmpy2` with pure Python fallback | Confirmed active: `gmpy2` 2.3.2 is installed and linked with GNU MP. `verify_backend_consistency()` passes 100%. Arithmetic is deterministic and exact. |
| [math_family.py](file:///d:/project/Twin%20prime%20numbers/src/phase4/math_family.py#L13-L59) | 13–59 | Index mapping $k \leftrightarrow t$ and residue derivation | Exact bijection $k = 6t + 3$. `compute_t_residues_for_prime` correctly computes $t_- \equiv (r - 3) \cdot 6^{-1} \pmod q$ and $t_+ \equiv (-r - 3) \cdot 6^{-1} \pmod q$ for $q \ge 5$. Verified no modular inverse failure for $q \in \{2, 3\}$. |
| [t_sieve.py](file:///d:/project/Twin%20prime%20numbers/src/phase4/t_sieve.py#L106-L172) | 106–172 | SieveR1_TSpace implementation | Vectorized NumPy array slicing. Memory footprint is $\sim 1$ byte/candidate in $t$-space, 3x more compact than odd-$k$ buffers. |
| [worker.py](file:///d:/project/Twin%20prime%20numbers/src/phase4/worker.py#L47-L214) | 47–214 | Pipeline execution & lease management | Atomic SQLite lease claiming with 15s heartbeats. Independent verification executed via child subprocess before recording discovery. |
| [cli.py](file:///d:/project/Twin%20prime%20numbers/src/phase4/cli.py#L198-L226) | 198–226 | Multiprocessing spawn on Windows | Uses `multiprocessing.get_context("spawn")`. Fix applied: worker loop replenishment ensured so workers do not exit prematurely after 20 initial tasks. |
| [storage.py](file:///d:/project/Twin%20prime%20numbers/src/phase4/storage.py#L30-L75) | 30–75 | SQLite WAL persistence & transactional schema | WAL mode enabled (`PRAGMA journal_mode=WAL`). Leases expire safely on unexpected crash and can be reclaimed idempotently. |

---

## 4. Hardware Vulnerabilities and System Realities

1. **CPU Thermal Throttling on 15W TDP Package:**
   - Intel Core i5-10210U has 4 physical cores and 8 logical threads with nominal 15W TDP.
   - Long-duration 100% all-thread loads saturate cooling, causing frequency reduction from ~2.8 GHz boost down to 1.6 GHz base.
   - Sustained throughput is maximized by running **2 to 3 worker processes** rather than 8, maintaining higher sustained CPU clock speeds.
2. **Missing ACPI User Thermal Sensor:**
   - Windows user-mode ACPI thermal queries (`MSAcpi_ThermalZoneTemperature`) are restricted or unavailable without elevated Administrator privileges.
   - Conservative safety policy enabled: worker concurrency is clamped to safe limits (maximum 3 workers) and status logs report missing ACPI thermal sensors honestly.
3. **GPU Driver Integration:**
   - NVIDIA driver 582.78 provides direct access to `nvcuda.dll` Driver API.
   - GeForce MX250 Pascal architecture (`sm_61`) is supported via PTX JIT compilation.
   - All ctypes function pointers are strictly declared with 64-bit arguments to prevent memory faults on Windows x64.
