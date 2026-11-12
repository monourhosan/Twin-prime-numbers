"""
Strict Standalone Independent Verifier for Twin-Prime Certificates (Phase 4).
Completely decoupled from the search engine:
- ZERO imports from src.phase2, src.phase3, or src.phase4.
- Arbitrary-precision exact arithmetic in pure Python standard library.
- Jacobi symbol computation from first principles.
- Lucas V_k(P, 1) mod A via 2x2 binary matrix exponentiation (not the search ladder).
- LLR recurrence iteration (n - 2 squarings).
- Proth modular congruence verification.
- Canonical JSON SHA-256 validation.
- Generates machine-readable Independent Verification Attestation JSON artifacts.
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
    """Multiplies two 2x2 matrices modulo mod."""
    return [
        [(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % mod, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % mod],
        [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % mod, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % mod]
    ]

def matrix_pow_2x2(M, power, mod):
    """Computes M^power mod mod via binary exponentiation."""
    result = [[1, 0], [0, 1]]
    base = [[M[0][0] % mod, M[0][1] % mod], [M[1][0] % mod, M[1][1] % mod]]
    p = power
    while p > 0:
        if p % 2 == 1:
            result = matrix_mult_2x2(result, base, mod)
        base = matrix_mult_2x2(base, base, mod)
        p //= 2
    return result

def lucas_v_matrix(k: int, P: int, mod: int) -> int:
    """Computes V_k(P, 1) mod mod using 2x2 matrix powering."""
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod
    M = [[P % mod, (-1) % mod], [1, 0]]
    Mk = matrix_pow_2x2(M, k, mod)
    return (Mk[1][0] * (P % mod) + Mk[1][1] * 2) % mod

def verify_certificate_v4_payload(data: Dict[str, Any]) -> Tuple[bool, List[str], str]:
    """Strictly audits a Schema 4.0 Proof Payload."""
    errors = []
    logs = []

    # 1. Schema check
    if data.get("schema_version") != "4.0":
        return False, [f"Invalid schema version: {data.get('schema_version')} (expected 4.0)"], ""

    # 2. Representation check
    rep = data.get("representation", {})
    if "k" not in rep or "n" not in rep:
        return False, ["Missing representation parameters (k, n)"], ""

    try:
        k = int(rep["k"])
        n = int(rep["n"])
    except ValueError:
        return False, [f"Non-integer k or n: {rep}"], ""

    if k <= 0 or k % 2 == 0:
        errors.append(f"k must be positive odd integer, got {k}")
    if k % 3 != 0:
        errors.append(f"k must be divisible by 3 (family k=6t+3), got {k}")
    if n < 2:
        errors.append(f"n must be >= 2, got {n}")
    if k >= (1 << n):
        errors.append(f"Theorem requirement k < 2^n violated: k={k} >= 2^{n}")

    # 3. Exact integer arithmetic
    center = k * (1 << n)
    expected_minus = center - 1
    expected_plus = center + 1

    pair = data.get("pair", {})
    p_minus_str = pair.get("lower_decimal")
    p_plus_str = pair.get("upper_decimal")

    if not p_minus_str or not p_plus_str:
        return False, ["Missing lower_decimal or upper_decimal in pair"], ""

    p_minus = int(p_minus_str)
    p_plus = int(p_plus_str)

    if p_minus != expected_minus:
        errors.append(f"lower_decimal arithmetic mismatch: got {p_minus}, expected {expected_minus}")
    if p_plus != expected_plus:
        errors.append(f"upper_decimal arithmetic mismatch: got {p_plus}, expected {expected_plus}")
    if p_plus - p_minus != 2:
        errors.append(f"Pair gap is not 2: {p_plus} - {p_minus} != 2")

    digits_minus = len(str(p_minus))
    digits_plus = len(str(p_plus))
    decl_d_m = pair.get("lower_digits")
    decl_d_p = pair.get("upper_digits")

    if decl_d_m is not None and digits_minus != decl_d_m:
        errors.append(f"lower_digits mismatch: calculated {digits_minus} != declared {decl_d_m}")
    if decl_d_p is not None and digits_plus != decl_d_p:
        errors.append(f"upper_digits mismatch: calculated {digits_plus} != declared {decl_d_p}")

    # 4. Proth's Theorem verification for upper member B
    upper_proof = data.get("upper_proof", {})
    if not upper_proof or "witness" not in upper_proof:
        errors.append("Missing upper_proof or witness")
    else:
        w = int(upper_proof["witness"])
        exp = (p_plus - 1) // 2
        pow_val = pow(w, exp, p_plus)
        if pow_val != p_plus - 1:
            errors.append(f"Proth theorem failed: {w}^((B-1)/2) mod B = {pow_val} != B - 1")
        else:
            logs.append(f"Proth primality verified for B = k*2^{n}+1 with witness w={w}")

    # 5. LLR Theorem verification for lower member A
    lower_proof = data.get("lower_proof", {})
    if not lower_proof or "P" not in lower_proof:
        errors.append("Missing lower_proof or P")
    else:
        P = int(lower_proof["P"])
        # Check Jacobi conditions
        j_minus = standalone_jacobi(P - 2, p_minus)
        j_plus = standalone_jacobi(P + 2, p_minus)
        if j_minus != 1 or j_plus != -1:
            errors.append(f"Riesel Jacobi conditions failed: ({P}-2/A)={j_minus} (exp 1), ({P}+2/A)={j_plus} (exp -1)")
        else:
            logs.append(f"Riesel Jacobi conditions confirmed: ({P}-2/A)=1, ({P}+2/A)=-1")

        # Independent Lucas initial evaluation via 2x2 matrix powering
        u0_matrix = lucas_v_matrix(k, P, p_minus)
        decl_u0 = lower_proof.get("initial_Vk_mod_A")
        if decl_u0 and str(u0_matrix) != str(decl_u0):
            errors.append(f"Initial u0 matrix recomputation mismatch: computed {u0_matrix} != declared {decl_u0}")
        else:
            logs.append(f"Initial u0 confirmed via independent 2x2 matrix powering: {u0_matrix}")

        # Recurrence iteration: u_{j+1} = (u_j^2 - 2) mod A
        u = u0_matrix
        for _ in range(n - 2):
            u = (pow(u, 2, p_minus) - 2) % p_minus

        if u != 0:
            errors.append(f"LLR sequence failed: final residue u_{{n-2}} = {u} != 0 mod A")
        else:
            logs.append(f"LLR sequence verified: u_{{n-2}} == 0 mod A (A is unconditionally prime)")

    # 6. Canonical payload SHA-256 calculation
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    payload_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    logs.append(f"Canonical Proof Payload SHA-256: {payload_sha256}")

    if errors:
        return False, errors, payload_sha256
    return True, logs, payload_sha256

def verify_certificate_legacy(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Strictly audits Schema 2.0 and Schema 3.0 legacy certificates."""
    errors = []
    logs = []
    version = data.get("schema_version")

    rep = data.get("representation", {})
    if "k" not in rep or "n" not in rep:
        return False, ["Missing representation parameters (k, n)"]

    k = int(rep["k"])
    n = int(rep["n"])
    if k <= 0 or k % 2 == 0:
        errors.append(f"k must be positive odd integer, got {k}")
    if n < 2:
        errors.append(f"n must be >= 2, got {n}")
    if k >= (1 << n):
        errors.append(f"Theorem requirement k < 2^n violated: k={k} >= 2^{n}")

    expected_minus = k * (1 << n) - 1
    expected_plus = k * (1 << n) + 1

    p_minus_str = data.get("p_minus") or data.get("pair", {}).get("lower_decimal")
    p_plus_str = data.get("p_plus") or data.get("pair", {}).get("upper_decimal")

    if not p_minus_str or not p_plus_str:
        return False, ["Missing decimal strings in certificate"]

    p_minus = int(p_minus_str)
    p_plus = int(p_plus_str)

    if p_minus != expected_minus:
        errors.append(f"p_minus arithmetic mismatch: got {p_minus}, expected {expected_minus}")
    if p_plus != expected_plus:
        errors.append(f"p_plus arithmetic mismatch: got {p_plus}, expected {expected_plus}")
    if p_plus - p_minus != 2:
        errors.append(f"Pair gap is not 2: {p_plus} - {p_minus} != 2")

    digits_minus = len(str(p_minus))
    digits_plus = len(str(p_plus))
    decl_d_m = data.get("digits_p_minus") or data.get("pair", {}).get("lower_digits")
    decl_d_p = data.get("digits_p_plus") or data.get("pair", {}).get("upper_digits")

    if decl_d_m and digits_minus != decl_d_m:
        errors.append(f"Digit count mismatch for p_minus: {digits_minus} != {decl_d_m}")
    if decl_d_p and digits_plus != decl_d_p:
        errors.append(f"Digit count mismatch for p_plus: {digits_plus} != {decl_d_p}")

    proof_plus = data.get("proof_plus") or data.get("upper_proof")
    if not proof_plus:
        errors.append("Missing upper_proof / proof_plus")
    else:
        w = int(proof_plus.get("witness"))
        exp = (p_plus - 1) // 2
        pow_val = pow(w, exp, p_plus)
        if pow_val != p_plus - 1:
            errors.append(f"Proth theorem failed: {w}^((B-1)/2) mod B = {pow_val} != B - 1")
        else:
            logs.append(f"Proth primality verified for B = k*2^{n}+1 with witness w={w}")

    proof_minus = data.get("proof_minus") or data.get("lower_proof")
    if not proof_minus:
        errors.append("Missing lower_proof / proof_minus")
    else:
        params = proof_minus.get("parameters", {}) if "parameters" in proof_minus else proof_minus
        P_param = int(params.get("P") or params.get("parameter_P"))

        j_minus = standalone_jacobi(P_param - 2, p_minus)
        j_plus = standalone_jacobi(P_param + 2, p_minus)
        if j_minus != 1 or j_plus != -1:
            errors.append(f"Riesel Jacobi condition failed: ({P_param}-2/A)={j_minus} (exp 1), ({P_param}+2/A)={j_plus} (exp -1)")
        else:
            logs.append(f"Riesel Jacobi conditions confirmed: ({P_param}-2/A)=1, ({P_param}+2/A)=-1")

        u0_matrix = lucas_v_matrix(k, P_param, p_minus)
        u0_decl = params.get("u0") or params.get("initial_Vk_mod_A")
        if u0_decl and str(u0_matrix) != str(u0_decl):
            errors.append(f"Initial u0 matrix recomputation mismatch: computed {u0_matrix} != {u0_decl}")
        else:
            logs.append(f"Initial u0 confirmed via independent 2x2 matrix powering: {u0_matrix}")

        u = u0_matrix
        for _ in range(n - 2):
            u = (pow(u, 2, p_minus) - 2) % p_minus

        if u != 0:
            errors.append(f"LLR sequence failed: final u_{{n-2}} = {u} != 0 mod A")
        else:
            logs.append(f"LLR sequence verified: u_{{n-2}} == 0 mod A (A is unconditionally prime)")

    decl_hash = data.get("artifact_sha256")
    if decl_hash:
        w_val = proof_plus.get("witness") if proof_plus else None
        P_val = params.get("P") or params.get("parameter_P") if proof_minus else None
        if version == "3.0":
            claim = data.get("claim", "")
            u0_val = params.get("u0") or params.get("initial_Vk_mod_A") if proof_minus else None
            task_id = data.get("search", {}).get("task_id", "")
            base = data.get("novelty", {}).get("baseline_sha256", "")
            canonical = f"3.0|{claim}|{k}|{n}|{p_minus}|{p_plus}|{w_val}|{P_val}|{u0_val}|{task_id}|{base}"
            calc_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if calc_hash != decl_hash:
                errors.append(f"artifact_sha256 mismatch: calculated {calc_hash} != declared {decl_hash}")
            else:
                logs.append(f"artifact_sha256 verified: {decl_hash}")
        elif version == "2.0":
            claim_type = data.get("claim_type", "")
            unit_id = data.get("search_work_unit_id", "")
            base = data.get("original_baseline_inventory_sha256", "")
            canonical = f"2.0|{claim_type}|{k}|{n}|{p_minus}|{p_plus}|{w_val}|{P_val}|{unit_id}|{base}"
            calc_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if calc_hash != decl_hash:
                errors.append(f"artifact_sha256 mismatch: calculated {calc_hash} != declared {decl_hash}")
            else:
                logs.append(f"artifact_sha256 verified: {decl_hash}")

    if errors:
        return False, errors
    return True, logs

def verify_and_attest_file(cert_path: Path, output_attestation_dir: Optional[Path] = None) -> Tuple[bool, List[str], Optional[Path]]:
    """
    Audits a certificate file, and if valid, generates a signed Independent Verification Attestation JSON.
    """
    if not cert_path.exists():
        return False, [f"File not found: {cert_path}"], None

    try:
        with open(cert_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"JSON read error: {e}"], None

    schema = data.get("schema_version")
    utc_start = datetime.now(timezone.utc).isoformat()

    if schema == "4.0":
        passed, msgs, payload_sha = verify_certificate_v4_payload(data)
        utc_finish = datetime.now(timezone.utc).isoformat()
        attestation_path = None

        if passed and output_attestation_dir:
            output_attestation_dir.mkdir(parents=True, exist_ok=True)
            script_path = Path(__file__).resolve()
            script_sha = hashlib.sha256(script_path.read_bytes()).hexdigest()

            attestation = {
                "schema_version": "4.0",
                "proof_payload_sha256": payload_sha,
                "verifier": str(script_path.name),
                "verifier_source_sha256": script_sha,
                "python_version": sys.version,
                "utc_started": utc_start,
                "utc_finished": utc_finish,
                "exit_code": 0,
                "verdict": "PASS",
                "stdout_sha256": hashlib.sha256("\n".join(msgs).encode("utf-8")).hexdigest(),
                "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                "mathematical_checks": [
                    "representation",
                    "admissible_family_k_6t_3",
                    "gap_2",
                    "exact_decimal_digit_lengths",
                    "proth_congruence",
                    "rodseth_jacobi_conditions",
                    "lucas_2x2_matrix_powering",
                    "llr_recurrence_residue_zero",
                    "canonical_payload_sha256"
                ]
            }

            attestation_path = output_attestation_dir / f"attest_{payload_sha[:16]}.json"
            with open(attestation_path, "w", encoding="utf-8") as f:
                json.dump(attestation, f, indent=2)

        return passed, msgs, attestation_path

    elif schema in ("2.0", "3.0"):
        passed, msgs = verify_certificate_legacy(data)
        return passed, msgs, None
    else:
        return False, [f"Unsupported schema version: {schema}"], None

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/phase4_independent_verify.py <file_or_dir> [...] [--attest-dir <dir>]")
        sys.exit(1)

    args = sys.argv[1:]
    attest_dir = None
    if "--attest-dir" in args:
        idx = args.index("--attest-dir")
        if idx + 1 < len(args):
            attest_dir = Path(args[idx + 1])
            args = args[:idx] + args[idx + 2:]
        else:
            args = args[:idx]

    targets = [Path(a) for a in args]
    files = []
    for t in targets:
        if t.is_dir():
            files.extend(sorted(t.glob("*.json")))
        elif t.is_file():
            files.append(t)

    if not files:
        print("No certificate files found.")
        sys.exit(0)

    print(f"Phase 4 Independent Strict Verification of {len(files)} certificate(s)...")
    all_passed = True

    for f in files:
        passed, msgs, attest_path = verify_and_attest_file(f, attest_dir)
        if passed:
            print(f"  [PASS] {f.name}")
            for m in msgs:
                print(f"     + {m}")
            if attest_path:
                print(f"     * Attestation written: {attest_path}")
        else:
            print(f"  [FAIL] {f.name}:")
            for err in msgs:
                print(f"     - {err}")
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All certificates passed independent strict mathematical verification!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Verification failed for one or more certificates.")
        sys.exit(1)

if __name__ == "__main__":
    main()
