# Phase 6 Prior-Art Review and Algorithmic Differentiation

**Document ID:** `PHASE6-PRIOR-ART-001`  
**Date:** 2026-11-14T05:00:00+06:00  
**Phase:** Phase 6 (General-Integer Twin-Center Segmented Sieve - GITCSS)

---

## 1. Executive Summary & Problem Formulation

Previous phases in this repository (Phases 1 through 5) have explored twin-prime candidates belonging strictly to special, highly structured exponential or smooth-number families:
- **Phases 1–4 (CATS, CRT, HDRSS, ADRS-4):** Candidates restricted to the generalized Proth/Riesel form $k \cdot 2^n \pm 1$ for small multiplier $k$ and large exponent $n$.
- **Phase 5 (SCCA):** Candidates centered at smooth integers $C = F \cdot t$, where $F = 2^{e_2} 3^{e_3} 5^{e_5} 7^{e_7}$ with predetermined massive prime-power exponents.

While these algebraic structures enable rapid Lucas-Lehmer-Riesel (LLR) or classical Morrison/Pocklington primality testing because $N \pm 1$ is pre-factored by construction, they cover only an infinitesimal, measure-zero subset of all integers.

**Phase 6 breaks completely free from structured exponential families.** It addresses the universal space of **all consecutive integer pairs $(p, p+2)$** in arbitrary finite intervals $[p_{\min}, p_{\max}]$, operating through the universal representation:
$$p = 6m - 1, \quad p + 2 = 6m + 1 \quad (m \in \mathbb{Z}^+)$$
which represents 100% of twin-prime pairs beyond $(3, 5)$.

---

## 2. Prior-Art Survey

| Technique / System | Canonical Reference / Tool | Problem Solved | Prior Art Status | Existing in Repo? | Phase 6 Architectural Synthesis | Novelty Boundary (What is NOT novel) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wheel Factorization** | Pritchard (1981), *Comm. ACM*; Brent (1980) | Eliminates small prime multiples without modular divisions | Classical (1970s–1980s) | No general wheel in Python (Phase 2 used CRT wheel for $k \cdot 2^n \pm 1$) | Configurable wheel $\{5, 7, 11, 13\}$ precomputing admissible residues for center index $m \pmod W$. | Wheel factorization is a classical mathematical method; the concept is not novel. |
| **Segmented Sieve of Eratosthenes** | Bays & Hudson (1977); Sorenson (1998) | Limits working memory to CPU cache sizes ($L1/L2$) for arbitrary range sieving | Classical (1970s) | Bounded bitset in Rust (Phase 1); Segmented sieve for $t$ in Phase 5 | Memory-efficient bitset segmented sieve over universal center index $m$. | Segmented sieving is established prior art; not a novel algorithm. |
| **Twin-Prime Residue Sieving** | Hardy & Littlewood (1923), *Acta Math.*; NewPGen / TwinGen | Filters composite pairs using modular inverses modulo sieve primes | Established (1920s; software 1990s) | Used for $k \cdot 2^n$ in Phase 4 and $F \cdot t$ in Phase 5 | Derives and implements exact residue exclusions $m \equiv \pm 6^{-1} \pmod q$ for general integers. | Residue exclusion $m \equiv \pm 6^{-1} \pmod q$ is elementary number theory; not a novel theorem. |
| **Cache-Aware Bucket Sieving** | Sorenson (1998); Achterbahn / NFS sieve implementations | Avoids scanning large intervals for primes $q > \text{segment\_size}$ | Established in factor base sieves (1990s) | No bucket sieving existed in repo | Bucketed scheduling for large primes $q > S$, tested against flat segmentation. | Bucket sieving is standard in large sieves; not novel. |
| **Pocklington Primality Criterion** | Pocklington (1914); BLS (1975) Theorem 4 | Deterministic primality proof when $N - 1$ is partially factored ($F > \sqrt{N}$) | Classical (1914, 1975) | Used in Phase 1 and Phase 5 | Proves upper member $B = 6m + 1$ using complete prime factorization of $6m$. | BLS Theorem 4 is a classical theorem; not novel. |
| **Morrison Lucas Sequence Primality Criterion** | Morrison (1975); BLS (1975) Theorem 17 | Deterministic primality proof when $N + 1$ is partially factored ($F > \sqrt{N}$) | Classical (1975) | Used in Phase 5 for smooth centers | Proves lower member $A = 6m - 1$ using complete prime factorization of $6m$. | BLS Theorem 17 is a classical theorem; not novel. |
| **Dual Center Primality Coupling** | Selfridge et al. (1975); this work | Proves both members of a twin pair $(6m-1, 6m+1)$ using the single center factorization $6m$ | Known in twin prime literature | Used in Phase 5 for $C = F \cdot t$ | Applied to general integer centers $m$ where $m$ is factored without smooth restriction. | Mathematical coupling is known; implementation synthesis is new to repo. |

---

## 3. What Phase 6 Reuses vs. What Phase 6 Changes

### What is Reused:
1. Classical BLS Theorem 4 (Pocklington) and BLS Theorem 17 (Morrison) mathematical formulations.
2. Canonical Schema 6.0 JSON serialization with exact SHA-256 integrity verification.
3. Decoupled, zero-dependency independent attestation verifier architecture established in Phase 5.
4. Authoritative historical inventory verification against `research/phase5_audit/historical_inventory.json`.

### What is Changed & Genuinely Different:
1. **Search Domain:** Unrestricted general integer space $\mathbb{Z}^+$. No fixed powers of 2, 3, 5, or 7.
2. **Sieve Mathematics:** Two-residue arithmetic progression sieve operating on the universal center index $m$:
   $$m \not\equiv 6^{-1} \pmod q \quad \text{and} \quad m \not\equiv -6^{-1} \pmod q \quad (\forall q \ge 5)$$
3. **Multi-Stage Filtering Pipeline:**
   - Pre-sieve wheel filtering ($W = 5005$, eliminating 70.33% of candidates before prime sieving).
   - Segmented bitset sieve up to configurable limit $L$.
   - Multi-tier probable-prime screening (Fermat base-2 $\to$ 25-round Miller-Rabin $\to$ Lucas/BPSW).
   - Exact center prime factorization and dual deterministic certification.

---

## 4. Rigorous Novelty Boundaries

In accordance with Non-Negotiable Rules 5, 6, and 7:
1. **No New Theorems:** Phase 6 does not invent or claim any new mathematical theorem. All primality criteria rely strictly on published, peer-reviewed theorems of Brillhart, Lehmer, and Selfridge (1975).
2. **No Global Novelty Claims Without External Verification:** Any discovered twin-prime pair is labeled strictly as **`NEW_TO_REPOSITORY`** until audited against global external databases (such as Chris Caldwell's Prime Pages / PrimeGrid Top 5000 Twin Primes).
3. **No Unbounded or Conjectural Claims:** Finite search intervals cannot and will not be claimed to prove the Twin Prime Conjecture or the infinitude of twin primes.
