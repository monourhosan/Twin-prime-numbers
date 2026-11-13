# Phase 6 Discovery and Verification Report: Discovery of a General-Integer Twin-Prime Pair

**Document ID:** `PHASE6-DISCOVERY-REPORT-001`  
**Date:** 2026-11-14T05:21:00+06:00  
**Phase:** Phase 6 (General-Integer Twin-Center Segmented Sieve - GITCSS)  
**Authoritative Discovery Status:** **`DISCOVERY_CERTIFIED_AND_ATTESTED`**

---

## 1. Discovered Twin-Prime Pair

- **Exact Lower Prime ($A$):**
  ```text
  1000000000002371
  ```
- **Exact Upper Prime ($B$):**
  ```text
  1000000000002373
  ```
- **Difference:**
  $$B - A = 1000000000002373 - 1000000000002371 = 2$$
- **Decimal Digit Count:**
  - Lower Prime $A$: **16 decimal digits**
  - Upper Prime $B$: **16 decimal digits**
- **Center Representation:**
  $$C = 6m = 1000000000002372, \qquad m = 166666666667062$$
  $$A = 6m - 1, \qquad B = 6m + 1$$
- **Search Interval:**
  - $p \in [10^{15}, 10^{15} + 10^6]$
  - $m \in [166666666666667, 166666666833333]$
- **Timestamp of Discovery:** 2026-11-13T23:11:24.481478+00:00 (UTC)

---

## 2. Complete Prime Factorization of Center $6m$

To prove both primes deterministically using classical BLS criteria, the center $6m = 1,000,000,000,002,372$ was factored into its prime constituents:

$$6m = 2^2 \times 3^1 \times 83333333333531^1$$

### Deterministic Factor Primality Proof:
1. $2$: Prime (base case).
2. $3$: Prime (base case).
3. $q = 83333333333531$ (14 decimal digits):
   - Proven prime unconditionally via deterministic trial division up to $\sqrt{q} \approx 9,128,709$.
   - Tested by zero-dependency independent verifier in 0.32 seconds.
   - Zero prime factors exist below $\sqrt{q}$.

---

## 3. Deterministic Primality Certifications

### 3.1 Upper Member ($B = 1000000000002373$): Pocklington BLS Theorem 4 Proof
- **Theorem:** Brillhart, Lehmer, and Selfridge (1975), Theorem 4 ($N-1$ test).
- **Factored Part:** $F_B = B - 1 = 6m = 1,000,000,000,002,372$.
- **Remainder:** $R_B = 1$.
- **Factored Fraction:** $F_B / B = 1.0$ (100% factored, $F_B > \sqrt{B}$ holds by 8 orders of magnitude).
- **Prime Factor Set:** $\mathcal{F} = \{2, 3, 83333333333531\}$.
- **Witness Base:** $a = 2$.
  - Fermat Congruence:
    $$2^{B - 1} \equiv 1 \pmod B \quad (\text{PASS})$$
  - Coprimality Conditions:
    - For $q = 2$: $\gcd(2^{(B-1)/2} - 1, B) = 1$
    - For $q = 3$: $\gcd(2^{(B-1)/3} - 1, B) = 1$
    - For $q = 83333333333531$: $\gcd(2^{(B-1)/q} - 1, B) = 1$
- **Conclusion:** $B$ is unconditionally, deterministically prime.

### 3.2 Lower Member ($A = 1000000000002371$): Morrison BLS Theorem 17 Proof
- **Theorem:** Brillhart, Lehmer, and Selfridge (1975), Theorem 17 ($N+1$ test).
- **Odd Factored Part:** $F_{\text{odd}} = 3 \times 83333333333531 = 250,000,000,000,593$.
- **Size Condition:**
  $$(F_{\text{odd}} - 1)^2 \approx (2.5\times 10^{14})^2 = 6.25 \times 10^{28} \gg 10^{15} = A$$
- **Lucas Parameter:** $P = 5, Q = 1$.
- **Discriminant:** $D = P^2 - 4 = 21$.
- **Jacobi Symbol:**
  $$\left(\frac{21}{A}\right) = -1 \quad (\text{PASS})$$
- **Lucas Sequence Congruence:**
  $$U_{A + 1}(5, 1) \equiv 0 \pmod A \quad (\text{PASS})$$
- **Coprimality Conditions:**
  - For $q = 3$: $\gcd(U_{(A+1)/3}(5, 1), A) = 1$
  - For $q = 83333333333531$: $\gcd(U_{(A+1)/q}(5, 1), A) = 1$
- **Conclusion:** $A$ is unconditionally, deterministically prime.

---

## 4. Independent Verification and Attestation

The certificate was validated by the decoupled, zero-dependency independent verifier (`src/phase6/independent_verify.py`):
```bash
python -m src.phase6 verify proofs/phase6/certificates/cert_gitcss_m166666666667062_16d.json
```
**Verifier Output:**
```text
VERIFICATION SUCCESS: cert_gitcss_m166666666667062_16d.json
  Digits: 16 / 16
  Attestation: proofs\phase6\attestations\attest_6c0b671d46a457d1.json
```
- **Certificate Path:** `proofs/phase6/certificates/cert_gitcss_m166666666667062_16d.json`
- **Canonical Payload SHA-256:** `1f2d443508c19ee0650c239183998ccf4eba9bf265dc031b90dba66140c6b727`
- **Raw File SHA-256:** `6c0b671d46a457d16edc48aea5da33f4ab3444ff179b10cd2d652b223efaf6ee`
- **Attestation Path:** `proofs/phase6/attestations/attest_6c0b671d46a457d1.json`

---

## 5. Duplicate and Novelty Audit

1. **Repository Novelty Audit:**
   - Canonical Key: `1000000000002371:1000000000002373`
   - Compared against all 48 historical certificates in `research/phase5_audit/historical_inventory.json` (frozen SHA-256 `f0703dd...`).
   - Match Count: 0.
   - Result: **`NEW_TO_REPOSITORY`** (the first general-integer twin-prime discovery in repository history).
2. **Global Novelty Disclaimer:**
   - In accordance with Non-Negotiable Rule 5, this pair is certified as **new to this repository's research history**. It is not claimed to be the largest twin prime in the world, nor claimed to be globally unprecedented, as twin primes in the 16-digit range fall within reach of distributed searches.

---

## 6. 100-Digit Search Campaign Findings

As specified in Stage D, an exhaustive general-integer campaign was also executed in the 100-digit band:
- **Interval Searched:** $p \in [10^{99}, 10^{99} + 3,145,728]$
- **Centers Screened:** 524,288 candidate centers
- **Survivors Screened ($L=50,000$):** 11,004 survivors
- **Dual PRP Hits Found:** 58 pairs at 100 decimal digits passed Fermat base-2 and 25-round Miller-Rabin tests.
- **Proof Outcome:** In accordance with Non-Negotiable Rule 4 ("Do not report a probable prime as a proven prime"), each 100-digit Dual PRP hit was evaluated for complete center factorization. Because general 100-digit centers have prime factors exceeding trial-division bounds ($> 10^7$) and require ECPP for certification, these 58 candidates were honestly recorded as `UNPROVEN_DUE_TO_FACTORIZATION_LIMIT`.
- **Honest Status:** `NO_NEW_PAIR_FOUND_IN_TESTED_RANGE` for the 100-digit band. No fabricated proofs were emitted.

---

## 7. 350-Digit Unrestricted Campaign Findings (1,000,000 Centers)

Following the Phase 6 research brief instructions, an unrestricted campaign in the 350-digit band starting at the smallest multiple of 6 $\ge 10^{349}$ was executed:

```text
Campaign ID: unrestricted_350d_campaign
Search method: GITCSS (General-Integer Twin-Center Segmented Sieve, Wheel 30/210, Q=100,000)
Search interval: m in [1666...6667, 1666...7666667] (p in [10^349 + 1, 10^349 + 5999997])
Number of eligible centers processed: 1,000,000
Sieve cutoff: 100,000
Total sieve survivors: 18,913
Probable-prime candidates: 8 Dual PRPs
Proof attempts: 8
Accepted lower prime: NOT FOUND (FACTORIZATION_LIMIT_REACHED)
Accepted upper prime: NOT FOUND (FACTORIZATION_LIMIT_REACHED)
Exact difference: N/A (dual PRPs have difference exactly 2)
Decimal digits per member: 350
Lower-member proof method: Unconditionally unproven (exceeds general integer factorization bound without ECPP)
Upper-member proof method: Unconditionally unproven (exceeds general integer factorization bound without ECPP)
Independent verification result: N/A (candidates preserved in ledger data/phase6_candidates.jsonl)
Duplicate check result: All 8 Dual PRPs are newly discovered by this campaign and absent from repository
Certificate SHA-256: N/A (unproven)
Coverage status: COMPLETE_AND_CONTIGUOUS (1,000,000 centers in 4 contiguous segments)
Total runtime: 37.87 s
Hardware/software environment: Intel i5-10210U, 12GB RAM, Windows 11, Python 3.12.10, gmpy2 2.3.2 (GMP 6.3.0)
Reproduction command: python -m src.phase6.cli search --config configs/phase6/unrestricted_350d.json --no-stop --max-segments 4
```

### Empirical Alignment with Hardy-Littlewood Heuristic:
- **Heuristic Expectation:** $\frac{12 C_2}{(\ln 10^{350})^2} \times 10^6 \approx 12$ twin pairs per million eligible centers.
- **Observed Dual PRPs:** **8 Dual PRPs** (close empirical agreement with theoretical density).
- **Candidates Logged:** All 8 dual PRPs (centered at offsets $150799, 1531831, 3016051, 3643129, 3714781, 4025959, 5325601, 5854717$) are recorded in `data/phase6_candidates.jsonl`.
- **Scientific Integrity:** None of the 350-digit probable primes are falsely labeled as proven primes. The checkpoint and coverage manifest are fully preserved.
