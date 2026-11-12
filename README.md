# Discovering and Verifying Extremely Large Twin Primes: The CATS Project

[![Tests: Passing](https://img.shields.io/badge/Tests-10%2F10%20Passing-brightgreen)]()
[![Verification: Certified](https://img.shields.io/badge/Certificates-35%20Proven%20SHA--256-blue)]()
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green)]()

An autonomous, mathematically rigorous computational number theory project investigating the largest known twin primes, analyzing the unresolved nature of an ultimate final pair, and implementing **CATS** (*Certificate-Aware Adaptive Twin-prime Sieve*)—an algorithmic framework for large twin-prime search and primality certification.

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  

---

## 1. Key Research Findings

1. **Largest Known Twin-Prime Pair:**
   * **Formula:** $2996863034895 \times 2^{1290000} \pm 1$
   * **Size:** **388,342 decimal digits** each.
   * **Discoverer:** Tom Greer (USA) via PrimeGrid (Sophie Germain Prime Search subproject).
   * **Discovery Date:** 14 September 2016 at 04:24:46 UTC.
   * **Verification Date:** 19 September 2016 (verified by Don Palmer using LLR).
   * **Authoritative Listings:** Ranked #1 on [The PrimePages Top 20 (code L2035)](https://t5k.org/top20/page.php?id=1) and Tony Forbes' [pzktupel.de History](https://pzktupel.de/KTHIST/kt002.php).

2. **Most Recently Verified Discovery:**
   * **Formula:** $152748736824915 \times 2^{480480} \pm 1$
   * **Size:** **144,654 decimal digits** each (Rank #3 all-time size).
   * **Verification Date:** **10 January 2026**.
   * **Discoverers:** Daniel Brockwell, Göran Schmidt, Carlos Eduardo Pinho, Michael Kwok, Richard Kapek, Stephan Vink (prover code A90; tools: TwinGen, NewPGen, TPS, PRST).
   * **Scope Note:** Sub-record twin primes are discovered daily by hobbyists worldwide without central tracking; Brockwell et al. represents the latest addition to the authoritative top-tier tables.

3. **Can the "Last" Twin Prime Ever Be Identified?**
   * **Mathematical Answer:** **No.** The question is equivalent to the unsolved **Twin Prime Conjecture** ($|\Pi_2| = \infty$). If the conjecture is true, no last pair exists. If false, an ultimate last pair exists, but an unbounded computation cannot locate it without an analytic finiteness proof and an effective upper bound.
   * **Finite Solvability:** In contrast, for any specified closed interval $[L, U] \subset \mathbb{N}$, the **largest twin-prime pair within $[L, U]$** is strictly decidable and certifiable.

4. **Strongest Actually Achieved Computational Results:**
   * **Bounded Exhaustive Mode:** Certified the maximal twin pair in $[2, 10,000,000]$ as **$(9,999,971, \ 9,999,973)$**, verifying exactly 58,980 twin pairs in 2.83 seconds.
   * **Structured Mode:** Discovered and certified a new 34-digit verified pair:
     $$4107 \times 2^{100} \pm 1$$
     * Lower member: $5205862110637458953584332604028295903027$
     * Upper member: $5205862110637458953584332604028295903029$
     * Deterministically certified via Proth's Theorem ($w=5$) and Lucas-Lehmer-Riesel ($P=4$).
   * Generated **35 tamper-evident cryptographic JSON certificates** in `proofs/`, all audited by SymPy and Python big-integer arithmetic.

---

## 2. Repository Layout

```text
Twin prime numbers/
├── README.md                           # Accessible project overview and findings
├── FINDINGS.md                         # Detailed record audit and research summary
├── REPRODUCIBILITY.md                  # Exact commands, dependencies, and environment specs
├── Cargo.toml                          # Rust engine crate definition
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
├── proofs/                             # 35 Cryptographically verified JSON certificates
└── paper/
    ├── twin_prime_search_paper.md       # Full publication-style research manuscript
    └── figures/                        # Generated vector-quality PNG figures
```

---

## 3. Quickstart and Reproduction

### 3.1 Install Dependencies
```bash
python -m pip install numpy sympy matplotlib pytest
```

### 3.2 Run Test Suite
```bash
python -m pytest tests/
```

### 3.3 Run Exhaustive Bounded Search in $[2, 1,000,000]$
```bash
python -m src.cats bounded --min 2 --max 1000000
```

### 3.4 Search Structured Twin Primes with Proth & LLR Proofs
```bash
python -m src.cats structured -n 100 --k-min 1 --k-max 10000 --adaptive --prove --cert-dir proofs/
```

### 3.5 Run Independent Certificate Auditor
```bash
python scripts/verify_certificate.py proofs/
```

### 3.6 Re-run Full Experiments & Plots
```bash
python scripts/run_experiments.py
python scripts/generate_plots.py
```

---

## 4. Key Documents

* **[FINDINGS.md](file:///d:/project/Twin%20prime%20numbers/FINDINGS.md):** Detailed breakdown of record holders, latest verified entries, and computational results.
* **[REPRODUCIBILITY.md](file:///d:/project/Twin%20prime%20numbers/REPRODUCIBILITY.md):** Exact commands, system requirements, and verification protocols.
* **[research/sources.md](file:///d:/project/Twin%20prime%20numbers/research/sources.md):** Citations, URLs, and access timestamps for all external registries.
* **[research/mathematical_notes.md](file:///d:/project/Twin%20prime%20numbers/research/mathematical_notes.md):** Mathematical derivations and formal proofs.
* **[paper/twin_prime_search_paper.md](file:///d:/project/Twin%20prime%20numbers/paper/twin_prime_search_paper.md):** Full scholarly manuscript.
