"""
Unit tests for independent ECPP certificate verifier.
Tests elliptic curve arithmetic, group order conditions, and tamper resistance.
"""

from scripts.phase6b_ecpp_verify import EllipticCurveOverFp, verify_ecpp_certificate, is_prime_leaf

def test_elliptic_curve_arithmetic():
    """Verify group law arithmetic on a small known prime curve."""
    # p = 17, y^2 = x^3 + 2x + 2 mod 17
    # Points on curve: (5, 1) since 1^2 = 1, 5^3 + 2*5 + 2 = 125 + 10 + 2 = 137 = 8*17 + 1 = 1 mod 17.
    curve = EllipticCurveOverFp(a=2, b=2, p=17)
    assert curve.is_nonsingular() is True
    assert curve.is_on_curve(5, 1) is True
    assert curve.is_on_curve(5, 16) is True # -1 = 16 mod 17
    assert curve.is_on_curve(5, 2) is False

    # Point doubling: 2 * (5, 1)
    two_P = curve.point_add((5, 1), (5, 1))
    assert two_P is not None
    assert curve.is_on_curve(two_P[0], two_P[1]) is True

    # Scalar multiplication matches repeated addition
    three_P = curve.scalar_mul(3, (5, 1))
    assert three_P == curve.point_add(two_P, (5, 1))

    # P + (-P) = O (None)
    inv_P = (5, 16)
    assert curve.point_add((5, 1), inv_P) is None

def test_prime_leaf_check():
    """Verify trial division for small prime leaves."""
    assert is_prime_leaf(2) is True
    assert is_prime_leaf(3) is True
    assert is_prime_leaf(17) is True
    assert is_prime_leaf(101) is True
    assert is_prime_leaf(100) is False
    assert is_prime_leaf(1) is False

def test_ecpp_tamper_detection():
    """Verify that verifier rejects altered certificates."""
    dummy_cert = {
        "candidate": "1009",
        "steps": [
            {
                "a": "2",
                "b": "2",
                "m": "1000", # Fake order
                "q": "100", # Fake composite factor
                "x": "5",
                "y": "1"
            }
        ]
    }
    ok, err = verify_ecpp_certificate(dummy_cert)
    assert ok is False
    assert err is not None
