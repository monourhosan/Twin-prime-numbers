# Defect Reproductions: Phase 5 Pipeline & Verification Audit

**Audit Date:** 14 November 2026  
**Auditor:** Antigravity Autonomous Research & Verification Agent  

This document provides formal, reproducible proofs of the defects identified in `src/phase5/` and `scripts/phase5_independent_verify.py` before applying repairs.

---

## 1. Defect P0-A: Independent Verification is Not an Acceptance Gate

### Location
- [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L230-L257) inside `execute_discovery_search`
- [`src/phase5/campaign.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/campaign.py#L288-L305) inside `run_bounded_search`

### Pre-Fix Code Trace (`cli.py`)
```python
# Build and save Schema 5.0 Certificate
cert = TwinPrimeCertificateV5(...)
cert_path = cert.save(output_dir)
cert_data = cert.to_dict()

# Record discovery IN STORAGE BEFORE VERIFICATION
storage.record_discovery(...)

# Run immediate independent verification subprocess
verifier_script = Path(...) / "scripts" / "phase5_independent_verify.py"
if verifier_script.exists():
    v_res = subprocess.run([sys.executable, str(verifier_script), str(cert_path)], capture_output=True, text=True)
    if v_res.returncode == 0:
        print(...)
    else:
        print(...) # Only prints!

# ALWAYS APPENDED TO DISCOVERIES REGARDLESS OF VERIFICATION OUTCOME!
discoveries.append({
    "candidate": cand,
    "cert_path": cert_path,
    "sha256": cert_data["sha256"],
    "novelty_status": novelty_check
})
```

### Manifestation & Impact
If `scripts/phase5_independent_verify.py` is missing, fails, raises an exception, times out, or detects a tampered witness, the candidate is **still recorded in the database `discoveries` table** and **still returned as an accepted discovery** in `discoveries.append(...)`. This violates Non-Negotiable Rule 4 (never accept an unverified claim).

---

## 2. Defect P0-B: Self-Contaminated Novelty Checking & Identifier Mismatch

### Location
- [`src/phase5/storage.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/storage.py#L143-L151) inside `check_novelty`
- [`src/phase5/storage.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/storage.py#L343-L350) inside `is_known_discovery`

### Pre-Fix Code Trace (`storage.py`)
```python
def is_known_discovery(self, canonical_hash: str) -> bool:
    with self._get_connection() as conn:
        row = conn.execute("SELECT 1 FROM candidates WHERE canonical_hash = ?", (canonical_hash,)).fetchone()
        if row:
            return True
        row = conn.execute("SELECT 1 FROM discoveries WHERE sha256 = ?", (canonical_hash,)).fetchone()
        return row is not None
```

### Manifestation & Impact
1. **Self-Contamination:** When a candidate passes PRP screening, it is recorded into `candidates` table with status `PRP_BOTH` and its `canonical_hash`. If `is_known_discovery(canonical_hash)` is subsequently queried, it finds its own row in `candidates` and reports that the candidate is already known!
2. **Identifier Incompatibility:** In `discoveries`, the column `sha256` stores the SHA-256 digest of the entire JSON certificate payload. `canonical_hash` is the SHA-256 digest of the pair string `min:max`. Comparing `WHERE sha256 = canonical_hash` will always evaluate to `False` (unless by astronomical SHA-256 collision), rendering discovery lookups ineffective.

---

## 3. Defect P0-C: Empty-Directory Verification Returns Success (Exit Code 0)

### Location
- [`scripts/phase5_independent_verify.py`](file:///d:/project/Twin%20prime%20numbers/scripts/phase5_independent_verify.py#L303-L305) inside `main`

### Pre-Fix Code Trace
```python
if target.is_dir():
    cert_files = list(target.glob("cert_*.json"))
    if not cert_files:
        print(f"No certificate files matching cert_*.json found in {target}")
        sys.exit(0) # <--- EXITS WITH SUCCESS!
```

### Manifestation & Reproduction
```powershell
python -c "import tempfile, subprocess, sys; d = tempfile.mkdtemp(); res = subprocess.run([sys.executable, 'scripts/phase5_independent_verify.py', d]); print('Exit code:', res.returncode)"
```
**Observed Output:**
```
No certificate files matching cert_*.json found in C:\...\tmp...
Exit code: 0
```
**Impact:** A command like `python -m src.phase5 verify empty_folder/` silently returns success (`0`), falsely attesting that an empty directory has been verified.

---

## 4. Defect P1-D: Status Subcommand Hardcodes Database Path

### Location
- [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L378-L382) inside `run_status`

### Pre-Fix Code Trace
```python
def run_status(args):
    db_path = Path("runs/phase5/phase5_search.db")
    if not db_path.exists():
        print(f"No database found at {db_path}")
        return
```

### Manifestation & Impact
Regardless of the `--campaign` flag or whether the user ran a campaign with a custom `--config` pointing to a different `db_path` (e.g. `research/phase5_runs/<run_id>/campaign.db`), `python -m src.phase5 status` always looks at `runs/phase5/phase5_search.db`. It cannot inspect isolated campaign runs or custom databases.

---

## 5. Defect P1-E: Audit Subcommand Inspects Filenames, Not Proofs

### Location
- [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L57-L109) inside `run_audit`

### Manifestation & Impact
The `audit` command globs `cert_*.json`, parses the JSON, reads the top-level integer or string field `digits`, and prints:
```text
[Phase 5] cert_scca_133d_...json: 133 digits
Total historical certificates audited: 5
Current Repository Maximum: 133 digits
```
It does not invoke any independent verifier, does not verify that $B - A = 2$, does not check Pocklington or Morrison conditions, does not check SHA-256 certificate hashes, and does not report whether proofs are valid or malformed.

---

## 6. Defect P1-F: Work Unit Completion Discards Sieve & Screening Metrics

### Location
- [`src/phase5/cli.py`](file:///d:/project/Twin%20prime%20numbers/src/phase5/cli.py#L332) inside `run_discover`

### Pre-Fix Code Trace
```python
storage.complete_work_unit(wu["work_unit_id"], survivors=0, dual_prp=0, proven=len(finds))
```

### Manifestation & Impact
Although `execute_discovery_search` measures `len(survivors)` and `dual_prp_count`, `run_discover` passes hardcoded `0` for both to `complete_work_unit`. As a result, the database `work_units` table always records `survivors = 0` and `dual_prp = 0`, corrupting multi-family scheduler rewards and bandit statistics.
