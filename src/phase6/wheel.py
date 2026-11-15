"""
Configurable small-prime wheel factorization for universal center m sieving.
"""

from typing import List, Tuple
import math

class CenterWheel:
    """
    Precomputes admissible residue classes modulo wheel modulus W for center m.
    A residue r (mod W) is admissible iff:
      (6r - 1) % q != 0 AND (6r + 1) % q != 0
    for all primes q in the wheel base.
    """
    def __init__(self, primes: List[int] = (5, 7, 11, 13)):
        for p in primes:
            if p in (2, 3):
                raise ValueError("Wheel primes must be >= 5 (factors of 2 and 3 are already absorbed by 6m)")
            if p < 5:
                raise ValueError("Primes must be >= 5")
                
        self.primes = sorted(primes)
        self.W = 1
        for p in self.primes:
            self.W *= p
            
        # Build lookup table: bytearray of length W
        self.table = bytearray(b"\x01") * self.W
        
        # For each prime q in wheel, eliminate forbidden residues
        for q in self.primes:
            inv6 = pow(6, -1, q)
            neg_inv6 = (q - inv6) % q
            # Mark all r % q == inv6 or r % q == neg_inv6
            for r in range(inv6, self.W, q):
                self.table[r] = 0
            for r in range(neg_inv6, self.W, q):
                self.table[r] = 0
                
        self.admissible_residues = [r for r in range(self.W) if self.table[r]]
        self.survivor_ratio = len(self.admissible_residues) / self.W

    def is_admissible(self, m: int) -> bool:
        """Returns True if m mod W is admissible."""
        return bool(self.table[m % self.W])

    def tile_into_segment(self, segment: bytearray, m_base: int) -> int:
        """
        Tiles the precomputed wheel pattern into segment bytearray starting at m_base.
        Returns the number of surviving 1s in the segment.
        """
        seg_len = len(segment)
        offset = m_base % self.W
        
        # Fast tiling using table slices
        curr = 0
        while curr < seg_len:
            take = min(seg_len - curr, self.W - offset)
            segment[curr : curr + take] = self.table[offset : offset + take]
            curr += take
            offset = 0 # after first partial block, always align to 0
            
        return segment.count(1)
