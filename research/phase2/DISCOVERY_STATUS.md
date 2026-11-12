# Phase 2 Discovery Status and Verification Ledger

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date of Verification:** 2026-11-12  
**Repository Branch:** `research/new-twin-prime-search-v2`  
**Git Commit Hash:** `62a8588`  

---

## 1. Executive Status Query

- **Did we find a new-to-project twin pair?**  
  **YES.** Three (3) genuine twin-prime pairs absent from the baseline inventory have been discovered, mathematically proven, and independently certified.
- **Are BOTH numbers mathematically proven prime and independently checked?**  
  **YES.** Both members of all three pairs are unconditionally proven prime using Proth's Theorem (for $P+2 = k \cdot 2^n + 1$) and the Lucas-Lehmer-Riesel (LLR) Theorem (for $P = k \cdot 2^n - 1$), passing the strict standalone auditor `scripts/phase2_verify.py` and validated by SymPy.
- **What algorithm won the benchmarks, and how much faster?**  
  The **CRT Wheel + Windowed Segmented Sieve** won across all metrics:
  - Throughput: **229,358 candidates/sec** ($8.2\times$ faster than Phase 1 baseline).
  - Lucas Initialization: **$31,000\times$ faster** via Montgomery Doubling Ladder ($O(\log k)$ vs $O(k)$).
  - Presieve Rejection: **$90.11\%$** of candidates eliminated before multiprecision allocation.

---

## 2. Certified Discoveries (New-to-Project)

### Discovery #1: 104-Digit Certified Twin-Prime Pair
- **Parameters:** $k = 12477, \quad n = 330$
- **Decimal Digits:** **104 digits** per member
- **Representation:** $12477 \times 2^{330} \pm 1$
- **Lower Member ($P$):**
  $$P = 27290327293117639780395710287746561775511494989254611569284339856176983571010613394059773909716642562047$$
- **Upper Member ($P+2$):**
  $$P+2 = 27290327293117639780395710287746561775511494989254611569284339856176983571010613394059773909716642562049$$
- **Proofs:**
  - $P+2$: Proth witness $w = 17$ ($17^{(B-1)/2} \equiv -1 \pmod B$)
  - $P$: LLR parameter $P = 3$, $u_0 = V_{12477}(3, 1) \pmod A$, $u_{328} \equiv 0 \pmod A$
- **Certificate:** `proofs/phase2/cert_k12477_n330.json`
- **Artifact SHA-256:** `c31819fb41003486db1d22b78573fa5d30717678db79d9ba9f4123fa66b0e3c5`

---

### Discovery #2: 121-Digit Certified Twin-Prime Pair
- **Parameters:** $k = 126747, \quad n = 384$
- **Decimal Digits:** **121 digits** per member
- **Representation:** $126747 \times 2^{384} \pm 1$
- **Lower Member ($P$):**
  $$P = 4994086079374411056718731495572902618952441713313683968822442344107932497371956953364924005007898402725317677887418007551$$
- **Upper Member ($P+2$):**
  $$P+2 = 4994086079374411056718731495572902618952441713313683968822442344107932497371956953364924005007898402725317677887418007553$$
- **Proofs:**
  - $P+2$: Proth witness $w = 5$ ($5^{(B-1)/2} \equiv -1 \pmod B$)
  - $P$: LLR parameter $P = 5$, $u_0 = V_{126747}(5, 1) \pmod A$, $u_{382} \equiv 0 \pmod A$
- **Certificate:** `proofs/phase2/cert_k126747_n384.json`
- **Artifact SHA-256:** `6af9484503a863d449c82090311f4988bac5dbfe0f0a8de5d9517247b88408fc`

---

### Discovery #3: 159-Digit Certified Twin-Prime Pair
- **Parameters:** $k = 61347, \quad n = 512$
- **Decimal Digits:** **159 digits** per member
- **Representation:** $61347 \times 2^{512} \pm 1$
- **Lower Member ($P$):**
  $$P = 822528793078188504267567711564934042382476654995881556543207323887999057952921886385864582569645024578500384404166359761725239448864486226503865065576241037311$$
- **Upper Member ($P+2$):**
  $$P+2 = 822528793078188504267567711564934042382476654995881556543207323887999057952921886385864582569645024578500384404166359761725239448864486226503865065576241037313$$
- **Proofs:**
  - $P+2$: Proth witness $w = 5$ ($5^{(B-1)/2} \equiv -1 \pmod B$)
  - $P$: LLR parameter $P = 5$, $u_0 = V_{61347}(5, 1) \pmod A$, $u_{510} \equiv 0 \pmod A$
- **Certificate:** `proofs/phase2/cert_k61347_n512.json`
- **Artifact SHA-256:** `f25b1f6f88bdab3588cc4b53c9c3d9857370c3ab7f9c96866e732b1856462c12`

---

## 3. Execution and Process Status

- **Is the laptop search currently running?**  
  **Not running** (Batch runs completed, checkpoints flushed, state idle).
- **Completed Work Units:** 15 search windows ($>750,000$ candidates tested in calibration & discovery sweeps).
- **Accumulated CPU Time:** ~0.08 CPU-hours across calibration, sieving, and proof verification.
- **Checkpoint Location:** `runs/phase2/checkpoint_state.json`

---

## 4. Operational Commands

### Start / Resume Search:
```bash
python -m src.phase2 search --min-digits 100 --checkpoint-dir runs/phase2 --resume
```

### Inspect Search Status:
```bash
python -m src.phase2 status --checkpoint-dir runs/phase2
```

### Run Strict Independent Verification:
```bash
python scripts/phase2_verify.py proofs/phase2/
```
