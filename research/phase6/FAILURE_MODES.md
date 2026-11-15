# Phase 6 Failure Modes, Boundary Edge Cases, and Mitigations

**Document ID:** `PHASE6-FAILURE-MODES-001`  
**Date:** 2026-11-14T05:03:00+06:00  
**Phase:** Phase 6

---

## 1. Summary of Identified Risk Modes

| Risk ID | Failure Mode | Root Cause | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **FM-01** | Exceptional pair $(3, 5)$ missed | $p = 3 \implies p+1=4 \not\equiv 0 \pmod 6$. | Search misses the only twin prime with $p \le 3$. | Explicit small-prime exception handler in `test_residue_classes.py` and interval mapper. GITCSS documentation clearly notes that general form $6m \pm 1$ applies for $p > 3$. |
| **FM-02** | Small-prime equality false composite marking | Sieve prime $q$ equals candidate $A = 6m - 1$ (e.g., $q = 5, m = 1 \implies A = 5$). | Sieve marks $A$ as divisible by $q$, erroneously discarding a prime. | Small-prime equality guard: for small intervals where $q = 6m \pm 1$, prime equality is preserved and tested in unit test suite. Large-number campaigns begin well above $L$. |
| **FM-03** | Segment boundary off-by-one error | Incorrect offset calculation $j = (r - m_{\text{base}}) \bmod q$ or interval conversion $\lceil (p_{\min}+1)/6 \rceil$. | Candidate missed at boundary, or overlapping evaluations. | Exact integer arithmetic formulas unit-tested against brute force across arbitrary segment boundaries. |
| **FM-04** | Floating-point precision loss | Using `math.ceil((p_min+1)/6)` on large integers $> 2^{53}$. | Truncation of large integer coordinates. | Non-negotiable rule 9: Strictly prohibit floating-point arithmetic. Use integer division `(p_min + 1 + 5) // 6`. |
| **FM-05** | Wheel alignment stride miscalculation | Segment base $m_{\text{base}}$ not aligned to wheel period $W = 5005$. | Corrupted residue masking across segment start. | Offset formula `offset = m_base % W` dynamically slides wheel tile pattern for any arbitrary starting index. |
| **FM-06** | Miller-Rabin pseudoprime leakage | Pseudoprime passes probabilistic primality check. | Non-prime candidate claimed as prime. | Screening never claims primality. Both members require full deterministic BLS proofs with independent verification. |
| **FM-07** | Morrison discriminant degeneracy | $D = P^2 - 4$ is a quadratic residue modulo $A$, or $A \mid D$. | Lucas sequence test theorem hypothesis violated. | Prover explicitly verifies $(D/A) = -1$ using Jacobi symbol calculation before computing Lucas sequence. |
| **FM-08** | Unfactored center factor primality assertion | Believing a composite factor $q \mid m$ is prime without proof. | Invalid Pocklington or Morrison certificate. | Every reported prime factor $q \mid m$ must pass trial-division primality proof by the independent verifier. |
| **FM-09** | Windows file lock contention on SQLite | Connection not closed or WAL checkpoint pending during test teardown. | `PermissionError [WinError 32]` during cleanup or resumption. | Explicit connection closing context managers and explicit `close()` method on storage handlers. |
| **FM-10** | Crash during segment processing | Process terminated mid-segment. | Incomplete segment recorded as completed, creating silent gap. | Atomic database transactions: segments marked `COMPLETED` only after all survivors are screened and flushed. |
| **FM-11** | 350-digit generic center factorization barrier | Factoring general 350-digit centers requires factors $> 10^{175}$. | BLS Theorems 4 and 17 cannot certify generic 350-digit integers without ECPP. | Honest classification: candidates passing multi-stage screening are recorded as Dual PRPs, explicitly distinguished from proven primes. |
| **FM-12** | OS Application Control binary blocking | Windows WDAC/AppLocker blocks unwhitelisted native binaries (e.g., Rust `target/debug` or Primo). | External proof binaries cannot execute on the host. | Utilize pure Python + gmpy2 (backed by pre-compiled GNU MP 6.3.0 DLLs) and document the exact dependency boundary. |
