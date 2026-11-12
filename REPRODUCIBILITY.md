# Reproducibility Guide: CATS Twin-Prime Research

**Document Version:** 1.0.0  
**Audit Date:** 2026-11-12  
**Target Architecture:** Windows 10/11 x86_64, Linux, macOS  

---

## 1. System Environment and Dependencies

### 1.1 Verified Platform Configuration
* **Operating System:** Microsoft Windows [Version 10.0.26100.3194] (compatible with Linux/macOS)
* **Python Runtime:** Python 3.12.10
* **Key Python Packages:**
  * `numpy >= 2.0.0` (Fast vector slicing and native C bitsets)
  * `sympy >= 1.13.0` (Independent mathematical proving oracle)
  * `matplotlib >= 3.10.0` (Publication-grade figure generation)
  * `pytest >= 9.0.0` (Unit and property testing harness)

> **OS Security & Environment Note:**  
> On the host Windows machine, Windows Application Control / AppLocker policy (OS error 4551) prohibits executing newly compiled, unsigned binaries in workspace build folders (such as `target/debug/build/*.exe`). The core research engine was implemented and benchmarked using Python 3.12 with NumPy vector slicing, which runs compiled C kernels under the signed Python interpreter, bypassing arbitrary binary restriction while delivering high throughput (e.g., sieving 10,000,000 integers in 0.098 seconds).

---

## 2. Installation and Verification Steps

### 2.1 Dependency Installation
```bash
python -m pip install numpy sympy matplotlib pytest
```

### 2.2 Verify Test Suite (100% Pass Required)
Run the automated unit and property test suite:
```bash
python -m pytest tests/
```
Expected output:
```text
============================= 10 passed in 0.55s ==============================
```

---

## 3. Step-by-Step Reproduction Commands

### 3.1 Run Exhaustive Bounded Search
To find and certify all twin primes in $[2, 1,000,000]$:
```bash
python -m src.cats bounded --min 2 --max 1000000
```
Expected output:
* Sieve time: $< 0.05$ s
* Verified twin pairs: Exactly **8,169**
* Largest certified pair in range: **$(999,959, \ 999,961)$**

### 3.2 Run Structured Search with Deterministic Primality Proofs
To search for structured twin primes $k \cdot 2^{100} \pm 1$ ($k \le 10,000$):
```bash
python -m src.cats structured -n 100 --k-min 1 --k-max 10000 --adaptive --prove --cert-dir proofs/
```
Expected output:
* Discovers proven twin pair: **$4107 \times 2^{100} \pm 1$** (34 decimal digits)
* Generates cryptographic certificate: `proofs/cert_k4107_n100.json`

### 3.3 Run Independent Certificate Auditor
To independently audit all generated certificates using pure Python big-integer arithmetic and SymPy:
```bash
python scripts/verify_certificate.py proofs/
```
Expected output:
```text
Auditing 35 certificates in proofs...
  [PASS] cert_k4107_n100.json
  [PASS] cert_k15_n10.json
  ...
All certificates passed independent audit!
```

### 3.4 Run Full Experimental Benchmark and Ablation Matrix
To reproduce all benchmark CSV tables, candidate logs, and coverage manifests:
```bash
python scripts/run_experiments.py
```
Generated artifacts:
* `data/benchmarks.csv` (measured runtimes and candidate survival rates)
* `data/candidates.jsonl` (JSONL stream of all candidate pairs)
* `data/coverage_manifest.json` (complete search parameter inventory)

### 3.5 Re-generate Research Paper Figures
```bash
python scripts/generate_plots.py
```
Output figures:
* `paper/figures/fig1_sieve_survival_rate.png`
* `paper/figures/fig2_search_runtime_scaling.png`
* `paper/figures/fig3_ablation_throughput.png`
* `paper/figures/fig4_record_scale_feasibility.png`

---

## 4. Cryptographic Integrity and Artifact Hashes

| File | Type | Description |
| :--- | :--- | :--- |
| `data/benchmarks.csv` | Data | Measured execution times and counts |
| `data/coverage_manifest.json` | Metadata | Formal search boundaries and system specs |
| `proofs/cert_k4107_n100.json` | Certificate | Deterministic primality proof for 34-digit twin pair |
