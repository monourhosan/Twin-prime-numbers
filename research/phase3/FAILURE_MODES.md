# Phase 3 Failure Modes, Guardrails, and Risk Mitigations

**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  
**Date:** 2026-11-12  

---

## 1. Algorithmic and Mathematical Failure Modes

### 1.1 Premature Coverage Marking on Early Exit
- **Risk:** In Phase 2, when a search halted upon finding `max_proven` pairs, the enclosing work unit was marked `COMPLETED` even though hundreds of candidate multipliers remained untested.
- **Phase 3 Guardrail:** Strict state partitioning. If a search halts before traversing all eligible candidates in $[K_0, K_1)$, the task status is recorded as `PARTIAL` and the exact next multiplier `next_unprocessed_k` is persisted. Resuming continues from that exact point without skipping or duplicating candidates.

### 1.2 False Mathematical Primality (PRP vs Proof)
- **Risk:** Fast Miller-Rabin tests (PRP) can yield pseudoprimes. Storing a PRP hit as "PROVEN" invalidates scientific claims.
- **Phase 3 Guardrail:** Explicit enum separation (`PRPStatus.PROBABLE_PRIME != ProofStatus.PROVEN`). Deterministic primality requires successful execution of Proth's theorem ($w^{(B-1)/2} \equiv -1 \pmod B$) and the complete LLR sequence ($u_{n-2} \equiv 0 \pmod A$).

### 1.3 Precondition Violations
- **Risk:** Proth's theorem and the LLR test fail if $k \ge 2^n$ or if Jacobi conditions $\left(\frac{P-2}{A}\right)=1, \left(\frac{P+2}{A}\right)=-1$ are not met.
- **Phase 3 Guardrail:** Precondition checkers validate $k < 2^n$, $k$ odd, $n \ge 2$, and re-evaluate Jacobi symbols before executing modular squarings.

### 1.4 Equal-Member-to-Sieve-Prime Sieve Exclusion
- **Risk:** In small intervals, if a prime member equals a sieving prime $q$, modular elimination might falsely discard a genuine prime.
- **Phase 3 Guardrail:** In Phase 3, $n \ge 672 \implies A > 10^{200}$. Since the maximum sieve prime $Q \le 100,000 \ll 10^{200}$, the condition $A > Q$ holds unconditionally for all search candidates.

---

## 2. Infrastructure and System Failure Modes

### 2.1 Database and Checkpoint Corruption
- **Risk:** Sudden power interruption, battery depletion, or forced process termination during disk writes.
- **Phase 3 Guardrail:** SQLite configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and `synchronous = NORMAL`. Disk updates execute as atomic transactions.

### 2.2 Process Saturation and Thermal Throttling
- **Risk:** Full logical core saturation causing excessive CPU temperatures or laptop battery drain.
- **Phase 3 Guardrail:** Configurable worker caps, support for graceful external `.pause` and `.stop` files, and cooperative yielding.
