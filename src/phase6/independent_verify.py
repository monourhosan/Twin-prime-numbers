"""
Strict Standalone Independent Verifier for Phase 6 Twin-Prime Certificates (Schema 6.0).
Completely decoupled from the search engine:
- ZERO imports from src.
- Arbitrary-precision exact arithmetic in pure Python standard library.
- First-principles Jacobi symbol calculation.
- First-principles 2x2 companion matrix powering for Lucas sequence U_k(P, 1) mod A.
- First-principles modular exponentiation and GCD checks for Pocklington theorem on B.
- Canonical JSON SHA-256 validation.
- First-principles trial division for all reported prime factors.
- Generates machine-readable Independent Verification Attestation JSON artifacts.
"""

import sys
import os
import json
import math
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

def standalone_is_small_prime(n: int, limit: int = 10000000) -> bool:
    """Deterministic primality check from first principles via trial division up to limit."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    while d * d <= n and d <= limit:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    return d * d > n

def standalone_jacobi(a: int, n: int) -> int:
    """Computes Jacobi symbol (a / n) for positive odd n from first principles."""
    if n <= 0 or n % 2 == 0:
        return 0
    a = a % n
    t = 1
    while a != 0:
        while a % 2 == 0:
            a //= 2
            r = n % 8
            if r in (3, 5):
                t = -t
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            t = -t
        a = a % n
    return t if n == 1 else 0

def standalone_lucas_u(P: int, k: int, N: int) -> int:
    """Computes Lucas sequence term U_k(P, 1) mod N using 2x2 companion matrix binary exponentiation."""
    if k == 0:
        return 0
    if k == 1:
        return 1 % N

    a00, a01 = 1, 0
    a10, a11 = 0, 1

    b00, b01 = P % N, (-1) % N
    b10, b11 = 1, 0

    exponent = k
    while exponent > 0:
        if exponent & 1:
            t00 = (a00 * b00 + a01 * b10) % N
            t01 = (a00 * b01 + a01 * b11) % N
            t10 = (a10 * b00 + a11 * b10) % N
            t11 = (a10 * b01 + a11 * b11) % N
            a00, a01, a10, a11 = t00, t01, t10, t11
        t00 = (b00 * b00 + b01 * b10) % N
        t01 = (b00 * b01 + b01 * b11) % N
        t10 = (b10 * b00 + b11 * b10) % N
        t11 = (b10 * b01 + b11 * b11) % N
        b00, b01, b10, b11 = t00, t01, t10, t11
        exponent >>= 1

    return a10 % N

def verify_phase6_certificate(cert_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Independently verifies Phase 6 Schema 6.0 Certificate from first principles.
    Returns (is_valid, error_list, evidence_dict).
    """
    errors: List[str] = []
    evidence: Dict[str, Any] = {}

    # 1. Schema check
    if cert_data.get("schema_version") != "6.0":
        errors.append(f"Invalid schema_version: expected '6.0', got {cert_data.get('schema_version')}")

    pair = cert_data.get("pair", {})
    try:
        A = int(pair.get("lower_prime_A", "0"))
        B = int(pair.get("upper_prime_B", "0"))
        m = int(pair.get("center_m", "0"))
        C = int(pair.get("center_C", "0"))
    except ValueError as e:
        errors.append(f"Failed to parse integers in certificate pair: {e}")
        return False, errors, evidence

    # 2. Arithmetic identities
    if 6 * m != C:
        errors.append(f"Center consistency mismatch: 6 * m ({6*m}) != center_C ({C})")
    if 6 * m - 1 != A:
        errors.append(f"Lower candidate mismatch: 6 * m - 1 ({6*m - 1}) != lower_prime_A ({A})")
    if 6 * m + 1 != B:
        errors.append(f"Upper candidate mismatch: 6 * m + 1 ({6*m + 1}) != upper_prime_B ({B})")
    if B - A != 2:
        errors.append(f"Difference mismatch: B - A ({B - A}) != 2")

    evidence["arithmetic_verified"] = len(errors) == 0

    proofs = cert_data.get("proofs")
    if not isinstance(proofs, dict):
        errors.append("Missing or invalid 'proofs' dictionary in certificate")
        return False, errors, evidence

    factors_dict = proofs.get("factors_of_center", {})
    if not factors_dict:
        errors.append("No factors_of_center provided in certificate proofs")
        return False, errors, evidence

    # 3. Factor product and primality from first principles
    prod = 1
    factors_list: List[int] = []
    for p_str, exp in factors_dict.items():
        p_val = int(p_str)
        exp_val = int(exp)
        if not standalone_is_small_prime(p_val):
            errors.append(f"Reported prime factor {p_val} failed first-principles trial division primality")
        prod *= (p_val ** exp_val)
        factors_list.append(p_val)

    if prod != C:
        errors.append(f"Factorization product mismatch: prod ({prod}) != center_C ({C})")

    evidence["factors_verified"] = len(errors) == 0

    # 4. Pocklington Verification on B
    proof_B = proofs.get("proof_upper_B", {})
    witness_a = proof_B.get("witness_a")
    if witness_a is None or not (2 <= witness_a < B):
        errors.append(f"Invalid Pocklington witness a: {witness_a}")
    else:
        # a^(B-1) = 1 mod B
        if pow(witness_a, B - 1, B) != 1:
            errors.append(f"Pocklington Fermat congruence failed: {witness_a}^(B-1) != 1 mod B")
        # gcd(a^((B-1)/q) - 1, B) == 1
        for q in factors_list:
            rem = pow(witness_a, (B - 1) // q, B)
            g = math.gcd(rem - 1, B)
            if g != 1:
                errors.append(f"Pocklington coprimality failed for factor {q}: gcd={g}")

    # 5. Morrison Verification on A
    proof_A = proofs.get("proof_lower_A", {})
    P_val = proof_A.get("parameter_P")
    if P_val is None or P_val < 3:
        errors.append(f"Invalid Morrison parameter P: {P_val}")
    else:
        D = P_val * P_val - 4
        jac = standalone_jacobi(D, A)
        if jac != -1:
            errors.append(f"Morrison Jacobi symbol condition failed: ({D}/{A}) = {jac} != -1")
        # U_{A+1}(P, 1) = 0 mod A
        u_full = standalone_lucas_u(P_val, A + 1, A)
        if u_full != 0:
            errors.append(f"Morrison Lucas zero congruence failed: U_{{A+1}}({P_val}, 1) = {u_full} != 0 mod A")
            
        # Check size condition on odd factored part
        odd_factors = [q for q in factors_list if q > 2]
        F_odd = 1
        for p_str, exp in factors_dict.items():
            if int(p_str) > 2:
                F_odd *= (int(p_str) ** int(exp))
        if 2 * F_odd <= int(A**0.5) + 1 and (F_odd - 1) * (F_odd - 1) <= A:
            errors.append(f"Morrison size condition violated: 2*F_odd ({2*F_odd}) <= sqrt(A) + 1 ({int(A**0.5)+1})")
            
        # gcd(U_{(A+1)/q}, A) == 1 for odd prime factors
        for q in odd_factors:
            u_sub = standalone_lucas_u(P_val, (A + 1) // q, A)
            g = math.gcd(u_sub, A)
            if g != 1:
                errors.append(f"Morrison coprimality condition failed for factor {q}: gcd={g}")

    # 6. Canonical SHA-256 validation
    claimed_sha = cert_data.get("canonical_sha256")
    clone = dict(cert_data)
    clone.pop("canonical_sha256", None)
    expected_sha = hashlib.sha256(
        json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()

    if claimed_sha != expected_sha:
        errors.append(f"Canonical SHA-256 digest mismatch: claimed {claimed_sha} != expected {expected_sha}")

    evidence["pocklington_pass"] = proof_B is not None and len(errors) == 0
    evidence["morrison_pass"] = proof_A is not None and len(errors) == 0
    evidence["sha256_verified"] = claimed_sha == expected_sha

    return len(errors) == 0, errors, evidence

def verify_file(cert_path: Path, attestation_dir: Optional[Path] = None) -> bool:
    """Verifies a single certificate file and generates attestation artifact."""
    if not cert_path.exists():
        print(f"ERROR: Certificate file not found: {cert_path}")
        return False

    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_bytes = cert_path.read_bytes()
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    is_valid, errors, evidence = verify_phase6_certificate(data)

    if attestation_dir is None:
        attestation_dir = cert_path.parent.parent / "attestations"
    attestation_dir.mkdir(parents=True, exist_ok=True)

    attestation_file = attestation_dir / f"attest_{raw_sha256[:16]}.json"
    attestation_data = {
        "schema_version": "6.0",
        "verifier": "src/phase6/independent_verify.py",
        "target_certificate": cert_path.name,
        "target_raw_sha256": raw_sha256,
        "verification_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "result": "PASS" if is_valid else "FAIL",
        "pair": data.get("pair", {}),
        "errors": errors,
        "independent_evidence": evidence
    }

    with open(attestation_file, "w", encoding="utf-8") as f:
        json.dump(attestation_data, f, indent=2)
        f.write("\n")

    if is_valid:
        print(f"VERIFICATION SUCCESS: {cert_path.name}")
        print(f"  Digits: {data.get('pair', {}).get('digits_A')} / {data.get('pair', {}).get('digits_B')}")
        print(f"  Attestation: {attestation_file}")
        return True
    else:
        print(f"VERIFICATION FAILED: {cert_path.name}")
        for err in errors:
            print(f"  - {err}")
        return False
