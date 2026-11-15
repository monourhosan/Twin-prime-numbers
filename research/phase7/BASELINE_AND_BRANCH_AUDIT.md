# Phase 7 Baseline and Branch Audit

**Date:** 2026-11-14  
**Author:** Google Antigravity (Computational Number Theory & Proof Audit Mission)  
**Starting Branch:** `research/phase6b-certification`  
**Phase 7 Active Branch:** `research/phase7-high-density`  
**Base Commit Hash:** `1b484ef286fa06472461c8216fb282e191d5fa16`  
**Working Tree Status at Fork:** Clean (0 uncommitted files, 0 untracked files)  

---

## 1. Branch Ancestry & Commit Lineage

The Phase 7 research branch `research/phase7-high-density` was branched directly from `origin/research/phase6b-certification` at commit `1b484ef`.

### Ancestry Verification
A topological git log audit confirms that all critical historical milestones and previous bugfix commits are strictly contained within the direct ancestry of this baseline:
1. `1b484ef` - chore: remove transient runtime artifacts and ignore runs/phase6b/ (HEAD of PR #4)
2. `52eb0ab` - feat(phase6b): implement hybrid proof router, ECPP verifier, reliability repairs, and audit 350d/1510d candidate space
3. `fec3682` - feat(phase6): implement QCP-6 quadratic co-factor search and discover 108d/110d twin primes (PR #3)
4. `aef473b` - fix(phase5): repair verification gate, novelty checking, and deliver Phase 6 readiness audit
5. `c9d4619` - feat(phase6): add 350-digit unrestricted campaign, CLI operations, and empirical benchmarks (PR #2)
6. `b498712` - feat(phase6): implement GITCSS engine, discover 16d general twin pair, and audit 100d space
7. `1b9e617` - feat(phase5): repair SCCA pipeline, validate mathematical proofs, and execute bounded 1510d search
8. `6ed8960` - feat(phase5): add 1510d stretch search pipeline and test logs (main)

All historical commits are present in ancestry; no rebase, merge conflict, or missing parent commits exist.

---

## 2. Hardware and Environment Audit

Audit executed live via PowerShell CIM instances and Python runtime introspection:

- **Host Processor:** Intel(R) Core(TM) i5-10210U CPU @ 1.60GHz
  - Physical Cores: 4
  - Logical Processors: 8
  - Architecture: x86_64 / AMD64 Family 6 Model 142 Stepping 12
- **Host Memory:**
  - Total Visible RAM: 12,430,196 KB (~11.85 GB)
  - Free Physical RAM: ~1.92 GB at idle
  - Memory Guardrail: Single-worker default, conservative batch allocations, strict memory monitoring before and during large candidate tests.
- **Operating System:** Windows 11 Pro 64-bit (build 10.0.26300)
- **Python Runtime:** Python 3.12.10 (tags/v3.12.10:0cc8128, Apr 8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
- **Core Mathematical Libraries:**
  - `gmpy2`: 2.3.2 (C-accelerated multiprecision arithmetic via MPIR/GMP and MPFR)
  - `sympy`: 1.14.0 (computational number theory & symbolic mathematics)
  - `numpy`: 2.5.4
  - `pytest`: 9.2.0
- **External Certification Engines:**
  - `PARI/GP`: Not installed on host PATH (`where.exe gp` returned not found; `C:\Program Files\pari*` absent).
  - `WSL`: Not installed (`wsl.exe --list` returned "The Windows Subsystem for Linux is not installed").
  - Policy enforcement: In accordance with prompt guardrails, no unauthorized downloads or security prompt bypasses will be executed. ECPP tasks requiring external PARI/GP will be accurately flagged as blocked by environment until authorized.

---

## 3. Test Suite Count Recomputation

Historical reports in PR #4 contained conflicting test counts: the README cited 159 tests, while an earlier reliability audit cited 156.
We executed a full test run using `python -m pytest`:

```
collected 159 items
============================ 159 passed in 11.84s =============================
```

**Verdict:** The exact live baseline test count is **159 passing tests**, zero failures, zero errors, zero skips.

---

## 4. Pre-Run Historical Certificate Inventory and Audit

A full repository scan identified exactly 52 historical certificates across Phases 1 through 6. All proof files remain 100% immutable byte-for-byte.

### Summary of Historical Sets:
- **Phase 1 (Small Base):** 35 certificates (`proofs/cert_k*.json`), digit range [5, 34]. Verified via first-principles Proth.
- **Phase 2 (CRT-Wheel):** 3 certificates (`proofs/phase2/cert_k*.json`), 104d, 121d, 159d. Verified via `scripts/phase2_verify.py` (3/3 PASS).
- **Phase 3 (HDRSS):** 3 certificates (`proofs/phase3/cert_k*.json`), 207d, 314d, 507d. Verified via `scripts/phase3_independent_verify.py` (3/3 PASS).
- **Phase 4 (ADRS):** 2 certificates (`proofs/phase4/`), 1028d (`cert_k1836723_n3392.json`) and 1509d (`imported_cert_k416343_n4992.json`). Verified via `scripts/phase4_independent_verify.py` (2/2 PASS).
- **Phase 5 (SCCA):** 5 certificates (`proofs/phase5/`), 6d, 12d, 12d, 59d, 133d. Verified via `scripts/phase5_independent_verify.py` (5/5 PASS).
- **Phase 6 (GITCSS & QCP-6):** 4 certificates (`proofs/phase6/certificates/`), 4d, 16d, 108d, 110d. Verified via `scripts/phase6_independent_verify.py` (4/4 PASS).

**Total Historical Proofs Verified:** 52 / 52 (100% PASS rate across all independent verifiers).

---

## 5. Audit of Previous Claims and Historical Discrepancies

1. **1,509-digit Pair Provenance:**
   - Artifact `proofs/phase4/imported_cert_k416343_n4992.json` (1,509 decimal digits) contains imported exploratory coordinates (`provenance: "Imported external discovery"`, found by PrimeGrid / Yves Gallot in 2007). It is mathematically valid and verified, but **not an original discovery of this repository**.
   - Prior to Phase 7, the largest verified twin-prime pair originally discovered within this repository was the 1,028-digit pair (`cert_k1836723_n3392.json`).
2. **Phase 6 GITCSS 350-Digit PRPs:**
   - 8 dual PRPs at 350 digits (`10^349` base) exist in `data/phase6b_pending_pairs.jsonl`. None have been certified because classical factorization of general 350-digit centers requires GNFS or ECPP, and no local ECPP engine was installed.
3. **Phase 6B Stretch 1512d Candidate Window Size:**
   - Config `configs/phase6/stretch_1512d.json` specifies `k_start: 3`, `k_end: 150003`, with $k = 6t + 3$.
   - Stepping by 6 across $[3, 150003)$ yields:
     $$\frac{150003 - 3}{6} = 25,000 \text{ eligible } k \text{ centers (and } t \in [0, 25000)\text{)}.$$
   - Previous reports referencing "50,000 centers" conflated the raw span $150,000 / 3$ with the actual step-6 progression. All Phase 7 models use exact mathematical half-open integer intervals.
