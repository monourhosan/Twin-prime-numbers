"""Feature 17: Deterministic Dual-BLS Certification.

Verifies:
1. Pocklington BLS (1975) Theorem 4 deterministic primality proof for upper member B.
2. Morrison BLS (1975) Theorem 17 deterministic primality proof for lower member A.
3. Fermat base witness verification for all prime factors of F.
4. Lucas sequence parameter verification (P, Q=1, D) with (D/A) = -1.
5. Combined Dual-BLS certificate generation via Phase11ContractAdapter.prove_pair.
"""

from pathlib import Path
import pytest
import gmpy2
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_primorial_anchor,
    compute_factors_of_F,
    compute_divisor_and_cofactor,
    get_odd_part,
    prove_pocklington_upper,
    prove_morrison_lower,
    standalone_lucas_u,
)


@pytest.fixture
def sample_pair_and_factors() -> tuple[int, int, int, int, dict]:
    """Generates a small test candidate pair with factored divisor."""
    y = 3
    t = 21  # x = 6 * 21 = 126 (x >= 86, so Morrison bound holds)
    Sy, Sy_factors = compute_primorial_anchor(y)
    t_factors = {3: 1, 7: 1}
    factors_F = compute_factors_of_F(Sy_factors, t_factors)

    C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
    F, _ = compute_divisor_and_cofactor(126)
    F_odd = get_odd_part(F)

    return A, B, F, F_odd, factors_F


@pytest.mark.phase11_tier1
def test_f17_pocklington_upper_proof(sample_pair_and_factors: tuple) -> None:
    """Verifies Pocklington Theorem 4 succeeds on upper member B."""
    A, B, F, F_odd, factors_F = sample_pair_and_factors
    ok, witnesses = prove_pocklington_upper(B, F, factors_F)
    assert ok is True
    # Witnesses map each prime factor str to its base a
    for p in factors_F.keys():
        assert str(p) in witnesses
        assert witnesses[str(p)] > 1


@pytest.mark.phase11_tier1
def test_f17_morrison_lower_proof(sample_pair_and_factors: tuple) -> None:
    """Verifies Morrison Theorem 17 succeeds on lower member A."""
    A, B, F, F_odd, factors_F = sample_pair_and_factors
    ok, witnesses = prove_morrison_lower(A, F_odd, factors_F)
    assert ok is True
    assert "parameter_P" in witnesses
    assert witnesses["parameter_Q"] == 1
    assert "discriminant_D" in witnesses
    assert witnesses["jacobi_symbol"] == -1
    assert "lucas_zero_congruence" in witnesses


@pytest.mark.phase11_tier1
def test_f17_pocklington_witness_verification(sample_pair_and_factors: tuple) -> None:
    """Verifies witness a satisfies Pocklington conditions mod B."""
    A, B, F, F_odd, factors_F = sample_pair_and_factors
    ok, witnesses = prove_pocklington_upper(B, F, factors_F)
    assert ok is True

    # 1. a^(B-1) = 1 mod B and gcd(a^((B-1)/p) - 1, B) = 1
    for p in factors_F.keys():
        a = witnesses[str(p)]
        assert gmpy2.powmod(a, B - 1, B) == 1
        exp = (B - 1) // p
        val = (gmpy2.powmod(a, exp, B) - 1) % B
        assert gmpy2.gcd(val, B) == 1


@pytest.mark.phase11_tier1
def test_f17_morrison_lucas_witness_verification(sample_pair_and_factors: tuple) -> None:
    """Verifies Lucas parameters (P, Q=1, D) satisfy Jacobi symbol and rank conditions."""
    A, B, F, F_odd, factors_F = sample_pair_and_factors
    ok, witnesses = prove_morrison_lower(A, F_odd, factors_F)
    assert ok is True

    P = witnesses["parameter_P"]
    D = witnesses["discriminant_D"]

    # 1. Jacobi symbol (D / A) == -1
    assert gmpy2.jacobi(D, A) == -1

    # 2. U_(A+1) = 0 mod A
    u_full = standalone_lucas_u(A + 1, P, A)
    assert u_full == 0

    # 3. gcd(U_((A+1)/q), A) == 1 for all odd q | F_odd
    for q in factors_F.keys():
        if q == 2:
            continue
        u_sub = standalone_lucas_u((A + 1) // q, P, A)
        assert gmpy2.gcd(u_sub, A) == 1


@pytest.mark.phase11_tier1
def test_f17_dual_bls_certification_combined() -> None:
    """Verifies combined Dual-BLS certificate generation via Phase11ContractAdapter."""
    cert = Phase11ContractAdapter.prove_pair(y=3, t=21)
    assert "Morrison" in cert["proof_method_lower"]
    assert "Pocklington" in cert["proof_method_upper"]
    assert cert["witnesses_lower"]["parameter_Q"] == 1
    assert len(cert["witnesses_upper"]) > 0
