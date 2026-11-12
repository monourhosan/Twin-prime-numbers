# Discovering and Verifying Extremely Large Twin Primes: The CATS, Phase 2, Phase 3 HDRSS, & Phase 4 ADRS Project

[![Tests: 54/54 Passing](https://img.shields.io/badge/Tests-54%2F54%20Passing-brightgreen)](tests/)
[![Phase 4 Discovery: 1,028d](https://img.shields.io/badge/Phase%204%20Discovery-1%2C028%20Digits-brightgreen)](proofs/phase4/)
[![Certificates: 42 Proven](https://img.shields.io/badge/Certificates-42%20Proven%20SHA--256-blue)](proofs/)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Paper: Phase 4 Manuscript](https://img.shields.io/badge/Paper-Phase%204%20Manuscript-orange)](paper/phase4/manuscript.md)

An autonomous, mathematically rigorous computational number theory project investigating the largest known twin primes, analyzing the unresolved nature of an ultimate final pair, and implementing:
1. **CATS** (*Certificate-Aware Adaptive Twin-prime Sieve*);
2. **Phase 2 CRT-Wheeled Streaming Discovery Engine**;
3. **Phase 3 HDRSS** (*Hybrid Dual-Residue Streaming Sieve*);
4. **Phase 4 ADRS-4** (*Adaptive Dual-Residue Search, Phase 4*) with compact $t$-space block sieving ($k=6t+3$), GMP acceleration, durable SQLite WAL leases with automatic crash recovery, and decoupled $2 \times 2$ matrix-powering attestation.

* **Primary Auditor:** **Monour Hosan Saif**
* **Contributors:** **Gemini and ChatGPT**
* **Research Group:** Antigravity Autonomous Number Theory Research Group
* **Affiliation:** Computational Number Theory & Verification Lab

---

## 1. Key Research Findings

### 1.1 The Largest Known Twin-Prime Pair (World Record)
* **Exact Mathematical Form:**
  $$2996863034895 \times 2^{1290000} \pm 1$$
* **Decimal Digits:** Exactly **388,342 digits** in each prime member.
* **Discoverer:** Tom Greer (USA) via PrimeGrid (Sophie Germain Prime Search subproject on BOINC).
* **Discovery Date:** 14 September 2016 at 04:24:46 UTC.
* **Verification Date:** 19 September 2016 (verified by Don Palmer using Jean Penné's LLR).
* **Authoritative Listings:** Ranked #1 on [The PrimePages Top 20 (prover code L2035)](https://t5k.org/top20/page.php?id=1) and Tony Forbes' [pzktupel.de Prime k-tuple History](https://pzktupel.de/KTHIST/kt002.php).

### 1.2 Most Recently Verified Discovery (Latest Top-Tier Entry)
* **Form:**
  $$152748736824915 \times 2^{480480} \pm 1$$
* **Decimal Digits:** **144,654 digits** each (ranked #3 all-time size).
* **Verification Date:** **10 January 2026**.
* **Discoverers:** Daniel Brockwell, Göran Schmidt, Carlos Eduardo Pinho, Michael Kwok, Richard Kapek, Stephan Vink (prover code `A90`; software: TwinGen, NewPGen, TPS, PRST).
* **Scope Note:** Sub-record twin primes are discovered daily by computational hobbyists worldwide without central registration; Brockwell et al. is the newest entry on the verified top-tier tables.

### 1.3 Can the "Last" Twin Prime Ever Be Identified?
* **Mathematical Answer:** **No.** The question is logically equivalent to the negation of the **Twin Prime Conjecture** ($|\Pi_2| = \infty$). Number theory has neither proved that twin primes terminate nor proved that they continue indefinitely. While bounded-gap breakthroughs (Zhang 2013; Maynard 2013; Polymath8b 2014) established prime gaps $\le 246$, the gap of 2 remains open due to the parity barrier in sieve theory.
* **Finite Counterpart:** For any specified closed interval $[L, U] \subset \mathbb{N}$, the **largest twin-prime pair within $[L, U]$** is strictly decidable and provable.

---

## 2. Strongest Results Achieved in This Project

### 2.0 Phase 4 Breakthrough Discovery (1,000+ Digits Milestone)
Deploying the Phase 4 ADRS-4 engine with compact $t$-space sieving and GMP-accelerated multiprecision arithmetic, we discovered and certified a **1,028-decimal-digit twin-prime pair**:
$$1836723 \times 2^{3392} \pm 1$$
* **Decimal Digits:** **1,028 digits** each member ($2,056$ total digits in pair).
* **Lower Member ($A$):** $1836723 \times 2^{3392} - 1$
* **Upper Member ($B$):** $1836723 \times 2^{3392} + 1$
* **Deterministically Proven:**
  - $B$: Proth witness $w = 13$ ($13^{(B-1)/2} \equiv -1 \pmod B$).
  - $A$: Lucas-Lehmer-Riesel parameter $P = 3$, Jacobi symbols $((3-2)/A) = 1, ((3+2)/A) = -1$, initial $u_0 = V_{1836723}(3, 1) \pmod A$, final residue $u_{3390} \equiv 0 \pmod A$.
* **Cryptographic Artifacts:**
  - Proof Payload: [`proofs/phase4/cert_k1836723_n3392.json`](proofs/phase4/cert_k1836723_n3392.json)
  - Independent Attestation: [`proofs/phase4/attestations/attest_46a7116dc819e120.json`](proofs/phase4/attestations/attest_46a7116dc819e120.json) (Status: **PASS**, verified via decoupled $2 \times 2$ matrix powering).
* **Coverage Verification:** 100% gap-free coverage certified over 2,400,000 $k$-span at $n=3328$ and 1,837,122 $k$-span at $n=3392$.

### 2.1 Phase 3 Discoveries (207, 314, and 507 Digits)
Deploying the Phase 3 HDRSS engine, we discovered and certified three new-to-project twin-prime pairs scaling to multi-hundred digits:
1. **Pilot Discovery (207 digits):**
   $$15993 \times 2^{672} \pm 1$$
   * Deterministically proven: Proth witness $w = 7$, LLR parameter $P = 3$.
   * Certificate: [`proofs/phase3/cert_k15993_n672.json`](proofs/phase3/cert_k15993_n672.json). Independently verified via $2 \times 2$ matrix powering: **PASS**.
2. **Primary Campaign Milestone (314 digits):**
   $$254697 \times 2^{1024} \pm 1$$
   * Deterministically proven: Proth witness $w = 5$, LLR parameter $P = 9$.
   * Certificate: [`proofs/phase3/cert_k254697_n1024.json`](proofs/phase3/cert_k254697_n1024.json). Independently verified: **PASS**.
3. **Stretch Campaign Milestone (507 digits):**
   $$1183377 \times 2^{1664} \pm 1$$
   * Deterministically proven: Proth witness $w = 5$, LLR parameter $P = 5$.
   * Certificate: [`proofs/phase3/cert_k1183377_n1664.json`](proofs/phase3/cert_k1183377_n1664.json). Independently verified: **PASS**.

### 2.2 Phase 2 Discoveries (100+ to 159 Digits)
1. **104-Digit Pair:** $12477 \times 2^{330} \pm 1$ ($w=17, P=3$, [`proofs/phase2/cert_k12477_n330.json`](proofs/phase2/cert_k12477_n330.json)).
2. **121-Digit Pair:** $126747 \times 2^{384} \pm 1$ ($w=5, P=5$, [`proofs/phase2/cert_k126747_n384.json`](proofs/phase2/cert_k126747_n384.json)).
3. **159-Digit Pair:** $61347 \times 2^{512} \pm 1$ ($w=5, P=5$, [`proofs/phase2/cert_k61347_n512.json`](proofs/phase2/cert_k61347_n512.json)).

### 2.3 Phase 1 Baseline Results (CATS)
1. **Bounded Range Exhaustive Certification:**
   * Certified all 58,980 twin primes in $[2, 10,000,000]$ in **2.8387 seconds**.
   * Provably maximal pair in $[2, 10^7]$: **$(9,999,971, \ 9,999,973)$**.
2. **Historical 34-Digit Baseline Pair:**
   * Certified pair: $4107 \times 2^{100} \pm 1$ (34 digits, [`proofs/cert_k4107_n100.json`](proofs/cert_k4107_n100.json)).
3. **Total Cryptographic Proof Inventory:**
   * **42 tamper-evident JSON certificates** across `proofs/`, `proofs/phase2/`, `proofs/phase3/`, and `proofs/phase4/`, all passing strict independent verification.

   * Deterministically proven: Proth witness $w=5$, LLR parameter $P=5$. Certificate: [`proofs/phase2/cert_k61347_n512.json`](proofs/phase2/cert_k61347_n512.json).

### 2.2 Phase 1 Baseline Results (CATS)
1. **Bounded Range Exhaustive Certification:**
   * Certified all twin primes in $[2, 10,000,000]$ in **2.8387 seconds**.
   * Exact count: **58,980 twin pairs** (matching theoretical counts).
   * Maximal certified pair in $[2, 10^7]$: **$(9,999,971, \ 9,999,973)$**.
2. **Historical 34-Digit Baseline Pair:**
   * Certified pair: $4107 \times 2^{100} \pm 1$ (34 digits).
   * Lower member: `5206241015137338151946960064479231`
   * Upper member: `5206241015137338151946960064479233`
   * Certificate: [`proofs/cert_k4107_n100.json`](proofs/cert_k4107_n100.json).
3. **Total Cryptographic Proof Inventory:**
   * **38 tamper-evident JSON certificates** across `proofs/` and `proofs/phase2/`, all independently verified with 100% success.


---

## 3. Algorithmic Architecture: CATS

The **CATS** (*Certificate-Aware Adaptive Twin-prime Sieve*) framework introduces:
1. **Dual-Residue Bitset Sieve (DR-Sieve):** For candidate form $k \cdot 2^n \pm 1$ and odd prime $q$, precomputes modular inverses $a = 2^n \pmod q$ and eliminates both forbidden arithmetic progressions $k \equiv \pm a^{-1} \pmod q$ in a single strided vector pass.
2. **Adaptive Sieve-Depth (ASD) Calibration:** Dynamically balances marginal modular sieve cost against multiprecision primality proof effort to determine the optimal sieve cutoff $Q^*(n)$.
3. **Certificate-Cost-Aware Pipeline (CCAP):** Performs early-exit filtering on $B = k \cdot 2^n + 1$ before initiating the $N+1$ LLR verification on $A = k \cdot 2^n - 1$.

```text
+-------------------------------------------------------------+
|                     CATS Search Pipeline                    |
+-------------------------------------------------------------+
                               |
                               v
            [ Precompute Modular Inverses a^(-1) mod q ]
                               |
                               v
            [ Dual-Residue Elimination: k = +/- a^(-1) mod q ]
                               |
                               v
                [ Sieve Survivors Bitset (k) ]
                               |
                               v
        +-----------------------------------------------+
        |  Asymmetric Verification Pipeline (CCAP)       |
        |  1. Fast Miller-Rabin PRP base-2 on (center+1) |
        |     --> Exit immediately if composite (99.9%) |
        |  2. Proth Deterministic Theorem on (center+1)  |
        |     --> If proven prime:                      |
        |  3. Lucas-Lehmer-Riesel (LLR) on (center-1)   |
        |     --> If proven prime:                      |
        +-----------------------------------------------+
                               |
                               v
         [ Cryptographic JSON Certificate (SHA-256) ]
```

---

## 4. Visual Evidence and Research Plots

| Figure 1: Sieve Survival Rate | Figure 2: Verification Scaling |
| :---: | :---: |
| ![Figure 1](paper/figures/fig1_sieve_survival_rate.png) | ![Figure 2](paper/figures/fig2_search_runtime_scaling.png) |
| **Figure 3: Empirical Ablation** | **Figure 4: Record-Scale Cost Projection** |
| ![Figure 3](paper/figures/fig3_ablation_throughput.png) | ![Figure 4](paper/figures/fig4_record_scale_feasibility.png) |

---

## 5. Repository Structure

```text
Twin-prime-numbers/
├── README.md                           # Project overview, findings, and reproduction
├── FINDINGS.md                         # Detailed record audit and research summary
├── REPRODUCIBILITY.md                  # Exact commands, dependencies, and environment specs
├── Cargo.toml                          # Rust engine crate definition
├── .gitignore                          # Git ignore rules
├── research/
│   ├── sources.md                      # Primary source audit and timestamped references
│   ├── mathematical_notes.md           # Theorems, lemmas, and proofs of sieve elimination
│   └── prior_art_and_novelty.md        # Literature review and algorithmic classification
├── src/
│   ├── cats/                           # Python/NumPy implementation of CATS
│   │   ├── bitset.py                   # Fast bitset manipulation
│   │   ├── primality.py                # Deterministic MR, Proth, and LLR provers
│   │   ├── sieve.py                    # Dual-residue bounded and structured sieves
│   │   ├── adaptive.py                 # Adaptive Sieve Depth (ASD) cost model
│   │   ├── certificate.py              # Cryptographic certificate generator & verifier
│   │   └── cli.py                      # Multi-command CLI
│   └── (Rust modules: bitset.rs, primality.rs, sieve.rs, certificate.rs, adaptive.rs)
├── tests/
│   └── test_cats.py                    # Pytest unit, property, and regression tests
├── configs/
│   └── default_experiments.json        # Reusable experiment configurations
├── scripts/
│   ├── reference_oracle.py             # Independent SymPy ground-truth oracle
│   ├── verify_certificate.py           # Independent certificate auditor script
│   ├── run_experiments.py              # Master experiment orchestrator
│   └── generate_plots.py               # Generates high-resolution publication figures
├── data/
│   ├── benchmarks.csv                  # Measured execution times across all runs
│   ├── candidates.jsonl                # Stream of discovered candidate pairs
│   └── coverage_manifest.json          # Formally logged search boundaries and coverage
├── proofs/                             # 35 Cryptographically verified JSON certificates (Phase 1)
│   ├── phase2/                         # 3 Breakthrough certificates: 104d, 121d, 159d
│   └── phase3/                         # 3 Breakthrough certificates: 207d, 314d, 507d
├── research/
│   ├── phase3/                         # Phase 3 HDRSS audit, mathematics, benchmarks & ledger
│   │   ├── AUDIT_FINDINGS.md
│   │   ├── MATHEMATICAL_SPECIFICATION.md
│   │   ├── BENCHMARKS.md
│   │   ├── SEARCH_LEDGER.md
│   │   ├── DISCOVERY_STATUS.md
│   │   ├── FAILURE_MODES.md
│   │   └── PRIOR_ART.md
│   ├── phase2/                         # Phase 2 audit, mathematics, benchmarks & status
│   └── (Phase 1 notes: sources.md, mathematical_notes.md, prior_art_and_novelty.md)
├── src/
│   ├── cats/                           # Phase 1 CATS engine
│   ├── phase2/                         # Phase 2 CRT-wheeled window engine & provers
│   └── phase3/                         # Phase 3 HDRSS engine & independent matrix verifier
├── paper/
│   ├── phase3/
│   │   ├── phase3_twin_prime_research_paper.md # Phase 3 Research Manuscript
│   │   └── figures/                    # Phase 3 publication charts
│   ├── phase2_new_twin_prime_discovery.md      # Phase 2 Research Manuscript
│   └── twin_prime_search_paper.md              # Phase 1 publication manuscript
├── REPRODUCIBILITY_PHASE3.md           # Phase 3 audit and reproduction manual
└── REPRODUCIBILITY_PHASE2.md           # Phase 2 audit and reproduction manual
```

---

## 6. Quickstart and Reproduction

### 6.1 Install Dependencies
```bash
python -m pip install numpy sympy matplotlib pytest
```

### 6.2 Run Full Test Suite (29/29 Passing, 100%)
```bash
python -m pytest -v tests/
```

### 6.3 Phase 3 Independent Certificate Verification (Zero-Shared-Code Matrix Powering)
Strictly verify the 207-, 314-, and 507-digit breakthrough twin prime certificates without circular trust:
```bash
python scripts/phase3_independent_verify.py proofs/phase3/
```

### 6.4 Phase 3 HDRSS CLI Operations
```bash
# Run baseline audit and check historical proof consistency
python -m src.phase3 audit --repo .

# Run real-world benchmark suite across S0, S1, and S2
python scripts/phase3_benchmark.py

# Launch / Resume primary campaign for >= 300-digit pairs (n=1024)
python -m src.phase3 search --config configs/phase3/target_300.json --resume

# Launch / Resume stretch campaign for >= 500-digit pairs (n=1664)
python -m src.phase3 search --config configs/phase3/stretch_500.json --resume

# Inspect live status and heartbeat
python -m src.phase3 status --campaign target_300

# Gracefully pause a running campaign
python -m src.phase3 pause --campaign target_300
```

### 6.5 Legacy Phase 2 & Phase 1 Verification
```bash
# Verify Phase 2 certificates (104d, 121d, 159d)
python scripts/phase2_verify.py proofs/phase2/

# Verify Phase 1 certificates
python scripts/verify_certificate.py proofs/
```

---

## 7. Key Documents & Links

### Phase 3 Breakthrough Deliverables (200+ to 500+ Digits)
* **Phase 3 Research Manuscript:** [paper/phase3/phase3_twin_prime_research_paper.md](paper/phase3/phase3_twin_prime_research_paper.md)
* **Phase 3 Reproducibility Manual:** [REPRODUCIBILITY_PHASE3.md](REPRODUCIBILITY_PHASE3.md)
* **Phase 3 Discovery Status & Ledger:** [research/phase3/DISCOVERY_STATUS.md](research/phase3/DISCOVERY_STATUS.md)
* **Search Ledger & Coverage Record:** [research/phase3/SEARCH_LEDGER.md](research/phase3/SEARCH_LEDGER.md)
* **Mathematical Specification & Theorem Proofs:** [research/phase3/MATHEMATICAL_SPECIFICATION.md](research/phase3/MATHEMATICAL_SPECIFICATION.md)
* **Empirical Benchmarks (S0 vs S1 vs S2):** [research/phase3/BENCHMARKS.md](research/phase3/BENCHMARKS.md)
* **Audit Findings & Defect Resolutions:** [research/phase3/AUDIT_FINDINGS.md](research/phase3/AUDIT_FINDINGS.md)
* **Failure Modes & Mitigations:** [research/phase3/FAILURE_MODES.md](research/phase3/FAILURE_MODES.md)
* **Prior Art & Citations:** [research/phase3/PRIOR_ART.md](research/phase3/PRIOR_ART.md)
* **Phase 3 Proof Certificates (207d, 314d, 507d):** [proofs/phase3/](proofs/phase3/)

### Historical Project Deliverables
* **Phase 2 Research Manuscript:** [paper/phase2_new_twin_prime_discovery.md](paper/phase2_new_twin_prime_discovery.md)
* **Phase 1 Research Manuscript:** [paper/twin_prime_search_paper.md](paper/twin_prime_search_paper.md)
* **Research Findings:** [FINDINGS.md](FINDINGS.md)
* **Proof Certificates Directory:** [proofs/](proofs/)
* **Proof Certificates Directory:** [proofs/](proofs/)
