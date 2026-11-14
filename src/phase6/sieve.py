"""
Phase 6: Sieve Engines (Q-Reference, Q-Segment, Q-Event, and Method R).
High-throughput segmented residue marking and empirical density tracking.
"""

import math
from typing import List, Dict, Generator, Tuple, Optional
import gmpy2

from .polynomial_roots import compute_method_q_forbidden_j, compute_method_r_forbidden_j
from .families import MethodQFamily, MethodRFamily


def generate_sieve_primes(limit: int) -> List[int]:
    """
    Generates all primes up to limit using simple sieve of Eratosthenes.
    Returns list of primes.
    """
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    p = 2
    while p * p <= limit:
        if sieve[p]:
            sieve[p * p : limit + 1 : p] = bytearray(len(sieve[p * p : limit + 1 : p]))
        p += 1
    return [i for i, is_prime in enumerate(sieve) if is_prime]


class QSieveReference:
    """
    Q-Reference: Direct modular evaluation over candidate window.
    Serves as the ground-truth correctness oracle for small windows.
    """

    def __init__(self, family: MethodQFamily, sieve_limit: int):
        self.family = family
        self.sieve_limit = sieve_limit
        self.primes = [p for p in generate_sieve_primes(sieve_limit) if p >= 5 and family.S % p != 0]

    def sieve_window(self, j_start: int, j_end: int) -> List[int]:
        survivors = []
        h = self.family.h
        S = self.family.S
        for j in range(j_start, j_end):
            t = 2 * j + 1
            eliminated = False
            for q in self.primes:
                x = (S * t) % q
                A_mod = (x * x - h * x - 1) % q
                if A_mod == 0:
                    eliminated = True
                    break
                B_mod = (x * x - h * x + 1) % q
                if B_mod == 0:
                    eliminated = True
                    break
            if not eliminated:
                survivors.append(j)
        return survivors


class QSieveSegment:
    """
    Q-Segment: High-throughput packed segmented sieve in j-space.
    Precomputes forbidden residues per prime and marks cache-sized segments.
    """

    def __init__(self, family: MethodQFamily, sieve_limit: int):
        self.family = family
        self.sieve_limit = sieve_limit
        self.primes = [p for p in generate_sieve_primes(sieve_limit) if p >= 5 and family.S % p != 0]
        # Precompute forbidden residues for all primes
        self.forbidden_residues: List[Tuple[int, List[int]]] = []
        for q in self.primes:
            roots = compute_method_q_forbidden_j(q, family.h, family.S)
            if roots:
                self.forbidden_residues.append((q, roots))

    def theoretical_survivor_fraction(self) -> float:
        """
        Computes the theoretical product ∏(1 - rho(q)/q) for admissible progressions.
        """
        prod = 1.0
        for q, roots in self.forbidden_residues:
            rho = len(roots)
            prod *= (1.0 - (rho / q))
        return prod

    def sieve_segment(self, j_start: int, segment_length: int) -> List[int]:
        """
        Sieves a contiguous segment [j_start, j_start + segment_length).
        Returns list of survivor j indices.
        """
        # Bytearray: 0 = survivor, 1 = eliminated
        seg = bytearray(segment_length)
        
        for q, roots in self.forbidden_residues:
            for r in roots:
                # First index in segment with j = r (mod q)
                rem = j_start % q
                first = (r - rem) % q
                seg[first : segment_length : q] = b"\x01" * len(seg[first : segment_length : q])

        survivors = [j_start + i for i, byte in enumerate(seg) if byte == 0]
        return survivors

    def stream_segments(
        self,
        j_start: int,
        j_end: int,
        segment_size: int = 100000
    ) -> Generator[List[int], None, None]:
        cur = j_start
        while cur < j_end:
            length = min(segment_size, j_end - cur)
            yield self.sieve_segment(cur, length)
            cur += length


class QSieveEvent:
    """
    Q-Event: Experimental bucket-based sieve for very large primes (q > segment_length).
    Small primes (q <= segment_length) are sieved directly; large primes are bucketed.
    """

    def __init__(self, family: MethodQFamily, sieve_limit: int, segment_size: int = 100000):
        self.family = family
        self.sieve_limit = sieve_limit
        self.segment_size = segment_size
        all_primes = [p for p in generate_sieve_primes(sieve_limit) if p >= 5 and family.S % p != 0]
        
        self.small_residues: List[Tuple[int, List[int]]] = []
        self.large_residues: List[Tuple[int, List[int]]] = []
        
        for q in all_primes:
            roots = compute_method_q_forbidden_j(q, family.h, family.S)
            if roots:
                if q <= segment_size:
                    self.small_residues.append((q, roots))
                else:
                    self.large_residues.append((q, roots))

    def sieve_segment(self, j_start: int, segment_length: int) -> List[int]:
        seg = bytearray(segment_length)
        
        # Sieve small primes
        for q, roots in self.small_residues:
            for r in roots:
                rem = j_start % q
                first = (r - rem) % q
                seg[first : segment_length : q] = b"\x01" * len(seg[first : segment_length : q])

        # Sieve large primes
        for q, roots in self.large_residues:
            for r in roots:
                rem = j_start % q
                first = (r - rem) % q
                if first < segment_length:
                    seg[first : segment_length : q] = b"\x01" * len(seg[first : segment_length : q])

        return [j_start + i for i, byte in enumerate(seg) if byte == 0]


class RSieveSegment:
    """
    Method R Segmented Sieve:
    Dual-offset linear sieve on j where C = C0 + 6j.
    """

    def __init__(self, family: MethodRFamily, sieve_limit: int):
        self.family = family
        self.sieve_limit = sieve_limit
        self.primes = [p for p in generate_sieve_primes(sieve_limit) if p >= 5]
        self.forbidden_residues: List[Tuple[int, List[int]]] = []
        for q in self.primes:
            roots = compute_method_r_forbidden_j(q, family.C0)
            if roots:
                self.forbidden_residues.append((q, roots))

    def sieve_segment(self, j_start: int, segment_length: int) -> List[int]:
        seg = bytearray(segment_length)
        for q, roots in self.forbidden_residues:
            for r in roots:
                rem = j_start % q
                first = (r - rem) % q
                seg[first : segment_length : q] = b"\x01" * len(seg[first : segment_length : q])
        return [j_start + i for i, byte in enumerate(seg) if byte == 0]
