"""
Phase 9 Deterministic Dual-BLS Primality Certification Prover.
Generates unconditional primality certificates for twin-prime pairs (A, B)
on the PACCM-9 cubic manifold: C = 2*x^2*(3x + 1), A = C - 1, B = C + 1.

Proof Theorems:
- Upper Member B: Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington N-1)
- Lower Member A: Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison N+1)
"""

import math
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
import gmpy2

from .anchor import PrimorialAnchor, is_small_prime_deterministic
from .math import construct_pair, lucas_u_mod, find_morrison_params


def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes SHA-256 of JSON payload excluding any existing sha256 field."""
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class PACCM9Prover:
    """
    Constructs and certifies PACCM-9 twin-prime pairs deterministically.
    """

    def __init__(self, anchor: PrimorialAnchor):
        self.anchor = anchor

    def prove_pair(
        self,
        t: int,
        campaign_id: str = "phase9_campaign"
    ) -> Optional[Dict[str, Any]]:
        """
        Generates an unconditional, deterministic primality proof certificate
        for twin-prime pair at multiplier t.
        """
        assert is_small_prime_deterministic(t), f"Multiplier t={t} must be prime"

        x = self.anchor.compute_x(t)
        C, A, B = construct_pair(x)

        # Quick PRP sanity check before attempting proof
        if gmpy2.is_prime(A) == 0 or gmpy2.is_prime(B) == 0:
            return None

        # Factored divisor F = 2 * x^2
        factors_F = self.anchor.get_F_factorization(t, t_is_prime=True)
        distinct_primes = sorted(list(factors_F.keys()))
        odd_primes = [p for p in distinct_primes if p != 2]

        F = 1
        for p, exp in factors_F.items():
            F *= p ** exp

        F_odd = 1
        for p in odd_primes:
            F_odd *= p ** factors_F[p]

        # 1. Size condition checks
        if F * F <= B:
            raise RuntimeError(f"BLS size condition failed on B: F^2 <= B")
        if (F_odd - 1) * (F_odd - 1) <= A:
            raise RuntimeError(f"Morrison size condition failed on A: (F_odd - 1)^2 <= A")

        # 2. Upper Member B: Pocklington BLS Theorem 4
        # For each prime factor q_i in distinct_primes, find witness a_i
        witnesses_B: Dict[str, int] = {}
        candidate_bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97)
        B_minus_1 = B - 1

        for q in distinct_primes:
            found_w = False
            for w in candidate_bases:
                if gmpy2.powmod(w, B_minus_1, B) == 1:
                    exp_q = B_minus_1 // q
                    term = gmpy2.powmod(w, exp_q, B) - 1
                    if math.gcd(int(term), B) == 1:
                        witnesses_B[str(q)] = w
                        found_w = True
                        break
            if not found_w:
                # Search larger witnesses if needed
                for w in range(101, 1000):
                    if gmpy2.powmod(w, B_minus_1, B) == 1:
                        exp_q = B_minus_1 // q
                        term = gmpy2.powmod(w, exp_q, B) - 1
                        if math.gcd(int(term), B) == 1:
                            witnesses_B[str(q)] = w
                            found_w = True
                            break
                if not found_w:
                    raise RuntimeError(f"Failed to find Pocklington witness for prime factor {q} on upper member B")

        # 3. Lower Member A: Morrison BLS Theorem 17
        P, D = find_morrison_params(A, odd_factors=odd_primes)
        A_plus_1 = A + 1

        # Check U_{A+1} = 0 mod A
        u_full = lucas_u_mod(P, 1, A_plus_1, A)
        if u_full != 0:
            raise RuntimeError(f"Morrison zero congruence failed on A: U_{{A+1}} = {u_full} != 0 mod A")

        # Check gcd(U_{(A+1)/q}, A) == 1 for all odd prime factors q in F
        factor_gcds_A: Dict[str, str] = {}
        for q in odd_primes:
            exp_q = A_plus_1 // q
            u_part = lucas_u_mod(P, 1, exp_q, A)
            g = math.gcd(u_part, A)
            if g != 1:
                raise RuntimeError(f"Morrison gcd condition failed on A for factor {q}: gcd={g}")
            factor_gcds_A[str(q)] = "1"

        # 4. Construct complete certificate payload
        digits_A = len(str(A))
        digits_B = len(str(B))

        cert_payload: Dict[str, Any] = {
            "schema_version": "9.0",
            "campaign_id": campaign_id,
            "method": "PACCM-9",
            "discovery_type": "DETERMINISTIC_TWIN_PRIME_DISCOVERY",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "representation": {
                "family": "primorial_anchored_cubic_cofactor",
                "manifold_equation": "C = 2*x^2*(3x + 1), A = C - 1, B = C + 1",
                "y_bound": self.anchor.y,
                "S_y_digits": self.anchor.digits,
                "S_y_decimal": str(self.anchor.S_y),
                "t": t,
                "x_decimal": str(x),
                "F_decimal": str(F),
                "F_odd_decimal": str(F_odd),
                "prime_factors_count": len(distinct_primes),
                "distinct_primes": distinct_primes,
                "factors_F": {str(k): v for k, v in factors_F.items()}
            },
            "pair": {
                "difference": 2,
                "digits": digits_A,
                "center_decimal": str(C),
                "lower_decimal": str(A),
                "upper_decimal": str(B)
            },
            "proofs": {
                "upper_member": {
                    "theorem": "Brillhart-Lehmer-Selfridge (1975) Theorem 4 (Pocklington N-1)",
                    "candidate": str(B),
                    "digits": digits_B,
                    "proof_factor_F": str(F),
                    "size_condition": "PASS (F^2 > B)",
                    "witnesses": witnesses_B,
                    "status": "PROVEN_PRIME"
                },
                "lower_member": {
                    "theorem": "Brillhart-Lehmer-Selfridge (1975) Theorem 17 (Morrison N+1 Rank)",
                    "candidate": str(A),
                    "digits": digits_A,
                    "proof_factor_F_odd": str(F_odd),
                    "size_condition": "PASS ((F_odd - 1)^2 > A)",
                    "parameter_P": P,
                    "parameter_Q": 1,
                    "discriminant_D": D,
                    "jacobi_symbol": -1,
                    "verification": {
                        "lucas_zero_congruence": f"U_{{A+1}}({P}, 1) = 0 mod A",
                        "factor_gcds": factor_gcds_A
                    },
                    "status": "PROVEN_PRIME"
                }
            },
            "status": "PROVEN"
        }

        # Calculate canonical SHA-256
        cert_hash = compute_canonical_sha256(cert_payload)
        cert_payload["sha256"] = cert_hash

        return cert_payload
