# Phase 6 Reproducibility and Verification Protocol (QCP-6)

**Protocol Date:** 2026-11-14T11:56:00+06:00  
**Repository:** `https://github.com/monourhosan/Twin-prime-numbers`  
**Git Branch:** `research/phase6-qcp`  
**Base Commit:** `aef473b1aacbb7ec9a20fbeed780e24712abc777`  

---

## 1. System and Dependency Specifications

- **OS:** Windows 11 Home Single Language (64-bit AMD64)
- **CPU:** Intel Core i5-10210U @ 1.60GHz (4 physical cores, 8 logical processors)
- **Python:** 3.12.10
- **gmpy2:** 2.3.2 (backed by GNU MP / GMP 6.3.0, MPFR 4.2.1, MPC 1.3.1)
- **sympy:** 1.14.0
- **pytest:** 9.2.0

---

## 2. Step-by-Step Reproduction Commands

All commands are noninteractive and must be executed from the repository root:

### Step 1: Environment & Historical Inventory Audit
```bash
python -m src.phase6 audit --repo .
```
**Expected Output:**
- Branch: `research/phase6-qcp`
- gmpy2 version: 2.3.2
- Historical exclusion inventory: 50 unique centers loaded
- Total certificates in repository: 50
- Exit code: 0

### Step 2: Run Empirical Benchmarks
```bash
python -m src.phase6 benchmark --config configs/phase6/pilot.json
```
**Expected Output:**
- Benchmarks Q-reference, Q-segment, Q-event, and Method R linear sieves.
- Benchmarks A-first vs B-first screening order.
- Generates `research/phase6/BENCHMARKS.md` and `research/phase6/benchmarks_raw.csv`.
- Exit code: 0

### Step 3: Dry-Run Discovery Setup Validation
```bash
python -m src.phase6 discover --config configs/phase6/primary.json --dry-run
```
**Expected Output:**
- Status: `DRY_RUN_COMPLETED`
- Tests 0 candidates; validates configuration and partition setup.
- Exit code: 0

### Step 4: Execute Live Primary Discovery Search
```bash
python -m src.phase6 discover --config configs/phase6/primary.json
```
**Expected Output:**
- Sifts through initial work units.
- Discovers candidate at $t = 23947$ (108 digits).
- Proves upper member $B$ via BLS Theorem 4 (Pocklington).
- Proves lower member $A$ via BLS Theorem 17 (Morrison Lucas rank).
- Emits certificate: `proofs/phase6/certificates/cert_qcp6_108d_t23947.json`.
- Status: `CERTIFIED_FRESH_PAIR`.
- Exit code: 0

### Step 5: Resume Search Campaign
```bash
python -m src.phase6 discover --config configs/phase6/primary.json --resume
```
**Expected Output:**
- Resumes from next uncompleted work unit in SQLite ledger.
- Discovers second pair at $t = 131295$ (110 digits).
- Status: `CERTIFIED_FRESH_PAIR`.
- Exit code: 0

### Step 6: Query Campaign Ledger Status
```bash
python -m src.phase6 status --campaign primary
```
**Expected Output:**
- Reports completed units, candidates tested, survivors found, prp hits, proven pairs.
- Exit code: 0

### Step 7: Independent First-Principles Verification
```bash
python scripts/phase6_independent_verify.py proofs/phase6/certificates/cert_qcp6_108d_t23947.json
```
or audit the entire Phase 6 proof directory:
```bash
python -m src.phase6 verify proofs/phase6/
```
**Expected Output:**
- Standalone zero-dependency verifier recomputes all checks:
  - Canonical JSON SHA-256 integrity match.
  - Full factor primality by trial division.
  - Pocklington Fermat congruence and gcd condition on $B$.
  - Morrison sequence non-degeneracy, Jacobi symbol, Lucas congruence, and gcd condition on $A$ via 2x2 companion matrix exponentiation.
- Result: `Verification SUCCESS`.
- Emits cryptographic attestation in `proofs/phase6/attestations/`.
- Exit code: 0

### Step 8: Full Repository Regression Test Suite
```bash
python -m pytest tests/phase6/ -q
python -m pytest tests/ -q
```
**Expected Output:**
- `tests/phase6/`: 31 passed in ~1.1s.
- `tests/`: 150 passed in ~10.5s (0 failures, 0 errors, 100% pass rate).
- Exit code: 0

---

## 3. Cryptographic Artifact Digests

| Artifact File | Role | Exact SHA-256 Digest |
|---|---|---|
| `configs/phase6/primary.json` | Live campaign configuration | `e0bc30f691d179619c96df8a9a08e169da40ff719e737df35fe0c326d21469e7` |
| `proofs/phase6/certificates/cert_qcp6_108d_t23947.json` | 108d Discovery certificate | `a79f1ceabb2f5f00f1f24dcc6d6df82aa65fee73fae77292f2238524c857ef79` |
| `proofs/phase6/attestations/attest_a79f1ceabb2f5f00.json` | Independent verification attestation | `ef563e4823528b7e28b2a3d0ec42ba799ca86851b3f9ff4d528b32087d3dfa53` |
