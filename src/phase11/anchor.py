"""Phase 11 Primorial Anchor and Factorization Tracking.

Manages primorial anchor S_y = product_{p <= y} p, exact prime factorization
records for algebraic divisor F(x) = 6*x^3, and super-root dominance verification.
"""


import gmpy2
from sympy.ntheory import factorint, primerange


def compute_primorial_anchor(y: int) -> tuple[int, dict[int, int]]:
    """Computes S_y = prod_{p <= y} p and its exact square-free factorization.

    Requires y >= 3 so that 6 | S_y.
    """
    if y < 3:
        raise ValueError(f"Primorial anchor y must be >= 3, got {y}")
    primes = list(primerange(2, y + 1))
    Sy = 1
    factors: dict[int, int] = {}
    for p in primes:
        Sy *= p
        factors[p] = 1
    if Sy % 6 != 0:
        raise ValueError(f"S_y must be divisible by 6, got {Sy}")
    return Sy, factors


def compute_factors_of_F(
    Sy_factors: dict[int, int],
    t_factors: dict[int, int]
) -> dict[int, int]:
    """Computes exact prime factorization of F(x) = 6 * x^3 where x = S_y * t.

    F = 2 * 3 * (S_y * t)^3 = 2^(1 + 3*e_2) * 3^(1 + 3*e_3) * prod_{p > 3} p^(3*e_p).
    Analytically tracks factors with zero large-integer factoring needed.
    """
    all_primes = set(Sy_factors.keys()) | set(t_factors.keys()) | {2, 3}
    factors_F: dict[int, int] = {}
    for p in sorted(all_primes):
        e_Sy = Sy_factors.get(p, 0)
        e_t = t_factors.get(p, 0)
        e_x = e_Sy + e_t
        exp = 3 * e_x
        if p in (2, 3):
            exp += 1
        if exp > 0:
            factors_F[p] = exp
    return factors_F


class PrimorialAnchor:
    """Manages anchor properties and exact prime factorization records."""

    def __init__(self, y: int):
        if y < 3:
            raise ValueError(f"Anchor y must be >= 3, got {y}")
        self.y = y
        self.S_y, self.factors_Sy = compute_primorial_anchor(y)
        self.primes = sorted(self.factors_Sy.keys())
        self.num_primes = len(self.primes)
        self.digits = len(str(self.S_y))

    def compute_x(self, t: int) -> int:
        """Returns coordinate x = S_y * t."""
        return self.S_y * t

    def factor_t(self, t: int) -> dict[int, int]:
        """Factors integer multiplier t using SymPy factorint."""
        if t <= 1:
            return {}
        return dict(factorint(t))

    def get_F_factorization(self, t: int) -> dict[int, int]:
        """Returns exact prime factorization of F(x) = 6 * (S_y * t)^3."""
        t_factors = self.factor_t(t)
        return compute_factors_of_F(self.factors_Sy, t_factors)

    def check_morrison_dominance(self, t: int) -> tuple[bool, int, int]:
        """Evaluates Morrison dominance condition: (F_odd - 1)^2 > A(x).

        Returns (is_satisfied, margin, x).
        """
        x = self.compute_x(t)
        x_mpz = gmpy2.mpz(x)
        F = 6 * (x_mpz ** 3)
        tz = (int(F) & -int(F)).bit_length() - 1
        F_odd = int(F) >> tz
        C = 12 * (x_mpz ** 5) + 6 * (x_mpz ** 3)
        A = int(C - 1)
        lhs = (F_odd - 1) ** 2
        margin = lhs - A
        return (margin > 0, margin, x)
