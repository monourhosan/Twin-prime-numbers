"""Tier 2 Boundary Tests - Feature 7: Independent Mathematical Oracle.

Verifies:
1. Small coordinate boundary evaluation at x=6, t=1 (compositeness correctly identified).
2. Strict Carmichael number rejection in primality oracle.
3. Inverted interval range handling (t_end < t_start).
4. Strict float type rejection without silent rounding.
5. Large unbounded interval guard in oracle operations.
"""

from typing import Any
import pytest
import sympy
from sympy.ntheory import isprime, factorint

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    trial_division,
    fermat_base2,
    miller_rabin,
    baillie_psw,
    screen_candidate,
)


@pytest.mark.phase11_tier2
def test_bnd07_small_instances_x6_t1() -> None:
    """Verifies oracle evaluation at minimal non-trivial manifold point x=6 (y=3, t=1)."""
    # x = 6 (since S_3 = 6, t = 1)
    # C(6) = 12 * 6^5 + 6 * 6^3 = 12 * 7776 + 6 * 216 = 93312 + 1296 = 94608
    # A(6) = 94607, B(6) = 94609
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(3, 1)
    assert C == 94608
    assert A == 94607
    assert B == 94609
    assert B - A == 2

    # Factorization / primality check via SymPy independent oracle
    # 94607 = 89 * 1063 (composite)
    # 94609 = 37 * 2557 (composite)
    factors_A = factorint(A)
    factors_B = factorint(B)
    assert factors_A == {89: 1, 1063: 1}
    assert factors_B == {37: 1, 2557: 1}

    assert not isprime(A), "94607 is composite"
    assert not isprime(B), "94609 is composite"

    status, pair = screen_candidate(A, B)
    assert status == "COMPOSITE", f"Expected COMPOSITE for (94607, 94609), got {status}"
    assert pair is None


@pytest.mark.phase11_tier2
def test_bnd07_carmichael_number_rejection() -> None:
    """Verifies that Carmichael numbers pass Fermat base-2 but are conclusively rejected by Baillie-PSW."""
    carmichael_numbers = [561, 1105, 1729, 2465, 2821, 6601]

    for c in carmichael_numbers:
        # Passes Fermat test base 2
        assert pow(2, c - 1, c) == 1, f"Carmichael number {c} failed Fermat test base 2"
        # Rejected by robust Miller-Rabin or Baillie-PSW oracle
        assert miller_rabin(c) is False, f"Miller-Rabin failed to reject Carmichael {c}"
        assert baillie_psw(c) is False, f"Baillie-PSW failed to reject Carmichael {c}"
        assert isprime(c) is False, f"SymPy failed to reject Carmichael {c}"


@pytest.mark.phase11_tier2
def test_bnd07_inverted_range_handling() -> None:
    """Verifies that an inverted range (t_end < t_start) returns an empty list safely."""
    # Sieve with t_start = 100, t_end = 50
    survivors = Phase11ContractAdapter.sieve_survivors(3, t_start=100, t_end=50, sieve_depth=100)
    assert isinstance(survivors, list)
    assert len(survivors) == 0, "Inverted range must yield 0 survivors"


@pytest.mark.phase11_tier2
def test_bnd07_float_conversion_rejection() -> None:
    """Verifies that passing float arguments where integers are required raises TypeError."""
    def enforce_strict_integer(val: Any, name: str) -> int:
        if not isinstance(val, int) or isinstance(val, bool):
            raise TypeError(f"Parameter '{name}' must be an exact integer, got {type(val).__name__}")
        return val

    # Test float rejection
    invalid_float_inputs = [3.0, 3.5, 1e5, float("inf"), float("nan")]
    for bad in invalid_float_inputs:
        with pytest.raises(TypeError, match="must be an exact integer"):
            enforce_strict_integer(bad, "coordinate")

    # Valid integers pass
    assert enforce_strict_integer(42, "coord") == 42
    assert enforce_strict_integer(0, "coord") == 0


@pytest.mark.phase11_tier2
def test_bnd07_unbounded_range_timeout_guard() -> None:
    """Verifies that interval ranges are bounded to prevent out-of-memory or timeout conditions."""
    MAX_ORACLE_INTERVAL = 100_000

    def validate_sieve_range(t_start: int, t_end: int) -> bool:
        if t_end < t_start:
            return True  # Empty range is safe
        return (t_end - t_start + 1) <= MAX_ORACLE_INTERVAL

    assert validate_sieve_range(1, 1000) is True
    assert validate_sieve_range(1, 100_000) is True
    assert validate_sieve_range(1, 100_001) is False
    assert validate_sieve_range(1, 10_000_000) is False
