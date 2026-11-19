"""Unit and Property Tests for Milestone M3 Primality Screening Pipeline (`src/phase11/screening.py`).

Verifies:
  1. Fast trial division up to limit Q, wheel step alternation (d=5, diff=2 <-> 4), and limit boundaries.
  2. Fermat base-2 pseudoprime test, Fermat pseudoprimes, and discrimination against base-3.
  3. Carmichael numbers (561, 1105, 1729, 2465, 2821): survive Fermat-2, killed by Miller-Rabin and BPSW.
  4. Strong Fermat pseudoprimes (341, 645): survive Fermat-2, killed by Miller-Rabin and BPSW.
  5. Multi-base Miller-Rabin test: primes, composites, custom bases vs default 12 bases.
  6. Baillie-PSW primality test: primes, composites, prime powers, and pseudoprime rejection.
  7. screen_candidate(): 3-way partition into DUAL_PRP, SINGLE_PRP, and COMPOSITE.
"""

from src.phase11.screening import (
    baillie_psw,
    fermat_base2,
    miller_rabin,
    screen_candidate,
    trial_division,
)

# --- 1. Trial Division Tests ---

def test_trial_division_primes_and_composites() -> None:
    """Verifies trial division correctness on primes, composites, and prime powers."""
    # Negative and non-prime boundaries
    assert trial_division(-10) is False
    assert trial_division(0) is False
    assert trial_division(1) is False

    # Small primes
    assert trial_division(2) is True
    assert trial_division(3) is True

    # Multiples of 2 and 3
    for comp in [4, 6, 8, 9, 10, 12, 14, 15, 18, 20, 21, 22, 24, 26, 27]:
        assert trial_division(comp) is False, f"Composite {comp} survived trial division"

    # Primes within default limit (1000)
    for p in [5, 7, 11, 13, 17, 19, 23, 29, 31, 97, 199, 541, 997]:
        assert trial_division(p) is True, f"Prime {p} failed trial division"

    # Prime powers
    for pp in [4, 8, 9, 16, 25, 27, 49, 121, 125, 169, 289, 343, 361, 529, 841, 961, 1331]:
        assert trial_division(pp) is False, f"Prime power {pp} survived trial division"

    # Composite with prime factors strictly above limit 1000
    # 1009 * 1013 = 1022117 (smallest factor is 1009 > 1000)
    assert trial_division(1009 * 1013, limit=1000) is True


def test_trial_division_wheel_boundary_and_step_alternation() -> None:
    """Verifies wheel step alternation (d=5, diff=2 <-> 4) and factor limit Q=1000."""
    # The wheel sequence: 5 (+2)-> 7 (+4)-> 11 (+2)-> 13 (+4)-> 17 (+2)-> 19 (+4)-> 23 (+6? 23+6=29)...
    # diff alternates 2, 4, 2, 4... checking 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43...
    wheel_primes = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    for p in wheel_primes:
        assert trial_division(p * p, limit=1000) is False, f"Failed detecting factor {p} in {p*p}"

    # Near limit 1000
    # 997 is prime (< 1000)
    assert trial_division(997 * 997, limit=1000) is False
    assert trial_division(997 * 1009, limit=1000) is False

    # 1009 is the first prime > 1000
    assert trial_division(1009 * 1009, limit=1000) is True
    # But with limit=1010, factor 1009 is caught
    assert trial_division(1009 * 1009, limit=1010) is False


# --- 2. Fermat Base-2 Tests ---

def test_fermat_base2_primes_composites_and_pseudoprimes() -> None:
    """Verifies Fermat base-2 primality test on primes, composites, and pseudoprimes."""
    # Boundaries
    assert fermat_base2(-5) is False
    assert fermat_base2(0) is False
    assert fermat_base2(1) is False
    assert fermat_base2(2) is True

    # Evens > 2
    for even in [4, 6, 8, 10, 100]:
        assert fermat_base2(even) is False

    # Odd primes
    for p in [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 97, 101, 997]:
        assert fermat_base2(p) is True

    # Odd composites (not base-2 pseudoprimes)
    for c in [9, 15, 21, 25, 27, 33, 35, 49, 63, 77, 121]:
        assert fermat_base2(c) is False

    # 91 = 7 * 13: 3^90 = 1 mod 91, but 2^90 = 64 mod 91 != 1.
    # Essential to ensure base is 2 and not mutated to 3!
    assert fermat_base2(91) is False


# --- 3. Carmichael Numbers & Pseudoprimes Tests ---

def test_carmichael_numbers_survive_fermat_killed_by_mr_and_bpsw() -> None:
    """Verifies Carmichael numbers survive Fermat base-2 but are killed by Miller-Rabin and Baillie-PSW."""
    carmichaels = [561, 1105, 1729, 2465, 2821]
    for c in carmichaels:
        assert fermat_base2(c) is True, f"Carmichael {c} should pass Fermat base-2"
        assert miller_rabin(c) is False, f"Carmichael {c} must be killed by Miller-Rabin"
        assert baillie_psw(c) is False, f"Carmichael {c} must be killed by Baillie-PSW"


def test_strong_fermat_pseudoprimes() -> None:
    """Verifies strong Fermat pseudoprimes survive Fermat base-2 but are killed by MR and BPSW."""
    # 341 = 11 * 31 (smallest base-2 Fermat pseudoprime)
    # 2^340 = 1 mod 341; but 3^340 = 56 mod 341 != 1 (distinguishes base 2 from base 3!)
    assert fermat_base2(341) is True
    assert miller_rabin(341) is False
    assert baillie_psw(341) is False

    # 645 = 3 * 5 * 43 (Fermat base-2 pseudoprime)
    assert fermat_base2(645) is True
    assert miller_rabin(645) is False
    assert baillie_psw(645) is False


# --- 4. Miller-Rabin Tests ---

def test_miller_rabin_primes_and_composites() -> None:
    """Verifies Miller-Rabin deterministic test on primes and composites."""
    assert miller_rabin(-1) is False
    assert miller_rabin(0) is False
    assert miller_rabin(1) is False

    # Small primes
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        assert miller_rabin(p) is True

    # Larger primes
    for p in [41, 43, 47, 53, 59, 61, 997, 1009, 10007]:
        assert miller_rabin(p) is True

    # Composites with small factors <= 37
    for c in [4, 6, 9, 15, 25, 35, 49, 77, 121]:
        assert miller_rabin(c) is False

    # Composites whose prime factors are all > 37 (kills bases=[1] mutant)
    composites_factors_gt_37 = [
        41 * 41,        # 1681
        41 * 43,        # 1763
        41 * 47,        # 1927
        43 * 47,        # 2021
        43 * 43,        # 1849
        47 * 53,        # 2491
    ]
    for c in composites_factors_gt_37:
        assert miller_rabin(c) is False, f"Composite {c} with factors > 37 survived Miller-Rabin"


def test_miller_rabin_custom_bases_vs_default() -> None:
    """Verifies Miller-Rabin behavior with custom base lists vs default 12 bases."""
    # 8321 = 53 * 157 is a strong pseudoprime to base 2 with factors > 37
    assert miller_rabin(8321, bases=[2]) is True
    assert miller_rabin(8321, bases=[2, 3]) is False
    assert miller_rabin(8321) is False  # Default 12 bases

    # 1373653 = 829 * 1657 is a strong pseudoprime to bases 2 and 3
    assert miller_rabin(1373653, bases=[2, 3]) is True
    assert miller_rabin(1373653, bases=[2, 3, 5]) is False
    assert miller_rabin(1373653) is False  # Default 12 bases


# --- 5. Baillie-PSW Tests ---

def test_baillie_psw_primality() -> None:
    """Verifies Baillie-PSW primality test."""
    assert baillie_psw(-2) is False
    assert baillie_psw(0) is False
    assert baillie_psw(1) is False

    for p in [2, 3, 5, 7, 11, 13, 17, 1009, 10007, 65537]:
        assert baillie_psw(p) is True

    for c in [4, 6, 9, 15, 25, 91, 121, 341, 561, 1105, 1729, 1763, 2047, 1373653]:
        assert baillie_psw(c) is False


# --- 6. Candidate Screening Pipeline (screen_candidate) ---

def test_screen_candidate_distinguishes_dual_single_and_composite() -> None:
    """Verifies screen_candidate correctly distinguishes DUAL_PRP, SINGLE_PRP, and COMPOSITE."""
    # Case 1: Both composite: y=3, t=1 -> A=1151423, B=1151425
    status, pair = screen_candidate(3, 1)
    assert status == "COMPOSITE"
    assert pair is None

    # Case 2: SINGLE_PRP with prime_A=False, prime_B=True: y=3, t=17
    # Ensures SINGLE_PRP is never misidentified as DUAL_PRP
    status, pair = screen_candidate(3, 17)
    assert status == "SINGLE_PRP"
    assert pair is None

    # Case 3: SINGLE_PRP with prime_A=True, prime_B=False: y=3, t=27
    status, pair = screen_candidate(3, 27)
    assert status == "SINGLE_PRP"
    assert pair is None

    # Case 4: DUAL_PRP: y=3, t=5 (verified twin prime pair)
    status, pair = screen_candidate(3, 5)
    assert status == "DUAL_PRP"
    assert pair is not None
    c_val, a_val, b_val = pair
    assert b_val - a_val == 2
    assert c_val == a_val + 1 == b_val - 1
    assert baillie_psw(a_val) is True
    assert baillie_psw(b_val) is True

    # Case 5: DUAL_PRP: y=3, t=21 (verified twin prime pair, x=126)
    status, pair = screen_candidate(3, 21)
    assert status == "DUAL_PRP"
    assert pair is not None
    c_val, a_val, b_val = pair
    assert b_val - a_val == 2
    assert c_val == a_val + 1 == b_val - 1
    assert baillie_psw(a_val) is True
    assert baillie_psw(b_val) is True
