"""
Deterministic Primality Prover for HDC-7 Candidates.
Implements:
1. Proth's Theorem (1878) for Upper Member B' = k * 2^n + 1
2. Lucas-Lehmer-Riesel (LLR) Theorem (1969, 1994) for Lower Member A = k * 2^n - 1
Produces Schema 7.0 cryptographic certificates with canonical SHA-256 digests.
"""

import time
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from src.phase7.math import (
    compute_candidate_pair,
    jacobi_symbol,
    lucas_v_montgomery,
    lucas_v_matrix
)

try:
    import gmpy2
    HAVE_GMPY2 = True
except ImportError:
    HAVE_GMPY2 = False


def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes SHA-256 of canonical serialized JSON (excluding sha256 field)."""
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class HDCProver:
    """
    Unconditional deterministic prover for primorial Proth/LLR twin prime candidates.
    """
    def __init__(
        self,
        proth_witness_pool: Tuple[int, ...] = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47),
        llr_parameter_pool: Tuple[int, ...] = (3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22, 24),
        use_gmpy2: bool = True
    ):
        self.proth_witness_pool = proth_witness_pool
        self.llr_parameter_pool = llr_parameter_pool
        self.use_gmpy2 = use_gmpy2 and HAVE_GMPY2

    def prove_proth_upper(self, k: int, n: int, Bprime: int) -> Tuple[bool, Optional[int], str, float]:
        """
        Executes Proth's theorem proof for B' = k * 2^n + 1.
        Returns (is_prime, witness_w, details, elapsed_sec).
        """
        t0 = time.perf_counter()
        if k >= (1 << n):
            return False, None, f"Precondition k < 2^n violated (k={k} >= 2^{n})", 0.0

        exp = (Bprime - 1) // 2
        for w in self.proth_witness_pool:
            if self.use_gmpy2:
                res = int(gmpy2.powmod(w, exp, Bprime))
            else:
                res = pow(w, exp, Bprime)

            if res == Bprime - 1:
                elapsed = time.perf_counter() - t0
                return True, w, "PROVEN_PRIME via Proth's Theorem", elapsed
            
            # Fermat compositeness check: if w^(B-1) != 1 mod B
            if self.use_gmpy2:
                chk = int(gmpy2.powmod(res, 2, Bprime))
            else:
                chk = pow(res, 2, Bprime)
            if chk != 1:
                elapsed = time.perf_counter() - t0
                return False, w, f"Fermat compositeness witness: base {w}", elapsed

        elapsed = time.perf_counter() - t0
        return False, None, "Witness pool exhausted", elapsed

    def prove_llr_lower(self, k: int, n: int, A: int) -> Tuple[bool, Optional[int], Optional[int], str, float]:
        """
        Executes Lucas-Lehmer-Riesel (LLR) primality proof for A = k * 2^n - 1.
        Returns (is_prime, parameter_P, u0, details, elapsed_sec).
        """
        t0 = time.perf_counter()
        if k >= (1 << n):
            return False, None, None, f"Precondition k < 2^n violated (k={k} >= 2^{n})", 0.0
        if n < 2:
            return False, None, None, f"Precondition n >= 2 violated (n={n})", 0.0

        # 1. Parameter selection
        selected_P = None
        for P in self.llr_parameter_pool:
            jm = jacobi_symbol(P - 2, A)
            jp = jacobi_symbol(P + 2, A)
            if jm == 1 and jp == -1:
                selected_P = P
                break

        if selected_P is None:
            elapsed = time.perf_counter() - t0
            return False, None, None, "No parameter P satisfied Jacobi conditions", elapsed

        # 2. Initial u0 = V_k(P, 1) mod A
        u0 = lucas_v_montgomery(k, selected_P, A)

        # 3. LLR recurrence: exactly n - 2 rounds
        u = u0
        if self.use_gmpy2:
            u_mpz = gmpy2.mpz(u)
            A_mpz = gmpy2.mpz(A)
            for _ in range(n - 2):
                u_mpz = (gmpy2.square(u_mpz) - 2) % A_mpz
            final_u = int(u_mpz)
        else:
            for _ in range(n - 2):
                u = (pow(u, 2, A) - 2) % A
            final_u = u

        elapsed = time.perf_counter() - t0
        if final_u == 0:
            return True, selected_P, u0, "PROVEN_PRIME via LLR Theorem", elapsed
        else:
            return False, selected_P, u0, f"Final residue u_{{n-2}} = {final_u} != 0 (COMPOSITE)", elapsed

    def prove_pair(self, B_cut: int, MB: int, t: int, n: int, search_provenance: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Independently proves both members of candidate pair C = MB*(2t+1)*2^n.
        If both members pass, returns the complete Schema 7.0 certificate dict.
        """
        k, C, A, Bprime = compute_candidate_pair(MB, t, n)

        # 1. Prove Upper Member (Proth)
        ok_B, witness_w, msg_B, time_B = self.prove_proth_upper(k, n, Bprime)
        if not ok_B:
            return None

        # 2. Prove Lower Member (LLR)
        ok_A, param_P, u0, msg_A, time_A = self.prove_llr_lower(k, n, A)
        if not ok_A:
            return None

        # Both members unconditionally proven!
        cert_data = {
            "schema_version": "7.0",
            "campaign_id": "hdc7_primorial_campaign",
            "discovery_type": "CERTIFIED_FRESH_1510_PLUS" if len(str(A)) >= 1510 else "CERTIFIED_FRESH_FALLBACK",
            "representation": {
                "family": "primorial_constrained_proth_llr",
                "B_primorial": B_cut,
                "M_B": str(MB),
                "t": t,
                "k": str(k),
                "n": n
            },
            "pair": {
                "digits": len(str(A)),
                "center_decimal": str(C),
                "lower_decimal": str(A),
                "upper_decimal": str(Bprime),
                "difference": 2
            },
            "proofs": {
                "lower_member": {
                    "theorem": "Lucas-Lehmer-Riesel (1969) / Rodseth (1994)",
                    "parameter_P": param_P,
                    "jacobi_conditions": {
                        f"({param_P}-2/A)": 1,
                        f"({param_P}+2/A)": -1
                    },
                    "u0": str(u0),
                    "llr_rounds": n - 2,
                    "final_residue": 0,
                    "verdict": "PROVEN_PRIME",
                    "prover_time_sec": time_A
                },
                "upper_member": {
                    "theorem": "Proth (1878) Theorem",
                    "witness_w": witness_w,
                    "congruence": f"{witness_w}^((B-1)/2) == -1 mod B",
                    "verdict": "PROVEN_PRIME",
                    "prover_time_sec": time_B
                }
            },
            "search_evidence": search_provenance or {
                "utc_certified": datetime.now(timezone.utc).isoformat(),
                "verifier": "HDCProver_v7.0"
            }
        }
        cert_data["sha256"] = compute_canonical_sha256(cert_data)
        return cert_data
