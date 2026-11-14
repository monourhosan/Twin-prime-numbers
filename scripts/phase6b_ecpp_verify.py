"""
Independent Elliptic Curve Primality Proving (ECPP) Certificate Verifier.
Implements the Goldwasser-Kilian-Atkin primality certificate verification theorem.
Verifies elliptic curve nonsingularity, point on curve, Hasse-Weil bounds,
group order scalar multiplication, non-identity subgroup conditions, and downward chain recursion.
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

class EllipticCurveOverFp:
    """Weierstrass curve y^2 = x^3 + ax + b (mod p)."""
    def __init__(self, a: int, b: int, p: int):
        self.a = a % p
        self.b = b % p
        self.p = p

    def is_nonsingular(self) -> bool:
        """Delta = -16*(4*a^3 + 27*b^2) != 0 mod p."""
        delta = (-16 * (4 * pow(self.a, 3, self.p) + 27 * pow(self.b, 2, self.p))) % self.p
        return delta != 0

    def is_on_curve(self, x: int, y: int) -> bool:
        """Checks y^2 = x^3 + ax + b mod p."""
        lhs = pow(y, 2, self.p)
        rhs = (pow(x, 3, self.p) + self.a * x + self.b) % self.p
        return lhs == rhs

    def point_add(self, P1: Optional[Tuple[int, int]], P2: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Affine point addition on E(F_p). None represents point at infinity (O)."""
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
            # Point doubling
            inv = pow(2 * y1, -1, p)
            lam = ((3 * x1 * x1 + self.a) * inv) % p
        else:
            inv = pow(x2 - x1, -1, p)
            lam = ((y2 - y1) * inv) % p

        x3 = (lam * lam - x1 - x2) % p
        y3 = (lam * (x1 - x3) - y1) % p
        return x3, y3

    def scalar_mul(self, k: int, P: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Double-and-add scalar multiplication k*P."""
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

def is_prime_leaf(n: int) -> bool:
    """Exact check for small prime terminal leaves (< 10^7)."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    while d * d <= n:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    return True

def verify_ecpp_step(step: Dict[str, Any], claimed_prime: int) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Verifies a single Goldwasser-Kilian-Atkin ECPP step:
    p: prime to prove
    a, b: curve parameters
    m: group order |E(F_p)|
    q: large prime factor of m
    P = (x, y): generator point
    """
    p = claimed_prime
    a = int(step["a"])
    b = int(step["b"])
    m = int(step["m"])
    q = int(step["q"])
    x = int(step["x"])
    y = int(step["y"])

    # 1. Curve nonsingularity
    curve = EllipticCurveOverFp(a, b, p)
    if not curve.is_nonsingular():
        return False, f"Curve y^2 = x^3 + {a}x + {b} is singular mod {p}", None

    # 2. Point validity on curve
    if not curve.is_on_curve(x, y):
        return False, f"Point ({x}, {y}) is not on curve mod {p}", None

    # 3. Hasse-Weil bound: (sqrt(p) - 1)^2 < m < (sqrt(p) + 1)^2
    sqrt_p = math.isqrt(p)
    low_bound = p + 1 - 2 * (sqrt_p + 1)
    high_bound = p + 1 + 2 * (sqrt_p + 1)
    if not (low_bound < m < high_bound):
        return False, f"Group order m={m} violates Hasse-Weil bound for p={p}", None

    # 4. Divisibility: q must divide m
    if m % q != 0:
        return False, f"Claimed factor q={q} does not divide group order m={m}", None

    # 5. Atkin-Morain inequality: q > (p^(1/4) + 1)^2
    # Equivalent to q^2 > (sqrt(p) + 2*p^(1/4) + 1)^2 or check integer 4th root:
    # Goldwasser-Kilian condition: q > (p^(1/4) + 1)^2
    fourth_root = int(math.isqrt(math.isqrt(p))) + 1
    threshold = (fourth_root + 1) ** 2
    if q <= threshold:
        return False, f"Prime factor q={q} does not satisfy Atkin-Morain threshold {threshold}", None

    # 6. Scalar multiplication check:
    # m * P == O mod p
    # (m / q) * P != O mod p
    P = (x, y)
    m_div_q = m // q
    Q = curve.scalar_mul(m_div_q, P)
    if Q is None:
        return False, f"(m/q)*P evaluated to point at infinity; subgroup order condition failed", None

    mP = curve.scalar_mul(q, Q)
    if mP is not None:
        return False, f"m*P != O mod p; group order m={m} invalid for point P", None

    # Step is mathematically sound! Next prime to verify recursively is q.
    return True, None, q

def verify_ecpp_certificate(cert_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verifies full ECPP certificate chain down to terminal leaf prime.
    """
    root_p = int(cert_data["candidate"])
    steps = cert_data.get("steps", [])
    
    current_p = root_p
    for idx, step in enumerate(steps):
        ok, err, next_p = verify_ecpp_step(step, current_p)
        if not ok:
            return False, f"Step {idx} verification failed for prime {current_p}: {err}"
        current_p = next_p

    # Terminal leaf verification
    leaf_p = current_p
    if leaf_p >= 10000000:
        return False, f"ECPP chain terminated at unproven large leaf {leaf_p} (must be < 10^7)"
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

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

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
