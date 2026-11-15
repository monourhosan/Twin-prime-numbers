"""
Verification that BucketCenterSieve matches SegmentedCenterSieve.
"""

from src.phase6.segmented import SegmentedCenterSieve
from src.phase6.bucket_sieve import BucketCenterSieve
from src.phase6.wheel import CenterWheel

def test_bucket_sieve_bit_exact_agreement():
    """Verify BucketCenterSieve produces exact same survivors as SegmentedCenterSieve."""
    sieve_limit = 5000
    seg_size = 500
    wheel = CenterWheel([5, 7])
    
    seg_sieve = SegmentedCenterSieve(sieve_limit=sieve_limit, wheel=wheel)
    bucket_sieve = BucketCenterSieve(sieve_limit=sieve_limit, segment_size=seg_size, wheel=wheel)
    
    # Run across 4 consecutive segments
    for i in range(4):
        m_base = 1000 + i * seg_size
        survivors_seg = seg_sieve.sieve_segment(m_base, seg_size)
        survivors_bucket = bucket_sieve.sieve_segment(m_base, seg_size)
        assert survivors_seg == survivors_bucket, f"Mismatch in segment {i} at m_base={m_base}"
