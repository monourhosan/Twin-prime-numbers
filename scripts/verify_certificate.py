"""
Independent Primality Certificate Auditor
Reads a JSON certificate, verifies the SHA-256 digest, and independently re-proves
primality using Python's native arbitrary-precision arithmetic and SymPy.
"""

import sys
import json
import hashlib
from pathlib import Path
import sympy

def audit_certificate(cert_path: Path):
    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cert_id = data["certificate_id"]
    p_minus = int(data["p_minus"])
    p_plus = int(data["p_plus"])
    status = data["proof_status"]
    digits = data["digits"]
    sha256_decl = data["sha256_hash"]

    # 1. Check digit lengths
    assert len(str(p_plus)) == digits, f"Digit count mismatch: {len(str(p_plus))} vs {digits}"
    assert p_plus - p_minus == 2, f"Gaps is not 2: {p_plus} - {p_minus} = {p_plus - p_minus}"

    # 2. Verify SHA-256 hash
    hasher = hashlib.sha256()
    p_plus_cond = data.get("p_plus_proof", {}).get("condition_checked", "") if data.get("p_plus_proof") else ""
    p_minus_cond = data.get("p_minus_proof", {}).get("condition_checked", "") if data.get("p_minus_proof") else ""
    canonical_str = f"{cert_id}|{data['pair_type']}|{data['p_minus']}|{data['p_plus']}|{status}|{p_plus_cond}|{p_minus_cond}"
    hasher.update(canonical_str.encode("utf-8"))
    sha256_calc = hasher.hexdigest()

    assert sha256_calc == sha256_decl, f"Hash mismatch: calculated {sha256_calc} != {sha256_decl}"

    # 3. Independent SymPy ground truth check
    assert sympy.isprime(p_minus), f"p_minus is composite: {p_minus}"
    assert sympy.isprime(p_plus), f"p_plus is composite: {p_plus}"

    # 4. Independent Proth theorem check
    if data.get("p_plus_proof"):
        w = data["p_plus_proof"]["witness"]
        assert pow(w, (p_plus - 1) // 2, p_plus) == p_plus - 1, f"Proth witness {w} failed for {p_plus}"

    # 5. Independent LLR check
    if data.get("p_minus_proof") and data.get("n") and data.get("k"):
        n = data["n"]
        k = data["k"]
        p_witness = data["p_minus_proof"]["witness_p"]
        v_prev = 2
        v_curr = p_witness
        for _ in range(1, k):
            v_next = (p_witness * v_curr - v_prev) % p_minus
            v_prev = v_curr
            v_curr = v_next
        u = v_curr
        for _ in range(n - 2):
            u = (pow(u, 2, p_minus) - 2) % p_minus
        assert u == 0, f"LLR sequence failed for {p_minus}: final u = {u}"

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_certificate.py <path_to_cert.json>")
        sys.exit(1)
    target = Path(sys.argv[1])
    if target.is_dir():
        certs = list(target.glob("*.json"))
        print(f"Auditing {len(certs)} certificates in {target}...")
        for c in certs:
            audit_certificate(c)
            print(f"  [PASS] {c.name}")
        print("All certificates passed independent audit!")
    else:
        audit_certificate(target)
        print(f"[PASS] Certificate {target.name} verified successfully.")
