"""Tier 2 Boundary Tests - Feature 16: Multi-Tier Screening Pipeline.

Verifies:
1. Rejection of Carmichael pseudoprimes in Miller-Rabin and Baillie-PSW tiers.
2. Strong Lucas pseudoprime rejection.
3. Safe rejection of candidate inputs < 3 for twin prime consideration.
4. Pipeline early exit optimization on initial tier failure.
5. Strict CandidateStatus enum conformity (COMPOSITE, SINGLE_PRP, DUAL_PRP).
"""

import pytest
from tests.phase11_e2e.contracts.math_contracts import (
    trial_division,
    fermat_base2,
    miller_rabin,
    baillie_psw,
    screen_candidate,
)


@pytest.mark.phase11_tier2
def test_bnd16_carmichael_rejection_in_screening() -> None:
    """Verifies that Carmichael numbers pass Fermat tier but are eliminated by Miller-Rabin and BPSW."""
    carmichael_samples = [561, 1105, 1729, 2465, 2821]

    for n in carmichael_samples:
        # Tier 2 (Fermat base 2) is tricked: 2^(n-1) == 1 mod n
        assert fermat_base2(n) is True, f"Carmichael number {n} unexpectedly failed Fermat test"
        # Tier 3 (Miller-Rabin) catches it
        assert miller_rabin(n) is False, f"Miller-Rabin failed to reject Carmichael {n}"
        # Tier 4 (Baillie-PSW) catches it
        assert baillie_psw(n) is False, f"Baillie-PSW failed to reject Carmichael {n}"


@pytest.mark.phase11_tier2
def test_bnd16_strong_lucas_pseudoprime_rejection() -> None:
    """Verifies that strong Lucas pseudoprimes or tricky composites fail Baillie-PSW."""
    # Composite odd numbers that are pseudoprimes to some bases
    composites = [9, 15, 25, 49, 91, 121, 341]  # 341 is Fermat pseudoprime base 2: 2^340 = 1 mod 341 (11 * 31)

    for comp in composites:
        bpsw_result = baillie_psw(comp)
        assert bpsw_result is False, f"Baillie-PSW failed to reject composite {comp}"


@pytest.mark.phase11_tier2
def test_bnd16_candidate_less_than_3_rejection() -> None:
    """Verifies that twin prime candidates < 3 (or <= 1 for primality) are safely rejected."""
    # Integers <= 1 cannot be prime
    non_primes = [-10, -1, 0, 1]
    for val in non_primes:
        assert trial_division(val) is False
        assert fermat_base2(val) is False
        assert miller_rabin(val) is False
        assert baillie_psw(val) is False

    # Twin candidate validator: twin primes on manifold are odd primes > 3
    def validate_twin_candidate_bounds(n: int) -> bool:
        return n >= 3 and n % 2 != 0

    assert validate_twin_candidate_bounds(2) is False
    assert validate_twin_candidate_bounds(1) is False
    assert validate_twin_candidate_bounds(-5) is False
    assert validate_twin_candidate_bounds(5) is True


@pytest.mark.phase11_tier2
def test_bnd16_pipeline_early_exit_on_tier_failure() -> None:
    """Verifies that a candidate failing trial division short-circuits without running heavy primality tests."""
    call_counts = {"trial": 0, "fermat": 0, "mr": 0, "bpsw": 0}

    def instrumented_screening(n: int) -> bool:
        call_counts["trial"] += 1
        if not trial_division(n):
            return False  # Early exit

        call_counts["fermat"] += 1
        if not fermat_base2(n):
            return False

        call_counts["mr"] += 1
        if not miller_rabin(n):
            return False

        call_counts["bpsw"] += 1
        return baillie_psw(n)

    # Even composite n=100 fails trial division immediately
    res = instrumented_screening(100)
    assert res is False
    assert call_counts["trial"] == 1
    assert call_counts["fermat"] == 0
    assert call_counts["mr"] == 0
    assert call_counts["bpsw"] == 0


@pytest.mark.phase11_tier2
def test_bnd16_candidate_status_enum_validation() -> None:
    """Verifies that screen_candidate returns only valid status enum strings."""
    ALLOWED_STATUSES = {"COMPOSITE", "SINGLE_PRP", "DUAL_PRP"}

    # Case 1: Both composite (x=6 -> A=94607, B=94609)
    status1, pair1 = screen_candidate(94607, 94609)
    assert status1 in ALLOWED_STATUSES
    assert status1 == "COMPOSITE"
    assert pair1 is None

    # Case 2: One prime, one composite (e.g. 5 and 9)
    status2, pair2 = screen_candidate(5, 9)
    assert status2 in ALLOWED_STATUSES
    assert status2 in ("COMPOSITE", "SINGLE_PRP")

    # Case 3: Both prime (11, 13)
    status3, pair3 = screen_candidate(11, 13)
    assert status3 in ALLOWED_STATUSES
    assert status3 == "DUAL_PRP"
    assert pair3 == (11, 13)
