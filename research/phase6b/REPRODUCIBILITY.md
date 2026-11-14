# Phase 6B — Exact Reproduction Guide & Artifact Manifest

**Document Version:** 1.0  
**Date:** 2026-11-14  
**Branch:** `research/phase6b-certification`  
**Commit:** `fec3682` (with additive Phase 6B research files)

---

## 1. Hardware & Software Environment

Reproduction was executed on the following validated environment:

- **Operating System:** Windows 11 Home / Pro (AMD64, build 10.0.26300)
- **CPU:** Intel Core i5-10210U @ 1.60 GHz (4 cores, 8 logical threads)
- **RAM:** 12.0 GB (LPDDR3-2133)
- **Python Version:** 3.12.10 (64-bit)
- **Core Dependencies:**
  - `gmpy2`: 2.3.2 (backed by MPIR 3.0.0, MPFR 4.2.1, MPC 1.3.1)
  - `sympy`: 1.14.0
  - `pytest`: 9.2.0
  - `platformdirs`: 4.14.5

---

## 2. Step-by-Step Reproduction Instructions

Execute all commands from the repository root (`d:\project\Twin prime numbers`):

### Step 1: Execute Full Test Suite
Verify that all 156 repository tests (including Phase 6B repair tests and ECPP verifier tests) pass without failure:
```powershell
python -m pytest tests/ -q
# Expected outcome: 156 passed in ~10-12s
```

### Step 2: Audit Historical Repository Proofs
Verify that all 54 historical certificates from Phase 1 through Phase 6 are independently verifiable:
```powershell
python -m src.phase5 audit
# Expected outcome: Total historical certificates audited: 54 | Verified: 54 | Failed: 0
```

### Step 3: Execute Phase 6B Proof Router on Pending 350-Digit Pairs
Audit and route the eight 350-digit probable twin pairs:
```powershell
python -m src.phase6 prove-pending --input data/phase6b_pending_pairs.jsonl
# Expected outcome: Confirms all 8 pairs require ECPP; reports Blocker P6B-BLOCKER-01
```

### Step 4: Validate Independent ECPP Certificate Verifier
Execute unit and tamper tests for the Goldwasser-Kilian-Atkin ECPP verifier:
```powershell
python -m pytest tests/phase6/test_ecpp_verifier.py -v
# Expected outcome: 3 passed in <0.1s
```

### Step 5: Test 1,512-Digit Stretch Campaign
Dry-run the stretch configuration targeting $k \cdot 2^{5020} \pm 1$:
```powershell
python -m src.phase4 search --config configs/phase6/stretch_1512d.json --dry-run
# Expected outcome: Validates configuration SHA-256 and bounds
```

---

## 3. Phase 6B Deliverables Manifest

| Category | File Path | Description |
|---|---|---|
| **Research Report** | `research/phase6b/BASELINE_AUDIT.md` | Audit of 350d candidate provenance, deduplication, and 50-round MR verification. |
| **Research Report** | `research/phase6b/PROOF_BACKEND.md` | Hybrid router architecture, PARI issue #2723 gate, and blocker declaration. |
| **Research Report** | `research/phase6b/BUG_FIXES_AND_TESTS.md` | Analysis and repair of 4 reliability bugs with Mertens saturation theorem. |
| **Research Report** | `research/phase6b/BENCHMARKS.md` | Multi-scale empirical throughput, latency, and family yield comparisons. |
| **Research Report** | `research/phase6b/DISCOVERY_REPORT.md` | Exact outcomes for 350d recovery and 1,510+ digit stretch campaign. |
| **Research Report** | `research/phase6b/NOVELTY_AUDIT.md` | Scoping of claims, PrimePages criteria, and local record preservation. |
| **Research Report** | `research/phase6b/REPRODUCIBILITY.md` | Step-by-step reproduction guide and artifact map. |
| **Source Engine** | `src/phase6/proof_router.py` | Intelligent proof router and ECPP dispatch interface. |
| **Source Engine** | `src/phase6/proof_backend.py` | Repaired deterministic prover with timeout and factor primality checks. |
| **Source Engine** | `src/phase6/screening.py` | Repaired multi-tier candidate screening pipeline. |
| **Source Engine** | `src/phase6/campaign.py` | Repaired search campaign with gap-free cursor recording. |
| **Source Engine** | `src/phase6/coverage.py` | Enhanced SQLite coverage tracker with segment status support. |
| **Source Engine** | `src/phase6/cli.py` | Added `prove-pending` CLI command. |
| **Script** | `scripts/phase6b_ecpp_verify.py` | Independent Goldwasser-Kilian-Atkin ECPP certificate verifier. |
| **Test Suite** | `tests/phase6/test_phase6b_repairs.py` | Automated regression tests for all 4 repaired defects. |
| **Test Suite** | `tests/phase6/test_ecpp_verifier.py` | Unit tests for curve arithmetic and tamper resistance. |
| **Data Ledger** | `data/phase6b_pending_pairs.jsonl` | Lossless inventory of the 8 350-digit probable twin pairs. |
| **Configuration** | `configs/phase6/stretch_1512d.json` | 1,512-digit stretch campaign configuration. |
