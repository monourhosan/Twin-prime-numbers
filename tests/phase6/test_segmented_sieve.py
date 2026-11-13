"""
Differential testing of SegmentedCenterSieve against SymPy oracle.
"""

import sympy
from src.phase6.segmented import SegmentedCenterSieve
from src.phase6.wheel import CenterWheel

def test_sieve_never_eliminates_true_twin_primes():
    """Verify that every true twin prime pair (6m - 1, 6m + 1) in [5, 2000] survives sieving."""
    sieve = SegmentedCenterSieve(sieve_limit=500, wheel=CenterWheel([5, 7, 11, 13]))
    
    # Sieve segment [1, 500)
    survivors = sieve.sieve_segment(m_base=1, segment_size=500, preserve_small_primes=True)
    survivor_set = set(survivors)
    
    # Ground truth via SymPy
    for m in range(1, 501):
        A = 6 * m - 1
        B = 6 * m + 1
        if sympy.isprime(A) and sympy.isprime(B):
            assert m in survivor_set, f"True twin prime pair ({A}, {B}) at m={m} was erroneously eliminated!"

def test_segment_boundary_continuity():
    """Verify that two contiguous segments [0, 500) and [500, 1000) match a single segment [0, 1000)."""
    sieve = SegmentedCenterSieve(sieve_limit=200, wheel=CenterWheel([5, 7]))
    single = sieve.sieve_segment(m_base=1, segment_size=1000)
    
    part1 = sieve.sieve_segment(m_base=1, segment_size=500)
    part2 = sieve.sieve_segment(m_base=501, segment_size=500)
    
    combined = part1 + part2
    assert single == combined, "Segment splitting produced different survivors than unified segment!"
