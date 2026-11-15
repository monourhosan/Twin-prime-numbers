"""
PAQCS Unconditional Primality Prover Engine (Phase 8).
Executes dual-BLS deterministic primality proofs:
- Pocklington / BLS (1975) Theorem 4 for Upper Member B (N - 1)
- Morrison / BLS (1975) Theorem 17 for Lower Member A (N + 1)
Generates complete canonical JSON certificates.
"""

import hashlib
import json
import math
import time
from typing import Dict, List, Tuple, Optional, Any
import gmpy2

from .paqcs_math import construct_pair, lucas_u_ladder
from .paqcs_anchor import PrimorialAnchor


def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes SHA-256 over canonical JSON serialization with sorted keys and excluded self-hash."""
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical_bytes = json.dumps(clean, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical_bytes).hexdigest()


class PAQCSProver:
    """
    Proves primality unconditionally for PAQCS twin prime pairs.
    """

    def __init__(
        self,
        anchor: PrimorialAnchor,
        witness_pool: Tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)
    ):
        self.anchor = anchor
        self.witness_pool = witness_pool

    def prove_upper_member_pocklington(
        self,
        B: int,
        F: int,
        prime_factors_F: List[int]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Upper member B = x^2 - hx + 1.
        B - 1 = F * (x - h) where F = x.
        Pocklington size condition: F^2 > B.
        Fermat condition: a^(B-1) = 1 mod B.
        Gcd condition: gcd(a^((B-1)/q) - 1, B) = 1 for each q | F.
        """
        if B <= 2 or B % 2 == 0:
            return False, None, f"B must be positive odd integer > 2, got {B}"
        if (B - 1) % F != 0:
            return False, None, "F does not divide B - 1"
        if F * F <= B:
            return False, None, f"Pocklington size condition failed: F^2 <= B"

        B_mpz = gmpy2.mpz(B)
        B_minus_1 = B_mpz - 1
        witness_map: Dict[str, int] = {}
        gcd_map: Dict[str, str] = {}

        for q in prime_factors_F:
            q_mpz = gmpy2.mpz(q)
            exp_q = B_minus_1 // q_mpz
            found_w = False
            for w in self.witness_pool:
                w_mpz = gmpy2.mpz(w)
                if w >= B:
                    continue
                # Fermat check
                if gmpy2.powmod(w_mpz, B_minus_1, B_mpz) != 1:
                    continue
                term = (gmpy2.powmod(w_mpz, exp_q, B_mpz) - 1) % B_mpz
                g = gmpy2.gcd(term, B_mpz)
                if g == 1:
                    witness_map[str(q)] = w
                    gcd_map[str(q)] = "1"
                    found_w = True
                    break
            if not found_w:
                return False, None, f"No Pocklington witness found for prime factor q={q}"

        proof_artifact = {
            "theorem": "Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington N-1)",
            "candidate": str(B),
            "digits": len(str(B)),
            "proof_factor_F": str(F),
            "prime_factors_count": len(prime_factors_F),
            "size_condition": "PASS (F^2 > B)",
            "witnesses": witness_map,
            "factor_gcds": gcd_map,
            "status": "PROVEN_PRIME"
        }
        return True, proof_artifact, None

    def prove_lower_member_morrison(
        self,
        A: int,
        F: int,
        prime_factors_F: List[int],
        max_P_trials: int = 100
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Lower member A = x^2 - hx - 1.
        A + 1 = F * (x - h) where F = x.
        Morrison size condition: (F - 1)^2 > A.
        Jacobi condition: (P^2 - 4 / A) = -1.
        Lucas rank condition: U_{A+1}(P, 1) = 0 mod A and gcd(U_{(A+1)/q}(P, 1), A) = 1 for all q | F.
        """
        if A <= 2 or A % 2 == 0:
            return False, None, f"A must be positive odd integer > 2, got {A}"
        if (A + 1) % F != 0:
            return False, None, "F does not divide A + 1"
        if (F - 1) * (F - 1) <= A:
            return False, None, "Morrison size condition failed: (F - 1)^2 <= A"

        A_mpz = gmpy2.mpz(A)
        A_plus_1 = int(A + 1)
        chosen_P: Optional[int] = None
        chosen_D: Optional[int] = None
        chosen_gcd_map: Dict[str, str] = {}

        for P in range(3, 3 + max_P_trials):
            D = P * P - 4
            if gmpy2.gcd(A_mpz, 2 * D) != 1 or gmpy2.jacobi(D, A_mpz) != -1:
                continue

            # Full Lucas sequence check: U_{A+1} = 0 mod A
            u_full = lucas_u_ladder(A_plus_1, P, A)
            if u_full != 0:
                continue

            # Per-factor rank condition
            gcd_map: Dict[str, str] = {}
            all_gcd_1 = True
            for q in prime_factors_F:
                exp_q = A_plus_1 // q
                u_q = lucas_u_ladder(exp_q, P, A)
                g = math.gcd(u_q, A)
                gcd_map[str(q)] = str(g)
                if g != 1:
                    all_gcd_1 = False
                    break

            if all_gcd_1:
                chosen_P = P
                chosen_D = D
                chosen_gcd_map = gcd_map
                break

        if chosen_P is None:
            return False, None, f"Could not find valid Lucas parameter P within {max_P_trials} trials"

        proof_artifact = {
            "theorem": "Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison N+1 Rank)",
            "candidate": str(A),
            "digits": len(str(A)),
            "proof_factor_F": str(F),
            "prime_factors_count": len(prime_factors_F),
            "size_condition": "PASS ((F - 1)^2 > A)",
            "parameter_P": chosen_P,
            "parameter_Q": 1,
            "discriminant_D": chosen_D,
            "jacobi_symbol": -1,
            "verification": {
                "lucas_zero_congruence": f"U_{{A+1}}({chosen_P}, 1) = 0 mod A",
                "factor_gcds": chosen_gcd_map
            },
            "status": "PROVEN_PRIME"
        }
        return True, proof_artifact, None

    def prove_twin_pair(
        self,
        t: int,
        h: int = 3,
        campaign_id: str = "paqcs_primary_1511d"
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Executes complete unconditional dual-BLS proof for pair generated by t.
        """
        t0 = time.perf_counter()
        x, C, A, B = construct_pair(self.anchor.S_y, t, h=h)
        F = x
        distinct_primes, multiplicities = self.anchor.factor_x(t)

        # 1. Prove upper member B (Pocklington)
        ok_B, proof_B, err_B = self.prove_upper_member_pocklington(B, F, distinct_primes)
        if not ok_B:
            return False, None, f"Upper member proof failed: {err_B}"

        # 2. Prove lower member A (Morrison)
        ok_A, proof_A, err_A = self.prove_lower_member_morrison(A, F, distinct_primes)
        if not ok_A:
            return False, None, f"Lower member proof failed: {err_A}"

        total_time = time.perf_counter() - t0

        certificate = {
            "schema_version": "8.0",
            "campaign_id": campaign_id,
            "method": "PAQCS",
            "discovery_type": "CERTIFIED_FRESH_1511_PLUS",
            "representation": {
                "family": "primorial_anchored_quadratic_cofactor",
                "h": h,
                "y_bound": self.anchor.y,
                "S_y_decimal": str(self.anchor.S_y),
                "S_y_digits": self.anchor.digits,
                "t": t,
                "x_decimal": str(x),
                "factors_sha256": self.anchor.factors_sha256,
                "x_factorization": {str(p): mult for p, mult in multiplicities.items()}
            },
            "pair": {
                "digits": len(str(A)),
                "difference": int(B - A),
                "center_decimal": str(C),
                "lower_decimal": str(A),
                "upper_decimal": str(B)
            },
            "proofs": {
                "upper_member": proof_B,
                "lower_member": proof_A
            },
            "metrics": {
                "proof_elapsed_sec": total_time,
                "proven_primes_count": len(distinct_primes)
            }
        }
        certificate["sha256"] = compute_canonical_sha256(certificate)
        return True, certificate, None
