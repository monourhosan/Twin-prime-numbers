"""Tier 2 Boundary Tests - Feature 8: Property & Equivalence Testing.

Verifies:
1. Asymmetric sieve interval batch sizes (not divisible by 16 or 64).
2. Monotonicity under varying sieve depth bounds.
3. Injected 1-bit survivor corruption detection in differential comparison.
4. Equivalence at low multiplier boundary points t=1, 2.
5. Minimal failing case isolation and shrinking under differential discrepancy.
"""

import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import compute_manifold, compute_primorial_anchor


@pytest.mark.phase11_tier2
def test_bnd08_asymmetric_batch_sizes() -> None:
    """Verifies that odd and prime batch sizes produce the exact same survivors as unbatched sieving."""
    y = 3
    t_start, t_end = 1, 100
    depth = 50

    # Unbatched gold standard
    expected_survivors = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, depth)

    # Batched with odd batch sizes (13, 29, 37)
    for batch_size in [7, 13, 31]:
        batched_survivors = []
        cur = t_start
        while cur <= t_end:
            sub_end = min(cur + batch_size - 1, t_end)
            sub_survivors = Phase11ContractAdapter.sieve_survivors(y, cur, sub_end, depth)
            batched_survivors.extend(sub_survivors)
            cur = sub_end + 1

        assert batched_survivors == expected_survivors, f"Mismatch with batch size {batch_size}"


@pytest.mark.phase11_tier2
def test_bnd08_varying_sieve_depth_bounds() -> None:
    """Verifies that deeper sieving produces a strict subset of survivors (monotonicity)."""
    y = 3
    t_start, t_end = 1, 200

    survivors_shallow = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth=50)
    survivors_deep = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth=500)

    # Set inclusion: every survivor in the deep sieve must also have survived the shallow sieve
    set_shallow = set(survivors_shallow)
    set_deep = set(survivors_deep)

    assert set_deep.issubset(set_shallow), "Monotonicity violation: deep sieve has candidates absent in shallow sieve"
    assert len(set_deep) <= len(set_shallow), "Deeper sieve cannot have more survivors than shallow sieve"


@pytest.mark.phase11_tier2
def test_bnd08_injected_one_bit_corruption_detection() -> None:
    """Verifies that injecting a 1-bit discrepancy between two engines is immediately detected."""
    y = 3
    gold_survivors = Phase11ContractAdapter.sieve_survivors(y, 1, 50, sieve_depth=30)
    assert len(gold_survivors) > 0

    # Simulate Engine B having a 1-bit corruption (dropped survivor or false survivor)
    corrupted_drop = list(gold_survivors[:-1])
    corrupted_add = list(gold_survivors) + [9999]

    def diff_survivors(list_a: list[int], list_b: list[int]) -> tuple[bool, list[int], list[int]]:
        missing_in_b = sorted(set(list_a) - set(list_b))
        extra_in_b = sorted(set(list_b) - set(list_a))
        return len(missing_in_b) == 0 and len(extra_in_b) == 0, missing_in_b, extra_in_b

    ok_drop, missing, extra = diff_survivors(gold_survivors, corrupted_drop)
    assert not ok_drop
    assert len(missing) == 1
    assert missing[0] == gold_survivors[-1]

    ok_add, missing_a, extra_a = diff_survivors(gold_survivors, corrupted_add)
    assert not ok_add
    assert extra_a == [9999]


@pytest.mark.phase11_tier2
def test_bnd08_boundary_points_t1_t2() -> None:
    """Verifies differential consistency at the extreme low multiplier boundary points t=1 and t=2."""
    for t in [1, 2]:
        C, A, B = Phase11ContractAdapter.compute_candidate_pair(3, t)
        Sy, _ = compute_primorial_anchor(3)
        expected_x = Sy * t
        C_ref, A_ref, B_ref = compute_manifold(expected_x)

        assert (C, A, B) == (C_ref, A_ref, B_ref)
        assert B - A == 2
        assert C % 6 == 0


@pytest.mark.phase11_tier2
def test_bnd08_minimal_failing_case_shrinking() -> None:
    """Verifies that differential comparison isolates the smallest offending multiplier t."""
    def find_first_difference(engine_a_func, engine_b_func, t_range: tuple[int, int]) -> int | None:
        for t in range(t_range[0], t_range[1] + 1):
            if engine_a_func(t) != engine_b_func(t):
                return t
        return None

    # Synthetic mock where engine B fails only at t=42
    engine_a = lambda t: (12 * (6 * t)**5 + 6 * (6 * t)**3)
    engine_b = lambda t: (12 * (6 * t)**5 + 6 * (6 * t)**3) if t != 42 else 0

    first_fail = find_first_difference(engine_a, engine_b, (1, 100))
    assert first_fail == 42, f"Expected shrunk minimal failing case at t=42, got {first_fail}"
