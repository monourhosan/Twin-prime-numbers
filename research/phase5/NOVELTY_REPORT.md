# Phase 5 Novelty & Deduplication Report

**Audit Date:** 2026-11-13  
**Authors:** Computational Number Theory & Algorithm Design Group (Antigravity Research)  
**Assigned Novelty Classification:** `NEW_TO_REPO_ONLY; GLOBAL_PRIORITY_UNKNOWN`  

---

## 1. Project Deduplication Audit

To ensure that the newly discovered twin-prime pairs are genuinely novel to the repository, they were cross-referenced against all 8 historical pairs across Phases 1 through 4:

| Historical Pair (File) | Decimal Digits | Representation Form | Lower Member (Prefix...Suffix) | Match Result with Phase 5 Discoveries |
|---|---|---|---|---|
| Phase 1 34d | 34 digits | $k \cdot 2^n \pm 1$ | `52062410...9231` | **NO MATCH** (Distinct digits and representation) |
| `cert_k12477_n330.json` | 104 digits | $12477 \cdot 2^{330} \pm 1$ | `27038827...8407` | **NO MATCH** (Distinct digits and representation) |
| `cert_k126747_n384.json` | 121 digits | $126747 \cdot 2^{384} \pm 1$ | `50014022...3887` | **NO MATCH** (Distinct digits and representation) |
| `cert_k61347_n512.json` | 159 digits | $61347 \cdot 2^{512} \pm 1$ | `82264669...6575` | **NO MATCH** (Distinct digits and representation) |
| `cert_k15993_n672.json` | 207 digits | $15993 \cdot 2^{672} \pm 1$ | `88200155...6607` | **NO MATCH** (Distinct digits and representation) |
| `cert_k254697_n1024.json` | 314 digits | $254697 \cdot 2^{1024} \pm 1$ | `45749007...6623` | **NO MATCH** (Distinct digits and representation) |
| `cert_k1183377_n1664.json` | 507 digits | $1183377 \cdot 2^{1664} \pm 1$ | `54291886...8703` | **NO MATCH** (Distinct digits and representation) |
| `cert_k1836723_n3392.json` | 1,028 digits | $1836723 \cdot 2^{3392} \pm 1$ | `71985442...4271` | **NO MATCH** (Distinct digits and representation) |
| `imported_cert_k416343_n4992.json` | 1,509 digits | $416343 \cdot 2^{4992} \pm 1$ | `12984144...1567` | **NO MATCH** (Distinct digits and representation) |

### Findings:
1. **Integer Non-Collision:** None of the Phase 5 candidates match any previously generated integer value in the repository.
2. **Structural Distinctness:** All Phase 1–4 discoveries belong to the single-power-of-2 family ($k \cdot 2^n \pm 1$). The Phase 5 discoveries belong to the multi-factor smooth-center family ($2^a \cdot 3^b \cdot 5^c \cdot 7^d \cdot t \pm 1$), having distinct prime factor sets and arithmetic representations.

---

## 2. External Catalog Comparison

### 2.1 Public Twin-Prime Top Listings
- **Source 1:** PrimePages (The Largest Known Primes, https://t5k.org/largest.html).
- **Source 2:** Largest Known Prime k-Tuples / Twins (https://pzktupel.de/Top10.php).
- **World Record Benchmark:** The leading known twin-prime pair is $2996863034895 \cdot 2^{1290000} \pm 1$ with **388,342 decimal digits** per member (discovered in September 2016 by PrimeGrid / P. Blazek).

### 2.2 Scoping Limitations
1. Public top-20 and largest-known tables only track prime pairs in the hundreds of thousands of digits; they are **not exhaustive catalogs** of twin primes under 5,000 digits.
2. Therefore, while our discovered 59-digit and 133-digit pairs are completely new to this repository and have no matching records in public registries, we make **no claim of global priority**.
3. The novelty classification is rigorously and honestly maintained as:
   `NEW_TO_REPO_ONLY; GLOBAL_PRIORITY_UNKNOWN`

---

## 3. Scientific Integrity Affirmations

1. **Conjecture Status:** This discovery does **not** prove the Twin Prime Conjecture (that there are infinitely many twin primes).
2. **Theorem Attribution:** No new mathematical theorem is claimed; the certificates strictly implement the published theorems of Brillhart, Lehmer, and Selfridge (1975) and Morrison (1975).
3. **No Fabricated Records:** Probable-prime tests were not labeled proofs, and all certificates were verified by an isolated, independent script.
