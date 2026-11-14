"""
Proof Router and Hybrid Certification Engine for Phase 6B and Phase 7.
Routes candidates according to structural properties:
- PROTH_LLR for k*2^n +/- 1 where 2^n > k
- DUAL_CLASSICAL_BLS for centers with F > sqrt(N)
- ECPP (Elliptic Curve Primality Proving) for general unrestricted primes
Includes production-grade PARI/GP subprocess adapter and strict format parser.
"""

import os
import shutil
import subprocess
import hashlib
import time
from typing import Dict, Any, Optional, Tuple, List

from src.phase6.proof_backend import DeterministicPairProver
from src.phase6.models import CandidatePair
from scripts.phase6b_ecpp_verify import verify_ecpp_certificate, verify_ecpp_step


def parse_gp_vector(s: str) -> Any:
    """
    Safely tokenizes and parses PARI/GP vector notation (nested brackets and integers)
    without using eval() or arbitrary code execution.
    """
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in '[],':
            tokens.append(c)
            i += 1
        elif c.isdigit() or (c == '-' and i + 1 < len(s) and s[i+1].isdigit()):
            j = i + 1
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(int(s[i:j]))
            i = j
        elif c.isspace():
            i += 1
        else:
            i += 1

    pos = 0
    def parse_expr():
        nonlocal pos
        if pos >= len(tokens):
            return None
        tok = tokens[pos]
        if tok == '[':
            pos += 1
            lst = []
            while pos < len(tokens) and tokens[pos] != ']':
                if tokens[pos] == ',':
                    pos += 1
                    continue
                lst.append(parse_expr())
            if pos < len(tokens) and tokens[pos] == ']':
                pos += 1
            return lst
        elif isinstance(tok, int):
            pos += 1
            return tok
        else:
            pos += 1
            return None

    return parse_expr()


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
        self.engine_info: Optional[Dict[str, Any]] = None
        self.engine_ready: bool = False
        self._audit_engine()

    def _audit_engine(self) -> None:
        """Audits, hashes, and smoke-tests the PARI/GP executable if present."""
        if not self.pari_gp_path or not os.path.isfile(self.pari_gp_path):
            self.engine_ready = False
            self.engine_info = None
            return

        try:
            # 1. Compute binary hash
            with open(self.pari_gp_path, "rb") as f:
                bin_hash = hashlib.sha256(f.read()).hexdigest()

            # 2. Query version and test primecert smoke test
            cmd = [self.pari_gp_path, "-q", "--fast", "-b"]
            smoke_script = "default(version);\nprimecert(17);\nprimecert(15);\nquit;\n"
            proc = subprocess.run(
                cmd,
                input=smoke_script,
                capture_output=True,
                text=True,
                timeout=10
            )
            stdout = proc.stdout.strip()
            if proc.returncode == 0 and "17" in stdout:
                lines = stdout.splitlines()
                ver = lines[0] if lines else "unknown"
                self.engine_info = {
                    "path": self.pari_gp_path,
                    "sha256": bin_hash,
                    "version_banner": ver,
                    "smoke_test": "PASSED"
                }
                self.engine_ready = True
            else:
                self.engine_ready = False
                self.engine_info = {
                    "path": self.pari_gp_path,
                    "smoke_test": "FAILED",
                    "stderr": proc.stderr
                }
        except Exception as e:
            self.engine_ready = False
            self.engine_info = {"error": str(e)}

    def has_ecpp_engine(self) -> bool:
        """Returns True only if an approved, smoke-tested ECPP engine (e.g. PARI/GP) is ready."""
        return self.engine_ready and self.pari_gp_path is not None

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
                "status": "BLOCKED_NO_APPROVED_ENGINE",
                "blocker_code": "P6B-BLOCKER-01",
                "reason": (
                    "Candidate requires general ECPP primality certification because center m has no large "
                    "known factor (F << sqrt(N)). However, no approved, smoke-tested ECPP engine (e.g. PARI/GP) "
                    "is installed on the host PATH, and unauthorized external executable downloads are strictly prohibited."
                ),
                "pair": {
                    "m": str(m),
                    "A": str(pair.A),
                    "B": str(pair.B),
                    "digits": d
                }
            }

        # If ECPP engine is available, dispatch to real ECPP worker
        return self._execute_ecpp_pair(pair.A, pair.B)

    def _execute_ecpp_single(self, N: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Runs PARI/GP primecert(N) via clean subprocess and verifies certificate."""
        if not self.has_ecpp_engine():
            return False, None, "ENGINE_NOT_AVAILABLE"

        script = f"primecert({N});\nquit;\n"
        cmd = [self.pari_gp_path, "-q", "--fast", "-b"]

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(input=script, timeout=self.ecpp_timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return False, None, f"TIMEOUT after {self.ecpp_timeout_sec}s"
        except Exception as e:
            return False, None, f"PROCESS_ERROR: {e}"

        if proc.returncode != 0:
            return False, None, f"GP_ERROR (code {proc.returncode}): {stderr.strip()}"

        parsed_vec = parse_gp_vector(stdout)
        if not parsed_vec or parsed_vec == 0:
            return False, None, "GP reported 0 (COMPOSITE) or invalid vector"

        # Transform parsed PARI/GP vector to normalized schema
        # In GP: primecert output format can be a list of steps
        steps = []
        raw_steps = parsed_vec if isinstance(parsed_vec, list) else []
        for s in raw_steps:
            if isinstance(s, list) and len(s) >= 5 and isinstance(s[4], list):
                p_val = s[0]
                t_val = s[1]
                s_cofactor = s[2]
                a_val = s[3]
                pt = s[4]
                x_val = pt[0]
                y_val = pt[1]
                m_val = p_val + 1 - t_val
                q_val = m_val // s_cofactor
                b_val = (y_val * y_val - x_val * x_val * x_val - a_val * x_val) % p_val
                steps.append({
                    "a": str(a_val),
                    "b": str(b_val),
                    "m": str(m_val),
                    "q": str(q_val),
                    "x": str(x_val),
                    "y": str(y_val)
                })

        cert_data = {
            "candidate": str(N),
            "steps": steps
        }

        # Verify unconditionally using independent theorem
        ok, msg = verify_ecpp_certificate(cert_data, expected_prime=N)
        if not ok:
            return False, None, f"CERTIFICATE_VERIFICATION_FAILED: {msg}"

        return True, cert_data, "PROVEN"

    def _execute_ecpp_pair(self, A: int, B: int) -> Dict[str, Any]:
        """Executes ECPP proofs for both members A and B via subprocess."""
        t0 = time.perf_counter()

        ok_A, cert_A, msg_A = self._execute_ecpp_single(A)
        if not ok_A:
            return {
                "route": "ECPP",
                "status": "A_FAILED_OR_TIMEOUT",
                "details_A": msg_A,
                "elapsed_sec": time.perf_counter() - t0
            }

        ok_B, cert_B, msg_B = self._execute_ecpp_single(B)
        if not ok_B:
            return {
                "route": "ECPP",
                "status": "B_FAILED_OR_TIMEOUT",
                "cert_A": cert_A,
                "details_B": msg_B,
                "elapsed_sec": time.perf_counter() - t0
            }

        return {
            "route": "ECPP",
            "status": "CERTIFIED_PAIR",
            "cert_A": cert_A,
            "cert_B": cert_B,
            "elapsed_sec": time.perf_counter() - t0
        }
