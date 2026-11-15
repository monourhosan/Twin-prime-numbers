# Phase 6B Baseline Audit & Candidate Reconciliation

**Audit Date:** 2026-11-14T12:15:00+06:00  
**Repository:** `https://github.com/monourhosan/Twin-prime-numbers`  
**Active Branch:** `research/phase6b-certification`  
**Base Commit:** `fec3682` (`feat(phase6): implement QCP-6 quadratic co-factor search and discover 108d/110d twin primes`)  
**Working Tree Status:** Clean  

---

## 1. System, Toolchain, and Dependency Audit

- **Operating System:** Microsoft Windows 11 Home Single Language (Build 10.0.26300, 64-bit AMD64)
- **Processor:** Intel(R) Core(TM) i5-10210U CPU @ 1.60GHz (4 physical cores, 8 logical processors)
- **System Memory:** 11.85 GB physical RAM (~1.5 GB available)
- **Python Runtime:** Python 3.12.10 (MSC v.1943 64-bit AMD64)
- **Math Libraries:**
  - `gmpy2`: Version 2.3.2 (backed by GNU MP / GMP 6.3.0, MPFR 4.2.1, MPC 1.3.1)
  - `sympy`: Version 1.14.0
  - `numpy`: Version 2.5.4
  - `scipy`: Version 1.18.1
- **Toolchain & Subsystem Status:**
  - `rustc` 1.85.0 / `cargo` installed; ad-hoc newly compiled binary execution inside `target/debug/build/` is blocked by Windows Application Control (`os error 4551`). Precompiled C-extension DLLs (such as `gmpy2`) execute with native speed without violation.
  - `wsl`: The Windows Subsystem for Linux is **not installed** on this host (`wsl --status` returns error).
  - `PARI/GP` (`gp.exe`): Neither PARI/GP nor Primo is currently installed in PATH or present on the filesystem.
  - `winget`: Available, but does not offer official PARI/GP packages.
- **Baseline Test Suite Status:**
  - Full repository test suite (`python -m pytest tests/ -q`): **150 passed in 10.31s** (0 failed, 0 errors, 100% pass rate).

---

## 2. Comprehensive Inventory Audit

### 2.1 Certified Historical Pairs
The repository contains 52 fully certified and independently attested twin-prime certificates:
- **Phase 1 (CATS):** 35 certificates (5 to 34 digits, $k \cdot 2^n \pm 1$)
- **Phase 2 (CRT Wheel):** 3 certificates (104, 121, 159 digits, $k \cdot 2^n \pm 1$)
- **Phase 3 (HDRSS):** 3 certificates (207, 314, 507 digits, $k \cdot 2^n \pm 1$)
- **Phase 4 (ADRS-4):** 2 certificates (1,028 digits in-repo discovery, 1,509 digits imported external discovery)
- **Phase 5 (SCCA):** 5 certificates (6 to 133 digits, $F \cdot t \pm 1$)
- **Phase 6 (Prior GITCSS):** 2 calibration certificates (4 and 16 digits)
- **Phase 6 (Method Q QCP-6):** 2 primary certified discoveries (108 digits and 110 digits, unconditionally proven via Pocklington BLS Thm 4 and Morrison BLS Thm 17)

### 2.2 Streaming Candidate Log Audit (`data/phase6_candidates.jsonl`)
A forensic audit of the 34.8 MB JSONL candidate file (`data/phase6_candidates.jsonl`) was conducted:
- **Total Logged Entries:** 38,521 candidate evaluations
- **Total Dual PRP Hits:** 111 records
  - **4 Digits:** 1 record (`run_smoke_test_1794611462`, $m = 170$)
  - **16 Digits:** 1 record (`run_pilot_general_discovery_1794611484`, $m = 166666666667062$)
  - **100 Digits:** 100 records across 4 campaigns (last run logged 58 dual PRPs)
  - **350 Digits:** 9 records across 2 campaigns:
    - `run_pilot_350d_campaign_1794613686`: 1 record ($m = \dots 6666691800$)
    - `run_unrestricted_350d_campaign_1794613703`: 8 records (including the identical $m = \dots 6666691800$)
  - **Unique 350-Digit Pairs:** Exactly **8 unique candidate pairs**.

---

## 3. Reconciliation of the Eight 350-Digit Candidate Pairs

### 3.1 Offset Discrepancy Diagnosis
The Phase 6 documentation previously reported candidate center offsets relative to $10^{349}$ as:
$$\{150799, 1531831, 3016051, 3643129, 3714781, 4025959, 5325601, 5854717\}$$
Forensic comparison against the candidate ledger reveals that these values represent the **lower prime offset** $A - 10^{349}$, not the center offset. Since $A = C - 1$, the exact center offsets $C - 10^{349}$ are:
$$\text{Offset}_C = \text{Offset}_A + 1$$
$$\{150800, 1531832, 3016052, 3643130, 3714782, 4025960, 5325602, 5854718\}$$
For every candidate, $C = 10^{349} + \text{Offset}_C$ is strictly divisible by 6 ($C \equiv 0 \pmod 6$), $m = C/6$ is an integer, $A = C - 1$, $B = C + 1$, and $B - A = 2$.

### 3.2 Inventory Table of Reconciled 350-Digit Dual PRPs
Every pair was re-screened using `gmpy2.is_prime` with 50 rounds of Miller-Rabin and the Lucas/BPSW test:

| Index | Offset $C - 10^{349}$ | Offset $A - 10^{349}$ | Digits | 50-Round MR $A$ | 50-Round MR $B$ | Provenance Campaign | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|---|:---:|
| 1 | `+150800` | `+150799` | 350 | **PRP (True)** | **PRP (True)** | `run_pilot_350d` & `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 2 | `+1531832` | `+1531831` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 3 | `+3016052` | `+3016051` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 4 | `+3643130` | `+3643129` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 5 | `+3714782` | `+3714781` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 6 | `+4025960` | `+4025959` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 7 | `+5325602` | `+5325601` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |
| 8 | `+5854718` | `+5854717` | 350 | **PRP (True)** | **PRP (True)** | `run_unrestricted_350d` | `PRP_PENDING_PROOF` |

All 8 pairs are saved losslessly as exact decimal strings in `data/phase6b_pending_pairs.jsonl`.

### 3.3 Factorization Breakdown of $C = 6m$
For classical BLS Theorem 4 (Pocklington) or Theorem 17 (Morrison) to certify $B = 6m + 1$ or $A = 6m - 1$, the known factored divisor $F$ of $6m$ must satisfy:
$$F > \sqrt{B} \approx 10^{175} \quad (\ge 175\text{ decimal digits})$$
Trial division and small-prime factoring on $m$ reveals:
- Candidate 1 ($+150800$): Factored $F = 2^3 \cdot 5^2 \cdot 11^2$ (6 digits), unfactored cofactor: **344 digits**.
- Candidate 2 ($+1531832$): Factored $F = 2^2 \cdot 13^1$ (2 digits), unfactored cofactor: **347 digits**.
- Candidate 3 ($+3016052$): Factored $F = 2^1 \cdot 3^3 \cdot 7^1$ (3 digits), unfactored cofactor: **346 digits**.
- Candidate 4 ($+3643130$): Factored $F = 5^1$ (1 digit), unfactored cofactor: **348 digits**.
- Candidate 5 ($+3714782$): No prime factors $< 50$, unfactored cofactor: **349 digits**.
- Candidate 6 ($+4025960$): Factored $F = 2^2 \cdot 3^3 \cdot 5^1 \cdot 13^1 \cdot 37^1$ (6 digits), unfactored cofactor: **343 digits**.
- Candidate 7 ($+5325602$): No prime factors $< 50$, unfactored cofactor: **349 digits**.
- Candidate 8 ($+5854718$): Factored $F = 11^1$ (2 digits), unfactored cofactor: **348 digits**.

**Mathematical Finding:** Because the cofactors of $m$ have 343 to 349 digits, algebraic $N \pm 1$ factorization without GNFS is completely impossible. Consequently, certifying these 8 candidates cannot be achieved via classical BLS theorems; it fundamentally requires **general-purpose Elliptic Curve Primality Proving (ECPP)**.
