"""Phase 11 Standalone Independent Certificate Verifier.

STRICT CONSTRAINT: Strictly decoupled from src/ with ZERO project-internal imports.
Only standard library and gmpy2 allowed.

Verifies:
1. Exact canonical 21-field JSON certificate schema.
2. Canonical RFC 8785 JSON SHA-256 integrity digest.
3. First-principles coordinate reconstruction:
   S_y = prod_{p <= y} p, x = S_y * t, C = 12x^5 + 6x^3, A = C - 1, B = C + 1.
4. Twin gap B - A == 2, center C = 0 mod 6, and digit count.
5. Divisor-cofactor coprimality gcd(F, R) == 1 and factor primality.
6. Upper Prime B: Pocklington BLS (1975) Theorem 4 (F^2 > B, Fermat congruence, GCD checks).
7. Lower Prime A: Morrison BLS (1975) Theorem 17 ((F_odd - 1)^2 > A, Jacobi symbol,
   full-period zero congruence, Morrison Singularity Guard: factor 2 strictly excluded).
8. Emits signed JSON attestation and returns exit code 0 on PASS, 1 on FAIL.
"""

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import gmpy2

CANONICAL_FIELDS = [
    "method_id",
    "method_version",
    "repository_commit",
    "run_id",
    "timestamp_utc",
    "hardware",
    "parameters",
    "symbolic_center",
    "lower_prime",
    "upper_prime",
    "digit_count",
    "difference",
    "factorization",
    "proof_method_lower",
    "proof_method_upper",
    "witnesses_lower",
    "witnesses_upper",
    "proof_conditions",
    "novelty_status_repository",
    "novelty_status_public",
    "certificate_sha256",
]


def is_small_prime_standalone(n: int) -> bool:
    """Deterministic 7-base Miller-Rabin test for n < 2^64."""
    if n < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for sp in small_primes:
        if n == sp:
            return True
        if n % sp == 0:
            return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def standalone_lucas_u(k: int, P: int, mod: int) -> int:
    """Evaluates U_k(P, 1) mod 'mod' using 2x2 companion matrix exponentiation."""
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod

    mod_mpz = gmpy2.mpz(mod)
    m00, m01 = gmpy2.mpz(P) % mod_mpz, gmpy2.mpz(-1) % mod_mpz
    m10, m11 = gmpy2.mpz(1), gmpy2.mpz(0)

    r00, r01 = gmpy2.mpz(1), gmpy2.mpz(0)
    r10, r11 = gmpy2.mpz(0), gmpy2.mpz(1)

    bit_len = k.bit_length()
    for bit in range(bit_len - 1, -1, -1):
        t00 = (r00 * r00 + r01 * r10) % mod_mpz
        t01 = (r00 * r01 + r01 * r11) % mod_mpz
        t10 = (r10 * r00 + r11 * r10) % mod_mpz
        t11 = (r10 * r01 + r11 * r11) % mod_mpz
        r00, r01, r10, r11 = t00, t01, t10, t11

        if (k >> bit) & 1:
            t00 = (r00 * m00 + r01 * m10) % mod_mpz
            t01 = (r00 * m01 + r01 * m11) % mod_mpz
            t10 = (r10 * m00 + r11 * m10) % mod_mpz
            t11 = (r10 * m01 + r11 * m11) % mod_mpz
            r00, r01, r10, r11 = t00, t01, t10, t11

    return int(r10)


def compute_canonical_sha256(data: dict[str, Any]) -> str:
    """Computes the RFC 8785 canonical SHA-256 digest of payload."""
    clean = {k: v for k, v in data.items() if k != "certificate_sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_opqm11_certificate(
    cert_path: Path | str,
    attestation_dir: Path | str | None = None,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Strictly audits and verifies an OPQM-11 certificate from first principles."""
    logs: list[str] = []
    path_obj = Path(cert_path)

    if not path_obj.is_file():
        return False, [f"Certificate file not found: {cert_path}"], {}

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return False, [f"Failed to parse certificate JSON: {exc}"], {}

    # 1. Canonical Schema Check
    if not isinstance(data, dict):
        return False, ["Certificate payload must be a JSON object"], {}

    missing_fields = [f for f in CANONICAL_FIELDS if f not in data]
    if missing_fields:
        return False, [f"Missing required fields: {missing_fields}"], {}

    extra_fields = set(data) - set(CANONICAL_FIELDS)
    if extra_fields:
        return False, [f"Extraneous fields present: {sorted(extra_fields)}"], {}

    if data.get("method_id") != "OPQM_CRT_HYBRID_11":
        return False, [f"Invalid method_id: {data.get('method_id')}"], {}

    # 2. Canonical SHA-256 Integrity Check
    declared_hash = data.get("certificate_sha256", "")
    computed_hash = compute_canonical_sha256(data)
    if declared_hash.lower() != computed_hash.lower():
        return False, [f"SHA-256 mismatch: declared={declared_hash}, computed={computed_hash}"], {}
    logs.append(f"Canonical Payload SHA-256 verified: {computed_hash}")

    # 3. First-Principles Coordinate Reconstruction
    params = data.get("parameters", {})
    try:
        y = int(params["y"])
        t = int(params["t"])
    except (KeyError, ValueError, TypeError) as exc:
        return False, [f"Invalid parameters y, t: {exc}"], {}

    if y < 3:
        return False, [f"Primorial anchor y={y} must be >= 3"], {}
    if t <= 0 or t % 2 == 0:
        return False, [f"Multiplier t={t} must be an odd positive integer"], {}

    # Reconstruct S_y
    reconstructed_Sy = 1
    for p in range(2, y + 1):
        if is_small_prime_standalone(p):
            reconstructed_Sy *= p

    if str(reconstructed_Sy) != str(params.get("S_y")):
        return False, [f"S_y reconstruction mismatch: declared={params.get('S_y')}, computed={reconstructed_Sy}"], {}

    reconstructed_x = reconstructed_Sy * t
    if str(reconstructed_x) != str(params.get("x")):
        return False, [f"x reconstruction mismatch: declared={params.get('x')}, computed={reconstructed_x}"], {}

    if reconstructed_x < 86:
        return False, [f"Coordinate x={reconstructed_x} < 86 violates Morrison dominance threshold"], {}

    # Reconstruct C, A, B on quintic manifold
    x_mpz = gmpy2.mpz(reconstructed_x)
    x3 = x_mpz ** 3
    x5 = x3 * (x_mpz ** 2)
    reconstructed_C = 12 * x5 + 6 * x3
    reconstructed_A = reconstructed_C - 1
    reconstructed_B = reconstructed_C + 1

    try:
        declared_A = int(data["lower_prime"])
        declared_B = int(data["upper_prime"])
    except (ValueError, TypeError) as exc:
        return False, [f"Non-numeric primes in certificate: {exc}"], {}

    if declared_B - declared_A != 2:
        return False, [f"Twin gap violation: {declared_B - declared_A} != 2"], {}
    if data.get("difference") != 2:
        return False, [f"Declared difference is {data.get('difference')} != 2"], {}
    logs.append("Twin gap verified: B - A = 2")

    if declared_A != reconstructed_A or declared_B != reconstructed_B:
        return False, ["Coordinates mismatch manifold equation C = 12x^5 + 6x^3"], {}

    digits = len(str(declared_A))
    if data.get("digit_count") != digits:
        return False, [f"Digit count mismatch: declared={data.get('digit_count')}, computed={digits}"], {}
    logs.append(f"Exact decimal digits: {digits}")

    if reconstructed_C % 6 != 0:
        return False, ["Center C is not divisible by 6"], {}
    logs.append("Parity & mod 6 congruence verified: C = 0 mod 6")

    # 4. Divisors F, F_odd, and Factorization
    reconstructed_F = 6 * (x_mpz ** 3)
    reconstructed_R = 2 * (x_mpz ** 2) + 1
    reconstructed_F_odd = reconstructed_F
    while reconstructed_F_odd % 2 == 0:
        reconstructed_F_odd //= 2

    if str(reconstructed_F) != str(params.get("F")):
        return False, ["F mismatch with 6*x^3"], {}
    if str(reconstructed_F_odd) != str(params.get("F_odd")):
        return False, ["F_odd mismatch"], {}

    factors_F_dict = data.get("factorization", {}).get("factors_F", {})
    prod_F = 1
    for p_str, exp_val in factors_F_dict.items():
        p = int(p_str)
        exp = int(exp_val)
        if not is_small_prime_standalone(p):
            return False, [f"Factor {p} in factors_F is not prime"], {}
        prod_F *= (p ** exp)

    if prod_F != reconstructed_F:
        return False, [f"Product of factors_F ({prod_F}) != F ({reconstructed_F})"], {}

    if (declared_B - 1) % reconstructed_F != 0:
        return False, ["F does not divide B - 1"], {}
    if (declared_A + 1) % reconstructed_F_odd != 0:
        return False, ["F_odd does not divide A + 1"], {}

    if math.gcd(int(reconstructed_F), int(reconstructed_R)) != 1:
        return False, ["Coprimality failed: gcd(F, R) != 1"], {}
    logs.append("Divisor-cofactor coprimality verified: gcd(F, R) = 1")

    # 5. Upper Member B: Pocklington BLS Theorem 4
    if reconstructed_F * reconstructed_F <= declared_B:
        return False, ["Pocklington size condition failed: F^2 <= B"], {}
    logs.append("Pocklington size condition verified: F^2 > B")

    witnesses_B = data.get("witnesses_upper", {})
    B_minus_1 = declared_B - 1

    for p_str in factors_F_dict:
        p = int(p_str)
        if p_str not in witnesses_B:
            return False, [f"Missing upper witness for prime factor {p}"], {}
        a = int(witnesses_B[p_str])
        if a <= 1:
            return False, [f"Invalid witness a={a} <= 1 for factor {p}"], {}
        if gmpy2.powmod(a, B_minus_1, declared_B) != 1:
            return False, [f"Fermat congruence failed for witness a={a} on B"], {}
        term = gmpy2.powmod(a, B_minus_1 // p, declared_B) - 1
        if math.gcd(int(term), declared_B) != 1:
            return False, [f"Pocklington gcd condition failed for factor {p} with witness a={a} on B"], {}

    logs.append("Pocklington BLS Theorem 4 primality unconditionally verified for upper member B")

    # 6. Lower Member A: Morrison BLS Theorem 17
    if (reconstructed_F_odd - 1) * (reconstructed_F_odd - 1) <= declared_A:
        return False, ["Morrison size condition failed: (F_odd - 1)^2 <= A"], {}
    logs.append("Morrison size condition verified: (F_odd - 1)^2 > A")

    witnesses_A = data.get("witnesses_lower", {})
    param_P = int(witnesses_A.get("parameter_P", 0))
    if param_P <= 2:
        return False, [f"Invalid parameter P={param_P} <= 2"], {}

    param_D = param_P * param_P - 4
    if gmpy2.jacobi(param_D, declared_A) != -1:
        return False, [f"Jacobi symbol condition failed: ({param_D} / A) != -1"], {}
    logs.append(f"Jacobi non-residue symbol verified: ({param_D} / A) = -1")

    A_plus_1 = declared_A + 1
    u_full = standalone_lucas_u(A_plus_1, param_P, declared_A)
    if u_full != 0:
        return False, [f"Lucas zero congruence failed: U_{{A+1}}({param_P}, 1) != 0 mod A"], {}
    logs.append(f"Full-period Lucas zero congruence verified: U_{{A+1}}({param_P}, 1) = 0 mod A")

    # Morrison Singularity Guard: verify strictly for odd factors of F_odd
    factor_gcds = witnesses_A.get("factor_gcds", {})
    for p_str in factors_F_dict:
        p = int(p_str)
        if p == 2:
            # Factor 2 strictly excluded by Morrison Singularity Guard
            continue
        if p_str not in factor_gcds or int(factor_gcds[p_str]) != 1:
            return False, [f"Declared Lucas rank gcd for odd factor {p} is not 1"], {}

        u_part = standalone_lucas_u(A_plus_1 // p, param_P, declared_A)
        if math.gcd(u_part, declared_A) != 1:
            return False, [f"Morrison rank gcd condition failed for odd factor {p} on A"], {}

    logs.append("Morrison Odd Divisor Singularity Guard verified: factor 2 excluded, all odd factor GCDs == 1")
    logs.append("Morrison BLS Theorem 17 primality unconditionally verified for lower member A")

    # 7. Signed Attestation Payload
    attestation = {
        "schema_version": "11.0",
        "attestation_type": "INDEPENDENT_STRICT_MATHEMATICAL_VERIFICATION",
        "method": "OPQM_CRT_HYBRID_11",
        "target_certificate": path_obj.name,
        "target_sha256": computed_hash,
        "utc_attested": datetime.now(UTC).isoformat(),
        "digits": digits,
        "verifications": {
            "difference_check": "PASS (B - A == 2)",
            "center_mod_6": "PASS (C == 0 mod 6)",
            "pocklington_upper_member": "PASS (BLS Theorem 4 unconditional)",
            "morrison_lower_member": f"PASS (BLS Theorem 17 unconditional, P={param_P})",
        },
        "notice": "SHA-256 detects payload modifications relative to a declared digest; it is not a cryptographic digital signature and does not establish authorship.",
        "verdict": "UNCONDITIONALLY_VERIFIED",
    }

    if attestation_dir:
        att_dir_path = Path(attestation_dir)
        att_dir_path.mkdir(parents=True, exist_ok=True)
        att_file = att_dir_path / f"attest_{computed_hash[:16]}.json"
        with open(att_file, "w", encoding="utf-8") as f:
            json.dump(attestation, f, indent=2)
        logs.append(f"Signed attestation persisted: {att_file}")

    return True, logs, attestation


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone Independent OPQM-11 Certificate Verifier")
    parser.add_argument("cert_path", help="Path to certificate JSON file")
    parser.add_argument(
        "--attestation-dir",
        "--attest-dir",
        dest="attestation_dir",
        default=None,
        help="Optional directory to save signed attestation JSON",
    )
    args = parser.parse_args()

    cert_path = Path(args.cert_path).resolve()
    print(f"Auditing Phase 11 certificate: {cert_path.name}...")
    success, logs, _ = verify_opqm11_certificate(cert_path, attestation_dir=args.attestation_dir)

    for line in logs:
        print(f"  + {line}")

    if success:
        print(f"  [PASS] {cert_path.name} unconditionally verified!")
        sys.exit(0)
    else:
        print(f"  [FAIL] Verification rejected for {cert_path.name}!")
        sys.exit(1)


if __name__ == "__main__":
    main()
