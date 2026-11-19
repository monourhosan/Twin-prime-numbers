"""Tier 2 Boundary Tests - Feature 10: Symmetric Quintic Modular Sieve.

Verifies:
1. Misaligned slice offsets (t_start not congruent to 0 mod 32).
2. Edge sieve depths (very low depth vs deep depth).
3. Zero-survivor interval handling.
4. All-survivor synthetic interval handling.
5. Bit-exact consistency under CPU fallback.
"""

import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


@pytest.mark.phase11_tier2
def test_bnd10_misaligned_slice_offsets() -> None:
    """Verifies sieve correctness when t_start is not aligned to word or warp boundaries (e.g. 32 or 64)."""
    y = 3
    # Misaligned starts: 1, 17, 33, 47, 99
    misaligned_starts = [1, 17, 33, 47, 99]

    for start in misaligned_starts:
        end = start + 64
        survivors = Phase11ContractAdapter.sieve_survivors(y, start, end, sieve_depth=50)
        assert isinstance(survivors, list)
        for s in survivors:
            assert start <= s <= end, f"Survivor {s} out of interval [{start}, {end}]"


@pytest.mark.phase11_tier2
def test_bnd10_sieve_depth_edges() -> None:
    """Verifies sieve behavior at minimal depth (e.g. depth=5 or 10) vs deeper sieve."""
    y = 3
    t_start, t_end = 1, 50

    # Minimal depth: only primes up to 7
    survivors_shallow = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth=7)
    # Deeper depth: primes up to 200
    survivors_deep = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth=200)

    assert len(survivors_shallow) >= len(survivors_deep)
    assert set(survivors_deep).issubset(set(survivors_shallow))


@pytest.mark.phase11_tier2
def test_bnd10_zero_survivor_interval_handling() -> None:
    """Verifies that an interval with 0 survivors is handled cleanly as an empty list."""
    y = 3
    # At t=1 (x=6): A(6)=94607 has factor 89 and B(6)=94609 has factor 37.
    # Sieving with depth >= 89 eliminates t=1, producing 0 survivors in [1, 1].
    survivors = Phase11ContractAdapter.sieve_survivors(y, 1, 1, sieve_depth=100)
    assert survivors == [], f"Expected 0 survivors for t=1 with depth 100, got {survivors}"


@pytest.mark.phase11_tier2
def test_bnd10_all_survivor_synthetic_interval() -> None:
    """Verifies that when no sieving primes are applied, all t survive."""
    y = 3
    t_start, t_end = 10, 25

    # Depth < 2 means no primes are in primerange(2, depth+1) -> no elimination
    survivors = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth=1)
    expected_all = list(range(t_start, t_end + 1))
    assert survivors == expected_all, f"Expected all {len(expected_all)} to survive, got {len(survivors)}"


@pytest.mark.phase11_tier2
def test_bnd10_cpu_gpu_fallback_consistency() -> None:
    """Verifies that CPU execution produces deterministic output without requiring GPU hardware."""
    y = 3
    # Sieve with CPU logic
    run1 = Phase11ContractAdapter.sieve_survivors(y, 1, 100, sieve_depth=40)
    run2 = Phase11ContractAdapter.sieve_survivors(y, 1, 100, sieve_depth=40)

    assert run1 == run2, "Repeated sieve runs must be identical"
    # Ensure known survivor t=21 is in survivors (since x=126 gives twin primes)
    assert 21 in run1, "Known twin prime generator t=21 must survive sieve at depth 40"
