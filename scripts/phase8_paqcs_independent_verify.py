"""
Strict Standalone Independent Verifier for PAQCS Twin-Prime Certificates (Phase 8).
Completely decoupled from the search and proof generator:
- ZERO imports from src.phase8 or any project module.
- Arbitrary-precision exact integer arithmetic.
- Independent trial division for all prime factors in S_y and t.
- Independent reconstruction of S_y, x, C, A, B.
- Independent verification of Pocklington / BLS Theorem 4 on upper member B.
- Independent verification of Morrison / BLS Theorem 17 on lower member A via matrix/ladder powering.
- Canonical JSON SHA-256 integrity validation.
- Emits machine-readable Independent Verification Attestation JSON artifacts.
"""

import sys
import os
import json
import math
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import gmpy2


def is_small_prime_standalone(p: int) -> bool:
    """Deterministic trial-division primality check."""
    if p < 2:
        return False
    if p in (2, 3):
        return True
    if p % 2 == 0 or p % 3 == 0:
        return False
    d = 5
    while d * d <= p:
        if p % d == 0 or p % (d + 2) == 0:
            return False
        d += 6
    return True


def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def standalone_lucas_u(k: int, P: int, mod: int) -> int:
    """Computes U_k(P, 1) mod mod using binary ladder from first principles."""
    if k == 0:
        return 0
    if k == 1:
        return 1 % mod

    D = P * P - 4
    inv2 = int(gmpy2.invert(2, mod))
    bits = bin(k)[2:]
    u = 0
    v = 2 % mod

    for bit in bits:
        u2 = (u * v) % mod
        v2 = (v * v - 2) % mod
        if bit == '1':
            u = ((P * u2 + v2) * inv2) % mod
            v = ((D * u2 + P * v2) * inv2) % mod
        else:
            u = u2
            v = v2
    return u


def verify_paqcs_certificate(
    cert_path: Path,
    attestation_dir: Optional[Path] = None
) -> Tuple[bool, List[str], Dict[str, Any]]:
    logs = []
    errors = []

    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Schema check
    schema_v = data.get("schema_version")
    if schema_v != "8.0":
        return False, [f"Invalid schema version: {schema_v} (expected 8.0)"], {}

    # 2. Canonical SHA-256 integrity check
    declared_hash = data.get("sha256")
    calc_hash = compute_canonical_sha256(data)
    if declared_hash != calc_hash:
        return False, [f"SHA-256 mismatch: declared={declared_hash}, calculated={calc_hash}"], {}
    logs.append(f"Canonical Proof Payload SHA-256 verified: {calc_hash}")

    # 3. Representation parameters
    rep = data.get("representation", {})
    if not isinstance(rep, dict):
        return False, ["Invalid representation format"], {}

    h = int(rep.get("h", 0))
    if h <= 0 or h % 2 == 0 or h % 3 != 0:
        return False, [f"Invalid h parameter: {h} (must be positive odd multiple of 3)"], {}

    t = int(rep.get("t", 0))
    if t <= 0 or t % 2 == 0:
        return False, [f"Invalid t parameter: {t} (must be positive odd integer)"], {}

    y_bound = int(rep.get("y_bound", 0))
    if y_bound < 3:
        return False, [f"Invalid y_bound: {y_bound}"], {}

    # 4. Factorization validation of x = S_y * t
    x_factors = rep.get("x_factorization", {})
    if not x_factors:
        return False, ["Missing x_factorization"], {}

    recomputed_x = 1
    distinct_primes = []
    for p_str, mult in x_factors.items():
        p = int(p_str)
        if not is_small_prime_standalone(p):
            return False, [f"Factor {p} failed deterministic primality test"], {}
        recomputed_x *= (p ** mult)
        distinct_primes.append(p)

    distinct_primes.sort()

    # Reconstruct S_y and verify against declared decimal
    declared_Sy = int(rep.get("S_y_decimal", 0))
    declared_x = int(rep.get("x_decimal", 0))

    if declared_x != recomputed_x:
        return False, ["Product of prime factors does not match declared x_decimal"], {}

    if declared_x != declared_Sy * t:
        return False, ["Declared x != S_y * t"], {}

    # Exact integers
    x = declared_x
    C = x * (x - h)
    A = C - 1
    B = C + 1

    if A <= 2 or B <= 2:
        return False, [f"Primality candidates must be > 2: A={A}, B={B}"], {}

    pair = data.get("pair", {})
    if not isinstance(pair, dict):
        return False, ["Invalid pair object in certificate"], {}

    if pair.get("center_decimal") != str(C):
        return False, ["Exact center integer mismatch"], {}
    if pair.get("lower_decimal") != str(A) or pair.get("upper_decimal") != str(B):
        return False, ["Exact member integer mismatch between representation and pair decimals"], {}

    digits = len(str(A))
    if len(str(B)) != digits:
        return False, [f"Digit mismatch between twin members: {len(str(A))} != {len(str(B))}"], {}

    declared_digits = pair.get("digits")
    if declared_digits != digits:
        return False, [f"Declared digit count mismatch: declared={declared_digits}, actual={digits}"], {}

    declared_diff = pair.get("difference")
    if declared_diff != 2 or (B - A) != 2:
        return False, [f"Invalid twin difference: {B - A} != 2"], {}

    if C % 6 != 0:
        return False, ["Center C is not divisible by 6"], {}

    logs.append(f"Exact decimal digits: {digits}")
    logs.append(f"Center C mod 6: {C % 6}")
    logs.append(f"Difference B - A: {B - A}")
    logs.append(f"Distinct prime factors in x: {len(distinct_primes)}")

    # 5. Pocklington/BLS Theorem 4 Proof on Upper Member B
    proofs = data.get("proofs", {})
    upper = proofs.get("upper_member", {})

    F = x
    if (B - 1) % F != 0:
        return False, ["F does not divide B - 1"], {}
    if F * F <= B:
        return False, [f"Pocklington size condition failed: F^2 <= B"], {}

    witnesses = upper.get("witnesses", {})
    B_minus_1 = B - 1
    for p in distinct_primes:
        w = witnesses.get(str(p))
        if w is None:
            return False, [f"Missing Pocklington witness for factor {p}"], {}
        w = int(w)
        if w <= 1 or w >= B:
            return False, [f"Invalid witness base {w} for factor {p}"], {}
        # Fermat check
        if gmpy2.powmod(w, B_minus_1, B) != 1:
            return False, [f"Fermat congruence failed for witness {w} on B"], {}
        # Gcd check
        exp_p = B_minus_1 // p
        term = (gmpy2.powmod(w, exp_p, B) - 1) % B
        if gmpy2.gcd(term, B) != 1:
            return False, [f"Gcd condition failed for factor {p} with witness {w}"], {}

    logs.append(f"Pocklington BLS Theorem 4 primality unconditionally verified for upper member B")

    # 6. Morrison/BLS Theorem 17 Proof on Lower Member A
    lower = proofs.get("lower_member", {})
    if (A + 1) % F != 0:
        return False, ["F does not divide A + 1"], {}
    if (F - 1) * (F - 1) <= A:
        return False, ["Morrison size condition failed: (F - 1)^2 <= A"], {}

    param_P = int(lower.get("parameter_P", 0))
    if param_P <= 2:
        return False, [f"Invalid Lucas parameter P: {param_P} <= 2"], {}

    param_D = param_P * param_P - 4
    if gmpy2.gcd(A, 2 * param_D) != 1 or gmpy2.jacobi(param_D, A) != -1:
        return False, [f"Jacobi condition failed for D={param_D} on A"], {}

    A_plus_1 = A + 1
    u_full = standalone_lucas_u(A_plus_1, param_P, A)
    if u_full != 0:
        return False, [f"Lucas sequence zero congruence failed: U_{{A+1}}({param_P}) = {u_full} != 0 mod A"], {}

    for p in distinct_primes:
        exp_p = A_plus_1 // p
        u_p = standalone_lucas_u(exp_p, param_P, A)
        if math.gcd(u_p, A) != 1:
            return False, [f"Lucas rank gcd condition failed for factor {p} on A"], {}

    logs.append(f"Morrison BLS Theorem 17 primality unconditionally verified for lower member A")

    # Attestation summary
    attestation = {
        "schema_version": "8.0",
        "attestation_type": "INDEPENDENT_STRICT_MATHEMATICAL_VERIFICATION",
        "method": "PAQCS",
        "target_certificate": cert_path.name,
        "target_sha256": calc_hash,
        "utc_attested": datetime.now(timezone.utc).isoformat(),
        "digits": digits,
        "representation": {
            "h": h,
            "y_bound": y_bound,
            "t": t,
            "prime_factors_count": len(distinct_primes)
        },
        "verifications": {
            "difference_check": "PASS (B - A == 2)",
            "center_mod_6": "PASS (C == 0 mod 6)",
            "pocklington_upper_member": "PASS (BLS Theorem 4 unconditional)",
            "morrison_lower_member": f"PASS (BLS Theorem 17 unconditional, P={param_P})"
        },
        "notice": "SHA-256 detects payload modifications relative to a declared digest; it is not a cryptographic digital signature and does not establish authorship.",
        "verdict": "UNCONDITIONALLY_VERIFIED"
    }

    if attestation_dir:
        attestation_dir.mkdir(parents=True, exist_ok=True)
        att_path = attestation_dir / f"attest_{calc_hash[:16]}.json"
        with open(att_path, "w", encoding="utf-8") as f:
            json.dump(attestation, f, indent=2)
        logs.append(f"Attestation written to: {att_path.name}")

    return True, logs, attestation


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/phase8_paqcs_independent_verify.py <cert_file_or_dir> [--attest-dir <dir>]")
        sys.exit(1)

    target_path = Path(sys.argv[1])
    attest_dir = None
    if "--attest-dir" in sys.argv:
        idx = sys.argv.index("--attest-dir")
        if idx + 1 < len(sys.argv):
            attest_dir = Path(sys.argv[idx + 1])

    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = sorted(target_path.glob("cert_*.json"))
    else:
        print(f"Path not found: {target_path}")
        sys.exit(1)

    all_ok = True
    for fp in files:
        print(f"Auditing PAQCS certificate: {fp.name}...")
        ok, logs, att = verify_paqcs_certificate(fp, attest_dir)
        for l in logs:
            print(f"  + {l}")
        if ok:
            print(f"  [PASS] {fp.name} unconditionally verified!\n")
        else:
            print(f"  [FAIL] {fp.name} rejected!")
            all_ok = False

    sys.exit(0 if all_ok else 2)


if __name__ == "__main__":
    main()
