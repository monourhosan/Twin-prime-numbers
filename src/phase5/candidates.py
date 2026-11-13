"""
Phase 5 Candidate Model: Smooth-Center Twin-Prime Families.
Defines smooth center F = 2^a * 3^b * 5^c * 7^d ..., center C(t) = F * t,
and twin candidates A(t) = C - 1, B(t) = C + 1.
Ensures exact algebraic constraints and size conditions for deterministic proofs.
"""

import math
import hashlib
from typing import Dict, List, Tuple, Any, Optional

class SmoothCenterFamily:
    """
    Represents a family of centers parameterized by prime factor exponents:
    F = 2^a * 3^b * 5^c * 7^d * ...
    Requires a >= 1 and b >= 1 so C is a multiple of 6.
    """
    def __init__(self, exponents: Dict[int, int], family_id: Optional[str] = None):
        self.exponents: Dict[int, int] = {p: exp for p, exp in exponents.items() if exp > 0}
        
        # Must contain 2^a (a >= 1) and 3^b (b >= 1)
        if self.exponents.get(2, 0) < 1:
            raise ValueError("SmoothCenterFamily must have exponent a >= 1 for prime 2 (even center)")
        if self.exponents.get(3, 0) < 1:
            raise ValueError("SmoothCenterFamily must have exponent b >= 1 for prime 3 (coprime to 3)")
        
        # Compute exact integer F and F_odd
        self.F: int = 1
        self.F_odd: int = 1
        for p, exp in sorted(self.exponents.items()):
            term = p ** exp
            self.F *= term
            if p != 2:
                self.F_odd *= term
        
        self.prime_factors: List[int] = sorted(self.exponents.keys())
        self.odd_prime_factors: List[int] = [p for p in self.prime_factors if p != 2]
        
        # Unique family ID
        if family_id:
            self.family_id = family_id
        else:
            exp_str = "_".join(f"p{p}e{e}" for p, e in sorted(self.exponents.items()))
            self.family_id = f"scca_{exp_str}"

    def candidate(self, t: int) -> "TwinPairCandidate":
        return TwinPairCandidate(family=self, t=t)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "exponents": self.exponents,
            "F_decimal": str(self.F),
            "F_odd_decimal": str(self.F_odd),
            "prime_factors": self.prime_factors,
            "odd_prime_factors": self.odd_prime_factors,
            "bits_F": self.F.bit_length(),
            "digits_F": len(str(self.F))
        }

class TwinPairCandidate:
    """
    Represents a concrete candidate pair (A, B) = (C - 1, C + 1) where C = F * t.
    """
    def __init__(self, family: SmoothCenterFamily, t: int):
        if t <= 0:
            raise ValueError(f"t must be a positive integer, got {t}")
        self.family: SmoothCenterFamily = family
        self.t: int = t
        self.C: int = family.F * t
        self.A: int = self.C - 1
        self.B: int = self.C + 1
        self.digits_A: int = len(str(self.A))
        self.digits_B: int = len(str(self.B))

    def validate_algebraic(self) -> Tuple[bool, Optional[str]]:
        """
        Validates core mathematical properties:
        1. B - A == 2
        2. A > 2 and both A, B are positive odd integers
        3. gcd(A, B) == 1
        4. For all prime factors p | F, gcd(A, p) == 1 and gcd(B, p) == 1
        """
        if self.B - self.A != 2:
            return False, f"Gap violation: B - A = {self.B - self.A} != 2"
        if self.A <= 2:
            return False, f"Lower candidate too small: A = {self.A} <= 2"
        if self.A % 2 == 0 or self.B % 2 == 0:
            return False, "Candidates are not odd integers"
        if math.gcd(self.A, self.B) != 1:
            return False, f"gcd(A, B) = {math.gcd(self.A, self.B)} != 1"
        
        # Divisibility immunity against all prime factors of F
        for p in self.family.prime_factors:
            if self.A % p == 0:
                return False, f"A is divisible by factor p={p} of F"
            if self.B % p == 0:
                return False, f"B is divisible by factor p={p} of F"
        
        return True, None

    def satisfies_size_condition(self) -> Tuple[bool, Optional[str]]:
        """
        Verifies theorem preconditions for rigorous primality proofs:
        - For B (Pocklington BLS Thm 4): Factored part F_odd > sqrt(B)
          Exact integer check: F_odd^2 > B
        - For A (Morrison / BLS Thm 17): Factored part F_odd > sqrt(A) + 1
          Exact integer check: (F_odd - 1)^2 > A
        """
        F_odd = self.family.F_odd
        # Exact integer checks avoiding float precision loss
        if F_odd * F_odd <= self.B:
            return False, f"Pocklington size condition failed: F_odd^2 <= B (F_odd={F_odd})"
        if (F_odd - 1) * (F_odd - 1) <= self.A:
            return False, f"Morrison size condition failed: (F_odd - 1)^2 <= A (F_odd={F_odd})"
        return True, None

    def canonical_hash(self) -> str:
        """Computes deterministic canonical SHA-256 hash of the exact integer pair."""
        rep = f"{self.A}:{self.B}".encode("ascii")
        return hashlib.sha256(rep).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family.family_id,
            "t": str(self.t),
            "C_decimal": str(self.C),
            "A_decimal": str(self.A),
            "B_decimal": str(self.B),
            "digits_A": self.digits_A,
            "digits_B": self.digits_B,
            "canonical_hash": self.canonical_hash()
        }
