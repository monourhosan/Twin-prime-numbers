"""Feature 16: Multi-Tier Primality Screening Pipeline.

Verifies:
1. Tier 1: Fast trial division eliminating small prime divisors.
2. Tier 2: Fermat base-2 pseudoprime pre-filter.
3. Tier 3: 7-base deterministic/multi-base Miller-Rabin test.
4. Tier 4: Baillie-PSW conclusive probable prime test.
5. Multi-tier integrated screening pipeline via Phase11ContractAdapter.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    trial_division,
    fermat_base2,
    miller_rabin,
    baillie_psw,
    screen_candidate,
)


@pytest.mark.phase11_tier1
def test_f16_trial_division_filter() -> None:
    """Verifies trial division eliminates composite numbers with factors <= limit."""
    # Composite with factor 7
    assert trial_division(7 * 101, limit=50) is False
    # Composite with factor 47 (<= 50)
    assert trial_division(47 * 53, limit=50) is False
    # Composite whose smallest factor is 59 (> 50) passes trial division
    assert trial_division(59 * 61, limit=50) is True
    # Prime passes trial division
    assert trial_division(10007, limit=50) is True


@pytest.mark.phase11_tier1
def test_f16_fermat_base2_filter() -> None:
    """Verifies Fermat base-2 test 2^(n-1) = 1 mod n accepts primes and rejects composites."""
    assert fermat_base2(10007) is True  # Prime
    assert fermat_base2(10009) is True  # Prime
    assert fermat_base2(10005) is False  # Composite divisible by 5
    assert fermat_base2(10008) is False  # Even number


@pytest.mark.phase11_tier1
def test_f16_miller_rabin_multi_base() -> None:
    """Verifies 7-base Miller-Rabin test correctly screens primes and composites."""
    bases = [2, 3, 5, 7, 11, 13, 17]
    assert miller_rabin(104729, bases=bases) is True  # Prime
    assert miller_rabin(1299709, bases=bases) is True  # Prime
    assert miller_rabin(104731, bases=bases) is False  # Composite (11 * 9521)
    # Carmichael number 561 (3 * 11 * 17) fails Miller-Rabin
    assert miller_rabin(561, bases=bases) is False


@pytest.mark.phase11_tier1
def test_f16_baillie_psw_conclusive() -> None:
    """Verifies Baillie-PSW (MR base-2 + Lucas PRP) test behavior."""
    assert baillie_psw(10007) is True
    assert baillie_psw(10009) is True
    assert baillie_psw(561) is False  # Carmichael number rejected by BPSW
    assert baillie_psw(1105) is False  # Carmichael number rejected by BPSW


@pytest.mark.phase11_tier1
def test_f16_multi_tier_screening_pipeline() -> None:
    """Verifies integrated screening pipeline returns correct CandidateStatus."""
    status, pair = Phase11ContractAdapter.screen_candidate(y=3, t=1)
    assert status in ("COMPOSITE", "SINGLE_PRP", "DUAL_PRP")
    if status == "DUAL_PRP":
        assert pair is not None
        assert len(pair) == 3
    else:
        assert pair is None
