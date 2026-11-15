"""
Strict Standalone Independent Verifier for HDC-7 Twin-Prime Certificates (Phase 7).
Completely decoupled from the search and proof generator:
- ZERO imports from src.phase7 or any project module.
- Arbitrary-precision exact integer arithmetic.
- Standalone Jacobi symbol implementation.
- Lucas V_k(P, 1) mod A via independent 2x2 binary companion matrix exponentiation.
- Standalone LLR recurrence iteration (n - 2 rounds).
- Standalone Proth congruence verification.
- Canonical JSON SHA-256 integrity validation.
- Emits machine-readable Independent Verification Attestation JSON artifacts.
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional


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


def matrix_mult_2x2(A, B, mod):
    return [
        [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % mod, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % mod],
        [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % mod, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % mod]
    ]


def matrix_pow_2x2(M, power, mod):
    result = [[1, 0], [0, 1]]
    base = [[M[0][0] % mod, M[0][1] % mod], [M[1][0] % mod, M[1][1] % mod]]
    p = power
    while p > 0:
        if p & 1:
            result = matrix_mult_2x2(result, base, mod)
        base = matrix_mult_2x2(base, base, mod)
        p >>= 1
    return result


def standalone_lucas_v_matrix(k: int, P: int, mod: int) -> int:
    """Computes V_k(P, 1) mod mod using 2x2 companion matrix powering."""
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod
    M = [[P % mod, (-1) % mod], [1, 0]]
    Mk = matrix_pow_2x2(M, k, mod)
    return (Mk[1][0] * (P % mod) + Mk[1][1] * 2) % mod


def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_certificate_v7(cert_path: Path, attestation_dir: Optional[Path] = None) -> Tuple[bool, List[str], Dict[str, Any]]:
    logs = []
    errors = []

    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Schema check
    schema_v = data.get("schema_version")
    if schema_v != "7.0":
        return False, [f"Invalid schema version: {schema_v} (expected 7.0)"], {}

    # 2. Canonical SHA-256 verification
    declared_hash = data.get("sha256")
    calc_hash = compute_canonical_sha256(data)
    if declared_hash != calc_hash:
        return False, [f"SHA-256 mismatch: declared={declared_hash}, calculated={calc_hash}"], {}
    logs.append(f"Canonical Proof Payload SHA-256 verified: {calc_hash}")

    # 3. Representation parameters
    rep = data.get("representation", {})
    B_primorial = int(rep["B_primorial"])
    MB = int(rep["M_B"])
    t = int(rep["t"])
    k = int(rep["k"])
    n = int(rep["n"])

    # Verify k = MB * (2t + 1)
    if k != MB * (2 * t + 1):
        return False, [f"k calculation mismatch: {k} != MB*(2t+1)"], {}

    two_n = 1 << n
    if k >= two_n:
        return False, [f"Theorem requirement k < 2^n violated: {k} >= 2^{n}"], {}

    # Exact integers
    C = k * two_n
    A = C - 1
    Bprime = C + 1

    pair = data.get("pair", {})
    if str(A) != pair.get("lower_decimal") or str(Bprime) != pair.get("upper_decimal"):
        return False, ["Exact integer mismatch between representation and pair decimals"], {}

    digits = len(str(A))
    logs.append(f"Exact decimal digits: {digits}")
    logs.append(f"Center C mod 6: {C % 6}")
    logs.append(f"Difference B - A: {Bprime - A}")

    if Bprime - A != 2:
        return False, [f"Invalid twin prime difference: {Bprime - A} != 2"], {}
    if C % 6 != 0:
        return False, ["Center C is not divisible by 6"], {}

    # 4. Proth Proof for Upper Member
    proofs = data.get("proofs", {})
    upper = proofs.get("upper_member", {})
    witness_w = int(upper["witness_w"])
    exp = (Bprime - 1) // 2
    proth_res = pow(witness_w, exp, Bprime)
    if proth_res != Bprime - 1:
        return False, [f"Proth congruence failed: {witness_w}^((B-1)/2) = {proth_res} != -1 mod B"], {}
    logs.append(f"Proth primality verified for upper member B' (witness w={witness_w})")

    # 5. LLR Proof for Lower Member
    lower = proofs.get("lower_member", {})
    param_P = int(lower["parameter_P"])

    # Verify Jacobi conditions
    jm = standalone_jacobi(param_P - 2, A)
    jp = standalone_jacobi(param_P + 2, A)
    if jm != 1 or jp != -1:
        return False, [f"Jacobi conditions failed for P={param_P}: (P-2/A)={jm}, (P+2/A)={jp}"], {}
    logs.append(f"Riesel Jacobi conditions confirmed for lower member: ({param_P}-2/A)=1, ({param_P}+2/A)=-1")

    # Verify u0 via independent 2x2 companion matrix
    u0_calc = standalone_lucas_v_matrix(k, param_P, A)
    u0_declared = int(lower["u0"])
    if u0_calc != u0_declared:
        return False, [f"Initial u0 mismatch: calculated={u0_calc}, declared={u0_declared}"], {}
    logs.append(f"Initial u0 confirmed via independent 2x2 companion matrix powering")

    # Verify LLR recurrence: n - 2 rounds
    u = u0_calc
    for _ in range(n - 2):
        u = (pow(u, 2, A) - 2) % A

    if u != 0:
        return False, [f"LLR sequence failed: final residue u_{{n-2}} = {u} != 0"], {}
    logs.append(f"LLR recurrence sequence verified: u_{{n-2}} == 0 mod A (A is unconditionally prime)")

    # Attestation summary
    attestation = {
        "schema_version": "7.0",
        "attestation_type": "INDEPENDENT_STRICT_MATHEMATICAL_VERIFICATION",
        "target_certificate": cert_path.name,
        "target_sha256": calc_hash,
        "utc_attested": datetime.now(timezone.utc).isoformat(),
        "digits": digits,
        "representation": {
            "B_primorial": B_primorial,
            "M_B": str(MB),
            "t": t,
            "k": str(k),
            "n": n
        },
        "verifications": {
            "difference_check": "PASS (B - A == 2)",
            "center_mod_6": "PASS (C == 0 mod 6)",
            "proth_upper_member": f"PASS (witness w={witness_w})",
            "llr_lower_member": f"PASS (parameter P={param_P}, u_{{n-2}} == 0)",
            "u0_matrix_powering": "PASS (independent 2x2 matrix matches)"
        },
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
        print("Usage: python scripts/phase7_independent_verify.py <cert_file_or_dir> [--attest-dir <dir>]")
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
        print(f"Auditing Phase 7 certificate: {fp.name}...")
        ok, logs, att = verify_certificate_v7(fp, attest_dir)
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
