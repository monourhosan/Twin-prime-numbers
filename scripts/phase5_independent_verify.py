"""
Strict Standalone Independent Verifier for Phase 5 Twin-Prime Certificates (Schema 5.0).
Completely decoupled from the search engine:
- ZERO imports from src.
- Arbitrary-precision exact arithmetic in pure Python standard library.
- First-principles Jacobi symbol calculation.
- First-principles 2x2 companion matrix powering for Lucas sequence U_k(P, 1) mod A.
- First-principles modular exponentiation and GCD checks for Pocklington theorem on B.
- Canonical JSON SHA-256 validation.
- Generates machine-readable Independent Verification Attestation JSON artifacts.
- Fail-closed: returns nonzero exit codes for missing files, empty directories, and invalid proofs.
"""

import sys
import os
import json
import math
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

def is_small_prime_deterministic(n: int) -> bool:
    """Deterministic primality check for smooth center prime factors from first principles."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    while d * d <= n:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    return True

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

def matrix_mult_2x2_mod(A, B, mod: int):
    """Multiplies two 2x2 matrices modulo mod."""
    return [
        [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % mod, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % mod],
        [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % mod, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % mod]
    ]

def matrix_pow_2x2_mod(M, exp: int, mod: int):
    """Computes M^exp mod mod via binary exponentiation."""
    res = [[1, 0], [0, 1]]
    base = [[M[0][0] % mod, M[0][1] % mod], [M[1][0] % mod, M[1][1] % mod]]
    e = int(exp)
    while e > 0:
        if e & 1:
            res = matrix_mult_2x2_mod(res, base, mod)
        base = matrix_mult_2x2_mod(base, base, mod)
        e >>= 1
    return res

def lucas_u_matrix_standalone(k: int, P: int, mod: int) -> int:
    """Computes U_k(P, 1) mod mod using companion matrix M = [[P, -1], [1, 0]]."""
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod
    M = [[P, -1], [1, 0]]
    Mk = matrix_pow_2x2_mod(M, k, mod)
    return Mk[1][0]

def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes canonical SHA-256 over JSON dict excluding sha256 field."""
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def canonical_pair_id(A: int, B: int) -> str:
    """Computes deterministic canonical pair ID."""
    p_min = min(int(A), int(B))
    p_max = max(int(A), int(B))
    pair_str = f"twin-pair-v1:{p_min}:{p_max}"
    return hashlib.sha256(pair_str.encode("utf-8")).hexdigest()

def verify_certificate_v5_payload(data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Audits a Schema 5.0 Proof Payload from first principles.
    Returns (is_valid, error_list, attestation_evidence).
    """
    errors: List[str] = []
    evidence: Dict[str, Any] = {}

    # 1. Schema check
    if data.get("schema_version") != "5.0":
        return False, [f"Invalid schema version: {data.get('schema_version')} (expected 5.0)"], {}
    if data.get("family") != "smooth_center":
        return False, [f"Invalid family: {data.get('family')} (expected smooth_center)"], {}

    # 2. Canonical SHA-256 check
    stated_sha256 = data.get("sha256", "")
    computed_sha256 = compute_canonical_sha256(data)
    if stated_sha256 != computed_sha256:
        errors.append(f"SHA-256 mismatch: stated={stated_sha256}, computed={computed_sha256}")
    evidence["payload_sha256_verified"] = stated_sha256 == computed_sha256

    # 3. Parameters and exact integer reconstruction
    params = data.get("parameters", {})
    exponents_raw = params.get("exponents", {})
    try:
        exponents = {int(p): int(e) for p, e in exponents_raw.items()}
        t = int(params["t"])
    except Exception as e:
        return False, [f"Failed to parse parameters: {e}"], {}

    if exponents.get(2, 0) < 1:
        errors.append("Exponent for prime 2 must be >= 1")
    if exponents.get(3, 0) < 1:
        errors.append("Exponent for prime 3 must be >= 1")
    if t <= 0:
        errors.append(f"Parameter t must be positive, got {t}")

    # Verify primality of each claimed prime base p in exponents
    for p in exponents.keys():
        if not is_small_prime_deterministic(p):
            errors.append(f"Claimed prime factor base p={p} is composite or not a valid prime")

    # Reconstruct F and F_odd
    F = 1
    F_odd = 1
    for p, e in sorted(exponents.items()):
        term = p ** e
        F *= term
        if p != 2:
            F_odd *= term

    odd_prime_factors = sorted([p for p in exponents.keys() if p != 2])

    if str(F) != params.get("F_decimal"):
        errors.append(f"F_decimal mismatch: reconstructed={F}, stated={params.get('F_decimal')}")
    if str(F_odd) != params.get("F_odd_decimal"):
        errors.append(f"F_odd_decimal mismatch: reconstructed={F_odd}, stated={params.get('F_odd_decimal')}")

    # 4. Center, Lower, Upper exact reconstruction
    C = F * t
    A = C - 1
    B = C + 1

    if str(C) != data.get("center_decimal"):
        errors.append(f"center_decimal mismatch")
    if str(A) != data.get("lower_decimal"):
        errors.append(f"lower_decimal mismatch")
    if str(B) != data.get("upper_decimal"):
        errors.append(f"upper_decimal mismatch")

    digits_A = len(str(A))
    digits_B = len(str(B))
    if digits_A != data.get("digits_lower"):
        errors.append(f"digits_lower mismatch: calculated {digits_A}, stated {data.get('digits_lower')}")
    if digits_B != data.get("digits_upper"):
        errors.append(f"digits_upper mismatch: calculated {digits_B}, stated {data.get('digits_upper')}")

    # 5. Exact Algebraic Twins check
    stated_A = int(data.get("lower_decimal", A))
    stated_B = int(data.get("upper_decimal", B))
    if stated_B - stated_A != 2 or B - A != 2:
        errors.append(f"Gap is not 2: B - A = {stated_B - stated_A}")
    if stated_A <= 2 or A <= 2:
        errors.append(f"A <= 2: {A}")
    if stated_A % 2 == 0 or stated_B % 2 == 0 or A % 2 == 0 or B % 2 == 0:
        errors.append("Candidates are not odd")
    if math.gcd(stated_A, stated_B) != 1 or math.gcd(A, B) != 1:
        errors.append(f"gcd(A, B) != 1")

    evidence["canonical_pair_id"] = canonical_pair_id(A, B)
    evidence["A_reconstructed"] = str(A)
    evidence["B_reconstructed"] = str(B)

    # 6. Theorem Size Bounds Checks
    if F_odd * F_odd <= B:
        errors.append(f"Pocklington size condition violated: F_odd^2 <= B ({F_odd**2} <= {B})")
    if (F_odd - 1) * (F_odd - 1) <= A:
        errors.append(f"Morrison size condition violated: (F_odd - 1)^2 <= A")

    # 7. Independent Pocklington BLS Theorem 4 Proof Verification on B
    upper_proof = data.get("primality_proofs", {}).get("upper", {})
    if upper_proof.get("theorem") != "Pocklington_BLS_1975_Theorem_4":
        errors.append(f"Unknown upper proof theorem: {upper_proof.get('theorem')}")
    else:
        witness_a = int(upper_proof.get("witness_base_a", 0))
        if witness_a < 2:
            errors.append(f"Invalid witness base a: {witness_a}")
        else:
            # Check Fermat congruence
            fermat_res = pow(witness_a, B - 1, B)
            if fermat_res != 1:
                errors.append(f"Pocklington Fermat congruence failed: {witness_a}^(B-1) mod B = {fermat_res} != 1")
            
            # Check GCD conditions
            pock_gcd_evidence = {}
            for q in odd_prime_factors:
                val = pow(witness_a, (B - 1) // q, B)
                g = math.gcd((val - 1) % B, B)
                pock_gcd_evidence[str(q)] = g
                if g != 1:
                    errors.append(f"Pocklington GCD condition failed for factor q={q}: gcd={g}")
            evidence["pocklington_witness_a"] = witness_a
            evidence["pocklington_gcd_checks"] = pock_gcd_evidence

    # 8. Independent Morrison BLS Theorem 17 Proof Verification on A
    lower_proof = data.get("primality_proofs", {}).get("lower", {})
    if lower_proof.get("theorem") != "Morrison_BLS_1975_Theorem_17":
        errors.append(f"Unknown lower proof theorem: {lower_proof.get('theorem')}")
    else:
        P_val = int(lower_proof.get("parameter_P", 0))
        D_val = P_val * P_val - 4
        
        # Check Jacobi condition
        j = standalone_jacobi(D_val, A)
        if j != -1:
            errors.append(f"Morrison Jacobi symbol condition failed: (D/A) = {j} != -1 (D={D_val}, P={P_val})")
        
        # Check Lucas full period condition: U_{A+1}(P, 1) == 0 mod A
        u_full = lucas_u_matrix_standalone(A + 1, P_val, A)
        if u_full != 0:
            errors.append(f"Morrison Lucas congruence failed: U_{{A+1}} mod A = {u_full} != 0")
            
        # Check GCD conditions for all prime factors q | F_odd
        morr_gcd_evidence = {}
        for q in odd_prime_factors:
            u_q = lucas_u_matrix_standalone((A + 1) // q, P_val, A)
            g = math.gcd(u_q, A)
            morr_gcd_evidence[str(q)] = g
            if g != 1:
                errors.append(f"Morrison GCD condition failed for factor q={q}: gcd(U_{{(A+1)/q}}, A) = {g} != 1")
                
        evidence["morrison_parameter_P"] = P_val
        evidence["morrison_discriminant_D"] = D_val
        evidence["morrison_jacobi"] = j
        evidence["morrison_lucas_u_full_mod_A"] = u_full
        evidence["morrison_gcd_checks"] = morr_gcd_evidence

    is_valid = len(errors) == 0
    return is_valid, errors, evidence

def verify_file(cert_path: Path, attestation_dir: Optional[Path] = None, overwrite: bool = False) -> Tuple[bool, Optional[Path], List[str]]:
    """
    Verifies a single certificate file and writes an attestation artifact if not already present.
    Returns (is_valid, attestation_file_path, errors).
    """
    cert_path = Path(cert_path)
    if not cert_path.exists():
        print(f"ERROR: Certificate file not found: {cert_path}")
        return False, None, [f"Certificate file not found: {cert_path}"]

    try:
        with open(cert_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Malformed JSON in {cert_path}: {e}")
        return False, None, [f"Malformed JSON: {e}"]

    is_valid, errors, evidence = verify_certificate_v5_payload(data)
    
    # Target attestation directory
    target_dir = attestation_dir or (cert_path.parent / "attestations")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    sha256 = data.get("sha256", "unknown")
    short_hash = sha256[:16]
    attestation_file = target_dir / f"attest_{short_hash}.json"

    # Only write/update if file does not exist or overwrite requested (Rule 4 preservation)
    should_write = (not attestation_file.exists()) or overwrite

    if should_write:
        attestation_data = {
            "attestation_version": "5.0",
            "verifier": "scripts/phase5_independent_verify.py",
            "target_certificate": str(cert_path.name),
            "target_sha256": sha256,
            "verification_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "result": "PASS" if is_valid else "FAIL",
            "digits_lower": data.get("digits_lower"),
            "digits_upper": data.get("digits_upper"),
            "pair": {
                "lower_prime_A": evidence.get("A_reconstructed"),
                "upper_prime_B": evidence.get("B_reconstructed"),
                "pair_id": evidence.get("canonical_pair_id")
            },
            "errors": errors,
            "independent_evidence": evidence
        }
        with open(attestation_file, "w", encoding="utf-8") as f:
            json.dump(attestation_data, f, indent=2)

    if is_valid:
        print(f"VERIFICATION SUCCESS: {cert_path.name}")
        print(f"  Digits: {data.get('digits_lower')} / {data.get('digits_upper')}")
        print(f"  Attestation: {attestation_file} {'(created)' if should_write else '(preserved)'}")
        return True, attestation_file, []
    else:
        print(f"VERIFICATION FAILED: {cert_path.name}")
        for err in errors:
            print(f"  - {err}")
        return False, attestation_file, errors

def main():
    parser = argparse.ArgumentParser(description="Strict Standalone Independent Verifier for Phase 5 Certificates")
    parser.add_argument("target", help="Certificate JSON file or directory containing cert_*.json")
    parser.add_argument("--attestation-dir", default=None, help="Optional directory to write attestation artifacts")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing attestation artifacts")
    
    args = parser.parse_args()
    target = Path(args.target)
    att_dir = Path(args.attestation_dir) if args.attestation_dir else None

    if not target.exists():
        print(f"ERROR: Target does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    if target.is_dir():
        cert_files = sorted(list(target.glob("cert_*.json")) + list(target.glob("imported_cert_*.json")))
        if not cert_files:
            print(f"ERROR: No certificate files matching cert_*.json found in {target}", file=sys.stderr)
            sys.exit(2)

        total = len(cert_files)
        passed = 0
        failed = 0
        for cf in cert_files:
            ok, _, _ = verify_file(cf, attestation_dir=att_dir, overwrite=args.overwrite)
            if ok:
                passed += 1
            else:
                failed += 1

        print(f"\nAudit Summary: Total={total}, Verified={passed}, Failed={failed}")
        if failed > 0:
            sys.exit(1)
        sys.exit(0)
    else:
        ok, _, _ = verify_file(target, attestation_dir=att_dir, overwrite=args.overwrite)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
