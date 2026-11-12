# Phase 4 Paper Claim Ledger & Evidence Mapping

This ledger binds every scientific assertion, benchmark table, decimal representation, and primality claim in Phase 4 publications directly to an auditable data file, generation script, and SHA-256 hash.

---

## 1. Mathematical Ground Truth Claims

| Claim ID | Paper Section | Mathematical Claim | Source Data / Script | Artifact SHA-256 | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-001** | Section 1, 9 | $15993 \cdot 2^{672} \pm 1$ are twin primes (207 digits each) | `proofs/phase3/cert_k15993_n672.json` | `4d8d6f2a2ac9ed96fb11a5bbe32c49dd7a89aeb2e96e4a26af8dab9922f974a0` | Proth ($w=7$), LLR ($P=3$, $u_{670}=0$), matrix Lucas | VERIFIED |
| **CLM-002** | Section 1, 9 | $254697 \cdot 2^{1024} \pm 1$ are twin primes (314 digits each) | `proofs/phase3/cert_k254697_n1024.json` | `80e4f72de9db900f926fe753849e802f1af9fc1cb41165a248a80457cd65d74d` | Proth ($w=5$), LLR ($P=9$, $u_{1022}=0$), matrix Lucas | VERIFIED |
| **CLM-003** | Section 1, 9 | $1183377 \cdot 2^{1664} \pm 1$ are twin primes (507 digits each) | `proofs/phase3/cert_k1183377_n1664.json` | `a01afe7c4aafbf3c073b4fc168b2fe9aaadb7dd62c2728cc53adebf89b174e29` | Proth ($w=5$), LLR ($P=5$, $u_{1662}=0$), matrix Lucas | VERIFIED |
| **CLM-004** | Section 2 | Admissible multiplier family is $k = 6t + 3$ for primes $>3$ | `src/phase4/math_family.py` | Standalone proof in Section 2.1 | Divisibility by 3 of $k \cdot 2^n$ when $A, B$ are prime | THEOREM |
| **CLM-005** | Section 2 | Exponent $n=3328, k=3$ yields 1,003 decimal digits | `src/phase4/math_family.py` | Exact len(str(3*(1<<3328)-1)) == 1003 | Exact Python arbitrary-precision integer check | VERIFIED |

---

## 2. Benchmark & Throughput Claims

| Claim ID | Paper Section | Claim Description | Raw Data Source | Generating Script | Uncertainty / Metrics | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BM-001** | Section 8 | Sieve throughput comparison (S0 vs R0 vs R1 vs R2) | `runs/phase4/benchmarks/sieve_benchmarks.json` | `scripts/phase4_benchmark_compare.py` | 5 measured trials per condition, median + IQR | PENDING BENCHMARK |
| **BM-002** | Section 8 | GMP vs pure-Python modular arithmetic speedup | `runs/phase4/benchmarks/backend_benchmarks.json` | `scripts/phase4_benchmark_compare.py` | Exact integer congruence, elapsed wall ms | PENDING BENCHMARK |
| **BM-003** | Section 8 | Multi-process worker scaling ($W=1, 2, 4$) | `runs/phase4/benchmarks/worker_scaling.json` | `scripts/phase4_benchmark_compare.py` | CPU utilization, physical PIDs, candidates/sec | PENDING BENCHMARK |

---

## 3. Phase 4 Target Discovery Claims

| Claim ID | Target Size | Exponent $n$ | Multiplier $k$ | Decimal Digits | Proof Status | Independent Attestation | World Novelty |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **DISC-1000** | $\ge 1,000$ digits | 3392 | 1836723 | 1028 | PROVEN (Proth $w=13$, LLR $P=3$) | VERIFIED (`proofs/phase4/attestations/attest_46a7116dc819e120.json`) | UNVERIFIED |
| **DISC-1500** | $\ge 1,500$ digits | 5120 | Queued | ~1542 | CONFIG VALIDATED / QUEUED | PENDING | UNVERIFIED |
| **DISC-2000** | $\ge 2,000$ digits | 6656 | Queued | ~2005 | CONFIG VALIDATED / QUEUED | PENDING | UNVERIFIED |
