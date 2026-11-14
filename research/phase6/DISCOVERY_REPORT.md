# Phase 6 Discovery and Verification Report: Discovery of Unconditionally Proven 108-Digit Twin-Prime Pair

**Document ID:** `PHASE6-DISCOVERY-REPORT-002`  
**Date:** 2026-11-14T11:55:00+06:00  
**Phase:** Phase 6: Quadratic Co-Factor Proof Search (QCP-6)  
**Authoritative Discovery Status:** **`CERTIFIED_FRESH_PAIR`**  
**Independent Verification Attestation:** `proofs/phase6/attestations/attest_a79f1ceabb2f5f00.json`  

---

## 1. Discovered Twin-Prime Pair Summary

- **Primary Discovered Twin-Prime Pair:**
  - **Exact Lower Prime ($A$):**
    ```text
    580429447365073672176135517613336328521016173269486620796396610861564085752362937835064139064294668347640867
    ```
  - **Exact Upper Prime ($B$):**
    ```text
    580429447365073672176135517613336328521016173269486620796396610861564085752362937835064139064294668347640869
    ```
  - **Exact Integer Center ($C = (A + B) // 2$):**
    ```text
    580429447365073672176135517613336328521016173269486620796396610861564085752362937835064139064294668347640868
    ```
  - **Twin Gap:**
    $$B - A = 2$$
  - **Decimal Digit Counts:**
    - $\text{len}(A) = 108\text{ digits}$
    - $\text{len}(B) = 108\text{ digits}$
  - **Center Divisibility by 6:**
    $$C \equiv 0 \pmod 6 \quad (C = 6 \cdot 96738241227512278696022586268889388086836028878247770132732768476927347625393822972510689844049111391273478)$$

---

## 2. Compact Algebraic Representation (Method Q Family)

The discovery was produced under the quadratic co-factor parameter family:
$$x = S \cdot t$$
$$C = x(x - h)$$
$$A = x^2 - hx - 1$$
$$B = x^2 - hx + 1$$

with parameters:
- **Polynomial Offset ($h$):** $h = 3$
- **Factored Anchor ($S$):** 50 decimal digits, seed `2026111402`:
  $$S = 31814390296223916158011157598224064684469095400701$$
  Prime factors of $S$:
  $$S = 3^1 \cdot 10006721^1 \cdot 10048373^1 \cdot 10051141^1 \cdot 10075687^1 \cdot 10091327^1 \cdot 10139953^1 \cdot 10177487^1$$
- **Candidate Index ($t$):** $t = 23947$ ($t = 2j + 1$ with $j = 11973$).
  Prime factors of $t$:
  $$t = 7^1 \cdot 11^1 \cdot 311^1$$
- **Proof Factor ($F = x = S \cdot t$):** 54 decimal digits:
  $$F = 761859204423674120235893191004671676998981427560586847$$
  Full prime factorization of $F$:
  $$F = 3^1 \cdot 7^1 \cdot 11^1 \cdot 311^1 \cdot 10006721^1 \cdot 10048373^1 \cdot 10051141^1 \cdot 10075687^1 \cdot 10091327^1 \cdot 10139953^1 \cdot 10177487^1$$
  Every prime factor of $F$ is strictly $< 1.1 \times 10^7$ and unconditionally proven prime by trial division.

---

## 3. Unconditional Primality Proofs

### 3.1 Upper Member $B$ (108 Digits)
- **Theorem:** Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington $N-1$)
- **Factorization:** $B - 1 = F \cdot (x - 3) = F \cdot 761859204423674120235893191004671676998981427560586844$
- **Size Condition:**
  $$F^2 = 580429447365073672176135517613336328521016173269486623081974224132586446460042510849079170061238951029401409 > B$$
  Holds strictly: $F^2 - B = 3x - 1 > 0$.
- **Witnesses:**
  Base $a = 2$ satisfies:
  1. $2^{B - 1} \equiv 1 \pmod B$
  2. $\gcd(2^{(B - 1)/q} - 1, B) = 1$ for all 11 prime factors $q \in \{3, 7, 11, 311, 10006721, 10048373, 10051141, 10075687, 10091327, 10139953, 10177487\}$.
- **Conclusion:** Upper member $B$ is unconditionally proven prime.

### 3.2 Lower Member $A$ (108 Digits)
- **Theorem:** Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison $N+1$ Lucas Rank)
- **Factorization:** $A + 1 = F \cdot (x - 3)$
- **Size Condition:**
  $$(F - 1)^2 = 580429447365073672176135517613336328521016173269486621558255815285238205988256128839735816063276095908227716 > A$$
  Holds strictly: $(F - 1)^2 - A = x + 2 > 0$.
- **Lucas Sequence Parameters:**
  - $P = 3, \quad Q = 1, \quad D = P^2 - 4 = 5$
  - Non-degeneracy: $\gcd(A, 2 \cdot 5) = 1$
  - Jacobi Symbol: $\left(\frac{5}{A}\right) = -1$
- **Lucas Congruence and Coprimality Checks:**
  1. $U_{A + 1}(3, 1) \equiv 0 \pmod A$
  2. $\gcd(U_{(A + 1)/q}(3, 1), A) = 1$ for all 11 prime factors $q \mid F$.
- **Conclusion:** Lower member $A$ is unconditionally proven prime.

---

## 4. Independent Verification & Cryptographic Integrity

- **Certificate Artifact:** `proofs/phase6/certificates/cert_qcp6_108d_t23947.json`
- **Canonical SHA-256 Digest:** `a79f1ceabb2f5f00f1f24dcc6d6df82aa65fee73fae77292f2238524c857ef79`
- **Independent Attestation:** `proofs/phase6/attestations/attest_a79f1ceabb2f5f00.json`
- **Verifier:** `scripts/phase6_independent_verify.py`
  - Recomputed all mathematical checks from first principles.
  - Zero imports from `src.phase6`.
  - Recomputed Lucas sequence $U_k(3, 1) \pmod A$ using independent standard-library 2x2 companion matrix exponentiation.
  - Verified 100% of factor primality, modular congruences, gcd conditions, and canonical byte hashes.

---

## 5. Repository Novelty and Global Search Status

1. **Repository Novelty:**
   - Compared against canonical repository exclusion index of all 50 historical centers from Phases 1–5 and prior tests (`data/phase6/exclusion_index.json`).
   - The integer center $C$ is **100% NEW to the repository**.
2. **Global Novelty & Record Assessment:**
   - As of 2026-11-14, the world record twin-prime pair is $2996863034895 \cdot 2^{1290000} \pm 1$ (388,342 digits).
   - The PrimePages Top 20 entry threshold is 71,298 digits.
   - At 108 digits, this pair is an independent computational discovery within the primary target band, but does not qualify for the PrimePages Top 20 world ranking.
   - No match was found in checked repository records; external priority is unestablished.

---

## 6. Campaign Execution Metrics

| Metric | Measured Value |
|---|---|
| **Campaign ID** | `primary` |
| **Sieve Depth ($Q_{\max}$)** | 100,000 primes |
| **Candidates Sifted** | 25,000 ($j \in [10000, 35000)$) |
| **Sieve Survivors** | 973 (3.89% survivor fraction) |
| **Screening Order** | $B$-first early exit |
| **Dual PRP Hits** | 1 (Candidate $t = 23947$) |
| **Proof Latency** | 0.018 seconds |
| **Total Campaign Time** | 0.14 seconds |
| **Exit Condition** | Stop on first certified pair (`stop_on_first_certified = true`) |
