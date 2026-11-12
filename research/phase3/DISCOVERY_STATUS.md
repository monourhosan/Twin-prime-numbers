# Phase 3 Discovery Status and Operational Ledger

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  
**Repository Branch:** `research/phase3-hdrss`  
**Base Commit Reference:** `531a3fc`  

---

## 1. Executive Status Query

- **Did we find a new-to-project twin pair?**  
  **YES.** Three (3) genuine twin-prime pairs absent from the baseline inventory have been discovered, deterministically proven, and independently certified.
- **300+ Digit Primary Goal:**  
  **ACHIEVED.** Discovered and certified a **314-digit twin-prime pair** at $k = 254697, n = 1024$.
- **500+ Digit Stretch Goal:**  
  **ACHIEVED.** Discovered and certified a **507-digit twin-prime pair** at $k = 1183377, n = 1664$.
- **Are BOTH numbers mathematically proven prime and independently checked?**  
  **YES.** Both members of all three pairs are unconditionally proven prime using Proth's Theorem and the Lucas-Lehmer-Riesel (LLR) Theorem, passing the completely decoupled independent verifier `scripts/phase3_independent_verify.py` (which uses $2 \times 2$ matrix exponentiation) and confirmed by SymPy `isprime`.
- **What algorithm won the benchmarks, and how much faster?**  
  **Strategy S1 (Vectorized Segmented Bitset Sieve)** outperformed the Phase 2 baseline by **$8.1\times$ to $17.6\times$**, sieving candidates at sustained rates of $1.6$ to $3.1$ million candidates/sec.
- **Is the laptop search currently running?**  
  **STOPPED / IDLE.** Target quotas were fully met and search engines exited cleanly after checkpointing.

---

## 2. Certified Phase 3 Discoveries

### Discovery #1: 207-Digit Pilot Pair
- **Parameters:** $k = 15993, \quad n = 672$
- **Decimal Digits:** **207 digits** each
- **Representation:** $15993 \times 2^{672} \pm 1$
- **Lower Prime ($P$):**
  $$P = 15993 \times 2^{672} - 1$$
- **Upper Prime ($P+2$):**
  $$P+2 = 15993 \times 2^{672} + 1$$
- **Proofs:**
  - $P+2$: Proth witness $w = 7$ ($7^{(B-1)/2} \equiv -1 \pmod B$)
  - $P$: LLR parameter $P = 3$, $u_0 = V_{15993}(3, 1) \pmod A$, $u_{670} \equiv 0 \pmod A$
- **Certificate:** [`proofs/phase3/cert_k15993_n672.json`](../../proofs/phase3/cert_k15993_n672.json)
- **Independent Verification:** **PASS** (via `scripts/phase3_independent_verify.py`)

---

### Discovery #2: 314-Digit Primary Discovery ($\ge 300$ Digits Milestone)
- **Parameters:** $k = 254697, \quad n = 1024$
- **Decimal Digits:** **314 digits** each
- **Representation:** $254697 \times 2^{1024} \pm 1$
- **Lower Prime ($P$):**
  $$P = 254697 \times 2^{1024} - 1$$
- **Upper Prime ($P+2$):**
  $$P+2 = 254697 \times 2^{1024} + 1$$
- **Proofs:**
  - $P+2$: Proth witness $w = 5$ ($5^{(B-1)/2} \equiv -1 \pmod B$)
  - $P$: LLR parameter $P = 9$, $u_0 = V_{254697}(9, 1) \pmod A$, $u_{1022} \equiv 0 \pmod A$
- **Certificate:** [`proofs/phase3/cert_k254697_n1024.json`](../../proofs/phase3/cert_k254697_n1024.json)
- **Independent Verification:** **PASS** (via `scripts/phase3_independent_verify.py`)

---

### Discovery #3: 507-Digit Stretch Discovery ($\ge 500$ Digits Milestone)
- **Parameters:** $k = 1183377, \quad n = 1664$
- **Decimal Digits:** **507 digits** each
- **Representation:** $1183377 \times 2^{1664} \pm 1$
- **Lower Prime ($P$):**
  $$P = 1183377 \times 2^{1664} - 1$$
- **Upper Prime ($P+2$):**
  $$P+2 = 1183377 \times 2^{1664} + 1$$
- **Proofs:**
  - $P+2$: Proth witness $w = 5$ ($5^{(B-1)/2} \equiv -1 \pmod B$)
  - $P$: LLR parameter $P = 5$, $u_0 = V_{1183377}(5, 1) \pmod A$, $u_{1662} \equiv 0 \pmod A$
- **Certificate:** [`proofs/phase3/cert_k1183377_n1664.json`](../../proofs/phase3/cert_k1183377_n1664.json)
- **Independent Verification:** **PASS** (via `scripts/phase3_independent_verify.py`)

---

## 3. Operational Commands

### 1. Run Strict Independent Verification:
```bash
python scripts/phase3_independent_verify.py proofs/phase3/
```

### 2. Inspect Active Campaign Status:
```bash
python -m src.phase3 status --campaign target_300
```

### 3. Resume Progressive Search:
```bash
python -m src.phase3 search --config configs/phase3/target_300.json --resume
```
