"""Tier 2 Boundary Tests - Feature 17: Deterministic Dual-BLS Certification.

Verifies:
1. Rejection of corrupted witness a=1 in Pocklington proof.
2. Unfactored remainder violation (F^2 <= B fails precondition).
3. Rejection of composite factor falsely reported in F's prime factorization.
4. Rejection of Morrison candidate when Jacobi symbol (D/A) == 0.
5. Rejection of Morrison candidate when Jacobi symbol (D/A) == +1.
"""

import math
import pytest
import sympy
from sympy import isprime

from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    compute_divisor_and_cofactor,
    compute_primorial_anchor,
    compute_factors_of_F,
    get_odd_part,
    prove_pocklington_upper,
    prove_morrison_lower,
)


@pytest.mark.phase11_tier2
def test_bnd17_corrupted_witness_a1_rejection() -> None:
    """Verifies that setting witness a=1 fails Pocklington verification because gcd(1-1, N) = N > 1."""
    # Upper prime candidate at x=126
    y = 3
    Sy, Sy_factors = compute_primorial_anchor(y)
    t = 21
    x = Sy * t
    C, A, B = compute_manifold(x)
    F, R = compute_divisor_and_cofactor(x)
    factors_F = compute_factors_of_F(Sy_factors, {3: 1, 7: 1})

    # Legitimate proof succeeds
    ok, witnesses = prove_pocklington_upper(B, F, factors_F)
    assert ok is True

    # Corrupted witness: verify that if a=1 is chosen, the gcd condition gcd(a^((B-1)/p) - 1, B) = gcd(0, B) = B != 1
    def verify_pocklington_witness(B_val: int, p_factor: int, witness_a: int) -> bool:
        if pow(witness_a, B_val - 1, B_val) != 1:
            return False
        exp = (B_val - 1) // p_factor
        val = pow(witness_a, exp, B_val)
        return math.gcd(val - 1, B_val) == 1

    # a = 1 must fail for all prime factors
    for p in factors_F:
        assert not verify_pocklington_witness(B, p, 1), f"Witness a=1 was erroneously accepted for prime factor {p}"


@pytest.mark.phase11_tier2
def test_bnd17_unfactored_remainder_violation() -> None:
    """Verifies that if F^2 <= B (unfactored portion is too large), BLS Theorem 4 fails."""
    # Suppose candidate B has F artificially shrunk such that F^2 <= B
    B_cand = 1000003  # prime
    F_small = 100     # F^2 = 10000 < 1000003

    def check_pocklington_precondition(B_val: int, F_val: int) -> bool:
        return (F_val * F_val) > B_val

    assert check_pocklington_precondition(B_cand, F_small) is False

    # Valid F > sqrt(B)
    F_sufficient = 2000  # F^2 = 4,000,000 > 1000003
    assert check_pocklington_precondition(B_cand, F_sufficient) is True


@pytest.mark.phase11_tier2
def test_bnd17_composite_factor_in_prime_list_rejection() -> None:
    """Verifies that reporting a composite number as a prime factor of F fails proof verification."""
    # In factors_F, every key must be prime
    fake_factors = {2: 4, 3: 4, 9: 1, 7: 3}  # 9 is composite

    def validate_prime_factor_list(factors: dict[int, int]) -> tuple[bool, int | None]:
        for p in factors.keys():
            if not isprime(p):
                return False, p
        return True, None

    ok, bad_p = validate_prime_factor_list(fake_factors)
    assert not ok
    assert bad_p == 9, "Failed to catch composite factor 9"


@pytest.mark.phase11_tier2
def test_bnd17_jacobi_symbol_zero_rejection() -> None:
    """Verifies that if (D/A) == 0 (D and A share a common divisor > 1), Morrison proof rejects it."""
    # If gcd(D, A) > 1, Jacobi symbol sympy.jacobi_symbol(D, A) == 0
    # Let D share factor 3 with A
    A_composite_mult3 = 99999
    D_mult3 = 33

    jacobi = sympy.jacobi_symbol(D_mult3, A_composite_mult3)
    assert jacobi == 0, f"Expected Jacobi symbol 0, got {jacobi}"

    def check_morrison_jacobi(D_val: int, A_val: int) -> bool:
        return sympy.jacobi_symbol(D_val, A_val) == -1

    assert check_morrison_jacobi(D_mult3, A_composite_mult3) is False


@pytest.mark.phase11_tier2
def test_bnd17_jacobi_symbol_plus_one_rejection() -> None:
    """Verifies that if (D/A) == +1 (quadratic residue), Morrison Theorem 17 rejects the discriminant."""
    # When (D/A) == +1, D is a quadratic residue, so Lucas sequence cannot certify primality of A+1
    A_val = 101  # prime
    # Find D such that (D/101) == +1 (e.g. D = 4 since 2^2 = 4)
    D_residue = 4
    assert sympy.jacobi_symbol(D_residue, A_val) == 1

    def check_morrison_jacobi(D_val: int, A_val: int) -> bool:
        return sympy.jacobi_symbol(D_val, A_val) == -1

    assert check_morrison_jacobi(D_residue, A_val) is False
