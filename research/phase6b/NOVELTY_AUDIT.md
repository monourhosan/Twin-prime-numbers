# Phase 6B — Novelty Audit, Priority Scoping, and PrimePages Alignment

**Document Version:** 1.0  
**Date:** 2026-11-14  
**Branch:** `research/phase6b-certification`  
**Standard:** Strict Truthfulness and Scientific Integrity

---

## 1. Scoping of Claims: Local vs Global Priority

In strict accordance with the project guidelines and scientific methodology:

1. **No Global Priority Claim:**
   No claim of global discovery priority or world-record status is made for candidates discovered or certified within this repository.
   - The current world record twin prime pair is $2996863034895 \cdot 2^{1290000} \pm 1$ (388,342 digits, discovered in September 2016 by PrimeGrid).
   - All discoveries in this project (spanning 4 to 1,509 digits) serve as verifiable benchmarks and milestones for local search and proof infrastructure.

2. **No Twin Prime Conjecture Resolution:**
   No inference regarding the truth or falsehood of the Twin Prime Conjecture is made based on finite empirical search results or candidate density heuristics.

3. **Distinction of Claim Levels:**
   - `CERTIFIED_RECOVERED_PAIR`: A prior probable prime candidate from the repository that receives its first rigorous, independent mathematical certification.
   - `CERTIFIED_FRESH_PAIR`: A newly generated, previously unobserved candidate pair that is generated, sieved, screened, certified, and independently attested within the project.
   - `NEW_LOCAL_SIZE_RECORD`: A certified pair with digit count strictly exceeding the current repository maximum (1,509 digits).
   - `NO_CERTIFIED_PAIR_YET`: An honest record of a finite search window that yielded zero certified pairs within the allocated time or resource budget.
   - `BLOCKED`: An honest record that a required proof backend is unavailable on the host under existing security constraints.

---

## 2. Repository Historical Record Inventory

An exhaustive audit of the 54 certificates across all repository phases confirms:

| Phase | Architecture / Family | Maximum Certified Digits | Certificate Path | Independent Verifier |
|---|---|---|---|---|
| **Phase 1** | Proth / LLR ($k \cdot 2^n \pm 1$) | 34 digits | `proofs/cert_k4107_n100.json` | `scripts/verify_certificate.py` |
| **Phase 2** | Proth / LLR ($k \cdot 2^n \pm 1$) | 159 digits | `proofs/phase2/cert_k61347_n512.json` | `scripts/phase2_verify.py` |
| **Phase 3** | Proth / LLR ($k \cdot 2^n \pm 1$) | 507 digits | `proofs/phase3/cert_k1183377_n1664.json` | `scripts/phase3_independent_verify.py` |
| **Phase 4** | Proth / LLR ($k \cdot 2^n \pm 1$) | **1,509 digits** | `proofs/phase4/imported_cert_k416343_n4992.json` | `scripts/phase4_independent_verify.py` |
| **Phase 5** | SCCA Smooth Center ($C = F \cdot t$) | 133 digits | `proofs/phase5/cert_scca_133d_...json` | `scripts/phase5_independent_verify.py` |
| **Phase 6** | QCP-6 Quadratic Co-Factor | 110 digits | `proofs/phase6/certificates/cert_qcp6_110d_t131295.json` | `src/phase6/independent_verify.py` |

**Current Active Local Record:** 1,509 digits (`imported_cert_k416343_n4992.json`).

---

## 3. PrimePages Submission Criteria Alignment

The PrimePages (Chris Caldwell, University of Tennessee at Martin) maintains criteria for record primes:
- The top 5,000 largest known twin prime pairs currently require $> 5,000$ decimal digits.
- Twin primes below 5,000 digits are not eligible for submission to the PrimePages main database, but are valuable for open-source mathematical algorithm benchmarking and reproducible computational number theory.
