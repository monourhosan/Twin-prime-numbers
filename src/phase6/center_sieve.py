"""
Core residue calculations and striding logic for center index m.
"""

from typing import Tuple, List

def get_forbidden_residues(q: int) -> Tuple[int, int]:
    """
    Computes the two forbidden residue classes for m modulo sieve prime q >= 5:
      m = 6^(-1) mod q  (makes 6m - 1 divisible by q)
      m = -6^(-1) mod q (makes 6m + 1 divisible by q)
    """
    if q < 5:
        raise ValueError(f"Sieve prime must be >= 5, got {q}")
    inv6 = pow(6, -1, q)
    neg_inv6 = (q - inv6) % q
    return inv6, neg_inv6

def get_first_marked_indices(q: int, m_base: int) -> Tuple[int, int]:
    """
    Computes the first segment offsets j1, j2 in [0, q) where:
      m_base + j1 = inv6 (mod q)
      m_base + j2 = neg_inv6 (mod q)
    """
    inv6, neg_inv6 = get_forbidden_residues(q)
    base_rem = m_base % q
    j1 = (inv6 - base_rem) % q
    j2 = (neg_inv6 - base_rem) % q
    return j1, j2

def is_small_prime_equality(m: int, q: int) -> bool:
    """
    Returns True if q == 6m - 1 or q == 6m + 1, meaning the candidate member
    equals the prime q itself rather than being a strictly composite multiple.
    """
    return (6 * m - 1 == q) or (6 * m + 1 == q)
