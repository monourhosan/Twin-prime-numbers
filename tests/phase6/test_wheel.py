"""
Unit tests for configurable small-prime wheel factorization.
"""

import pytest
from src.phase6.wheel import CenterWheel

def test_wheel_moduli_and_counts():
    """Verify exact admissible residue counts for standard wheels."""
    # Wheel 5: primes {5} -> W=5, count = 5 - 2 = 3
    w5 = CenterWheel([5])
    assert w5.W == 5
    assert len(w5.admissible_residues) == 3
    assert w5.survivor_ratio == 0.60

    # Wheel 5, 7: primes {5, 7} -> W=35, count = (5-2)*(7-2) = 15
    w5_7 = CenterWheel([5, 7])
    assert w5_7.W == 35
    assert len(w5_7.admissible_residues) == 15
    assert abs(w5_7.survivor_ratio - (15 / 35)) < 1e-9

    # Wheel 5, 7, 11: primes {5, 7, 11} -> W=385, count = 3*5*9 = 135
    w5_7_11 = CenterWheel([5, 7, 11])
    assert w5_7_11.W == 385
    assert len(w5_7_11.admissible_residues) == 135

    # Wheel 5, 7, 11, 13: primes {5, 7, 11, 13} -> W=5005, count = 3*5*9*11 = 1485
    w13 = CenterWheel([5, 7, 11, 13])
    assert w13.W == 5005
    assert len(w13.admissible_residues) == 1485
    assert abs(w13.survivor_ratio - (1485 / 5005)) < 1e-9

def test_wheel_tiling_arbitrary_offsets():
    """Verify that wheel tiling correctly matches is_admissible for any offset."""
    wheel = CenterWheel([5, 7])
    seg_size = 120
    for offset in [0, 1, 17, 34, 35, 73]:
        seg = bytearray(seg_size)
        survivors = wheel.tile_into_segment(seg, m_base=offset)
        # Check every byte
        for i in range(seg_size):
            m = offset + i
            expected = 1 if wheel.is_admissible(m) else 0
            assert seg[i] == expected, f"Mismatch at m={m}: got {seg[i]}, expected {expected}"
        assert seg.count(1) == survivors
