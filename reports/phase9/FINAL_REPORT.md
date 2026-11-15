# Phase 9 Final Research and Discovery Report
## Discovery and Deterministic Dual-BLS Certification of a 364-Digit Twin-Prime Pair on the Primorial-Anchored Cubic-Cofactor Manifold (PACCM-9) Using the NVIDIA GeForce MX250

### 1. Executive Summary

Phase 9 achieved its primary research and discovery objective: the formulation of a new algebraic manifold, hardware-accelerated modular sieving on the laptop's dedicated **NVIDIA GeForce MX250** GPU, the discovery of a new twin-prime pair, and its unconditional deterministic certification via exact Dual-BLS theorems.

- **Primary Discovery:** A new-to-repository twin-prime pair ($B - A = 2$) with **364 decimal digits** per member.
- **Algebraic Manifold:** The Primorial-Anchored Cubic-Cofactor Manifold (PACCM-9):
  $$C(x) = 2 x^2 (3x + 1) = 6 x^3 + 2 x^2, \qquad A = C - 1, \qquad B = C + 1$$
  with symbolic coordinate $x = S_{283} \cdot 1129$, where $S_{283} = \prod_{p \le 283} p$.
- **Primality Proof Status:** Both members are **UNCONDITIONALLY PROVEN PRIMES**:
  - Upper Member $B$: Certified via Brillhart-Lehmer-Selfridge (1975) Theorem 4 ($N-1$ test) with factored divisor $F = 2 x^2 > \sqrt{B}$.
  - Lower Member $A$: Certified via Brillhart-Lehmer-Selfridge (1975) Theorem 17 ($N+1$ rank test / Morrison-BLS) with factored divisor $F_{\text{odd}} > \sqrt{A}$.
- **Independent Verification:** The discovery passed zero-import verification via `scripts/phase9_independent_verify.py` with attestation `proofs/phase9/attestations/attest_62d13fd6011ec338.json` (Status: `UNCONDITIONALLY_VERIFIED`).
- **Repository Novelty:** `NEW_TO_REPOSITORY` (0 matches across all 59 pre-existing historical pairs).
- **Public Novelty:** `NO_PUBLIC_MATCH_FOUND_IN_CHECKED_SOURCES` across The PrimePages, Tony Forbes' Prime $k$-tuple registry, and PrimeGrid.

---

### 2. Discovered Twin-Prime Pair Coordinates

#### 2.1 Symbolic Parameters
- **Anchor Prime:** $y = 283$
- **Primorial Anchor:** $S_{283} = \prod_{p \le 283} p$ (61 distinct prime factors, 118 decimal digits)
- **Prime Multiplier:** $t = 1129$
- **Manifold Coordinate:** $x = S_{283} \cdot 1129$ (121 decimal digits)
- **Even Center:** $C = 2 x^2 (3x + 1) = 6 x^3 + 2 x^2$ (364 decimal digits)

#### 2.2 Exact Decimal Values

**Lower Prime $A$ (364 Decimal Digits):**
```text
2930437718326521655617229560876590360206621115265912833279294373345056688224598465677967327585117702549519640464821316802011744771886981133779808711841478324562834287315183620367081430177713551066320799563590811908043543470972516405279894332551392518671452227921014981090124614038365394037463814243427109891738532955747377885874729355473796731879588148469018495799
```

**Upper Prime $B$ (364 Decimal Digits):**
```text
2930437718326521655617229560876590360206621115265912833279294373345056688224598465677967327585117702549519640464821316802011744771886981133779808711841478324562834287315183620367081430177713551066320799563590811908043543470972516405279894332551392518671452227921014981090124614038365394037463814243427109891738532955747377885874729355473796731879588148469018495801
```

- **Difference Check:** $B - A = 2$ exactly.
- **Center Modulo 6:** $C \equiv 0 \pmod 6$.

---

### 3. Primality Certification & Theorem Details

#### 3.1 Upper Member $B$: Pocklington-BLS (1975) Theorem 4
- **Theorem Statement:** If $N = F \cdot R + 1$ with $F > \sqrt{N}$ and $\gcd(F, R) = 1$, and for each prime $q \mid F$ there exists an integer $a_i$ such that $a_i^{N-1} \equiv 1 \pmod N$ and $\gcd(a_i^{(N-1)/q} - 1, N) = 1$, then $N$ is unconditionally prime.
- **Application:**
  - Factored Divisor: $F = 2 x^2 = 2 \cdot S_{283}^2 \cdot 1129^2$ (243 decimal digits).
  - Size Margin: $F^2 > B$ holds by 61 orders of magnitude ($F / \sqrt{B} \approx 10^{61}$).
  - Coprimality: $\gcd(2x^2, 3x + 1) = 1$ identically.
  - Witnesses: Successfully discovered and independently verified for all 62 prime factors $q \in \{2, 3, 5, \dots, 283, 1129\}$.

#### 3.2 Lower Member $A$: Morrison-BLS (1975) Theorem 17
- **Theorem Statement:** If $N = F \cdot R - 1$ with $F_{\text{odd}} > \sqrt{N+1}$ and $\gcd(F_{\text{odd}}, R) = 1$, and $(D/N) = -1$, and $U_{N+1}(P, 1) \equiv 0 \pmod N$ while $\gcd(U_{(N+1)/q}(P, 1), N) = 1$ for all odd primes $q \mid F$, then $N$ is unconditionally prime.
- **Application:**
  - Factored Divisor: $F_{\text{odd}} = S_{283}^2 \cdot 1129^2 / 4$ (242 decimal digits).
  - Size Margin: $(F_{\text{odd}} - 1)^2 > A$ holds by 59 orders of magnitude.
  - Parameters: $P = 295, Q = 1, D = 87021$, Jacobi symbol $(87021 / A) = -1$.
  - Lucas Sequence: $U_{A+1}(295, 1) \equiv 0 \pmod A$ verified.
  - Factor Gcds: $\gcd(U_{(A+1)/q}(295, 1), A) = 1$ verified for all 61 odd prime factors.

---

### 4. Verification and Attestation Integrity

- **Proof Certificate Path:** `proofs/phase9/certificates/cert_paccm9_364d_t1129.json`
- **Canonical Proof Payload SHA-256:**
  `62d13fd6011ec338f9324a0c9532bc90be297eb505a0f5ef0eebef349625b190`
- **Independent Attestation Path:** `proofs/phase9/attestations/attest_62d13fd6011ec338.json`
- **Verification Command:**
  ```powershell
  python scripts/phase9_independent_verify.py proofs/phase9/certificates/cert_paccm9_364d_t1129.json
  ```
  **Output:** `[PASS] cert_paccm9_364d_t1129.json unconditionally verified!`

---

### 5. Hardware Performance & Telemetry (NVIDIA GeForce MX250)

| Metric | Measured Value | Safe Laptop Limit | Safety Margin |
| :--- | :--- | :--- | :--- |
| **GPU Peak Temperature** | 64.0°C | 80.0°C (throttle) / 85.0°C (pause) | +16.0°C margin |
| **GPU Sieve Throughput** | 10.5 million cands/sec | N/A | 5.47x speedup vs CPU |
| **GPU VRAM Utilization** | 3.8 MiB | 2,048 MiB | 99.8% free |
| **Host System RAM Free** | ~1.2 GB (stable) | > 500 MB | Safe |
| **Proof Generation Time** | 5.95 seconds | 600.0 seconds | Instantaneous |
