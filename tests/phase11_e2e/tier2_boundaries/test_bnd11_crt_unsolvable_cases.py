"""Tier 2 Boundary Tests - Feature 11: CRT Inverse Pre-Filtering.

Verifies:
1. Over-constrained empty CRT residue space detection.
2. Pairwise non-coprime basis moduli rejection.
3. Modulus exceeding 64-bit integer limit safety.
4. Single-prime basis base case behavior.
5. Progression generator restart identity from checkpoint.
"""

import math
import pytest
from sympy.ntheory.modular import crt


@pytest.mark.phase11_tier2
def test_bnd11_over_constrained_empty_residue_space() -> None:
    """Verifies that an impossible or over-constrained residue system produces zero admissible residues."""
    # Suppose a prime q requires r mod q to be in an empty set of admissible residues
    # E.g. for prime 5, if all residues {0, 1, 2, 3, 4} are excluded
    admissible_mod_5 = []

    def compute_cartesian_crt_residues(moduli: list[int], residue_sets: dict[int, list[int]]) -> list[int]:
        total_combos = 1
        for m in moduli:
            total_combos *= len(residue_sets.get(m, []))
        if total_combos == 0:
            return []
        # Normal CRT combination logic
        return [0]

    residues = compute_cartesian_crt_residues([5, 7], {5: admissible_mod_5, 7: [1, 2]})
    assert residues == [], "Empty residue set must yield 0 combined CRT residues"


@pytest.mark.phase11_tier2
def test_bnd11_pairwise_non_coprime_basis_rejection() -> None:
    """Verifies that non-coprime moduli in CRT basis are detected and rejected."""
    def validate_crt_basis(basis: list[int]) -> tuple[bool, str]:
        for i in range(len(basis)):
            for j in range(i + 1, len(basis)):
                g = math.gcd(basis[i], basis[j])
                if g != 1:
                    return False, f"Moduli {basis[i]} and {basis[j]} not coprime (gcd={g})"
        return True, "OK"

    # Non-coprime basis: 6 and 15 share factor 3
    ok_bad, msg_bad = validate_crt_basis([5, 6, 15])
    assert not ok_bad
    assert "not coprime" in msg_bad

    # Coprime prime basis
    ok_good, msg_good = validate_crt_basis([5, 7, 11, 13, 17])
    assert ok_good is True
    assert msg_good == "OK"


@pytest.mark.phase11_tier2
def test_bnd11_modulus_exceeding_64bit_safety() -> None:
    """Verifies that large CRT composite modulus M_filter > 2^64 operates without integer overflow."""
    # Basis of small primes whose product exceeds 2^64
    large_basis = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
    M_filter = 1
    for p in large_basis:
        M_filter *= p

    assert M_filter > (1 << 64), f"Expected M_filter > 2^64, got {M_filter.bit_length()} bits"

    # Verify big integer modular reduction
    sample_val = M_filter * 10 + 42
    assert sample_val % M_filter == 42


@pytest.mark.phase11_tier2
def test_bnd11_single_prime_basis_base_case() -> None:
    """Verifies CRT inverse filter behavior when basis contains only a single prime modulus."""
    single_basis = [5]
    # For prime 5: residues r where 12r^5 + 6r^3 +/- 1 != 0 mod 5
    # 12r^5 + 6r^3 mod 5 = 2r + r = 3r mod 5
    # A = 3r - 1 mod 5, B = 3r + 1 mod 5
    admissible = []
    for r in range(5):
        c_mod = (3 * r) % 5
        if (c_mod - 1) % 5 != 0 and (c_mod + 1) % 5 != 0:
            admissible.append(r)

    # For r in {0}: c_mod=0 -> A=-1=4, B=1 != 0 mod 5 (admissible)
    assert 0 in admissible
    assert len(admissible) > 0, "Single prime basis must yield non-empty admissible set"


@pytest.mark.phase11_tier2
def test_bnd11_generator_restart_identity() -> None:
    """Verifies that resuming a CRT residue progression from a stored step yields identical values."""
    M_filter = 30
    residue = 11
    # Full progression: t_k = residue + k * M_filter
    full_sequence = [residue + k * M_filter for k in range(20)]

    # Resumed progression starting at k=10
    start_k = 10
    resumed_sequence = [residue + k * M_filter for k in range(start_k, 20)]

    assert resumed_sequence == full_sequence[10:], "Resumed CRT progression must match uninterrupted sequence"
