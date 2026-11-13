"""
Unit tests for exact integer interval mapping between p-space and center m-space.
"""

import pytest
from src.phase6.models import IntervalMapping

def test_interval_mapping_exact_integer():
    """Verify exact ceiling and floor mapping without floating point errors."""
    # p in [5, 17] -> eligible primes: 5, 11, 17
    # 5: m=1 (6*1 - 1 = 5)
    # 17: m=3 (6*3 - 1 = 17)
    mapping = IntervalMapping.from_p_range(5, 17)
    assert mapping.m_min == 1
    assert mapping.m_max == 3
    assert mapping.total_m_candidates == 3

    # Exact boundary test:
    # p_min = 6: ceil((6 + 1)/6) = 2 (smallest 6m - 1 >= 6 is 11 for m=2)
    # p_max = 12: floor((12 + 1)/6) = 2 (largest 6m - 1 <= 12 is 11 for m=2)
    mapping = IntervalMapping.from_p_range(6, 12)
    assert mapping.m_min == 2
    assert mapping.m_max == 2
    assert mapping.total_m_candidates == 1

def test_interval_mapping_large_integers():
    """Verify that integer division handles arbitrary-precision 100-digit boundaries correctly."""
    p_min = 10**99
    p_max = 10**99 + 1000
    mapping = IntervalMapping.from_p_range(p_min, p_max)
    assert mapping.m_min == (p_min + 1 + 5) // 6
    assert mapping.m_max == (p_max + 1) // 6
    assert mapping.total_m_candidates == mapping.m_max - mapping.m_min + 1
    # Check boundary candidates
    assert 6 * mapping.m_min - 1 >= p_min
    assert 6 * (mapping.m_min - 1) - 1 < p_min
    assert 6 * mapping.m_max - 1 <= p_max
    assert 6 * (mapping.m_max + 1) - 1 > p_max

def test_interval_mapping_invalid():
    """Verifies that p_min > p_max raises ValueError."""
    with pytest.raises(ValueError):
        IntervalMapping.from_p_range(100, 50)
