# Phase 3 Prior Art and Literature Review

**Author / Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  

---

## 1. Classical Sieve Theory and Vectorized Implementations

Segmented prime sieves were pioneered by Bays & Hudson (1977) and Sorenson (1990) to overcome $O(N)$ memory limitations by processing arithmetic intervals $[x, x+\Delta]$ in small, cache-friendly blocks.
- **TwinGen & NewPGen:** Developed by Yves Gallot and Paul Jobling, these tools pioneered dual-residue arithmetic progression filtering for $k \cdot 2^n \pm 1$ using modular inverses.
- **Phase 3 Contribution (HDRSS):** Adapts segmented strided sieving to modern vectorized SIMD buffers in Python/NumPy, proving that pure slice striding (`alive[i0::q] = False`) delivers an $8.1\times$ to $17.6\times$ speedup over scalar modular checking.

---

## 2. Deterministic Primality for $k \cdot 2^n \pm 1$

1. **Proth's Theorem (1878):**
   - Proth, F. (1878). "Théorèmes sur les nombres premiers." *Comptes Rendus de l'Académie des Sciences Paris*, 87, 926.
   - For $B = k \cdot 2^n + 1$ with $k < 2^n$, $w^{(B-1)/2} \equiv -1 \pmod B$ guarantees primality.
2. **Lucas-Lehmer-Riesel (LLR) Criterion:**
   - Riesel, H. (1969). "Lucasian Numbers." *BIT Numerical Mathematics*, 9(3), 257–264.
   - Brillhart, J., Lehmer, D. H., & Selfridge, J. L. (1975). "New Primality Criteria and Factorizations of $2^m \pm 1$." *Mathematics of Computation*, 29(130), 620–647.
3. **Lucas Sequences via Matrix Powering:**
   - Williams, H. C. (1972). "The Primality of Certain Integers of the Form $2Ar^n - 1$." *Acta Arithmetica*, 20, 169–176.
   - Crandall, R., & Pomerance, C. (2005). *Prime Numbers: A Computational Perspective*. Springer.
   - Implementing Lucas sequence calculation via $2 \times 2$ companion matrices ensures complete algorithmic decoupling from the Montgomery ladder.

---

## 3. World Records vs Repository Context

- **Current World Record:** $2,996,863,034,895 \times 2^{1,290,000} \pm 1$ ($388,342$ decimal digits), discovered by Tom Greer / PrimeGrid on September 14, 2016.
- **Project Discoveries:**
  - Phase 1 Baseline: 34 digits ($k=4107, n=100$)
  - Phase 2: 104d, 121d, 159d
  - Phase 3: **207d ($n=672$)**, **314d ($n=1024$)**, **507d ($n=1664$)**
  All Phase 3 discoveries are strictly classified as **new-to-project** verified pairs.
