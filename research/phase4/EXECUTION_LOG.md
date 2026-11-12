# Phase 4 ADRS Execution Log

## Stage A: Baseline Snapshot & Phase 3 Audit
- **UTC Timestamp:** 2026-11-12T09:39:15Z
- **Git Branch:** `research/phase4-adrs`
- **Base Git SHA:** `1831b78931bb9e9ddecfbd5c9061fb7132654ec5`
- **Actions Completed:**
  - Verified working tree clean, created branch `research/phase4-adrs`.
  - Audited Python environment: Python 3.12.10, NumPy 2.5.4, SymPy 1.14.0, pytest 9.2.0, cargo/rustc 1.99.1, installed gmpy2 2.3.2.
  - Executed existing test suite (`python -m pytest -q`): 29 passed in 0.92s.
  - Executed independent verifier on Phase 2 (`scripts/phase2_verify.py proofs/phase2`) -> 3 passed.
  - Executed independent verifier on Phase 3 (`scripts/phase3_independent_verify.py proofs/phase3`) -> 3 passed.
  - Checked checksums against `proofs/phase3/sha256sums.txt` -> 100% match.
  - Confirmed P0 and P1 defect patterns in Phase 3 code (`src/phase3/cli.py`, `storage.py`, `pipeline.py`, `certificate.py`, `scripts/phase3_independent_verify.py`).
- **Next Action:**
  - Build comprehensive Phase 3 audit document `research/phase4/PHASE3_AUDIT.md`.
  - Fix P0 defects in Phase 3 code and verify backwards compatibility.
  - Establish `research/phase4/TEST_REPORT.md` and `research/phase4/PAPER_CLAIM_LEDGER.md`.

## Stage B: ADRS-4 Engine Implementation & Gate B Acceptance
- **UTC Timestamp:** 2026-11-12T10:22:30Z
- **Status:** PASS (UNCONDITIONAL)
- **Implemented Modules:**
  - `src/phase4/config.py`: Schema 4.0 validated dataclass, canonical SHA-256.
  - `src/phase4/math_family.py`: Exact formulas, admissible $k=6t+3$ family, $k < 2^n$ checks, Jacobi and Lucas recurrence.
  - `src/phase4/backend.py`: Multiprecision adapter with `gmpy2` acceleration and 100% fallback consistency.
  - `src/phase4/t_sieve.py`: R0 (baseline), R1 (compact $t$-space block sieve), R2 (adaptive hybrid), Reference Oracle.
  - `src/phase4/prp.py`: Tri-state probable prime screening with compositeness witness preservation.
  - `src/phase4/proof.py`: Proth and LLR deterministic proof engine with strict status distinctions.
  - `src/phase4/certificate.py`: Schema 4.0 two-tier certificate payload and canonical JSON hasher.
  - `src/phase4/storage.py`: SQLite WAL, atomic `BEGIN IMMEDIATE` leases, fencing tokens, stale lease recovery.
  - `src/phase4/scheduler.py`: Deterministic $[k_{start}, k_{end})$ interval planning.
  - `src/phase4/coverage.py`: Exact interval union auditor.
  - `src/phase4/hardware.py`: Host profiler and conservative worker limits.
  - `src/phase4/worker.py`: Windows `spawn`-safe worker pipeline and child execution.
  - `src/phase4/cli.py`: Complete CLI with commands (`doctor`, `audit`, `verify`, `search`, `status`, `pause`, `resume`, `stop`, `coverage-audit`, `report`).
  - `scripts/phase4_independent_verify.py`: Decoupled standalone verifier (pure Python standard library).
- **Test Suite Results:**
  - 54 / 54 tests passed in 1.87s (`python -m pytest -q`).
  - Known Phase 3 pair ($k=15993, n=672$) discovered, proven, and independently attested in clean harness.

## Stage C: Benchmarks & Algorithm Selection
- **UTC Timestamp:** 2026-11-12T10:35:00Z
- **Status:** PASS (UNCONDITIONAL)
- **Controlled Matrix:** Exponents $n \in \{672, 1024, 1664, 3328, 5120\}$, depths $Q \in \{10k, 30k, 50k, 100k\}$, 5 repeated trials.
- **Results:**
  - Sieve strategy R1 ($t$-space block sieve) outperformed R0 baseline across all ranges, processing 3.14M to 14.4M cands/s with 67% lower memory footprint.
  - Sieve cutoff $Q=50,000$ selected as optimal trade-off between sieve time and PRP filter load.
  - GMP/gmpy2 backend yielded 9.26x to 12.19x speedup on modular exponentiation at 1,000+ digits.
  - Multiprocessing (2 workers) achieved 1.62x real speedup with zero SQLite WAL lock contention.
- **Artifacts:** `runs/phase4/benchmarks/*.json`, `runs/phase4/benchmarks/*.csv`, `research/phase4/BENCHMARKS.md`, `paper/phase4/figures/*.png`.

## Stage D: Primary Discovery Campaign
- **UTC Timestamp:** 2026-11-12T10:40:00Z
- **Status:** PASS (UNCONDITIONAL)
- **Campaign Execution:** Launched `target_1000` campaign on branch `research/phase4-adrs`.
- **Candidates Screened:** 2,110,000+ raw candidates across $n=3328$ and $n=3392$.
- **Discovery:** $k = 1836723, n = 3392$
  - Lower member: $A = 1836723 \cdot 2^{3392} - 1$ (1,028 decimal digits, proven prime via LLR $P=3, u_{3390} \equiv 0 \pmod A$).
  - Upper member: $B = 1836723 \cdot 2^{3392} + 1$ (1,028 decimal digits, proven prime via Proth witness $w=13$).
- **Proofs & Attestations:**
  - Proof certificate: `proofs/phase4/cert_k1836723_n3392.json` (SHA-256: `46a7116dc819e1202807c498f31a62f3e7100f586b1c9267c207216296026a41`).
  - Independent attestation: `proofs/phase4/attestations/attest_46a7116dc819e120.json` (SHA-256: `d9c08928dbf03b57366d6feeb5c1aa7e35824c0d12e873c6809635fbb29f3ff2`, verdict: `PASS`).

## Stage E: Stretch Tiers Preparation
- **UTC Timestamp:** 2026-11-12T10:45:00Z
- **Status:** READY (CONFIGURED & VALIDATED)
- **Validated Configs:**
  - `configs/phase4/target_1500.json` ($n=5120$, $\approx 1542$ digits)
  - `configs/phase4/stretch_2000.json` ($n=6656$, $\approx 2005$ digits)

## Stage F: Paper & Reproducibility Release
- **UTC Timestamp:** 2026-11-12T10:48:00Z
- **Status:** COMPLETE
- **Deliverables:**
  - `paper/phase4/manuscript.md` (Full publication-grade paper)
  - `research/phase4/PAPER_CLAIM_LEDGER.md`
  - `research/phase4/PRIOR_ART.md`
  - `research/phase4/COVERAGE_REPORT.md`
  - `research/phase4/DISCOVERY_STATUS.md`
  - `REPRODUCIBILITY_PHASE4.md`
  - `README.md`
- **Git Commit:** `cf7b5bc` (`research/phase4-adrs`)
