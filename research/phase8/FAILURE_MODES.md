# PAQCS Failure Modes, Safeguards, and Risk Analysis (Phase 8)

**Date:** 15 November 2026  
**Author:** Antigravity (Google DeepMind)  
**Status:** Audit & Quality Assurance  

---

## 1. Threat and Failure Mode Taxonomy

### FM-1: Unproven Factors in the Anchor Factorization
- **Risk:** A composite factor is falsely treated as prime in $S_y$ or $t$, invalidating the Pocklington or Morrison theorem hypotheses.
- **Safeguard:**
  1. All primes in $S_{1780}$ ($p \le 1,777$) are proven prime via deterministic trial division.
  2. All factors of $t$ ($t \le 1,000,000$) are completely factored and checked with deterministic trial division.
  3. The standalone verifier re-verifies primality of every single factor independently before evaluating proof congruences.

### FM-2: Inadequate BLS Theorem Size Conditions
- **Risk:** Factored divisor $F$ does not meet the strict inequality $F^2 > B$ or $(F-1)^2 > A$.
- **Safeguard:**
  Because $C = x(x - 3)$, $F = x$, $B = x^2 - 3x + 1$, and $A = x^2 - 3x - 1$:
  $$F^2 - B = 3x - 1 > 0$$
  $$(F - 1)^2 - A = x + 2 > 0$$
  Both inequalities are algebraically guaranteed for all $x \ge 1$. The prover and verifier both check exact numeric inequalities explicitly.

### FM-3: Probable-Prime Confusion
- **Risk:** A candidate passing Fermat or Miller-Rabin tests is reported as proven before deterministic BLS verification.
- **Safeguard:**
  Probable-prime candidates are strictly recorded as `SINGLE_PRP` or `DUAL_PRP` in candidate ledgers. The proof engine only issues certificates with status `PROVEN_PRIME` after completing all 274 witness congruences and Lucas rank evaluations.

### FM-4: Checkpoint Corruption or Missed Search Range
- **Risk:** Process interruption causes duplicate candidate tests or skipped search intervals.
- **Safeguard:**
  Atomic JSON checkpointing writes `current_t` and candidate counters after each completed block. Resuming reads exact `current_t` with no overlap or gaps.

### FM-5: Thermal and System Stress
- **Risk:** High concurrency causes laptop thermal throttling or excessive system load.
- **Safeguard:**
  Worker count is bounded to 6 (leaving 2 logical cores free for OS and responsive operation). Memory is bounded under 200 MB by streaming block segments.

### FM-6: Certificate Tampering / Digest Collisions
- **Risk:** Certificate payload is modified after generation.
- **Safeguard:**
  Canonical JSON SHA-256 serialization sorts keys and strips formatting. Standalone verifier strictly recalculates canonical digest and fails closed on any payload modification.
