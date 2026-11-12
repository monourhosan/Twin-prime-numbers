# Phase 3 Search Ledger and Work-Unit Coverage Record

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Storage Architecture:** SQLite WAL (`runs/phase3/*.sqlite`) + Cryptographic Version 3.0 Certificates  

---

## 1. Campaign Work-Unit Ledger

### 1.1 Pilot Campaign: `pilot_200` ($\ge 200$ Digits)
- **Target Exponent:** $n = 672$ ($\approx 202$ digits base)
- **Config:** `configs/phase3/pilot_200.json`
- **Work Units Executed:**
  - `task_pilot_n672_k3_50003`: $[3, 50003)$, **Status: COMPLETED**
    - Raw odd $k$ examined: $25,000$
    - Sieve survivors: $341$
    - PRP pair hits: $1$
    - **Proven Discoveries:** **$1$ proven pair at $k=15993, n=672$ (207 digits)**
    - Execution time: $0.11\text{ s}$
    - Certificate: [`proofs/phase3/cert_k15993_n672.json`](../../proofs/phase3/cert_k15993_n672.json)

---

### 1.2 Primary Campaign: `target_300` ($\ge 300$ Digits)
- **Target Exponent:** $n = 1024$ ($\approx 308$ digits base)
- **Config:** `configs/phase3/target_300.json`
- **Work Units Executed:**
  - `task_target_n1024_k3_50003`: $[3, 50003)$, **Status: COMPLETED** (0 PRPs)
  - `task_target_n1024_k50003_100003`: $[50003, 100003)$, **Status: COMPLETED** (0 PRPs)
  - `task_target_n1024_k100003_150003`: $[100003, 150003)$, **Status: COMPLETED** (0 PRPs)
  - `task_target_n1024_k150003_200003`: $[150003, 200003)$, **Status: COMPLETED** (0 PRPs)
  - `task_target_n1024_k200003_250003`: $[200003, 250003)$, **Status: COMPLETED** (0 PRPs)
  - `task_target_n1024_k250003_300003`: $[250003, 300003)$, **Status: PARTIAL** (Cursor at $k=254697$)
    - Raw odd $k$ examined: $2,347$
    - Sieve survivors: $16$
    - PRP pair hits: $1$
    - **Proven Discoveries:** **$1$ proven pair at $k=254697, n=1024$ (314 digits)**
    - Elapsed search time: $4.34\text{ s}$
    - Certificate: [`proofs/phase3/cert_k254697_n1024.json`](../../proofs/phase3/cert_k254697_n1024.json)

---

### 1.3 Stretch Campaign: `stretch_500` ($\ge 500$ Digits)
- **Target Exponent:** $n = 1664$ ($\approx 500$ digits base)
- **Config:** `configs/phase3/stretch_500.json`
- **Work Units Executed:**
  - Progressive search over $24$ windows of $50,000$ $k$-span ($[3, 1200003)$).
  - Terminal work unit: `task_stretch_n1664_k1150003_1200003`: $[1150003, 1200003)$, **Status: PARTIAL** (Cursor at $k=1183377$)
    - Raw odd $k$ examined in campaign: $591,687$
    - Sieve survivors: $4,044$
    - PRP pair hits: $1$
    - **Proven Discoveries:** **$1$ proven pair at $k=1183377, n=1664$ (507 digits)**
    - Elapsed search time: $60.22\text{ s}$
    - Certificate: [`proofs/phase3/cert_k1183377_n1664.json`](../../proofs/phase3/cert_k1183377_n1664.json)

---

## 2. Integrity and Continuation Invariant

No work unit where search stopped mid-window upon reaching discovery goals is mislabeled as `COMPLETED`. In both `target_300` and `stretch_500`, the terminal units are explicitly cataloged as `PARTIAL` with their exact resumption cursors saved in SQLite.
Resuming either campaign via:
```bash
python -m src.phase3 search --config configs/phase3/target_300.json --resume
```
picks up directly from $k=254697$ without skipping untested candidates or repeating already verified ranges.
