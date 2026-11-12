# Phase 4 Reproduction Guide: Laptop CPU + NVIDIA MX250 Acceleration

This guide provides tested, reproducible commands for auditing, benchmarking, verifying, and running the twin-prime search engine on Windows 11 with an Intel Core i5-10210U and NVIDIA GeForce MX250 GPU.

---

## 1. Environment & Prerequisites

- **OS:** Windows 10/11 64-bit AMD64.
- **Python:** Python 3.12+ (64-bit).
- **Core Packages:** `gmpy2`, `numpy`, `sympy`, `pytest`.
- **NVIDIA Driver:** Version 550+ (tested with driver 582.78).
- **Toolchain:** No external CUDA Toolkit installation is required. Uses Windows-native `C:\Windows\System32\nvcuda.dll` and driver JIT compilation.

To verify prerequisites:
```powershell
python -m pip install -r requirements.txt  # If needed
python -m src.phase4 laptop-doctor
```

---

## 2. Independent Proof Verification

Verify all certified twin-prime pairs (including the 1,028-digit pair and the imported 1,509-digit pair):
```powershell
python scripts/phase4_independent_verify.py proofs/phase4 proofs/phase3 proofs/phase2
```

Expected output:
```
Phase 4 Independent Strict Verification of 8 certificate(s)...
  [PASS] cert_k1836723_n3392.json (1,028 digits)
  [PASS] imported_cert_k416343_n4992.json (1,509 digits)
  [PASS] cert_k1183377_n1664.json (507 digits)
  [PASS] cert_k254697_n1024.json (314 digits)
  [PASS] cert_k15993_n672.json (207 digits)
  [PASS] cert_k61347_n512.json (159 digits)
  [PASS] cert_k126747_n384.json (121 digits)
  [PASS] cert_k12477_n330.json (104 digits)
[SUCCESS] All certificates passed independent strict mathematical verification!
```

---

## 3. Running Automated Test Suite

Execute the full suite of 64 unit, property, and differential tests:
```powershell
python -m pytest tests/
```

To run only the laptop acceleration tests:
```powershell
python -m pytest tests/test_laptop_acceleration.py -v
```

---

## 4. Running Benchmarks & Autotuning

Benchmark CPU vs GPU sieving, multiprecision arithmetic, and multi-process concurrency on this machine:
```powershell
python -m src.phase4 laptop-benchmark
```
or:
```powershell
python scripts/benchmark_laptop.py
```
Output results are recorded to:
- CSV: `data/laptop_acceleration/benchmarks.csv`
- Report: `research/laptop_acceleration/BENCHMARKS.md`

---

## 5. Operating the Search Campaign

### Option A: Direct Python CLI (Recommended for all environments)
```powershell
# Dry run validation
python -m src.phase4 search --config configs/laptop_i5_10210u_mx250.json --dry-run

# Start real campaign in background
python -m src.phase4 search --config configs/laptop_i5_10210u_mx250.json
```

### Option B: Windows Batch Launcher (Bypasses PowerShell script restrictions)
```cmd
scripts\run_laptop_campaign.bat
```

### Option C: PowerShell Launcher
```powershell
.\scripts\run_laptop_campaign.ps1
```

---

## 6. Campaign Management Commands

Monitor live search progress, query leases, pause, resume, and audit coverage:

```powershell
# Check status
python -m src.phase4 status --campaign laptop_2k_exploration

# Pause search gracefully (flushes checkpoints)
python -m src.phase4 pause --campaign laptop_2k_exploration

# Resume search
python -m src.phase4 resume --campaign laptop_2k_exploration

# Stop search
python -m src.phase4 stop --campaign laptop_2k_exploration

# Audit mathematical coverage for gaps or duplicates
python -m src.phase4 coverage-audit --campaign laptop_2k_exploration

# Generate progress report
python -m src.phase4 report --campaign laptop_2k_exploration
```
