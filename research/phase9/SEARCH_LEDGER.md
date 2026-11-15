# Phase 9: Search Ledger & Execution Audit Trail
## Proof-Aware Unrestricted Twin-Prime Search (PAUTS) & Primorial-Anchored Cubic-Cofactor Engine

### 1. Master Campaign Summary Ledger

| Run ID | Algebraic Manifold | Anchor ($y$) | $t$-Interval | Sieve Depth ($Q$) | Candidates Sieved | Survivors | Dual-PRPs | Proven Pairs | Discovery Status | Wall Time | Peak GPU Temp |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `phase9_benchmark` | PACCM-9 | $y=283$ | $[1, 50001]$ | 50,000 | 45,003 | 12,920 | N/A (bench) | N/A | **BENCHMARK_COMPLETE** | 18.2s | 64.0°C |
| `phase9_smoke_search` | PACCM-9 | $y=5$ | $[1, 51]$ | 500 | 26 | 2 | 2 | 2 | **TEST_COMPLETE** | 0.8s | 61.0°C |
| `phase9_primary_355d` | PACCM-9 | $y=283$ | $[1, 10001]$ | 50,000 | 5,001 | 1,421 | 1 | 1 | **DISCOVERY_CERTIFIED** | 14.8s | 64.0°C |

---

### 2. Detailed Campaign Audit: `phase9_primary_355d`

- **Execution Timestamp:** 2026-11-15 07:59:24 UTC (discovery) / 07:59:43 UTC (attestation) [recorded locally as 13:59:27 UTC+6]
- **Configuration Path:** `configs/phase9/primary_search.json`
- **Algebraic Manifold:** PACCM-9 ($C = 2x^2(3x + 1), A = C - 1, B = C + 1$)
- **Primorial Anchor Bound:** $y = 283$
  - Anchor $S_{283} = \prod_{p \le 283} p$ (61 distinct prime factors)
  - Decimal digits of $S_{283}$: 118 digits
- **Sieve Configuration:**
  - Lower prime bound: $q > 283$
  - Upper prime bound: $Q = 50,000$
  - Number of prime moduli: 4,522 primes
  - Hardware: NVIDIA GeForce MX250 (`sm_61`, PTX JIT Driver API)
  - Grid configuration: 256 threads/block, 18 blocks
- **Search Progression:**
  - $t$-interval searched: $[1, 10001]$ (odd integers)
  - Total candidates evaluated: 5,001
  - Sieve survivors: 1,421 (28.4% survival rate)
  - Prime multiplier candidates: 337
  - Single-PRP candidates: 2
  - Dual-PRP candidates: 1 ($t = 1129$)
- **Deterministic Primality Certification:**
  - Candidate Coordinate: $x = S_{283} \cdot 1129$
  - Exact Decimal Digits: 364 digits per member
  - Upper Member $B$: Pocklington-BLS (1975) Theorem 4 ($N-1$ test) with $F = 2 x^2$
    - Size condition: $F^2 > B$ (Margin: 61 orders of magnitude)
    - All 62 distinct prime factors in $F$ witnessed unconditionally
  - Lower Member $A$: Morrison-BLS (1975) Theorem 17 ($N+1$ test) with $F_{\text{odd}}$
    - Size condition: $(F_{\text{odd}} - 1)^2 > A$ (Margin: 59 orders of magnitude)
    - Parameter $P = 295, D = 87021$, Jacobi symbol $(87021 / A) = -1$
    - Lucas sequence zero congruence: $U_{A+1}(295, 1) \equiv 0 \pmod A$
    - Lucas sequence rank gcd condition: $\gcd(U_{(A+1)/q_i}(295, 1), A) = 1$ for all 61 odd prime factors
  - Certification Wall Time: 5.95 seconds
  - Certificate Path: `proofs/phase9/certificates/cert_paccm9_364d_t1129.json`
  - Canonical Proof Payload SHA-256: `62d13fd6011ec338f9324a0c9532bc90be297eb505a0f5ef0eebef349625b190`
- **Independent Verification Gate:**
  - Script: `scripts/phase9_independent_verify.py` (decoupled, zero project imports)
  - Status: `[PASS] UNCONDITIONALLY_VERIFIED`
  - Attestation Path: `proofs/phase9/attestations/attest_62d13fd6011ec338.json`
- **Novelty Audit:**
  - Historical Repository Inventory: Checked against all 59 existing pairs in `research/phase9/historical_inventory.json` $\to$ `NEW_TO_REPOSITORY` (0 matches).
  - External Record Sources (The PrimePages, Tony Forbes $k$-tuple registry, PrimeGrid): `NO_PUBLIC_MATCH_FOUND_IN_CHECKED_SOURCES`.

---

### 3. Checkpoint & Resumption State
The primary discovery campaign checkpoint is frozen at:
- Checkpoint Path: `data/phase9/phase9_primary_355d_checkpoint.json`
- Next Multiplier on Resume: $t = 10003$
- Resumption Command:
  ```powershell
  python -m src.phase9.cli search --campaign-id phase9_primary_355d --anchor-y 283 --t-start 10003 --t-end 50000 --sieve-depth 50000
  ```
