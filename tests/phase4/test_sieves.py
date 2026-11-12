"""
Phase 4 Differential Sieve Correctness Tests.
Proves 100% survivor equivalence among:
- ReferenceSieveOracle (exact trial-division)
- SieveR0_S1Baseline (NumPy odd-k stride)
- SieveR1_TSpace (compact t-space block sieve)
- SieveR2_Adaptive (adaptive proof-cost-aware sieve)
"""

import pytest
from src.phase4.t_sieve import (
    ReferenceSieveOracle, SieveR0_S1Baseline, SieveR1_TSpace, SieveR2_Adaptive
)

def test_sieve_equivalence_against_reference_small():
    n = 10
    Q = 500
    k_start = 3
    k_end = 2003

    ref = ReferenceSieveOracle(n=n, sieve_depth=Q)
    r0 = SieveR0_S1Baseline(n=n, sieve_depth=Q)
    r1 = SieveR1_TSpace(n=n, sieve_depth=Q)

    surv_ref = ref.sieve_window(k_start, k_end)
    surv_r0 = r0.sieve_window(k_start, k_end)
    surv_r1 = r1.sieve_window(k_start, k_end)

    assert sorted(surv_r0) == sorted(surv_ref), "R0 must match Reference Oracle"
    assert sorted(surv_r1) == sorted(surv_ref), "R1 must match Reference Oracle"
    assert len(surv_r1) > 0

def test_sieve_r0_vs_r1_phase3_regime():
    n = 672
    Q = 10_000
    k_start = 3
    k_end = 30_003

    r0 = SieveR0_S1Baseline(n=n, sieve_depth=Q)
    r1 = SieveR1_TSpace(n=n, sieve_depth=Q)
    r2 = SieveR2_Adaptive(n=n, initial_depth=10_000, max_depth=10_000)

    surv_r0 = r0.sieve_window(k_start, k_end)
    surv_r1 = r1.sieve_window(k_start, k_end)
    surv_r2 = r2.sieve_window(k_start, k_end)

    assert sorted(surv_r0) == sorted(surv_r1), "R0 and R1 must produce identical survivor sets"
    assert sorted(surv_r1) == sorted(surv_r2), "R1 and R2 must produce identical survivor sets"

def test_sieve_window_partitioning_invariance():
    n = 672
    Q = 5_000
    r1 = SieveR1_TSpace(n=n, sieve_depth=Q)

    # Monolithic window [3, 24003)
    mono = r1.sieve_window(3, 24003)

    # Two contiguous split windows [3, 12003) and [12003, 24003)
    w1 = r1.sieve_window(3, 12003)
    w2 = r1.sieve_window(12003, 24003)
    combined = sorted(w1 + w2)

    assert mono == combined, "Sieve must be strictly invariant across window partitioning"

def test_misaligned_k_boundaries():
    n = 1024
    Q = 5_000
    r1 = SieveR1_TSpace(n=n, sieve_depth=Q)

    # Start on even k (e.g. 4)
    w_even = r1.sieve_window(4, 1000)
    # Start on odd k not divisible by 3 (e.g. 5)
    w_non3 = r1.sieve_window(5, 1000)
    # Start on valid k=6t+3 (e.g. 9)
    w_valid = r1.sieve_window(9, 1000)

    assert w_even == w_valid
    assert w_non3 == w_valid
