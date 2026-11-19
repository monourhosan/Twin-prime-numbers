"""
Phase 11 Prototype vs. Independent Oracle Differential & Property Test Suite.

Verifies:
1. Symbolic algebraic invariants of the OPQM manifold via Oracle.
2. Invariant consistency across parameter intervals t in [1, 200] and anchor scales y in {3, 5, 7}.
3. Super-root crossover discrete threshold at x = 86 (F_odd - 1)^2 <= A for x < 86, > A for x >= 86.
4. Root-negation symmetry r_A = (q - r_B) mod q across all odd primes < 2000.
5. 50% quadratic inertness for prime moduli q = 5, 7 mod 8 (0 roots for R(x) = 2x^2 + 1).
6. Bit-for-bit differential equivalence of candidate generation between prototype and oracle.
7. Bit-for-bit differential equivalence of candidate sieving between prototype and oracle.
8. End-to-end verification of empirical twin-prime discovery instance x = 126.
9. Comprehensive edge cases and boundary condition validation.
"""


import pytest
import sympy as sp

from src.phase11 import oracle, prototype

# ==============================================================================
# 1. Symbolic Algebraic Proofs via Oracle
# ==============================================================================

def test_symbolic_oracle_invariants() -> None:
    """Verifies that all symbolic algebraic invariants evaluate identically to True."""
    sym_invariants = oracle.verify_symbolic_invariants()
    assert sym_invariants["twin_gap_identity"] is True
    assert sym_invariants["center_factorization"] is True
    assert sym_invariants["antisymmetry_C"] is True
    assert sym_invariants["candidate_reflection"] is True
    assert sym_invariants["irreducibility_A"] is True
    assert sym_invariants["irreducibility_B"] is True


# ==============================================================================
# 2. Invariants Across Parameter Interval [1, 200]
# ==============================================================================

@pytest.mark.parametrize("anchor_y", [3, 5, 7])
def test_invariants_across_t_range(anchor_y: int) -> None:
    """
    Verifies that prototype and oracle agree on all invariant checks
    for coordinates x = S_y * t across odd multipliers t in [1, 200].
    """
    S_y = prototype.compute_primorial(anchor_y)
    assert S_y == oracle.compute_primorial(anchor_y)
    assert S_y % 6 == 0
    
    for t in range(1, 201, 2):  # Odd multipliers
        x = S_y * t
        
        # Prototype invariants
        proto_inv = prototype.verify_invariants(x)
        oracle_inv = oracle.verify_invariants(x)
        
        # Cross-validation
        assert proto_inv == oracle_inv, f"Invariant mismatch at x={x} (t={t}, y={anchor_y})"
        
        assert proto_inv["twin_gap"] is True
        assert proto_inv["center_mod_6"] is True
        assert proto_inv["A_mod_6"] is True
        assert proto_inv["B_mod_6"] is True
        assert proto_inv["gcd_F_R"] is True
        assert proto_inv["pocklington_dominance"] is True
        
        # Morrison dominance condition
        if x >= 86:
            assert proto_inv["morrison_dominance"] is True
        else:
            assert proto_inv["morrison_dominance"] is False


# ==============================================================================
# 3. Super-Root Crossover Discrete Threshold at x = 86
# ==============================================================================

def test_super_root_crossover_at_86() -> None:
    """
    Verifies the Morrison super-root inequality crossover:
      (F_odd - 1)^2 <= A(x) for x < 86
      (F_odd - 1)^2 >  A(x) for x >= 86
    specifically checking boundaries x = 85 and x = 86.
    """
    # 1. Exact boundary at x = 85 (evaluated with F_odd = 3/8 * x^3)
    x_85 = 85
    F_odd_85 = (3 * (x_85 ** 3)) / 8.0
    A_85 = 12 * (x_85 ** 5) + 6 * (x_85 ** 3) - 1
    delta_85 = (F_odd_85 - 1) ** 2 - A_85
    assert delta_85 < 0, f"Expected delta_85 < 0, got {delta_85}"
    
    # 2. Exact boundary at x = 86 (nu_2(86) = 1 since 86 = 2 * 43)
    x_86 = 86
    assert (x_86 & -x_86) == 2, "86 must have nu_2 == 1"
    F_86 = prototype.factorable_divisor(x_86)
    F_odd_86 = F_86 >> 4  # 2^4 = 16
    assert F_odd_86 == 238521
    A_86, _B_86 = prototype.compute_pair(x_86)
    delta_86 = (F_odd_86 - 1) ** 2 - A_86
    assert delta_86 == 436731953
    assert delta_86 > 0
    
    # Invariant dictionaries at boundaries
    inv_85 = prototype.verify_invariants(85)
    inv_86 = prototype.verify_invariants(86)
    assert inv_85["morrison_dominance"] is False
    assert inv_86["morrison_dominance"] is True
    
    # Full scan over all x with nu_2(x) == 1 in [2, 200]
    for x in range(2, 201, 4):  # 2, 6, 10, 14, ... (nu_2 == 1)
        inv = prototype.verify_invariants(x)
        expected_morrison = (x >= 86)
        assert inv["morrison_dominance"] == expected_morrison, f"Threshold failure at x={x}"


# ==============================================================================
# 4. Root-Negation Sieve Symmetry Across Odd Primes < 2000
# ==============================================================================

def test_root_negation_symmetry_odd_primes() -> None:
    """
    Verifies that for every odd prime q < 2000:
    1. Roots of A and B mod q are strictly symmetric: r_A = (q - r_B) mod q.
    2. Root sets are strictly disjoint: roots_A cap roots_B == empty.
    3. Prototype and Oracle produce bit-for-bit identical root lists.
    """
    primes = list(sp.primerange(3, 2000))
    for q in primes:
        proto_rA, proto_rB = prototype.find_modular_roots(q)
        oracle_rA, oracle_rB = oracle.find_modular_roots(q)
        
        # Differential identity
        assert proto_rA == oracle_rA, f"r_A mismatch at q={q}"
        assert proto_rB == oracle_rB, f"r_B mismatch at q={q}"
        
        # Bijection via root negation
        expected_A = sorted([(q - r) % q for r in proto_rB])
        assert proto_rA == expected_A, f"Symmetry broken at q={q}"
        
        # Disjointness
        assert set(proto_rA).isdisjoint(set(proto_rB)), f"Root sets intersect at q={q}"


# ==============================================================================
# 5. 50% Quadratic Inertness of Cofactor R(x) = 2x^2 + 1
# ==============================================================================

def test_quadratic_inertness_50_percent() -> None:
    """
    Verifies that R(x) = 2x^2 + 1 = 0 mod q has:
    - 0 roots for all primes q = 5, 7 mod 8 (completely inert)
    - 2 roots for all primes q = 1, 3 mod 8
    across all odd primes < 2000.
    """
    x_sym = sp.Symbol('x')
    poly_R = 2 * x_sym**2 + 1
    
    inert_count = 0
    split_count = 0
    
    for q in sp.primerange(3, 2000):
        Fq = sp.GF(q)
        p = sp.Poly(poly_R, x_sym, domain=Fq)
        roots = list(p.ground_roots().keys())
        
        rem8 = q % 8
        if rem8 in (5, 7):
            assert len(roots) == 0, f"Expected 0 roots for R mod {q} (q % 8 = {rem8}), got {roots}"
            inert_count += 1
        elif rem8 in (1, 3):
            assert len(roots) == 2, f"Expected 2 roots for R mod {q} (q % 8 = {rem8}), got {roots}"
            split_count += 1
            
    assert inert_count > 0 and split_count > 0
    assert abs(inert_count - split_count) <= 15  # Equidistribution verification (~50% each: 157 vs 145)


# ==============================================================================
# 6. Bit-for-Bit Differential Equivalence: Candidate Generation
# ==============================================================================

@pytest.mark.parametrize("anchor_y", [3, 5, 7])
@pytest.mark.parametrize("t_range", [(1, 50), (51, 100)])
@pytest.mark.parametrize("crt_basis", [None, [5, 7], [11, 13, 17]])
def test_candidate_generation_differential_equivalence(
    anchor_y: int,
    t_range: tuple,
    crt_basis: list | None
) -> None:
    """Verifies that prototype and oracle produce bit-for-bit identical candidate sets."""
    proto_cands = prototype.generate_candidates(anchor_y, t_range, crt_basis)
    oracle_cands = oracle.generate_candidates(anchor_y, t_range, crt_basis)
    
    assert len(proto_cands) == len(oracle_cands)
    assert proto_cands == oracle_cands
    
    # Verify that all candidates preserve gap = 2 and odd parity
    for t, A, B in proto_cands:
        assert B - A == 2
        assert A % 2 == 1 and B % 2 == 1
        assert t % 2 == 1


# ==============================================================================
# 7. Bit-for-Bit Differential Equivalence: Candidate Sieving
# ==============================================================================

@pytest.mark.parametrize("prime_limit", [50, 100, 500, 1000])
def test_sieve_candidates_differential_equivalence(prime_limit: int) -> None:
    """Verifies that prototype and oracle produce bit-for-bit identical sieved survivor sets."""
    # Generate initial pool of candidates
    proto_raw = prototype.generate_candidates(anchor_y=3, t_range=(1, 120), crt_basis=None)
    oracle_raw = oracle.generate_candidates(anchor_y=3, t_range=(1, 120), crt_basis=None)
    assert proto_raw == oracle_raw
    
    proto_surv = prototype.sieve_candidates(proto_raw, prime_limit)
    oracle_surv = oracle.sieve_candidates(oracle_raw, prime_limit)
    
    assert len(proto_surv) == len(oracle_surv)
    assert proto_surv == oracle_surv


# ==============================================================================
# 8. Empirical Test Instance: x = 126
# ==============================================================================

def test_empirical_twin_prime_x126() -> None:
    """
    Validates the verified 12-digit empirical twin-prime test instance from Math Spec §3:
      x = 126 = S_3 * 21 = 6 * 21 (y = 3, t = 21).
      C = 381,107,634,768
      A = 381,107,634,767
      B = 381,107,634,769
    """
    y = 3
    t = 21
    S_y = prototype.compute_primorial(y)
    x = S_y * t
    assert x == 126
    
    C = prototype.compute_center(x)
    A, B = prototype.compute_pair(x)
    
    assert C == 381107634768
    assert A == 381107634767
    assert B == 381107634769
    assert B - A == 2
    
    # Invariant verification
    inv = prototype.verify_invariants(x)
    assert all(inv.values()) is True
    
    # Ground truth primality via Oracle
    assert oracle.verify_primality(A) is True
    assert oracle.verify_primality(B) is True
    
    # Candidate generation & sieving inclusion
    cands = prototype.generate_candidates(anchor_y=3, t_range=(20, 25), crt_basis=[5, 7])
    assert any(c[0] == 21 for c in cands)
    
    survivors = prototype.sieve_candidates(cands, prime_limit=1000)
    assert any(c[0] == 21 for c in survivors)
    
    prime_pairs = oracle.find_survivor_primes(survivors)
    assert (21, A, B) in prime_pairs


# ==============================================================================
# 9. Edge Cases & Boundary Conditions
# ==============================================================================

def test_edge_cases_and_input_validation() -> None:
    """Verifies edge cases, singular primes, empty ranges, and parameter exceptions."""
    # 1. Invalid coordinates x <= 0
    with pytest.raises(ValueError, match="positive"):
        prototype.compute_center(0)
    with pytest.raises(ValueError, match="positive"):
        prototype.compute_center(-5)
    with pytest.raises(ValueError, match="positive"):
        oracle.compute_center(0)
        
    # 2. Invalid primorial anchor y < 3
    with pytest.raises(ValueError, match=">= 3"):
        prototype.compute_primorial(2)
    with pytest.raises(ValueError, match=">= 3"):
        oracle.compute_primorial(1)
        
    # 3. Empty t_range
    assert prototype.generate_candidates(3, (50, 50)) == []
    assert prototype.generate_candidates(3, (50, 40)) == []
    assert oracle.generate_candidates(3, (50, 50)) == []
    
    # 4. Sieve on empty candidate list
    assert prototype.sieve_candidates([], prime_limit=100) == []
    assert oracle.sieve_candidates([], prime_limit=100) == []
    
    # 5. Sieve prime limit < 2
    dummy_cands = [(1, 17, 19)]
    assert prototype.sieve_candidates(dummy_cands, prime_limit=1) == dummy_cands
    assert oracle.sieve_candidates(dummy_cands, prime_limit=1) == dummy_cands
    
    # 6. Sieve primes q in (2, 3) return empty roots
    assert prototype.find_modular_roots(2) == ([], [])
    assert prototype.find_modular_roots(3) == ([], [])
    assert oracle.find_modular_roots(2) == ([], [])
    assert oracle.find_modular_roots(3) == ([], [])
    
    # 7. Singular discriminant primes q in (23, 157)
    # Roots must be unique (no duplicate root entries)
    for q in (23, 157):
        rA_proto, rB_proto = prototype.find_modular_roots(q)
        rA_oracle, rB_oracle = oracle.find_modular_roots(q)
        assert rA_proto == rA_oracle
        assert rB_proto == rB_oracle
        assert len(rB_proto) == len(set(rB_proto)), f"Duplicate root in B mod {q}"
        assert len(rA_proto) == len(set(rA_proto)), f"Duplicate root in A mod {q}"
        if q == 23:
            assert rB_proto == [4, 18]
        elif q == 157:
            assert rB_proto == [45]
