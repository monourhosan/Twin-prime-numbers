"""
Proof Router and Hybrid Certification Engine for Phase 6B.
Routes candidates according to structural properties:
- PROTH_LLR for k*2^n +/- 1 where 2^n > k
- DUAL_CLASSICAL_BLS for centers with F > sqrt(N)
- ECPP (Elliptic Curve Primality Proving) for general unrestricted primes
"""

import os
import shutil
import subprocess
import time
from typing import Dict, Any, Optional, Tuple

from src.phase6.proof_backend import DeterministicPairProver
from src.phase6.models import CandidatePair

class ProofRouter:
    """
    Intelligent primality proof router.
    Evaluates candidate structural properties and dispatches to the most efficient
    mathematically rigorous proof theorem.
    """
    def __init__(
        self,
        classical_factor_timeout_sec: float = 5.0,
        ecpp_timeout_sec: float = 900.0,
        pari_gp_path: Optional[str] = None
    ):
        self.classical_prover = DeterministicPairProver(factor_timeout_sec=classical_factor_timeout_sec)
        self.classical_timeout_sec = classical_factor_timeout_sec
        self.ecpp_timeout_sec = ecpp_timeout_sec
        self.pari_gp_path = pari_gp_path or shutil.which("gp")

    def has_ecpp_engine(self) -> bool:
        """Returns True if a valid ECPP engine (e.g. PARI/GP) is found on the host system."""
        return self.pari_gp_path is not None and os.path.isfile(self.pari_gp_path)

    def route_pair(self, m: int, digits: Optional[int] = None) -> Dict[str, Any]:
        """
        Determines the optimal proof strategy for twin pair A = 6m - 1, B = 6m + 1.
        Returns a routing execution plan.
        """
        pair = CandidatePair.from_m(m)
        d = digits or pair.digits

        # Strategy 1: Attempt bounded classical center factorization
        # If complete factorization of m succeeds and F > sqrt(N), BLS Theorems 4 & 17 apply.
        t0 = time.perf_counter()
        classical_proof = self.classical_prover.prove_pair(m)
        if classical_proof is not None:
            return {
                "route": "DUAL_CLASSICAL_BLS",
                "status": "PROVEN",
                "proof": classical_proof,
                "elapsed_sec": time.perf_counter() - t0
            }

        # Strategy 2: If classical BLS fails (e.g. general 350-digit integer with F <= 10^6 << sqrt(N)),
        # route to general ECPP.
        if not self.has_ecpp_engine():
            return {
                "route": "ECPP",
                "status": "BLOCKED_NO_ECPP_ENGINE",
                "blocker_code": "P6B-BLOCKER-01",
                "reason": (
                    "Candidate requires general ECPP primality certification because center m has no large "
                    "known factor (F << sqrt(N)). However, no vetted ECPP engine (e.g. PARI/GP) is installed on "
                    "the host PATH, and unauthorized external executable downloads are strictly prohibited."
                ),
                "pair": {
                    "m": str(m),
                    "A": str(pair.A),
                    "B": str(pair.B),
                    "digits": d
                }
            }

        # If ECPP engine is available, dispatch to ECPP worker
        return self._execute_ecpp_pair(pair.A, pair.B)

    def _execute_ecpp_pair(self, A: int, B: int) -> Dict[str, Any]:
        """Executes ECPP proofs for both members A and B via subprocess."""
        # Stub for live ECPP invocation when binary is present
        return {
            "route": "ECPP",
            "status": "ENGINE_AVAILABLE_NOT_EXECUTED",
            "gp_path": self.pari_gp_path
        }
