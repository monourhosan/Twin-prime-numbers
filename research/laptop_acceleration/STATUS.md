# Project Status: Laptop CPU + NVIDIA MX250 Twin-Prime Search

**Status Date:** 2026-11-13  
**Active Git Branch:** `research/laptop-mx250-acceleration`  
**Base Commit SHA:** `6b74b5df62`  
**Operational Status:** Ready / Benchmark Validated / Verified Discoveries Imported  

---

## 1. Verified Discoveries Summary

| Rank | Candidate Formula | Digits / Member | Upper Proof | Lower Proof | Verification Status | Artifact File |
|---|---|---|---|---|---|---|
| **1 (Max)** | $416343 \cdot 2^{4992} \pm 1$ | **1,509 digits** | Proth ($w=7$) | LLR ($P=3$, $u_{4990}=0$) | **PASS (Independently Verified)** | [imported_cert_k416343_n4992.json](file:///d:/project/Twin%20prime%20numbers/proofs/phase4/imported_cert_k416343_n4992.json) |
| **2** | $1836723 \cdot 2^{3392} \pm 1$ | **1,028 digits** | Proth ($w=13$) | LLR ($P=3$, $u_{3390}=0$) | **PASS (Independently Verified)** | [cert_k1836723_n3392.json](file:///d:/project/Twin%20prime%20numbers/proofs/phase4/cert_k1836723_n3392.json) |
| **3** | $1183377 \cdot 2^{1664} \pm 1$ | **507 digits** | Proth ($w=5$) | LLR ($P=5$, $u_{1662}=0$) | **PASS (Independently Verified)** | [cert_k1183377_n1664.json](file:///d:/project/Twin%20prime numbers/proofs/phase3/cert_k1183377_n1664.json) |
| **4** | $254697 \cdot 2^{1024} \pm 1$ | **314 digits** | Proth ($w=5$) | LLR ($P=9$, $u_{1022}=0$) | **PASS (Independently Verified)** | [cert_k254697_n1024.json](file:///d:/project/Twin%20prime%20numbers/proofs/phase3/cert_k254697_n1024.json) |
| **5** | $15993 \cdot 2^{672} \pm 1$ | **207 digits** | Proth ($w=7$) | LLR ($P=3$, $u_{670}=0$) | **PASS (Independently Verified)** | [cert_k15993_n672.json](file:///d:/project/Twin%20prime%20numbers/proofs/phase3/cert_k15993_n672.json) |

All certificates pass strict independent verification with Python standard library matrix powering.

---

## 2. Hardware Engine State

- **CPU:** Intel Core i5-10210U @ 1.60GHz (4 physical cores, 8 logical threads, 15W TDP).
  - Selected worker concurrency: **3 worker processes** (7,783 cands/sec, 76.7% scaling efficiency).
- **GPU:** NVIDIA GeForce MX250 (2,048 MB VRAM, Pascal sm_61).
  - Sieve throughput: **15,000,000 to 26,000,000 cands/sec** (**4.1x to 17.8x speedup** over CPU vectorized slicing).
  - Operating temperature: **58–60°C** (well within the 80°C soft threshold).
- **RAM / Storage:** 3.8+ GB RAM available, 335+ GB disk free on C:, 75+ GB free on D:.
- **Test Suite:** 64 tests passing in 7.08s (100% pass rate).

---

## 3. Active Campaign Configuration

- **Target Campaign:** `laptop_2k_exploration`
- **Target Digit Regime:** $\ge 2,000$ digits ($n \in [4992, 6656, 7168, 8192]$)
- **Profile Configuration:** `configs/laptop_i5_10210u_mx250.json`
- **Database:** `runs/phase4/laptop_2k_exploration/laptop_2k_exploration.sqlite` (SQLite WAL mode)
