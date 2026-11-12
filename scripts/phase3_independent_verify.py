"""
Standalone Strict Independent Verifier for Twin-Prime Certificates (Phase 3).
Completely decoupled from the search engine:
- Zero imports from search engine modules (src.phase2 or src.phase3).
- Computes Lucas V_k(P, 1) mod A via 2x2 Binary Matrix Exponentiation (not Montgomery ladder).
- Standalone Jacobi symbol calculation.
- Verifies exact Proth & LLR mathematical preconditions and congruences.
- Strict fail-closed validation on any tampering.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

BASELINE_INVENTORY_SHA256 = "66256602ba495853c0ef9ead316f36f0b9c57d99211eea7fe420d15c24416356"

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
    """
    Computes V_k(P, 1) mod mod using 2x2 matrix powering:
    [V_{k+1}, V_k]^T = [[P, -1], [1, 0]]^k * [V_1, V_0]^T mod mod
    where V_0 = 2, V_1 = P.
    """
    if k == 0:
        return 2 % mod
    if k == 1:
        return P % mod
    M = [[P % mod, (-1) % mod], [1, 0]]
    Mk = matrix_pow_2x2(M, k, mod)
    # V_k is Mk[1][0] * V_1 + Mk[1][1] * V_0
    vk = (Mk[1][0] * (P % mod) + Mk[1][1] * 2) % mod
    return vk

def verify_certificate_file(cert_path: Path) -> Tuple[bool, List[str]]:
    """Strictly audits a JSON certificate file."""
    errors = []
    logs = []

    if not cert_path.exists():
        return False, [f"Certificate file not found: {cert_path}"]

    try:
        with open(cert_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"JSON parse error: {e}"]

    # 1. Schema version
    version = data.get("schema_version")
    if version not in ("2.0", "3.0"):
        errors.append(f"Unsupported schema version: {version}")

    # 2. Extract representation
    rep = data.get("representation", {})
    if "k" not in rep or "n" not in rep:
        errors.append("Missing representation parameters (k, n)")
        return False, errors

    try:
        k = int(rep["k"])
        n = int(rep["n"])
    except ValueError:
        errors.append(f"Non-integer k or n: k={rep.get('k')}, n={rep.get('n')}")
        return False, errors

    if k <= 0 or k % 2 == 0:
        errors.append(f"k must be positive odd integer, got k={k}")
    if n < 2:
        errors.append(f"n must be >= 2, got n={n}")
    if k >= (1 << n):
        errors.append(f"Theorem requirement k < 2^n violated: k={k} >= 2^{n}")

    # 3. Exact integer arithmetic
    expected_minus = k * (1 << n) - 1
    expected_plus = k * (1 << n) + 1

    p_minus_str = data.get("p_minus") or data.get("pair", {}).get("lower_decimal")
    p_plus_str = data.get("p_plus") or data.get("pair", {}).get("upper_decimal")

    if not p_minus_str or not p_plus_str:
        errors.append("Missing decimal strings in certificate")
        return False, errors

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

    # 4. Proth's Theorem verification for p_plus
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

    # 5. LLR Theorem verification for p_minus
    proof_minus = data.get("proof_minus") or data.get("lower_proof")
    if not proof_minus:
        errors.append("Missing lower_proof / proof_minus")
    else:
        params = proof_minus.get("parameters", {}) if "parameters" in proof_minus else proof_minus
        P_param = int(params.get("P") or params.get("parameter_P"))

        # Jacobi conditions
        j_minus = standalone_jacobi(P_param - 2, p_minus)
        j_plus = standalone_jacobi(P_param + 2, p_minus)
        if j_minus != 1 or j_plus != -1:
            errors.append(f"Riesel Jacobi condition failed: ({P_param}-2/A)={j_minus} (exp 1), ({P_param}+2/A)={j_plus} (exp -1)")
        else:
            logs.append(f"Riesel Jacobi conditions confirmed: ({P_param}-2/A)=1, ({P_param}+2/A)=-1")

        # Independent Lucas evaluation via matrix power
        u0_matrix = lucas_v_matrix(k, P_param, p_minus)
        u0_decl = params.get("u0") or params.get("initial_Vk_mod_A")
        if u0_decl and str(u0_matrix) != str(u0_decl):
            errors.append(f"Initial u0 matrix recomputation mismatch: computed {u0_matrix} != {u0_decl}")
        else:
            logs.append("Initial u0 confirmed via independent 2x2 matrix powering")

        # Recurrence iteration: u_{i+1} = u_i^2 - 2 mod A
        u = u0_matrix
        for _ in range(n - 2):
            u = (pow(u, 2, p_minus) - 2) % p_minus

        if u != 0:
            errors.append(f"LLR sequence failed: final u_{{n-2}} = {u} != 0 mod A")
        else:
            logs.append(f"LLR sequence verified: u_{{n-2}} == 0 mod A (A is unconditionally prime)")

    # 6. Artifact Checksum validation (P0 defect resolution)
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/phase3_independent_verify.py <file_or_directory> [...]")
        sys.exit(1)

    targets = [Path(arg) for arg in sys.argv[1:]]
    cert_files = []
    for target in targets:
        if target.is_dir():
            cert_files.extend(sorted(target.glob("*.json")))
        elif target.is_file():
            cert_files.append(target)
        else:
            print(f"Target not found: {target}")
            sys.exit(1)

    if not cert_files:
        print(f"No certificate files found to verify.")
        sys.exit(0)

    print(f"Independent Strict Verification of {len(cert_files)} certificate(s)...")
    all_passed = True
    for cf in cert_files:
        passed, messages = verify_certificate_file(cf)
        if passed:
            print(f"  [PASS] {cf.name}")
            for m in messages:
                print(f"     + {m}")
        else:
            print(f"  [FAIL] {cf.name}:")
            for err in messages:
                print(f"     - {err}")
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All certificates passed independent strict verification!")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more certificates failed independent verification!")
        sys.exit(1)

if __name__ == "__main__":
    main()
