# Phase 6 Reproducibility and Verification Protocol (QCP-6)

**Protocol Date:** 2026-11-15T11:52:00+06:00  
**Repository:** `https://github.com/monourhosan/Twin-prime-numbers`  
**Git Branch:** `research/phase6-independent-interval-search`  
**Base Commit:** `ea14acd964dd4500612d8e915fe1c94f4e4ce5e1`  

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

All commands are non-interactive and must be executed from the repository root:

### Step 1: Environment & Historical Inventory Audit
```powershell
python -m src.phase6 audit --repo .
```
**Expected Output:**
- Git Branch: `research/phase6-independent-interval-search`
- gmpy2 version: 2.3.2
- Historical exclusion inventory: 52 unique centers loaded
- Total certificates in repository: 56
- Exit code: 0

### Step 2: Run Full Regression and Unit Test Suite
```powershell
python -m pytest tests/ -v
```
**Expected Output:**
- `190 passed` (100% PASS across Phases 1–8).
- Exit code: 0

### Step 3: Run Fresh 107-Digit Discovery Campaign
```powershell
python -m src.phase6 discover --config configs/phase6/fresh_107d.json
```
**Expected Output:**
- Status: `CERTIFIED_FRESH_PAIR`
- Discovers and unconditionally proves fresh 108-digit pair at $t = 13345$.
- Artifact saved: `proofs/phase6/certificates/cert_qcp6_108d_t13345.json`.
- Exit code: 0

### Step 4: Run Strong 502/503-Digit Discovery Campaign
```powershell
python -m src.phase6 discover --config configs/phase6/strong_502d.json
```
**Expected Output:**
- Status: `CERTIFIED_FRESH_PAIR`
- Discovers and unconditionally proves fresh 503-digit pair at $t = 114833$.
- Artifact saved: `proofs/phase6/certificates/cert_qcp6_503d_t114833.json`.
- Exit code: 0

### Step 5: Execute Independent Zero-Dependency Verifier
```powershell
python -m src.phase6 verify proofs/phase6/certificates
python scripts/phase6_independent_verify.py proofs/phase6/certificates
```
**Expected Output:**
- Verifies all certificates in `proofs/phase6/certificates/` from first principles.
- Checks exact integer arithmetic, $(B - A) = 2$, $C \equiv 0 \pmod 6$, Pocklington Fermat congruence and GCD conditions, Morrison Lucas sequence $U_{A+1}(P, 1) \equiv 0 \pmod A$ via companion matrix powering, and canonical SHA-256 digests.
- Emits cryptographically signed JSON attestations in `proofs/phase6/attestations/`.
- Summary: `Total=8, Verified=8, Failed=0`.
- Exit code: 0
