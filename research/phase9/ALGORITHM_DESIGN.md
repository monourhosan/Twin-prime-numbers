# Phase 9: Algorithm and Software Architecture Design
## Proof-Aware Unrestricted Twin-Prime Search (PAUTS) & Primorial-Anchored Cubic-Cofactor Engine

### 1. High-Level Architecture & End-to-End Pipeline

The Phase 9 computational engine is designed as a modular, hardware-balanced pipeline. The workload is strictly partitioned between the NVIDIA GeForce MX250 GPU (massive low-precision modular streaming) and the Intel Core i5-10210U CPU (arbitrary-precision multi-precision arithmetic, probable-prime screening, and certificate generation):

```
+-----------------------------------------------------------------------------------+
|                                  CPU SETUP STAGE                                  |
|  1. Construct Primorial Anchor S_y = product_{p <= y} p                          |
|  2. For sieve primes q in (y, Q]: solve cubic roots 6x^3 + 2x^2 +/- 1 = 0 mod q   |
|  3. Compute forbidden multiplier residues: t_root = x_root * S_y^(-1) mod q       |
|  4. Upload prime and residue offset tables to NVIDIA MX250 VRAM                   |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        GPU ACCELERATED MODULAR SIEVE (MX250)                      |
|  - Launch PTX JIT kernel (sm_61, 256 threads/block)                               |
|  - Grid striding over t in [t_start, t_end]                                       |
|  - Mark composite bits in d_alive bitset buffer                                   |
|  - DtoH copy of compact alive buffer and flatnonzero extraction                   |
+-----------------------------------------------------------------------------------+
                                          |
                                          v  [Sieve Survivors: ~20% - 30%]
+-----------------------------------------------------------------------------------+
|                        CPU MULTI-STAGE SCREENING (GMP / gmpy2)                    |
|  Stage 1: Multiplier primality check (Miller-Rabin 64-bit deterministic)          |
|  Stage 2: Fermat base-2 test on B(t) (eliminates composites in ~0.2 ms)           |
|  Stage 3: Fermat base-2 test on A(t)                                              |
|  Stage 4: Miller-Rabin 3-base test on B(t) and A(t) (BPSW / PRP certification)    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v  [Dual-PRP Candidates]
+-----------------------------------------------------------------------------------+
|                     CPU DETERMINISTIC PROOF & CERTIFICATION                       |
|  Upper Member B: Pocklington-BLS (Theorem 4)                                      |
|    - Verify witness conditions for all 62 prime factors of F = 2*S_y^2*t^2        |
|  Lower Member A: Morrison-BLS (Theorem 17)                                        |
|    - Find Jacobi non-residue (D/A) = -1                                           |
|    - Evaluate Lucas ladder U_(A+1) = 0 mod A and gcd(U_((A+1)/q_i), A) = 1        |
|  Canonical serialization, SHA-256 computation, and atomic ledger update          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          INDEPENDENT VERIFICATION GATE                            |
|  - Zero-import external verifier (scripts/phase9_independent_verify.py)          |
|  - Reconstruct integers, re-verify gap of 2, recheck all BLS hypotheses           |
|  - Generate cryptographically signed JSON attestation                             |
+-----------------------------------------------------------------------------------+
```

---

### 2. Detailed Subsystem Specifications

#### 2.1 Primorial Anchor Construction (`src/phase9/anchor.py`)
- Given anchor bound $y$, computes $S_y = \prod_{p \le y} p$ using exact integer arithmetic.
- Maintains an exact prime factorization table $\{ (p_i, e_i) \}$ where $e_i = 1$ for all primes $p_i \le y$.
- Reconstructs $F = 2 \cdot S_y^2 \cdot t^2$ where for each $p_i \le y$, the exponent in $F$ is:
  $$v_2(F) = 2 \cdot v_2(S_y) + 1 + 2 \cdot v_2(t) = 3 + 2 \cdot v_2(t)$$
  $$v_p(F) = 2 \cdot v_p(S_y) + 2 \cdot v_p(t) = 2 + 2 \cdot v_p(t) \quad (\forall p > 2)$$
- Validates that $t$ is prime using the 7-base deterministic Miller-Rabin test for integers $< 2^{64}$.

#### 2.2 Sieve Root Engine (`src/phase9/math.py`)
- For each sieve prime $q \in (y, Q]$:
  Solves $f_B(x) = 6x^3 + 2x^2 + 1 \equiv 0 \pmod q$ and $f_A(x) = 6x^3 + 2x^2 - 1 \equiv 0 \pmod q$.
- Uses the polynomial powering algorithm: computes $x^q \pmod{f(x)}$ in $\mathbb{F}_q[x] / (f(x))$ in $O(\log q)$ steps.
- Solves linear and quadratic factors via Tonelli-Shanks.
- Inverts $S_y \pmod q$ to compute the exact forbidden residues for $t$:
  $$t_{\text{forbidden}} \equiv x_{\text{root}} \cdot S_y^{-1} \pmod q$$
- Output: `SievePrimePlan` objects containing the prime $q$ and its list of forbidden residues.

#### 2.3 GPU Sieve Driver (`src/phase9/gpu_sieve.py`)
- Communicates directly with the Windows NVIDIA Driver API via `ctypes` (`nvcuda.dll`).
- JIT-compiles an embedded PTX kernel targeting `sm_61` (Pascal architecture of the MX250).
- Memory footprint:
  - Primes table: $N_{\text{primes}} \times 4$ bytes (e.g. $50,000 \times 4 = 200$ KB).
  - Offset tables: $N_{\text{primes}} \times 4$ bytes per root.
  - Alive buffer: $N_t$ bytes (e.g. $50,000 \times 1 = 50$ KB).
  - Total VRAM usage: $< 5$ MB (well within the MX250's 2,048 MB VRAM).
- Safety Guardrails:
  - Queries `nvidia-smi` temperature before and during batches.
  - Soft throttle at $80^\circ$C (insert 100 ms pauses).
  - Hard pause at $85^\circ$C (checkpoint and stop).
  - Automatic CPU fallback if GPU initialization fails.

#### 2.4 CPU Multi-Stage Screening (`src/phase9/screening.py`)
- Rapid triage using GMP (`gmpy2`):
  1. Base-2 Fermat Test: `pow(2, B - 1, B) == 1`. Eliminates $> 99.999\%$ of composite sieve survivors in $\sim 0.2$ ms.
  2. Base-2 Fermat Test on $A$: `pow(2, A - 1, A) == 1`.
  3. Miller-Rabin 3-base test (bases 2, 3, 5) to establish probable-prime (`DUAL_PRP`) status.

#### 2.5 Dual-BLS Deterministic Prover (`src/phase9/prover.py`)
- Executes the deterministic certification algorithms:
  - For $B$: Pocklington-BLS (Theorem 4) across all prime factors $q_i \mid F$.
  - For $A$: Morrison-BLS (Theorem 17) using Lucas sequence $U_k(P, 1) \pmod A$.
- Emits fully auditable, self-contained JSON certificates with canonical SHA-256 hashes.

#### 2.6 Campaign Orchestrator & Persistence (`src/phase9/campaign.py`)
- Manages segmented batches of multiplier space $t \in [t_{\text{start}}, t_{\text{end}}]$.
- Writes atomic JSON checkpoints and ledger entries to `data/phase9/`.
- Ensures zero skipped or duplicated intervals upon process resumption.
