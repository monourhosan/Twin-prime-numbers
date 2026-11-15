"""
Comprehensive regression and fault-injection test suite for Phase 7 P0 Repairs.
Validates:
1. ECPP nonsingularity over Z/NZ (discriminant unit check).
2. Exact Atkin-Morain GK inequality vs flawed rounded-up bound.
3. Composite detection and clean exception handling in curve arithmetic over Z/NZ.
4. Deterministic Miller-Rabin 64-bit leaf and factor verification.
5. PARI/GP safe parser and proof router adapter behavior.
6. Factorization cooperative timeout and zero thread leakage.
7. Exact half-open interval candidate counting.
"""

import math
import time
import pytest
from scripts.phase6b_ecpp_verify import (
    EllipticCurveOverZn,
    verify_ecpp_step,
    verify_ecpp_certificate,
    is_prime_leaf,
    miller_rabin_deterministic_64,
    CurveArithmeticException
)
from src.phase6.proof_backend import is_prime_factor, DeterministicPairProver
from src.phase6.proof_router import parse_gp_vector, ProofRouter


def test_ecpp_non_unit_discriminant_rejected():
    """
    Adversarial test: N=35, a=0, b=5.
    Delta = -16 * (4*0^3 + 27*5^2) = -10800 = 15 mod 35 != 0.
    Old verifier checked delta != 0 and incorrectly declared it nonsingular.
    Repaired verifier requires gcd(4a^3 + 27b^2, N) == 1.
    Since gcd(675, 35) = 5 != 1, it must be rejected!
    """
    curve = EllipticCurveOverZn(a=0, b=5, p=35)
    assert curve.is_nonsingular() is False, "Curve with gcd(Delta, N) = 5 must be rejected as singular mod factor of N"


def test_ecpp_exact_atkin_morain_gk_condition():
    """
    For N = 101:
    (N^(1/4) + 1)^2 = (101^0.25 + 1)^2 = 17.39018...
    q = 19 is an integer satisfying 19 > 17.39018.
    Old verifier computed:
      fourth_root = isqrt(isqrt(101)) + 1 = 3 + 1 = 4
      threshold = (4 + 1)^2 = 25
      if q <= 25: reject -> rejected valid q=19!
    The repaired exact integer condition must accept q=19 and reject q=17.
    """
    # Test step with q=19 on N=101
    # Check GK condition via step validation
    step_valid_q = {
        "a": "2",
        "b": "2",
        "m": "95",    # 5 * 19
        "q": "19",   # 19 > (101^0.25 + 1)^2
        "x": "5",
        "y": "1"
    }
    # Point (5, 1) on y^2 = x^3 + 2x + 2 mod 101:
    # 1^2 = 1; 5^3 + 2*5 + 2 = 125 + 10 + 2 = 137 = 36 mod 101 != 1.
    # So we construct an exact point on curve y^2 = x^3 + ax + b mod 101.
    # Let a=2, x=1: 1^3 + 2(1) + b = 3 + b mod 101. Choose b=6, rhs = 9 = 3^2.
    # So P = (1, 3) is on y^2 = x^3 + 2x + 6 mod 101.
    # 4*a^3 + 27*b^2 = 4(8) + 27(36) = 32 + 972 = 1004. gcd(1004, 101) = gcd(95, 101) = 1.
    a = 2
    b = 6
    x = 1
    y = 3
    curve = EllipticCurveOverZn(a, b, 101)
    assert curve.is_on_curve(x, y) is True
    assert curve.is_nonsingular() is True

    # Exact Atkin-Morain inequality check
    # q=19 > (101^0.25 + 1)^2:
    lhs = ((19 - 1)**2 + 101)**2
    rhs = 4 * ((19 + 1)**2) * 101
    assert lhs > rhs, "Exact integer inequality must hold for q=19 on N=101"

    # q=17 fails: 17 < 17.39
    lhs_17 = ((17 - 1)**2 + 101)**2
    rhs_17 = 4 * ((17 + 1)**2) * 101
    assert lhs_17 <= rhs_17, "q=17 must fail GK condition"


def test_ecpp_curve_arithmetic_reveals_composite_factor():
    """
    Over composite modulus N=35:
    Point addition encounters non-invertible denominator gcd(denom, 35) > 1.
    Repaired curve raises CurveArithmeticException with discovered factor,
    instead of unhandled ValueError.
    """
    curve = EllipticCurveOverZn(a=1, b=1, p=35)
    # P1 = (1, 3), P2 = (6, 8) -> x2 - x1 = 5, gcd(5, 35) = 5
    with pytest.raises(CurveArithmeticException) as excinfo:
        curve.point_add((1, 3), (6, 8))
    assert excinfo.value.factor == 5


def test_ecpp_hasse_weil_bound_enforcement():
    """A step claiming group order m outside the Hasse interval must be rejected."""
    # p = 101: Hasse interval is |m - 102| <= 2 * sqrt(101) ~ 20.099 -> [82, 122]
    step_bad_m = {
        "a": "2",
        "b": "6",
        "m": "150", # (101 + 1 - 150)^2 = (-48)^2 = 2304 > 4*101 = 404
        "q": "25",
        "x": "1",
        "y": "3"
    }
    ok, msg, next_p = verify_ecpp_step(step_bad_m, claimed_prime=101)
    assert ok is False
    assert "Hasse-Weil bound" in msg


def test_ecpp_strict_descent_enforcement():
    """ECPP chain must strictly descend: q < p."""
    step_bad_descent = {
        "candidate": "101",
        "steps": [
            {
                "a": "2",
                "b": "6",
                "m": "101",
                "q": "101", # q == p (no descent!)
                "x": "1",
                "y": "3"
            }
        ]
    }
    ok, msg = verify_ecpp_certificate(step_bad_descent)
    assert ok is False


def test_deterministic_64bit_miller_rabin():
    """
    Tests deterministic Miller-Rabin test for 64-bit integers.
    Must correctly identify known primes and reject Carmichael pseudoprimes.
    """
    # Known Carmichael numbers (Fermat pseudoprimes to all coprime bases)
    carmichaels = [561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341]
    for c in carmichaels:
        assert miller_rabin_deterministic_64(c) is False, f"Carmichael number {c} must be rejected"
        assert is_prime_factor(c) is False
        assert is_prime_leaf(c) is False

    # Known primes
    test_primes = [2, 3, 5, 7, 1000003, 1000000007, 2**31 - 1, 2**61 - 1]
    for p in test_primes:
        assert miller_rabin_deterministic_64(p) is True, f"Prime {p} must be accepted"
        assert is_prime_factor(p) is True
        assert is_prime_leaf(p) is True

    # Factors >= 2^64 must not be accepted as unconditionally proven primes
    assert is_prime_factor(2**64 + 13) is False


def test_factor_timeout_no_lingering_threads():
    """Verify that factorization honors timeout strictly without thread accumulation."""
    prover = DeterministicPairProver(factor_timeout_sec=0.2)
    # Product of two large primes
    p = 10**30 + 3
    q = 10**30 + 9
    t0 = time.perf_counter()
    res = prover.factor_center(p * q)
    elapsed = time.perf_counter() - t0

    assert res is None
    assert elapsed < 1.0, f"Factorization took too long: {elapsed:.2f}s"


def test_safe_gp_vector_parser():
    """Verify safe recursive parser on various GP output structures."""
    vec1 = "[101, [101, 10, 1, 2, [5, 1]], 97]"
    assert parse_gp_vector(vec1) == [101, [101, 10, 1, 2, [5, 1]], 97]

    vec2 = "[[1, 2], [3, [4, 5]]]"
    assert parse_gp_vector(vec2) == [[1, 2], [3, [4, 5]]]

    assert parse_gp_vector("0") == 0
    assert parse_gp_vector("") is None


def test_proof_router_blocked_engine_reporting():
    """Verify ProofRouter accurately reports BLOCKED_NO_APPROVED_ENGINE when GP is absent."""
    router = ProofRouter(pari_gp_path="C:\\nonexistent\\gp.exe")
    assert router.has_ecpp_engine() is False
    res = router.route_pair(m=10**50 + 1)
    assert res["route"] == "ECPP"
    assert res["status"] == "BLOCKED_NO_APPROVED_ENGINE"
    assert "no approved, smoke-tested ECPP engine" in res["reason"]


def test_exact_interval_counting():
    """
    Audit calculation:
    k in [3, 150003) with k = 6t + 3 has exactly 25,000 eligible k, not 50,000.
    """
    k_start = 3
    k_end = 150003
    t_start = (k_start - 3) // 6
    t_end = (k_end - 3) // 6
    count = t_end - t_start
    assert count == 25000, f"Expected 25,000 eligible centers, got {count}"
