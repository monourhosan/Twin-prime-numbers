"""
Unit tests for CandidateScreener multi-tier filtering.
"""

from src.phase6.screening import CandidateScreener
from src.phase6.models import CandidatePair

def test_screener_rejects_composites():
    """Verify that known composites are rejected before reaching Miller-Rabin or dual PRP."""
    screener = CandidateScreener(mr_rounds=25)
    
    # m = 6 -> A = 35 (5*7), B = 37 (prime)
    res = screener.screen_candidate(6)
    assert res.is_dual_prp is False
    assert res.rejection_reason is not None

    # m = 8 -> A = 47 (prime), B = 49 (7*7)
    res = screener.screen_candidate(8)
    assert res.is_dual_prp is False

def test_screener_accepts_true_twin_primes():
    """Verify that known small twin primes pass all screening tiers."""
    screener = CandidateScreener(mr_rounds=25)
    
    # Twin prime pairs:
    # m = 2 -> (11, 13)
    # m = 3 -> (17, 19)
    # m = 5 -> (29, 31)
    # m = 7 -> (41, 43)
    # m = 10 -> (59, 61)
    # m = 12 -> (71, 73)
    for m in [2, 3, 5, 7, 10, 12]:
        res = screener.screen_candidate(m)
        assert res.is_dual_prp is True
        assert res.is_left_prp is True
        assert res.is_right_prp is True
        assert res.stage_passed == "MILLER_RABIN"
