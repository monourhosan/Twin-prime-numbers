"""
Unit Tests for Phase 5 Candidate Modeling and Algebraic Constraints.
"""

import pytest
import math
from src.phase5.candidates import SmoothCenterFamily, TwinPairCandidate

def test_smooth_center_family_validation():
    # Valid family
    fam = SmoothCenterFamily({2: 2, 3: 1, 5: 1}, family_id="test_fam")
    assert fam.F == 4 * 3 * 5
    assert fam.F_odd == 3 * 5
    assert fam.prime_factors == [2, 3, 5]
    assert fam.odd_prime_factors == [3, 5]

    # Invalid: missing factor 2
    with pytest.raises(ValueError, match="exponent a >= 1 for prime 2"):
        SmoothCenterFamily({3: 2, 5: 1})

    # Invalid: missing factor 3
    with pytest.raises(ValueError, match="exponent b >= 1 for prime 3"):
        SmoothCenterFamily({2: 2, 5: 1})

def test_twin_candidate_algebraic_properties():
    fam = SmoothCenterFamily({2: 3, 3: 2, 5: 1}, family_id="fam_alg")
    cand = fam.candidate(7)
    
    # Core twin-prime relationship
    assert cand.B - cand.A == 2
    assert cand.A % 2 == 1
    assert cand.B % 2 == 1
    assert cand.A > 2
    assert math.gcd(cand.A, cand.B) == 1

    # Validation pass
    ok, err = cand.validate_algebraic()
    assert ok is True
    assert err is None

    # Immunity to all prime factors of F
    for p in fam.prime_factors:
        assert cand.A % p != 0
        assert cand.B % p != 0

def test_twin_candidate_size_conditions():
    # Large F_odd, small t -> size condition satisfies
    fam_large = SmoothCenterFamily({2: 2, 3: 10, 5: 5}, family_id="fam_large")
    cand_valid = fam_large.candidate(3)
    ok, err = cand_valid.satisfies_size_condition()
    assert ok is True
    assert err is None

    # Small F_odd, huge t -> size condition fails
    fam_small = SmoothCenterFamily({2: 2, 3: 1}, family_id="fam_small")
    cand_invalid = fam_small.candidate(100000)
    ok, err = cand_invalid.satisfies_size_condition()
    assert ok is False
    assert "size condition failed" in err.lower()

def test_canonical_hash_determinism():
    fam = SmoothCenterFamily({2: 1, 3: 2, 5: 1}, family_id="fam_hash")
    cand1 = fam.candidate(5)
    cand2 = fam.candidate(5)
    assert cand1.canonical_hash() == cand2.canonical_hash()

    cand3 = fam.candidate(6)
    assert cand1.canonical_hash() != cand3.canonical_hash()
