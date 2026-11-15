# PAQCS Prior Art and Method Positioning (Phase 8)

**Date:** 15 November 2026  
**Author:** Antigravity (Google DeepMind)  
**Status:** Architecture Comparison & Historical Context  

---

## 1. Evolution of Repository Proof Families

Across Phases 1 through 8, the repository has explored multiple distinct algebraic families for twin prime generation:

```
[Phase 1--4: Pure Exponent Proth/Riesel]
      C = k * 2^n +/- 1 (HDC-7, ADRS-4, CATS)
      -> Requires k < 2^n, highly efficient Proth/LLR tests.
      -> Phase 7 achieved 1,510d pair at n=4985.
           |
           v
[Phase 5: Smooth-Center Search (SCCA)]
      C = F * t, A = C - 1, B = C + 1
      -> F is smooth prime product. Requires F^3 > 2C^2 for BLS Thm 5.
      -> At 1,510d, F must have > 1,007 digits, making small t impossible.
           |
           v
[Phase 6: General-Integer Interval Sieve (GITCSS)]
      C = 6m, unrestricted
      -> High candidate throughput (>1.5e7 centers/s), but N +/- 1 are generic composites.
      -> Requires GNFS / ECPP. Blocked at 100d+ on Windows due to App Control.
           |
           v
[Phase 6: Quadratic-Cofactor Proving (QCP-6)]
      C = x(x - 3), A = x^2 - 3x - 1, B = x^2 - 3x + 1
      -> x divides both A + 1 and B - 1!
      -> F = x satisfies F^2 > B and (F - 1)^2 > A simultaneously!
      -> Certified 108d, 110d, 502d, 503d pairs unconditionally.
           |
           v
[Phase 8: Primorial-Anchored QCP (PAQCS)]
      x = S_y * t, C = x(x - 3)
      -> Scale QCP-6 to the 1,511+ digit frontier.
      -> Primorial anchor S_{1780} provides 751 fully factored digits.
      -> Deterministic Pocklington & Morrison BLS proofs without ECPP.
```

---

## 2. Comparative Matrix: PAQCS vs Previous Methods

| Metric / Dimension | Phase 5 (SCCA) | Phase 6 (GITCSS) | Phase 7 (HDC-7) | Phase 8 (PAQCS) |
| :--- | :--- | :--- | :--- | :--- |
| **Algebraic Family** | Multi-factor smooth $C = F \cdot t$ | Unrestricted $C = 6m$ | Primorial Proth $k \cdot 2^n \pm 1$ | Primorial Quadratic $x(x - 3) \pm 1$ |
| **Proof System** | BLS Thm 5 ($F^3 > 2C^2$) | ECPP / APR-CL / GNFS | Proth Thm / Riesel LLR | Pocklington Thm 4 + Morrison Thm 17 |
| **Proof Precondition** | $F > C^{2/3}$ (hard at 1,510d) | ECPP tool chain required | $k < 2^n$, $k$ odd | $x^2 > B$ (trivially satisfied for $x > 0$) |
| **Local Density Boost** | ~10--20x | 1.0x (baseline) | ~30--50x | **44.7x** |
| **Windows Tool Dependency** | Native Python / gmpy2 | Blocked (needs `ecpp.exe`) | Native Python / gmpy2 | **Native Python / gmpy2** |
| **Independent Verifier** | First-principles | First-principles (small only) | First-principles matrix | **First-principles standalone** |
| **Highest Proven Digits** | 133 digits | 16 digits (58 PRP @ 100d unproven) | 1,510 digits | **1,511 digits** |

---

## 3. Why PAQCS Succeeds Where Others Stalled

1. **Overcomes SCCA Size Bottleneck:** SCCA requires the factored part $F$ to exceed $C^{2/3}$. For a 1,510-digit number, $F$ must exceed 1,007 digits, leaving very little space for $t$. In PAQCS, the quadratic structure ensures that $F = x$ only needs to exceed $\sqrt{B} \approx x$, which is satisfied for all positive $x$ because $B = x^2 - 3x + 1 < x^2$.
2. **Overcomes GITCSS Proving Block:** GITCSS was blocked at 100d because the cofactor is generic and cannot be factored. PAQCS completely pre-factors $x = S_y \cdot t$, so the cofactor is $100\%$ known by construction.
3. **Independent of Proth/LLR:** Unlike Phase 7, PAQCS does not rely on binary powers $2^n$ or Proth/LLR algebra. It is an independent discovery in the quadratic-cofactor family.
