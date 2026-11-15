# Historical Novelty Reconciliation & Provenance Analysis

**Audit Date:** 14 November 2026  
**Auditor:** Antigravity Autonomous Research & Verification Agent  
**Policy:** Non-Mutating Historical Preservation (Rule 1)  

---

## 1. Background & The Historical Context Problem

In historical Phase 5 certificates and README descriptions, newly discovered pairs were labeled with novelty metadata such as `NEW_TO_REPO_ONLY`.
When an audit is conducted at a later date, every previously discovered pair is now physically present in the checked-out repository.

### Semantic Distinctions
- `ALREADY_IN_REPOSITORY`: The integer pair $(A, B)$ exists in an authenticated pre-run historical inventory baseline created before the campaign starts.
- `NEW_TO_REPO_ONLY`: The integer pair was absent from all authenticated pre-run repository records at the precise timestamp of its discovery, but cannot be proven to be globally unknown across mathematical literature without external oracles.
- `UNKNOWN_NOVELTY`: Insufficient historical evidence exists to establish pre-run absence.

**Crucial Preservation Rule:**  
Historical certificate JSON files (`cert_scca_55d_...json`, `cert_scca_133d_...json`) must **never be rewritten in place** to alter their historical novelty status strings. Instead, this non-mutating reconciliation establishes the historical vs. contemporary interpretation backed by Git provenance.

---

## 2. Reconciled Pair Inventory & Provenance

| Certificate File | Stated Status | Contemporary Status | Discovery Date | Git Commit of First Inclusion | Verified Novelty Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cert_scca_smoke_p2e3_p3e4_p5e2_p7e1_t4_6d.json` | `NEW_TO_REPO_ONLY` | `ALREADY_IN_REPOSITORY` | 13 Nov 2026 | `a333b9b` | Known small integer pair (6 digits); novel to repository at time of commit `a333b9b`. |
| `cert_scca_fam1_..._t90_12d.json` | `NEW_TO_REPO_ONLY` | `ALREADY_IN_REPOSITORY` | 13 Nov 2026 | `a333b9b` | 12-digit pair; absent from Phases 1–4 catalogs prior to `a333b9b`. |
| `cert_scca_fam1_..._t104_12d.json` | `NEW_TO_REPO_ONLY` | `ALREADY_IN_REPOSITORY` | 13 Nov 2026 | `a333b9b` | 12-digit pair; absent from Phases 1–4 catalogs prior to `a333b9b`. |
| `cert_scca_55d_..._t877_59d.json` | `NEW_TO_REPO_ONLY` | `ALREADY_IN_REPOSITORY` | 13 Nov 2026 | `a333b9b` | 59-digit pair; strictly novel to repository prior to `a333b9b`. |
| `cert_scca_133d_..._t9718_133d.json` | `NEW_TO_REPO_ONLY` | `ALREADY_IN_REPOSITORY` | 13 Nov 2026 | `a333b9b` | 133-digit pair; strictly novel to repository prior to `a333b9b`. |

---

## 3. Methodological Reconciliation: Pre-Run Snapshot Isolation

To prevent the recurrence of Defect P0-B (where novelty queries were contaminated by active run tables):
1. **Pre-Run Snapshot:** At the start of every search campaign, the engine takes an immutable snapshot of all known pairs from [`HISTORICAL_CERTIFICATE_INVENTORY.json`](file:///d:/project/Twin%20prime%20numbers/research/phase5_integrity/HISTORICAL_CERTIFICATE_INVENTORY.json) into memory.
2. **Canonical Pair Identity:** All comparisons use the domain-separated key:
   \[
   \text{canonical\_pair\_key}(A, B) = \text{twin-pair-v1}:\min(A, B):\max(A, B)
   \]
3. **Decoupled Progression:** Active candidates entering PRP screening stages (`candidates` table) are excluded from novelty checks, ensuring a candidate never makes itself appear as an existing repository discovery.
4. **Conclusion:** Both the 59-digit and 133-digit pairs were authentically novel to the repository when first discovered in Phase 5, and their original certificate payloads remain authoritative and unmutated.
