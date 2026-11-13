"""
Fast, exact small-prime generation for Phase 6 sieve base.
"""

from typing import List

def generate_primes_up_to(limit: int) -> List[int]:
    """Generates all primes <= limit using a bytearray sieve of Eratosthenes."""
    if limit < 2:
        return []
    if limit == 2:
        return [2]
    
    n_bytes = (limit + 1) // 2
    sieve = bytearray(b"\x01") * n_bytes
    sieve[0] = 0 # 1 is not prime (representing 2*0 + 1)
    
    root = int(limit**0.5) // 2
    last_idx = n_bytes - 1
    
    for i in range(1, root + 1):
        if sieve[i]:
            p = 2 * i + 1
            # First composite is p*p = (2i+1)^2 = 4i^2 + 4i + 1 -> index 2i(i+1)
            start = 2 * i * (i + 1)
            if start <= last_idx:
                step = p
                count = ((last_idx - start) // step) + 1
                sieve[start::step] = b"\x00" * count
            
    primes = [2]
    primes.extend(2 * i + 1 for i in range(1, n_bytes) if sieve[i])
    return primes
