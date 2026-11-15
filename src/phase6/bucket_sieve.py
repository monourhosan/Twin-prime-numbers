"""
Bucket-scheduled segmented center sieve for large primes (q > segment_size).
"""

from typing import List, Dict, Optional
from collections import defaultdict
from src.phase6.wheel import CenterWheel
from src.phase6.center_sieve import get_forbidden_residues
from src.phase6.primes import generate_primes_up_to

class BucketCenterSieve:
    """
    Sieve that splits primes into small primes (q <= segment_size) and large primes (q > segment_size).
    Large primes are scheduled into bucket lists corresponding to future segment indices.
    """
    def __init__(self, sieve_limit: int = 100000, segment_size: int = 262144, wheel: Optional[CenterWheel] = None):
        self.sieve_limit = sieve_limit
        self.segment_size = segment_size
        self.wheel = wheel if wheel is not None else CenterWheel([5, 7, 11, 13])
        
        all_primes = generate_primes_up_to(sieve_limit)
        wheel_primes_set = set(self.wheel.primes) | {2, 3}
        filtered = [p for p in all_primes if p not in wheel_primes_set]
        
        self.small_primes = [p for p in filtered if p <= segment_size]
        self.large_primes = [p for p in filtered if p > segment_size]
        
        # Priority buckets: map from segment_idx -> list of (offset_in_segment, prime)
        self.buckets: Dict[int, List[int]] = defaultdict(list)
        self.initialized_for_base: Optional[int] = None

    def _init_large_primes(self, m_start: int):
        """Initializes bucket hit positions for large primes starting from m_start."""
        self.buckets.clear()
        self.initialized_for_base = m_start
        for q in self.large_primes:
            r1, r2 = get_forbidden_residues(q)
            base_rem = m_start % q
            j1 = (r1 - base_rem) % q
            j2 = (r2 - base_rem) % q
            
            # Place in initial bucket
            seg1 = j1 // self.segment_size
            off1 = j1 % self.segment_size
            self.buckets[seg1].append((off1, q))
            
            seg2 = j2 // self.segment_size
            off2 = j2 % self.segment_size
            self.buckets[seg2].append((off2, q))

    def sieve_segment(self, m_base: int, segment_size: Optional[int] = None) -> List[int]:
        """Sieves a single segment using bucket scheduling for large primes."""
        S = segment_size if segment_size is not None else self.segment_size
        if self.initialized_for_base is None or m_base < self.initialized_for_base:
            self._init_large_primes(m_base)
            
        seg_idx = (m_base - self.initialized_for_base) // self.segment_size
        segment = bytearray(b"\x01") * S
        
        # 1. Tile wheel
        self.wheel.tile_into_segment(segment, m_base)
        
        # 2. Sieve small primes (q <= S)
        for q in self.small_primes:
            base_rem = m_base % q
            inv6 = pow(6, -1, q)
            neg_inv6 = (q - inv6) % q
            j1 = (inv6 - base_rem) % q
            j2 = (neg_inv6 - base_rem) % q
            
            if j1 < S:
                segment[j1::q] = b"\x00" * (((S - 1 - j1) // q) + 1)
            if j2 < S:
                segment[j2::q] = b"\x00" * (((S - 1 - j2) // q) + 1)
                
        # 3. Process current bucket for large primes
        if seg_idx in self.buckets:
            hits = self.buckets.pop(seg_idx)
            for off, q in hits:
                if off < S:
                    segment[off] = 0
                # Compute next occurrence of this hit
                next_pos = off + q
                next_seg = seg_idx + (next_pos // S)
                next_off = next_pos % S
                self.buckets[next_seg].append((next_off, q))
                
        survivors = []
        for i in range(S):
            if segment[i]:
                m_val = m_base + i
                if m_val >= 1:
                    survivors.append(m_val)
        return survivors
