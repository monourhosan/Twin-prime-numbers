# Phase 7 Reproduction and Verifier Audit Report

**Date:** 15 November 2026  
**Auditor:** Antigravity (Google DeepMind)  
**Target:** `proofs/phase7/certificates/cert_hdc7_1510d_B13_n4985_t15658.json`  
**Standalone Verifier:** `scripts/phase7_independent_verify.py`  
**Attestation:** `proofs/phase7/attestations/attest_9e147e81b6d0879c.json`  

---

## 1. Executive Summary

The published Phase 7 HDC-7 1,510-digit twin prime pair:
$$C = k \cdot 2^n, \quad A = C - 1, \quad B = C + 1$$
$$k = 470,224,755, \quad n = 4,985$$
$$A = 470224755 \cdot 2^{4985} - 1, \quad B = 470224755 \cdot 2^{4985} + 1$$
has been **strictly reproduced and verified locally from first principles**.

All mathematical theorem hypotheses were verified unconditionally:
1. $k = M_B \cdot (2t + 1)$ where $B_{\text{primorial}} = 13$, $M_B = 3 \times 5 \times 7 \times 11 \times 13 = 15,015$, and $t = 15,658$.
2. $k$ is positive and odd ($k = 470,224,755 \equiv 1 \pmod 2$).
3. $k < 2^n$ ($470,224,755 < 2^{4985}$, since $470224755 \approx 2^{28.8}$).
4. Exact integer digit count: 1,510 decimal digits per member.
5. Exact twin difference: $B - A = 2$, $C \equiv 0 \pmod 6$.
6. Proth Primality of Upper Member $B$:
   - Proth witness $w = 23$ satisfies $23^{(B-1)/2} \equiv -1 \pmod B$.
7. Riesel / Lucas-Lehmer-Riesel (LLR) Primality of Lower Member $A$:
   - Parameter $P = 15$ satisfies Jacobi conditions:
     $$\left(\frac{P-2}{A}\right) = \left(\frac{13}{A}\right) = 1, \quad \left(\frac{P+2}{A}\right) = \left(\frac{17}{A}\right) = -1$$
   - Initial value $u_0 = V_k(15, 1) \pmod A$ verified via 2x2 companion matrix powering.
   - Recurrence $u_{i+1} = (u_i^2 - 2) \pmod A$ computed for $n - 2 = 4,983$ rounds terminates at $u_{4983} \equiv 0 \pmod A$.
8. Canonical SHA-256 payload digest matches `9e147e81b6d0879cd87edcb7cc577ba1e220519154901ed240de4319bb2ccc1e`.

---

## 2. Verifier Hardening Completed

The verifier `scripts/phase7_independent_verify.py` was inspected and hardened to ensure fail-closed execution against malformed or adversarial inputs:

1. **Explicit Multiplier Oddness Check:** Added requirement that $k > 0$ and $k \equiv 1 \pmod 2$. If $k$ is even, the theorem preconditions fail.
2. **Primorial Relationship Verification:** Recomputed $M_B$ as the product of all odd primes $3 \le p \le B_{\text{primorial}}$ from first principles.
3. **Exact Equality of Representation and Decimal Strings:** Verified that $A$ matches `pair.lower_decimal`, $B$ matches `pair.upper_decimal`, and $C$ matches `pair.center_decimal`.
4. **Consistency Checks:** Checked `digits`, `difference == 2`, `llr_rounds == n - 2`, and `final_residue == 0`.
5. **Digest Documentation:** Added notice documenting that SHA-256 detects payload tampering relative to a declared digest, but is not a cryptographic signature.

---

## 3. Adversarial Mutation Test Suite

A comprehensive adversarial suite was created in `tests/phase7/test_adversarial_v7.py` (17 test cases). Each test mutates one field and recomputes the canonical SHA-256 hash so that a simple digest check cannot mask the defect. Every mutation is rejected by the verifier:
- Even $k$ ($470224756$): REJECTED
- Zero $k$ ($0$): REJECTED
- Mutated exponent $n$ ($4986$): REJECTED
- Mutated center $C$ ($C + 6$): REJECTED
- Mutated member integers ($A - 2$, $B + 2$): REJECTED
- Mutated digit count ($1509$): REJECTED
- Mutated difference ($4$): REJECTED
- Non-witness Proth base ($w = 2$): REJECTED
- Mutated LLR parameter ($P = 5$): REJECTED
- Mutated Jacobi condition ($=-1$): REJECTED
- Mutated initial $u_0$: REJECTED
- Mutated LLR round count ($4982$): REJECTED
- Non-zero final residue ($1$): REJECTED
- Mismatched primorial metadata ($M_B = 15016$): REJECTED
- Tampered SHA-256 checksum: REJECTED

Result: 17/17 tests passing.

---

## 4. Independent Second Check Path

An entirely decoupled arithmetic verification using `gmpy2` was executed separately from `scripts/phase7_independent_verify.py`. Both the Proth exponentiation and the 4,983 LLR recurrence steps independently matched to the final bit ($u_{4983} \equiv 0 \pmod A$).
