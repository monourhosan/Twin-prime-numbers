"""
Strict Independent Mathematical Proof Verifier (Phase 2).
Recomputes and independently audits all mathematical proofs, theorems,
preconditions, witnesses, and inventory freshness without circular trust.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Tuple, List, Dict, Any

from .fast_lucas import lucas_v_fast
from .proof_backend import jacobi_symbol, validate_proth_preconditions, validate_llr_preconditions
from .certificate_v2 import TwinPrimeCertificateV2, BASELINE_INVENTORY_SHA256

def verify_certificate_strict(cert_path: Path) -> Tuple[bool, List[str]]:
    logs = []
    errors = []

    if not cert_path.exists():
        return False, [f"Certificate file does not exist: {cert_path}"]

    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Schema version
    if data.get("schema_version") != "2.0":
        errors.append(f"Invalid schema version: {data.get('schema_version')} (expected 2.0)")

    k = int(data["representation"]["k"])
    n = int(data["representation"]["n"])
    p_minus = int(data["p_minus"])
    p_plus = int(data["p_plus"])

    # 2. Mathematical relation and representation
    expected_minus = k * (1 << n) - 1
    expected_plus = k * (1 << n) + 1

    if p_minus != expected_minus:
        errors.append(f"p_minus mismatch: {p_minus} != {expected_minus}")
    if p_plus != expected_plus:
        errors.append(f"p_plus mismatch: {p_plus} != {expected_plus}")
    if p_plus - p_minus != 2:
        errors.append(f"Gap is not 2: {p_plus} - {p_minus} != 2")

    digits_minus = len(str(p_minus))
    digits_plus = len(str(p_plus))
    if digits_minus != data["digits_p_minus"]:
        errors.append(f"Digits minus mismatch: {digits_minus} != {data['digits_p_minus']}")
    if digits_plus != data["digits_p_plus"]:
        errors.append(f"Digits plus mismatch: {digits_plus} != {data['digits_p_plus']}")

    # 3. Checksum verification
    cert_obj = TwinPrimeCertificateV2.from_dict(data)
    if not cert_obj.verify_checksum():
        errors.append(f"Artifact SHA-256 checksum mismatch: declared {data['artifact_sha256']} != computed {cert_obj.compute_sha256()}")
    else:
        logs.append(f"SHA-256 checksum verified: {data['artifact_sha256']}")

    # 4. Proth's Theorem verification for p_plus
    w = int(data["proof_plus"]["witness"])
    v_proth, msg_proth = validate_proth_preconditions(k, n, p_plus)
    if not v_proth:
        errors.append(f"Proth precondition failure: {msg_proth}")
    else:
        exp = (p_plus - 1) // 2
        pow_val = pow(w, exp, p_plus)
        if pow_val != p_plus - 1:
            errors.append(f"Proth theorem failed: {w}^((B-1)/2) mod B = {pow_val} != B - 1")
        else:
            logs.append(f"Proth primality theorem verified for B = k*2^{n}+1 with witness w={w}")

    # 5. LLR Theorem verification for p_minus
    p_llr = int(data["proof_minus"]["parameters"]["P"])
    v_llr, msg_llr = validate_llr_preconditions(k, n, p_minus)
    if not v_llr:
        errors.append(f"LLR precondition failure: {msg_llr}")
    else:
        j1 = jacobi_symbol(p_llr - 2, p_minus)
        j2 = jacobi_symbol(p_llr + 2, p_minus)
        if j1 != 1 or j2 != -1:
            errors.append(f"LLR Jacobi condition failed: Jacobi(P-2, A)={j1} (exp 1), Jacobi(P+2, A)={j2} (exp -1)")
        else:
            logs.append(f"LLR parameter P={p_llr} satisfies Riesel Jacobi criteria: ({p_llr}-2/A)=1, ({p_llr}+2/A)=-1")

        # Verify initial u0
        u0_calc = lucas_v_fast(k, p_llr, p_minus)
        if str(u0_calc) != data["proof_minus"]["parameters"]["u0"]:
            errors.append(f"LLR initial u0 mismatch: computed {u0_calc} != {data['proof_minus']['parameters']['u0']}")
        else:
            logs.append("LLR initial value u0 verified")

        # Iterate sequence u_{i+1} = u_i^2 - 2 mod A
        u = u0_calc
        for _ in range(n - 2):
            u = (pow(u, 2, p_minus) - 2) % p_minus
        if u != 0:
            errors.append(f"LLR sequence failed: final u_{{n-2}} = {u} != 0 mod A")
        else:
            logs.append(f"LLR sequence verified: u_{{n-2}} == 0 mod A (A is unconditionally prime)")

    # 6. Baseline novelty check: ensure pair is NOT in baseline inventory
    baseline_path = Path("research/phase2/baseline_inventory.json")
    if baseline_path.exists():
        with open(baseline_path, "r", encoding="utf-8") as bf:
            baseline = json.load(bf)
        for old in baseline:
            if old.get("k") == k and old.get("n") == n:
                errors.append(f"Pair (k={k}, n={n}) is ALREADY PRESENT in baseline inventory (cert: {old.get('certificate_file')})")
                break
        logs.append("Freshness confirmed: pair is absent from frozen baseline inventory")

    if errors:
        return False, errors
    return True, logs
