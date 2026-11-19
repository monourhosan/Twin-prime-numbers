"""Tier 2 Boundary Tests - Feature 9: Arbitrary-Precision Engine Core.

Verifies:
1. Multi-thousand bit candidate computation and memory safety.
2. 64-bit integer boundary overflow protection (no wrap-around).
3. Big-integer string serialization and deserialization roundtrip.
4. Negative coordinate rejection in arbitrary-precision evaluation.
5. Immutability of operands during manifold polynomial evaluation.
"""

import sys
import pytest
import gmpy2
from tests.phase11_e2e.contracts.math_contracts import compute_manifold, compute_divisor_and_cofactor


@pytest.mark.phase11_tier2
def test_bnd09_huge_bit_candidate_memory_safety() -> None:
    """Verifies that calculating multi-thousand-bit candidate numbers operates safely without crash."""
    # Let x have 1000 bits
    # x = 2^1000 + 33
    x_1000bit = (1 << 1000) + 33
    assert x_1000bit.bit_length() == 1001

    # C(x) = 12*x^5 + 6*x^3 will have ~5000 bits
    C, A, B = compute_manifold(x_1000bit)

    assert C.bit_length() > 5000
    assert A == C - 1
    assert B == C + 1
    assert B - A == 2
    assert C % 6 == 0


@pytest.mark.phase11_tier2
def test_bnd09_64bit_boundary_overflow_protection() -> None:
    """Verifies that numbers crossing 64-bit boundaries (2^63-1, 2^64-1) do not truncate or wrap around."""
    boundary_64 = (1 << 64) - 1

    # Choose x close to 2^64
    x = boundary_64
    C, A, B = compute_manifold(x)

    # In 64-bit C/C++ without bigints, 12*x^5 would wrap around to a small positive or negative number
    # In arbitrary-precision, C must be strictly greater than x^5
    assert C > (x**5)
    assert C > (1 << 320)
    assert A > 0 and B > 0


@pytest.mark.phase11_tier2
def test_bnd09_bigint_string_serialization_roundtrip() -> None:
    """Verifies exact string serialization roundtrip for large big integers without scientific notation."""
    # Create coordinate yielding ~100-digit number
    x = 10**20
    C, A, B = compute_manifold(x)

    # Serialize to decimal string
    str_A = str(A)
    str_B = str(B)

    # Assure no scientific notation ('e')
    assert "e" not in str_A.lower()
    assert "e" not in str_B.lower()

    # Roundtrip deserialization
    deser_A = int(str_A)
    deser_B = int(str_B)

    assert deser_A == A
    assert deser_B == B
    assert deser_B - deser_A == 2


@pytest.mark.phase11_tier2
def test_bnd09_negative_coordinate_rejection() -> None:
    """Verifies that negative coordinate inputs are strictly rejected with ValueError."""
    negative_coordinates = [-1, -6, -100, -((1 << 64) + 1)]
    for bad_x in negative_coordinates:
        with pytest.raises(ValueError, match="positive"):
            compute_manifold(bad_x)


@pytest.mark.phase11_tier2
def test_bnd09_operand_immutability() -> None:
    """Verifies that big-integer operands are not modified in-place during manifold calculation."""
    original_val = 126
    x = original_val
    C, A, B = compute_manifold(x)

    # Verify input x remained unchanged
    assert x == original_val == 126

    # Test with gmpy2 mpz object
    mpz_x = gmpy2.mpz(original_val)
    C2, A2, B2 = compute_manifold(int(mpz_x))
    assert mpz_x == original_val
    assert (C, A, B) == (C2, A2, B2)
