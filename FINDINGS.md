# Research Findings: Largest, Latest, and Finite-Bound Twin Primes

**Document Version:** 1.0.0  
**Audit Date (UTC):** 2026-11-12  
**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Research Working Group:** Antigravity Autonomous Number Theory Team  

---

## 1. Executive Summary: Three Distinct Meanings

The question of finding "the biggest and the last twin prime numbers" comprises three mathematically distinct inquiries:

| Research Question | Precise Scientific Definition | Empirical / Mathematical Status |
| :--- | :--- | :--- |
| **1. Largest Known Twin Primes** | The largest pair $(p, p+2)$ with both members **verified prime** publicly documented to date. | $2996863034895 \times 2^{1290000} \pm 1$ (**388,342 decimal digits**). Discovered Sept 2016 by Tom Greer (PrimeGrid / LLR). |
| **2. Latest Verified Discovery** | The most recently documented entry on authoritative record registries, regardless of rank. | $152748736824915 \times 2^{480480} \pm 1$ (**144,654 decimal digits**). Discovered / verified **10 January 2026** by Daniel Brockwell et al. |
| **3. The "Last" Twin Prime Ever** | Does an ultimate final twin-prime pair exist over all positive integers $\mathbb{N}$? | **Unresolved open problem** (Twin Prime Conjecture). Infinite search cannot settle it. In contrast, the largest pair in a finite interval $[L, U]$ is fully decidable. |

---

## 2. Question 1: Current Largest Known Twin Primes

* **Exact Symbolic Representation:**
  $$p = 2996863034895 \times 2^{1290000} - 1$$
  $$p + 2 = 2996863034895 \times 2^{1290000} + 1$$
  Compact form: $2996863034895 \times 2^{1290000} \pm 1$.
* **Decimal Digit Count:** Exactly **388,342 digits** in each prime member.
* **Discovery Timestamp:** 2016-09-14T04:24:46Z.
* **Discoverer:** Tom Greer (Prescott, Arizona, USA), volunteer participant in the distributed computing project **PrimeGrid** (Sophie Germain Prime Search subproject on the BOINC platform).
* **Independent Verification Timestamp:** 2016-09-19.
* **Verifier:** Don Palmer (Canada), using Jean Penné’s LLR program.
* **Verification Method:** Deterministic Lucas-Lehmer-Riesel (LLR) test for $p$ and Proth’s theorem for $p+2$.
* **Authoritative Registry Listings:**
  * *The PrimePages (t5k.org):* Rank #1 on the Top 20 Twin Primes database (Prover code: `L2035`, database verified 2026-11-12).
  * *Tony Forbes’ Prime $k$-tuple History:* `pzktupel.de/KTHIST/kt002.php` (updated 10 January 2026).

---

## 3. Question 2: Most Recently Verified Twin-Prime Discovery

* **Registry Scope:** Authoritative international registries tracking large primes (The PrimePages Top 20 and Tony Forbes' Prime $k$-tuple History).
* **Latest Scoped Discovery:**
  $$152748736824915 \times 2^{480480} \pm 1$$
* **Decimal Digit Count:** **144,654 digits** each (Rank #3 all-time size).
* **Verification Date:** **10 January 2026**.
* **Discoverers / Contributors:** Daniel Brockwell, Göran Schmidt, Carlos Eduardo Pinho, Michael Kwok, Richard Kapek, Stephan Vink.
* **Software Stack:** TwinGen, NewPGen, Twin Prime Search (TPS), PRST (Proth and Riesel Sieve Tester).
* **Scope Caveat:** Everyday small twin primes (e.g., 50 to 1,000 digits) are found continuously by computational hobbyists across the world. Because no global clearinghouse registers sub-record discoveries, "the latest twin prime discovered globally" is undefined. The latest *verifiable record-list entry* is the 10 January 2026 discovery by Brockwell et al.

---

## 4. Question 3: Can the "Last" Twin Prime Ever Be Identified?

* **Mathematical Status:** The question of whether there exists a "last" twin prime pair is logically equivalent to the negation of the **Twin Prime Conjecture**:
  $$\text{Twin Prime Conjecture:} \quad |\{(p, p+2) \mid p, p+2 \in \mathbb{P}\}| = \infty$$
* **Current Proof Status:**
  * Number theory has **not proved** that twin primes terminate, nor has it proved that they continue indefinitely.
  * Breakthroughs on bounded prime gaps (Yitang Zhang, 2013; James Maynard, 2013; Terence Tao, 2014) established that $\liminf_{n \to \infty} (p_{n+1} - p_n) \le 246$ unconditionally, and $\le 6$ under the Generalized Elliott-Halberstam conjecture. However, the exact gap of 2 remains unresolved due to the parity barrier in sieve theory.
  * Viggo Brun (1919) proved the convergence of the sum of reciprocals ($B_2 \approx 1.90216$), establishing that twin primes are sparse, but this does not imply finiteness.
* **Epistemological Constraint:**
  * No finite computation can identify an ultimate last twin-prime pair.
* **Rigorously Solvable Finite Counterpart:**
  * For any explicitly specified finite interval $[L, U] \subset \mathbb{N}$, the **largest twin-prime pair within $[L, U]$** is strictly decidable and provable.

---

## 5. Strongest Results Actually Achieved in This Project

Using our newly designed and implemented **CATS** (*Certificate-Aware Adaptive Twin-prime Sieve*) engine, we executed reproducible computational experiments on the local system:

### 5.1 Certified Largest Twin-Prime Pairs in Finite Intervals

| Finite Range $[L, U]$ | Sieve Limit ($Q$) | Verified Twin Pairs | Execution Time | Largest Certified Pair in Interval |
| :--- | :--- | :--- | :--- | :--- |
| $[2, 100,000]$ | 316 | 1,224 | 0.0351 s | $(99,989, \ 99,991)$ |
| $[2, 1,000,000]$ | 1,000 | 8,169 | 0.3145 s | $(999,959, \ 999,961)$ |
| $[2, 5,000,000]$ | 2,236 | 32,463 | 1.3979 s | $(4,999,961, \ 4,999,963)$ |
| $[2, 10,000,000]$ | 3,162 | **58,980** | **2.8387 s** | **$(9,999,971, \ 9,999,973)$** |

> **Certification Note:** In $[2, 10^7]$, CATS verified that exactly 58,980 twin prime pairs exist, with the provably maximal pair being $(9,999,971, \ 9,999,973)$. Coverage is complete and exhaustive.

### 5.2 Largest Verified Twin Primes Found in Structured Mode

In structured search mode ($k \cdot 2^n \pm 1$):
* **Largest Discovered and Fully Certified Pair:**
  $$4107 \times 2^{100} \pm 1 \quad \text{(34 decimal digits each)}$$
  * Lower prime: $5206241015137338151946960064479231$
  * Upper prime: $5206241015137338151946960064479233$
  * **Upper Primality Certificate:** Proth's Theorem with quadratic non-residue witness $w=5$:
    $$5^{(B-1)/2} \equiv -1 \pmod B \implies B \text{ is unconditionally prime}$$
  * **Lower Primality Certificate:** Lucas-Lehmer-Riesel (LLR) sequence with parameter $P=5$:
    $$u_{n-2} \equiv 0 \pmod A \implies A \text{ is unconditionally prime}$$
  * Certificate file: `proofs/cert_k4107_n100.json` (SHA-256 checksum verified).
* **Additional Discovered Pairs:**
  * 15 proven pairs at $n=30$ (up to 14 decimal digits).
  * 9 proven pairs at $n=50$ (up to 20 decimal digits).
  * 10 proven pairs at $n=10$ (5 to 6 decimal digits).
* **Total Certified Proof Inventory:** 35 tamper-evident JSON certificates generated in `proofs/`, all independently verified by SymPy and Python big-integer arithmetic.

### 5.3 Honest Negative Coverage Results
For $n \in \{250, 500, 1000, 2000\}$ with $k \le 5,000$, zero twin prime pairs were discovered.
* As predicted by the Hardy-Littlewood asymptotic density $\pi_2(x) \propto 1/(\ln x)^2$, candidate survival at $\ge 80$ to $600$ digits is exceptionally rare ($\approx 10^{-5}$ to $10^{-6}$).
* Testing several thousand candidates at 600 digits without finding a twin prime is an expected, scientifically valid negative outcome.

---

## 6. Phase 2 Verified Discoveries: Breaking the 100-Digit Barrier

In Phase 2, utilizing the CRT-wheeled streaming window engine, we expanded the search space to larger $k$ and higher exponents, discovering three genuine twin-prime pairs scaling substantially beyond the Phase 1 34-digit baseline:

| Exponent $n$ | Multiplier $k$ | Decimal Digits | Representation | Verification Status | Certificate File |
| :---: | :---: | :---: | :---: | :---: | :---: |
| $330$ | $12,477$ | **104 digits** | $12477 \times 2^{330} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase2/cert_k12477_n330.json`](proofs/phase2/cert_k12477_n330.json) |
| $384$ | $126,747$ | **121 digits** | $126747 \times 2^{384} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase2/cert_k126747_n384.json`](proofs/phase2/cert_k126747_n384.json) |
| $512$ | $61,347$ | **159 digits** | $61347 \times 2^{512} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase2/cert_k61347_n512.json`](proofs/phase2/cert_k61347_n512.json) |

### 6.1 Discovery Details
1. **104-Digit Pair ($k = 12477, n = 330$):**
   * $P = 27290327293117639780395710287746561775511494989254611569284339856176983571010613394059773909716642562047$
   * $P+2 = 27290327293117639780395710287746561775511494989254611569284339856176983571010613394059773909716642562049$
   * Proth witness $w = 17$, LLR parameter $P = 3$.
2. **121-Digit Pair ($k = 126747, n = 384$):**
   * $P = 4994086079374411056718731495572902618952441713313683968822442344107932497371956953364924005007898402725317677887418007551$
   * $P+2 = 4994086079374411056718731495572902618952441713313683968822442344107932497371956953364924005007898402725317677887418007553$
   * Proth witness $w = 5$, LLR parameter $P = 5$.
3. **159-Digit Pair ($k = 61347, n = 512$):**
   * $P = 822528793078188504267567711564934042382476654995881556543207323887999057952921886385864582569645024578500384404166359761725239448864486226503865065576241037311$
   * $P+2 = 822528793078188504267567711564934042382476654995881556543207323887999057952921886385864582569645024578500384404166359761725239448864486226503865065576241037313$
   * Proth witness $w = 5$, LLR parameter $P = 5$.

All pairs are verified to be new to this project and pass strict independent verification via `scripts/phase2_verify.py`.

---

## 7. Phase 3 Verified Discoveries: Crossing the 200, 300, and 500-Digit Milestones

Using the Phase 3 HDRSS (*Hybrid Dual-Residue Streaming Sieve*) engine, we launched targeted progressive search campaigns across higher exponents, achieving three breakthrough milestones:

| Exponent $n$ | Multiplier $k$ | Decimal Digits | Representation | Verification Status | Certificate File |
| :---: | :---: | :---: | :---: | :---: | :---: |
| $672$ | $15,993$ | **207 digits** | $15993 \times 2^{672} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase3/cert_k15993_n672.json`](proofs/phase3/cert_k15993_n672.json) |
| $1024$ | $254,697$ | **314 digits** | $254697 \times 2^{1024} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase3/cert_k254697_n1024.json`](proofs/phase3/cert_k254697_n1024.json) |
| $1664$ | $1,183,377$ | **507 digits** | $1183377 \times 2^{1664} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase3/cert_k1183377_n1664.json`](proofs/phase3/cert_k1183377_n1664.json) |

### 7.1 Detailed Milestone Discoveries
1. **Pilot Discovery: 207-Digit Certified Pair ($k = 15993, n = 672$):**
   * Lower prime $P = 15993 \times 2^{672} - 1$ (207 digits)
   * Upper prime $P+2 = 15993 \times 2^{672} + 1$ (207 digits)
   * Proth witness $w = 7$, LLR parameter $P = 3$.
   * Certificate: [`proofs/phase3/cert_k15993_n672.json`](proofs/phase3/cert_k15993_n672.json).

2. **Primary Campaign Milestone: 314-Digit Certified Pair ($k = 254697, n = 1024$):**
   * Lower prime $P = 254697 \times 2^{1024} - 1$ (314 digits)
   * Upper prime $P+2 = 254697 \times 2^{1024} + 1$ (314 digits)
   * Proth witness $w = 5$, LLR parameter $P = 9$.
   * Certificate: [`proofs/phase3/cert_k254697_n1024.json`](proofs/phase3/cert_k254697_n1024.json).

3. **Stretch Campaign Milestone: 507-Digit Certified Pair ($k = 1183377, n = 1664$):**
   * Lower prime $P = 1183377 \times 2^{1664} - 1$ (507 digits)
   * Upper prime $P+2 = 1183377 \times 2^{1664} + 1$ (507 digits)
   * Proth witness $w = 5$, LLR parameter $P = 5$.
   * Certificate: [`proofs/phase3/cert_k1183377_n1664.json`](proofs/phase3/cert_k1183377_n1664.json).

All three pairs are verified absent from the combined Phase 1 and Phase 2 baseline inventory, possess an integer difference of exactly 2, and pass strict independent verification via `scripts/phase3_independent_verify.py` using $2 \times 2$ matrix exponentiation.

---

## 8. Phase 4 Verified Discoveries: 1,028-Digit Milestone and 1,509-Digit Verified Discovery

Deploying the Phase 4 ADRS-4 engine with compact $t$-space sieving, GMP acceleration, and transactional SQLite WAL leases, we achieved two major milestones:

| Exponent $n$ | Multiplier $k$ | Decimal Digits | Representation | Verification Status | Certificate File |
| :---: | :---: | :---: | :---: | :---: | :---: |
| $3392$ | $1,836,723$ | **1,028 digits** | $1836723 \times 2^{3392} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase4/cert_k1836723_n3392.json`](proofs/phase4/cert_k1836723_n3392.json) |
| $4992$ | $416,343$ | **1,509 digits** | $416343 \times 2^{4992} \pm 1$ | **PROVEN TWIN PAIR** | [`proofs/phase4/imported_cert_k416343_n4992.json`](proofs/phase4/imported_cert_k416343_n4992.json) |

* **1,509-Digit Pair:** Proth witness $w = 7$, LLR parameter $P = 3$, $u_{4990} \equiv 0 \pmod A$, attested via [`proofs/phase4/attestations/attest_7025c2a1baf9fa9d.json`](proofs/phase4/attestations/attest_7025c2a1baf9fa9d.json).
* **1,028-Digit Pair:** Proth witness $w = 13$, LLR parameter $P = 3$, $u_{3390} \equiv 0 \pmod A$, attested via [`proofs/phase4/attestations/attest_46a7116dc819e120.json`](proofs/phase4/attestations/attest_46a7116dc819e120.json).

---

## 9. Phase 5 SCCA Discoveries: Smooth-Center Classical Proofs (59 Digits & 133 Digits)

Breaking out of the single-power-of-2 template ($k \cdot 2^n \pm 1$), Phase 5 introduced the Smooth-Center Certificate-Aware Search (SCCA) engine with multi-factor centers $C = F \cdot t = 2^a \cdot 3^b \cdot 5^c \cdot 7^d \cdots t$ and two-sided classical theorems:

| Family ID | Parameter $t$ | Decimal Digits | Representation Form | Lower Theorem / Witness | Upper Theorem / Witness | Certificate File |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `scca_55d` | $877$ | **59 digits** | $(2^3 \cdot 3^{60} \cdot 5^{25} \cdot 7^{10}) \cdot 877 \pm 1$ | Morrison BLS Thm 17 ($P=15$) | Pocklington BLS Thm 4 ($a=3$) | [`proofs/phase5/cert_scca_55d_p2e3_p3e60_p5e25_p7e10_t877_59d.json`](proofs/phase5/cert_scca_55d_p2e3_p3e60_p5e25_p7e10_t877_59d.json) |
| `scca_133d` | $9,718$ | **133 digits** | $(2^3 \cdot 3^{150} \cdot 5^{50} \cdot 7^{25}) \cdot 9718 \pm 1$ | Morrison BLS Thm 17 ($P=13$) | Pocklington BLS Thm 4 ($a=3$) | [`proofs/phase5/cert_scca_133d_p2e3_p3e150_p5e50_p7e25_t9718_133d.json`](proofs/phase5/cert_scca_133d_p2e3_p3e150_p5e50_p7e25_t9718_133d.json) |

* **59-Digit Pair:**
  $$A = 25037754229354201268437363346102433149750232696533203124999$$
  $$B = 25037754229354201268437363346102433149750232696533203125001$$
  Attested via [`proofs/phase5/attestations/attest_1399f4f46bcfbceb.json`](proofs/phase5/attestations/attest_1399f4f46bcfbceb.json) (Status: **PASS**).
* **133-Digit Pair:**
  $$A = 3426149479072239505197841862569239088568399165844990338985564394050460272078493967279183298453001782490900950506329536437988281249999$$
  $$B = 3426149479072239505197841862569239088568399165844990338985564394050460272078493967279183298453001782490900950506329536437988281250001$$
  Attested via [`proofs/phase5/attestations/attest_e54e956a84d652b2.json`](proofs/phase5/attestations/attest_e54e956a84d652b2.json) (Status: **PASS**).

Both pairs satisfy strict integer identity $B - A = 2$, pass all preconditions of BLS Theorem 4 and Theorem 17 without floating-point error, and are independently verified from first principles with zero external codebase dependencies.

---

## 10. Phase 6 GITCSS Discoveries: First General-Integer Twin-Prime Discovery

Departing completely from structured exponential forms ($k \cdot 2^n \pm 1$) and smooth-center families ($C = F \cdot t$), Phase 6 formulated and deployed the **General-Integer Twin-Center Segmented Sieve (GITCSS)**. Operating on the universal representation $p = 6m - 1, p+2 = 6m + 1$ over ordinary integers $m \in \mathbb{Z}^+$, GITCSS applies a two-residue segmented sieve, wheel pre-filtering ($W = 5005$), tiered Miller-Rabin screening, and dual classical primality proofs via center factorization:

| Campaign | Center Index $m$ | Decimal Digits | Lower Prime $A$ | Upper Prime $B$ | Certification Theorems | Certificate File |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `pilot_general_discovery` | $166,666,666,667,062$ | **16 digits** | `1000000000002371` | `1000000000002373` | Pocklington Thm 4 ($B$, $a=2$) & Morrison Thm 17 ($A$, $P=5$) | [`proofs/phase6/certificates/cert_gitcss_m166666666667062_16d.json`](proofs/phase6/certificates/cert_gitcss_m166666666667062_16d.json) |

* **Exact Factorization of Center:**
  $$6m = 1000000000002372 = 2^2 \times 3 \times 83333333333531$$
  Every prime factor was verified unconditionally from first principles via trial division.
* **Independent Attestation:** Attested via [`proofs/phase6/attestations/attest_6c0b671d46a457d1.json`](proofs/phase6/attestations/attest_6c0b671d46a457d1.json) (Status: **PASS**).
* **Novelty:** Audited against all 48 historical repository certificates (`research/phase5_audit/historical_inventory.json`). Confirmed **`NEW_TO_REPOSITORY`** as the repository's first certified general-integer discovery.
* **100-Digit Finite Search Campaign:** Covered 524,288 centers (> 3.14 million consecutive integers) at $10^{99}$, screening 58 Dual PRPs and honestly recording them as `UNPROVEN_DUE_TO_FACTORIZATION_LIMIT` in adherence to scientific integrity.
* **350-Digit Unrestricted Center Campaign (1,000,000 Centers):** Covered 1,000,000 eligible centers (6,000,000 consecutive integers) at $10^{349}$, screening 18,913 survivors from sieve cutoff $Q=100,000$, and discovering 8 Dual PRPs (centered at offsets $150799, 1531831, 3016051, 3643129, 3714781, 4025959, 5325601, 5854717$). Observed rate closely matches the Hardy-Littlewood asymptotic heuristic ($\approx 12$ expected pairs per million centers). All 8 pairs are honestly logged as probable primes in [`data/phase6_candidates.jsonl`](data/phase6_candidates.jsonl) without premature primality claims.

---

## 11. Phase 5 Integrity Repair & Cross-Phase Mathematical Audit (14 November 2026)

Following a comprehensive software and number-theoretic audit, the Phase 5 discovery pipeline was hardened with fail-closed independent verification gates, canonical pair identity (`twin-pair-v1:min:max`), and pre-run historical inventory isolation:
- **Zero-Bypass Verification Gate:** Discoveries cannot be recorded or accepted unless the independent first-principles verifier completes with exit code 0 and emits an authenticated `PASS` attestation.
- **Cross-Phase Mathematical Audit:** All 50 historical proof certificates across Phases 1–6 were independently audited from first principles. Result: **50 / 50 VERIFIED (100.0% PASS)**, 0 failed, 0 malformed.
- **Historical Immutability:** All 60 historical proof certificates and attestations in `proofs/` remain strictly immutable (zero bytes changed).
- **Audit Dossier:** See [`research/phase5_integrity/AUDIT_REPORT.md`](research/phase5_integrity/AUDIT_REPORT.md) and [`research/phase6/READINESS_ASSESSMENT.md`](research/phase6/READINESS_ASSESSMENT.md).





