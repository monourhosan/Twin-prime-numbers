"""
Exhaustive Verification of SCCA Residue Filtering Against Brute Force Direct Divisibility.
Verifies that:
1. A candidate t is eliminated by prime q iff q divides (F*t - 1) or q divides (F*t + 1).
2. Primes q | F never eliminate any candidate (since gcd(F*t +/- 1, q) = 1).
3. No genuine twin-prime pair is ever eliminated by the sieve.
"""

import math
import pytest
from src.phase5.candidates import SmoothCenterFamily
from src.phase5.crt_walker import SegmentedSCCAFilter, ForbiddenResidues, generate_primes_up_to

def test_residue_rules_against_brute_force():
    families = [
        SmoothCenterFamily({2: 1, 3: 5, 5: 2}, family_id="f1_dense"),
        SmoothCenterFamily({2: 2, 3: 3, 5: 1, 7: 1, 11: 1}, family_id="f2_balanced"),
        SmoothCenterFamily({2: 1, 3: 4, 7: 2, 13: 1}, family_id="f3_skip5")
    ]
    
    t_range = range(1, 501)
    sieve_limit = 100
    primes = generate_primes_up_to(sieve_limit)

    for fam in families:
        filt = SegmentedSCCAFilter(fam, sieve_limit=sieve_limit)
        survivors = set(filt.sieve_segment(1, 501))
        
        # Brute-force direct divisibility check
        brute_survivors = set()
        for t in t_range:
            C = fam.F * t
            A = C - 1
            B = C + 1
            
            # Check if any prime q <= sieve_limit divides A or B
            eliminated = False
            for q in primes:
                if q == 2 or q in fam.prime_factors:
                    # Divisibility immunity guaranteed
                    assert A % q != 0, f"A={A} unexpectedly divisible by prime factor {q} of F"
                    assert B % q != 0, f"B={B} unexpectedly divisible by prime factor {q} of F"
                    continue
                    
                if A % q == 0 or B % q == 0:
                    eliminated = True
                    break
                    
            if not eliminated:
                brute_survivors.add(t)

        # Bit-exact equivalence between sieve filter and brute-force divisibility
        assert survivors == brute_survivors, f"Sieve mismatch for {fam.family_id}: {survivors ^ brute_survivors}"

def test_sieve_never_eliminates_prime_candidate():
    # If A and B are prime, the sieve must never eliminate t
    fam = SmoothCenterFamily({2: 1, 3: 3, 5: 2, 7: 1}, family_id="fam_known")
    cand = fam.candidate(3) # A = 28349 (prime), B = 28351 (prime)
    filt = SegmentedSCCAFilter(fam, sieve_limit=1000)
    survivors = filt.sieve_segment(1, 10)
    assert 3 in survivors, "Sieve erroneously eliminated known prime twin pair t=3!"
