"""
Independent Elliptic Curve Primality Proving (ECPP) Certificate Verifier.
Implements the Goldwasser-Kilian-Atkin primality certificate verification theorem.
Verifies elliptic curve nonsingularity over Z/NZ, point on curve, Hasse-Weil bounds,
group order scalar multiplication, non-identity subgroup conditions, and downward chain recursion.
Strictly sound over a possibly composite modulus N.
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False


def miller_rabin_deterministic_64(n: int) -> bool:
    """
    Jiang & Deng (2014) / Sinclair (2011) deterministic Miller-Rabin test
    for n < 2^64 using 7 proven bases:
    [2, 325, 9375, 28178, 450775, 9780504, 1795265022].
    Provably zero pseudoprimes below 2^64.
    """
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for sp in small_primes:
        if n == sp:
            return True
        if n % sp == 0:
            return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


class CurveArithmeticException(Exception):
    """Raised when an exceptional condition (e.g. non-invertible denominator revealing a factor) occurs."""
    def __init__(self, message: str, factor: Optional[int] = None):
        super().__init__(message)
        self.factor = factor


class EllipticCurveOverZn:
    """
    Weierstrass curve y^2 = x^3 + ax + b over ring Z/NZ.
    Does NOT assume N is prime; rigorously checks unit invertibility and reports factors.
    """
    def __init__(self, a: int, b: int, p: int):
        self.a = a % p
        self.b = b % p
        self.p = p # Represents modulus N

    def is_nonsingular(self) -> bool:
        """
        Check that Delta = -(4*a^3 + 27*b^2) is invertible in Z/NZ.
        Equivalently, gcd(4*a^3 + 27*b^2, N) == 1.
        """
        disc = (4 * pow(self.a, 3, self.p) + 27 * pow(self.b, 2, self.p)) % self.p
        return math.gcd(disc, self.p) == 1

    def is_on_curve(self, x: int, y: int) -> bool:
        """Checks y^2 = x^3 + ax + b mod N."""
        lhs = pow(y, 2, self.p)
        rhs = (pow(x, 3, self.p) + self.a * x + self.b) % self.p
        return lhs == rhs

    def point_add(self, P1: Optional[Tuple[int, int]], P2: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Affine point addition on E(Z/NZ). None represents point at infinity (O)."""
        if P1 is None:
            return P2
        if P2 is None:
            return P1

        x1, y1 = P1
        x2, y2 = P2

        p = self.p
        if x1 == x2:
            if (y1 + y2) % p == 0:
                return None # P + (-P) = O
            # Point doubling: denominator is 2 * y1
            denom = (2 * y1) % p
            g = math.gcd(denom, p)
            if g > 1:
                if g < p:
                    raise CurveArithmeticException(f"Non-trivial factor {g} of {p} discovered during point doubling", factor=g)
                return None
            inv = pow(denom, -1, p)
            lam = ((3 * x1 * x1 + self.a) * inv) % p
        else:
            denom = (x2 - x1) % p
            g = math.gcd(denom, p)
            if g > 1:
                if g < p:
                    raise CurveArithmeticException(f"Non-trivial factor {g} of {p} discovered during point addition", factor=g)
                return None
            inv = pow(denom, -1, p)
            lam = ((y2 - y1) * inv) % p

        x3 = (lam * lam - x1 - x2) % p
        y3 = (lam * (x1 - x3) - y1) % p
        return x3, y3

    def scalar_mul(self, k: int, P: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Double-and-add scalar multiplication k*P over Z/NZ."""
        if k == 0 or P is None:
            return None
        if k < 0:
            P = (P[0], (-P[1]) % self.p)
            k = -k

        R = None
        current = P
        while k > 0:
            if k & 1:
                R = self.point_add(R, current)
            current = self.point_add(current, current)
            k >>= 1
        return R


# Backwards compatibility alias
EllipticCurveOverFp = EllipticCurveOverZn


def is_prime_leaf(n: int) -> bool:
    """Exact check for terminal leaf prime using deterministic Miller-Rabin for n < 2^64."""
    if n < (1 << 64):
        return miller_rabin_deterministic_64(n)
    return False


def verify_ecpp_step(step: Dict[str, Any], claimed_prime: int) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Verifies a single Goldwasser-Kilian-Atkin ECPP step:
    p: integer to prove prime (modulus N)
    a, b: curve parameters
    m: claimed group order
    q: large prime factor of m
    P = (x, y): generator point
    """
    p = claimed_prime

    if p <= 3 or p % 2 == 0 or p % 3 == 0:
        return False, f"Modulus p={p} must be odd integer > 3 and coprime to 6", None

    try:
        a = int(step["a"])
        b = int(step["b"])
        m = int(step["m"])
        q = int(step["q"])
        x = int(step["x"])
        y = int(step["y"])
    except (KeyError, ValueError, TypeError) as e:
        return False, f"Malformed step schema: {e}", None

    # 1. Curve nonsingularity over Z/pZ: gcd(4a^3 + 27b^2, p) == 1
    curve = EllipticCurveOverZn(a, b, p)
    if not curve.is_nonsingular():
        return False, f"Curve y^2 = x^3 + {a}x + {b} is singular or has non-unit discriminant mod {p}", None

    # 2. Point validity on curve
    if not curve.is_on_curve(x, y):
        return False, f"Point ({x}, {y}) is not on curve mod {p}", None

    # 3. Exact Hasse-Weil bound: (p + 1 - m)^2 <= 4*p
    t_frob = p + 1 - m
    if t_frob * t_frob > 4 * p:
        return False, f"Group order m={m} violates exact Hasse-Weil bound (t^2 = {t_frob**2} > 4*p = {4*p})", None

    # 4. Divisibility: q must divide m, 1 < q < p
    if q <= 1 or q >= p:
        return False, f"Factor q={q} out of valid bounds (1 < q < {p})", None
    if m <= 0 or m % q != 0:
        return False, f"Claimed factor q={q} does not divide group order m={m}", None

    # 5. Exact Goldwasser-Kilian-Atkin inequality: q > (p^(1/4) + 1)^2
    # Exact integer test: q > 1 and (q - 1)^2 > p and ((q - 1)^2 + p)^2 > 4 * (q + 1)^2 * p
    if (q - 1)**2 <= p:
        return False, f"Factor q={q} fails GK-Atkin lower condition ((q-1)^2 <= p={p})", None
    lhs = ((q - 1)**2 + p)**2
    rhs = 4 * ((q + 1)**2) * p
    if lhs <= rhs:
        return False, f"Prime factor q={q} does not satisfy exact Atkin-Morain threshold q > (p^(1/4)+1)^2", None

    # 6. Scalar multiplication check:
    # Q = (m / q) * P != O mod p
    # q * Q == m * P == O mod p
    P = (x, y)
    m_div_q = m // q
    try:
        Q = curve.scalar_mul(m_div_q, P)
        if Q is None:
            return False, f"(m/q)*P evaluated to point at infinity; subgroup order condition failed", None

        mP = curve.scalar_mul(q, Q)
        if mP is not None:
            return False, f"m*P != O mod p; group order m={m} invalid for point P", None
    except CurveArithmeticException as ce:
        return False, f"Modulus {p} is composite: {ce}", None

    # Step is mathematically sound! Next prime to verify recursively is q.
    return True, None, q


def verify_ecpp_certificate(cert_data: Dict[str, Any], expected_prime: Optional[int] = None) -> Tuple[bool, str]:
    """
    Verifies full ECPP certificate chain down to terminal leaf prime.
    """
    try:
        root_p = int(cert_data["candidate"])
    except (KeyError, ValueError, TypeError):
        return False, "Certificate missing or invalid 'candidate' integer field"

    if expected_prime is not None and root_p != expected_prime:
        return False, f"Certificate candidate {root_p} does not match expected integer {expected_prime}"

    steps = cert_data.get("steps")
    if not isinstance(steps, list):
        return False, "Certificate 'steps' field must be a list"

    current_p = root_p
    prev_p = None
    for idx, step in enumerate(steps):
        ok, err, next_p = verify_ecpp_step(step, current_p)
        if not ok:
            return False, f"Step {idx} verification failed for prime {current_p}: {err}"
        if next_p is None or next_p >= current_p:
            return False, f"Step {idx} does not strictly descend: {next_p} >= {current_p}"
        current_p = next_p

    # Terminal leaf verification
    leaf_p = current_p
    if leaf_p >= (1 << 64):
        return False, f"ECPP chain terminated at unproven large leaf {leaf_p} (must be < 2^64 or recurse)"
    if not is_prime_leaf(leaf_p):
        return False, f"Terminal leaf {leaf_p} is not prime"

    return True, f"ECPP Certificate verified unconditionally. Chain depth: {len(steps)}, Leaf: {leaf_p}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/phase6b_ecpp_verify.py <cert_file.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File {path} not found.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {path}: {e}")
        sys.exit(1)

    ok, msg = verify_ecpp_certificate(data)
    if ok:
        print(f"VERIFICATION SUCCESS: {path.name}")
        print(f"  {msg}")
        sys.exit(0)
    else:
        print(f"VERIFICATION FAILURE: {path.name}")
        print(f"  {msg}")
        sys.exit(2)


if __name__ == "__main__":
    main()
