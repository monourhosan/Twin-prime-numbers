# Phase 6 Algorithm Design: General-Integer Twin-Center Segmented Sieve (GITCSS)

**Document ID:** `PHASE6-ALGO-DESIGN-001`  
**Date:** 2026-11-14T05:02:00+06:00  
**Phase:** Phase 6

---

## 1. System Architecture Overview

The GITCSS engine consists of seven loosely coupled, highly testable subsystems:

```
[Interval Request: p_min, p_max]
              │
              ▼
   [Exact Interval Mapping]  ---> [m_min, m_max]
              │
              ▼
    [Segment Tile Sieve]  <--- [Wheel Filter W=5005]
              │           <--- [Small Primes Sieve Cache]
              │           <--- [Bucket Sieve for q > S]
              ▼
      [Surviving m values]
              │
              ▼
   [Multi-Stage Screening]
     1. Small Prime Divisibility
     2. Fermat PRP Base-2 (gmpy2)
     3. 25-Round Miller-Rabin
     4. Lucas / BPSW Test
              │
              ▼ (Dual PRP Hit)
   [Deterministic Prover]
     - Complete Prime Factorization of m
     - Pocklington BLS Thm 4 Proof on B = 6m + 1
     - Morrison BLS Thm 17 Proof on A = 6m - 1
     - First-Principles Factor Primality Validation
              │
              ▼
   [Independent Verifier]  ---> [JSON Certificate + Attestation]
              │
              ▼
  [Historical Duplicate Audit] ---> [NEW_TO_REPOSITORY Verification]
              │
              ▼
  [Coverage Manifest & Ledger] ---> [phase6_coverage_manifest.json]
```

---

## 2. Segmented Sieve and Bitset Representation

### Memory Layout:
- A segment represents an interval of centers $m \in [m_{\text{base}}, m_{\text{base}} + S)$.
- Typical segment size $S$: $262,144$ ($2^{18}$) or $1,048,576$ ($2^{20}$) elements, fitting comfortably in L2/L3 CPU cache.
- In Python, we implement two representations for benchmarking:
  1. `bytearray(S)` initialized with 1s, where index $i$ corresponds to $m = m_{\text{base}} + i$. Fast direct slice assignment `arr[j::q] = b'\x00' * count`.
  2. Compact bitset using Python's native arbitrary-precision integers or `int.from_bytes` / bitmasks.

### Wheel Initialization:
Instead of setting all bytes to 1 and sieving wheel primes $\{5, 7, 11, 13\}$, each segment is initialized using the precomputed wheel pattern of period $W = 5005$:
$$\text{offset} = m_{\text{base}} \bmod W$$
The wheel pattern is tiled across the segment in blocks of $W$ bytes using `itertools` or memory slicing.

---

## 3. Bucket Sieving for Large Sieve Primes ($q > S$)

When sieving up to bound $L \gg S$, many primes satisfy $q > S$.
For primes $q > S$, each prime hits at most one position in the segment, or misses the segment entirely:
- **Standard Segmented Sieve:** For each prime $q$, recomputes the entry offset $j = (r - m_{\text{base}}) \bmod q$. For $q > S$, this wastes CPU cycles computing modular reductions for primes that do not hit the segment.
- **Bucket Sieve Architecture:**
  - Maintains a priority queue or array of buckets for each future segment $k = \lfloor m / S \rfloor$.
  - Each prime stores its next hit position $(m_{\text{hit}}, q)$.
  - When segment $k$ begins, it only processes the primes stored in bucket $k$, then computes their next hit position $m_{\text{next}} = m_{\text{hit}} + q$ and inserts them into bucket $\lfloor m_{\text{next}} / S \rfloor$.
  - **Empirical Threshold:** Both standard striding and bucketed scheduling are implemented and benchmarked in Stage B to determine the empirical crossover point.

---

## 4. Multi-Stage Screening Pipeline

Surviving center indices $m$ produce candidate pairs:
$$A = 6m - 1, \qquad B = 6m + 1$$

To avoid triggering expensive multiprecision factorization and Lucas sequence proofs on composite candidates, candidates pass through a tiered screening filter:

1. **Small-Prime Divisibility Check:**
   Verify $A$ and $B$ are not divisible by primes $\le 257$ (catches any missed sieve factors).
2. **Fermat Base-2 Screening:**
   Evaluate `gmpy2.powmod(2, A - 1, A) == 1` and `gmpy2.powmod(2, B - 1, B) == 1`.
   Rejects $> 99.999\%$ of composite sieve survivors in sub-microsecond latency.
3. **25-Round Miller-Rabin Test:**
   Evaluate Miller-Rabin with deterministic base sequence:
   $$[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]$$
   Probability of a composite surviving 25 rounds is $< 4^{-25} \approx 8.88 \times 10^{-16}$.
4. **Baillie-PSW / Lucas Probable Prime Test:**
   Evaluate standard Lucas probable-prime condition. No counterexample to Baillie-PSW is known.

---

## 5. Deterministic Dual Primality Prover

When both $A$ and $B$ pass all screening tiers, the candidate is a **Dual PRP Hit**. The deterministic prover executes:

1. **Center Factorization:**
   Factors $m = \prod_{i=1}^k q_i^{e_i}$ using trial division up to $10^5$, followed by Pollard's rho and ECM.
   - If complete prime factorization of $m$ is obtained: proceed to step 2.
   - If $m$ cannot be completely factored within the configured compute budget: record candidate as `UNPROVEN_DUE_TO_FACTORIZATION_LIMIT` and advance.
2. **Pocklington Proof on $B = 6m + 1$:**
   - Factor set $\mathcal{F} = \{2, 3\} \cup \{q_1, \dots, q_k\}$.
   - For each factor $q \in \mathcal{F}$, search witness $a \in \{2, 3, \dots, 100\}$ satisfying:
     $$a^{B-1} \equiv 1 \pmod B \quad \text{and} \quad \gcd(a^{(B-1)/q} - 1, B) = 1$$
3. **Morrison Proof on $A = 6m - 1$:**
   - Search parameter $P \in \{3, 4, 5, \dots\}$ such that Jacobi symbol $\left(\frac{P^2 - 4}{A}\right) = -1$.
   - Evaluate Lucas sequence condition $U_{A+1}(P, 1) \equiv 0 \pmod A$ using $2 \times 2$ companion matrix binary exponentiation.
   - For each factor $q \in \mathcal{F}$, verify $\gcd(U_{(A+1)/q}(P, 1), A) = 1$.
4. **Recursive Factor Primality:**
   - For each prime factor $q \in \mathcal{F}$, verify deterministic primality via trial division from first principles.

---

## 6. Zero-Dependency Independent Verifier

The verifier (`src/phase6/independent_verify.py` and standalone script) has:
- **Zero internal imports** from search modules or classes.
- Pure Python standard library exact integer arithmetic.
- Independent recomputation of $A = 6m - 1$ and $B = 6m + 1$.
- Verification that $B - A = 2$.
- Verification of Pocklington witness conditions and Morrison Lucas identities.
- First-principles trial-division primality proof for all reported factors.
- Emits standardized Attestation JSON with SHA-256 integrity digest.

---

## 7. Coverage Management and Resumability

- Coverage database tracks completed segments in `data/phase6_coverage_manifest.json` and SQLite.
- Segment tracking records: `segment_index`, `m_start`, `m_end`, `survivors_count`, `prp_count`, `proven_count`, `elapsed_seconds`, `timestamp`.
- Resumption loads the highest completed $m_{\text{end}}$ and resumes search at $m = \max(m_{\text{end}})$ with zero gaps and zero duplicate evaluations.
