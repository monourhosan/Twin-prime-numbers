# Prior Art, Algorithmic Context, and Novelty Assessment

**Document Version:** 4.0  
**Date:** 2026-11-12  

---

## 1. Mathematical Prior Art

ADRS-4 is an integrated computational engine based on established theorems of classical and modern computational number theory:
1. **Proth's Theorem (1878):**
   - Proth, François. *"Théorèmes sur les nombres premiers."* Comptes Rendus de l'Académie des Sciences Paris, 87 (1878): 926-928.
   - Provides unconditional primality proving for numbers of the form $k \cdot 2^n + 1$ with $k < 2^n$ via a single modular exponentiation.
2. **Lucas-Lehmer-Riesel (LLR) Primality Test:**
   - Riesel, Hans. *"Lucasian numbers."* BIT Numerical Mathematics, 9(1) (1969): 66-81.
   - Extends the Lucas-Lehmer test to numbers $A = k \cdot 2^n - 1$.
3. **Rödseth Parameterization (1994):**
   - Rödseth, Öystein J. *"A note on primality tests for $N = h \cdot 2^n - 1$."* BIT Numerical Mathematics, 34(3) (1994): 451-454.
   - Established deterministic criteria for choosing $P$ using Jacobi symbols $((P-2)/A) = 1$ and $((P+2)/A) = -1$, eliminating trial parameter searches.
4. **Alternative LLR Formulations:**
   - Atnashev, Pavel. *"A simpler alternative to Lucas–Lehmer–Riesel primality test."* Cryptology ePrint Archive, Report 2023/195 (2023).

---

## 2. Specialized Computational Engines

| System | Primary Language | Multiplication Algorithm | Primality Tests | Concurrency / Platform |
| :--- | :--- | :--- | :--- | :--- |
| **NewPGen** | C / Assembly | Sieve generation | Sieve pre-screening | Command-line utility |
| **LLR (Jean Pené)** | C / Assembly | GWNUM (IBDWT FFT) | Proth, LLR | Multi-core x86 |
| **PRST (Pavel Atnashev)** | C++ / Assembly | GWNUM / PRST core | Proth, LLR, PRP | Multi-core x86 |
| **PrimeGrid (BOINC)** | Distributed C/C++ | Distributed work units | Multi-project records | Distributed grid network |
| **ADRS-4 (This Work)** | Python / NumPy / GMP | GMP / NumPy C-stride | Proth, LLR, Decoupled Matrix Verifier | Fault-tolerant laptop/workstation with cryptographic attestation |

---

## 3. Algorithmic and Engineering Distinctions in ADRS-4

ADRS-4 does not claim to have discovered a new mathematical theorem. Its core engineering and scientific contributions are:
1. **Direct $t$-Space Sieving (Strategy R1):** Mapping candidate multipliers $k = 6t + 3$ into $t$-space eliminates wheel conversion overhead and cuts working array memory requirements by $67\%$ compared to standard odd-integer arrays.
2. **Crash Resilience & Atomic Leases:** SQLite WAL-backed fencing tokens and automatic zombie claim recovery guarantee zero orphaned intervals across unexpected reboots, sleeps, and interruptions.
3. **Cryptographically Decoupled Independent Attestation:** A strict, zero-import verification standard where certificates must be proven independently using $2 \times 2$ matrix binary exponentiation before a discovery is certified.
4. **Reproducibility & Provenance Tracking:** Complete synchronization between raw CSV/JSON benchmark outputs, SQLite manifests, and published paper tables.
