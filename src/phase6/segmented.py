"""
Segmented center sieve for general-integer twin-prime candidate generation.
"""

from typing import List, Optional
from src.phase6.wheel import CenterWheel
from src.phase6.center_sieve import get_first_marked_indices, is_small_prime_equality
from src.phase6.primes import generate_primes_up_to

class SegmentedCenterSieve:
    """
    High-throughput segmented sieve over universal center integers m in [m_base, m_base + segment_size).
    """
    def __init__(self, sieve_limit: int = 100000, wheel: Optional[CenterWheel] = None):
        self.sieve_limit = sieve_limit
        self.wheel = wheel if wheel is not None else CenterWheel([5, 7, 11, 13])
        
        # Precompute all sieve primes up to sieve_limit
        all_primes = generate_primes_up_to(sieve_limit)
        
        # Sieve primes exclude wheel primes and primes 2, 3
        wheel_primes_set = set(self.wheel.primes) | {2, 3}
        self.sieve_primes = [p for p in all_primes if p not in wheel_primes_set]

    def sieve_segment(
        self,
        m_base: int,
        segment_size: int,
        preserve_small_primes: bool = False
    ) -> List[int]:
        """
        Sieves a contiguous segment m in [m_base, m_base + segment_size).
        Returns a list of surviving center m values.
        """
        if segment_size <= 0:
            return []
            
        segment = bytearray(b"\x01") * segment_size
        
        # 1. Initialize segment using precomputed wheel pattern
        self.wheel.tile_into_segment(segment, m_base)
        
        # When preserving small primes in small tests, restore m=1 (5, 7) and m=2 (11, 13)
        if preserve_small_primes:
            if m_base <= 1 < m_base + segment_size:
                segment[1 - m_base] = 1
            if m_base <= 2 < m_base + segment_size:
                segment[2 - m_base] = 1
        
        # 2. Sieve with non-wheel primes
        if not preserve_small_primes:
            for q in self.sieve_primes:
                # Get first marked positions
                base_rem = m_base % q
                inv6 = pow(6, -1, q)
                neg_inv6 = (q - inv6) % q
                j1 = (inv6 - base_rem) % q
                j2 = (neg_inv6 - base_rem) % q
                
                # Mark slices
                if j1 < segment_size:
                    count1 = ((segment_size - 1 - j1) // q) + 1
                    segment[j1::q] = b"\x00" * count1
                if j2 < segment_size:
                    count2 = ((segment_size - 1 - j2) // q) + 1
                    segment[j2::q] = b"\x00" * count2
        else:
            # Slower path preserving small prime identities for unit tests near zero
            for q in self.sieve_primes:
                base_rem = m_base % q
                inv6 = pow(6, -1, q)
                neg_inv6 = (q - inv6) % q
                j1 = (inv6 - base_rem) % q
                j2 = (neg_inv6 - base_rem) % q
                
                for pos in range(j1, segment_size, q):
                    m_val = m_base + pos
                    if not is_small_prime_equality(m_val, q):
                        segment[pos] = 0
                for pos in range(j2, segment_size, q):
                    m_val = m_base + pos
                    if not is_small_prime_equality(m_val, q):
                        segment[pos] = 0

        # Collect surviving m indices
        # In bounded ranges, eliminate m <= 0 since m must be >= 1
        survivors = []
        for i in range(segment_size):
            if segment[i]:
                m_val = m_base + i
                if m_val >= 1:
                    survivors.append(m_val)
                    
        return survivors
