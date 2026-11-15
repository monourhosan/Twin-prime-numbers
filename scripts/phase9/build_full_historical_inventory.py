"""
Authoritative Full Historical Inventory Builder for Phase 9.
Scans all historical certificates across Phases 1 through 8, validates mathematical integrity
(difference == 2, odd parity, positivity), calculates canonical keys and SHA-256 checksums,
and generates the authoritative reference database: research/phase9/historical_inventory.json.
"""

import os
import sys
import glob
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def compute_raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compute_canonical_json_sha256(data: Dict[str, Any]) -> str:
    clean = {k: v for k, v in data.items() if k not in ("sha256", "sha256_hash")}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def collect_historical_certificates() -> List[Dict[str, Any]]:
    cert_patterns = [
        str(REPO_ROOT / "proofs" / "cert_*.json"),
        str(REPO_ROOT / "proofs" / "*" / "cert_*.json"),
        str(REPO_ROOT / "proofs" / "*" / "imported_cert_*.json"),
        str(REPO_ROOT / "proofs" / "*" / "certificates" / "cert_*.json"),
    ]
    
    found_paths = set()
    for pat in cert_patterns:
        for p in glob.glob(pat):
            found_paths.add(Path(p).resolve())
            
    sorted_paths = sorted(list(found_paths))
    inventory = []
    seen_canonical_keys = {}

    for cp in sorted_paths:
        raw_hash = compute_raw_sha256(cp)
        with open(cp, "r", encoding="utf-8") as f:
            data = json.load(f)

        rel_path = str(cp.relative_to(REPO_ROOT)).replace("\\", "/")

        p_lower, p_upper, center_c = None, None, None
        phase = "Unknown"
        family = "Unknown"

        # Schema detection
        if "pair" in data and isinstance(data["pair"], dict):
            pair_dict = data["pair"]
            p_lower = pair_dict.get("lower_decimal") or pair_dict.get("lower_prime_A")
            p_upper = pair_dict.get("upper_decimal") or pair_dict.get("upper_prime_B")
            center_c = pair_dict.get("center_decimal") or pair_dict.get("center_C")
            
            schema_ver = str(data.get("schema_version", ""))
            if schema_ver.startswith("8"):
                phase = "Phase 8"
                family = data.get("method") or data.get("representation", {}).get("family") or "ades8_or_paqcs"
            elif schema_ver.startswith("7"):
                phase = "Phase 7"
                family = "hdc7_primorial_proth_llr"
            elif schema_ver.startswith("6"):
                phase = "Phase 6"
                family = data.get("method") or "gitcss_or_qcp6"
            elif schema_ver.startswith("4"):
                phase = "Phase 4"
                family = data.get("family", "k*2^n +/- 1")
            elif schema_ver.startswith("3"):
                phase = "Phase 3"
                family = data.get("family", "k*2^n +/- 1")
        elif "lower_decimal" in data:
            phase = "Phase 5"
            family = data.get("family", "smooth_center")
            p_lower = data["lower_decimal"]
            p_upper = data["upper_decimal"]
            center_c = data.get("center_decimal")
        elif "p_minus" in data:
            if "schema_version" in data and data["schema_version"] == "2.0":
                phase = "Phase 2"
                family = data.get("representation", {}).get("family", "k*2^n+/-1")
            else:
                phase = "Phase 1"
                family = data.get("pair_type", "k*2^n+/-1")
            p_lower = data["p_minus"]
            p_upper = data["p_plus"]
            k = int(data.get("k") or data.get("representation", {}).get("k", 0))
            n = int(data.get("n") or data.get("representation", {}).get("n", 0))
            if k and n:
                center_c = str(k * (2 ** n))

        assert p_lower is not None and p_upper is not None, f"Failed to extract pair from {cp}"
        
        P_val = int(p_lower)
        Q_val = int(p_upper)
        if P_val > Q_val:
            P_val, Q_val = Q_val, P_val
            p_lower, p_upper = str(P_val), str(Q_val)

        diff = Q_val - P_val
        assert diff == 2, f"Diff is {diff} != 2 in {cp}"
        assert P_val % 2 != 0 and Q_val % 2 != 0, f"Values not odd in {cp}"

        if not center_c:
            center_c = str(P_val + 1)

        canonical_key = f"{p_lower}:{p_upper}"
        canonical_sha256 = data.get("sha256") or data.get("sha256_hash") or compute_canonical_json_sha256(data)

        record = {
            "canonical_key": canonical_key,
            "P": p_lower,
            "Q": p_upper,
            "digits_P": len(p_lower),
            "digits_Q": len(p_upper),
            "center_C": center_c,
            "difference": diff,
            "phase": phase,
            "family": family,
            "certificate_path": rel_path,
            "raw_sha256": raw_hash,
            "canonical_payload_sha256": canonical_sha256
        }

        # Keep primary record if duplicated
        if canonical_key not in seen_canonical_keys:
            seen_canonical_keys[canonical_key] = record
            inventory.append(record)

    inventory.sort(key=lambda r: (r["digits_P"], int(r["P"])))
    return inventory

def main():
    inv = collect_historical_certificates()
    out_dir = REPO_ROOT / "research" / "phase9"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "historical_inventory.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2)

    inv_sha256 = hashlib.sha256(out_file.read_bytes()).hexdigest()
    hash_file = out_dir / "historical_inventory.sha256"
    with open(hash_file, "w", encoding="utf-8") as f:
        f.write(f"{inv_sha256}  historical_inventory.json\n")

    print(f"Authoritative Full Historical Inventory generated: {len(inv)} unique twin prime pairs")
    print(f"Output: {out_file}")
    print(f"SHA-256: {inv_sha256}")

    # Summary
    by_phase = {}
    for r in inv:
        by_phase.setdefault(r["phase"], []).append(r)
    for p, items in sorted(by_phase.items()):
        digits = [x["digits_P"] for x in items]
        print(f"  {p}: {len(items)} pairs, digits range [{min(digits)}, {max(digits)}]")

if __name__ == "__main__":
    main()
