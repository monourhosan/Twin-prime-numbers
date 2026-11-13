"""
Builds the frozen authoritative historical inventory of all previously recorded twin-prime pairs
across all phases (Phase 1, 2, 3, 4, 5).
Computes exact raw file SHA-256 hashes, canonical payload SHA-256 hashes,
canonical pair keys (min(P, Q), max(P, Q)), and links any attestations.
"""

import os
import sys
import json
import glob
import hashlib
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parent.parent

def compute_raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compute_canonical_json_sha256(data: Dict[str, Any]) -> str:
    clean = {k: v for k, v in data.items() if k != "sha256"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def build_inventory() -> List[Dict[str, Any]]:
    # Collect all certificate JSON files
    cert_paths = sorted(
        glob.glob(str(REPO_ROOT / "proofs" / "cert_*.json")) +
        glob.glob(str(REPO_ROOT / "proofs" / "*" / "cert_*.json")) +
        glob.glob(str(REPO_ROOT / "proofs" / "*" / "imported_cert_*.json"))
    )

    inventory = []
    
    # Map of attestations
    attestations = {}
    for att_path in glob.glob(str(REPO_ROOT / "proofs" / "*" / "attestations" / "*.json")):
        p = Path(att_path)
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            # key by target cert name or hash
            target_name = d.get("target_certificate")
            target_hash = d.get("target_sha256") or d.get("proof_payload_sha256")
            rel_path = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
            if target_name:
                attestations[target_name] = {"path": rel_path, "verdict": d.get("result") or d.get("verdict"), "hash": target_hash}
            if target_hash:
                attestations[target_hash] = {"path": rel_path, "verdict": d.get("result") or d.get("verdict"), "name": target_name}
        except Exception:
            pass

    for cp_str in cert_paths:
        cp = Path(cp_str)
        raw_hash = compute_raw_sha256(cp)
        with open(cp, "r", encoding="utf-8") as f:
            data = json.load(f)

        rel_cert_path = str(cp.relative_to(REPO_ROOT)).replace("\\", "/")

        if "schema_version" in data and data["schema_version"] == "5.0":
            phase = "Phase 5"
            family = data.get("family", "smooth_center")
            P_str = data["lower_decimal"]
            Q_str = data["upper_decimal"]
            C_str = data.get("center_decimal", str(int(P_str) + 1))
            timestamp = data.get("search_provenance", {}).get("utc_found") or data.get("created_at") or "2026-11-13"
            source = "Phase 5 SCCA search"
            origin_type = "discovered_in_repo"
            canonical_sha256 = data.get("sha256") or compute_canonical_json_sha256(data)

        elif "schema_version" in data and data["schema_version"] in ("3.0", "4.0"):
            schema_v = data["schema_version"]
            phase = "Phase 4" if schema_v == "4.0" else "Phase 3"
            family = data.get("family", "k*2^n +/- 1")
            P_str = data["pair"]["lower_decimal"]
            Q_str = data["pair"]["upper_decimal"]
            k = int(data["representation"]["k"])
            n = int(data["representation"]["n"])
            C_str = str(k * (2 ** n))
            timestamp = data.get("search_evidence", {}).get("utc_found") or "unknown"
            if "imported" in cp.name:
                source = data.get("search_evidence", {}).get("provenance", "Imported external discovery")
                origin_type = "imported_external"
            else:
                source = f"{phase} ADRS search"
                origin_type = "discovered_in_repo"
            canonical_sha256 = compute_canonical_json_sha256(data)

        elif "schema_version" in data and data["schema_version"] == "2.0":
            phase = "Phase 2"
            family = data.get("representation", {}).get("family", "k*2^n+/-1")
            P_str = data["p_minus"]
            Q_str = data["p_plus"]
            k = int(data["representation"]["k"])
            n = int(data["representation"]["n"])
            C_str = str(k * (2 ** n))
            timestamp = data.get("timestamp_utc", "2026-11-12")
            source = "Phase 2 CRT-wheel search"
            origin_type = "discovered_in_repo"
            canonical_sha256 = compute_canonical_json_sha256(data)

        elif "certificate_id" in data:
            phase = "Phase 1"
            family = data.get("pair_type", "k * 2^n +/- 1")
            P_str = data["p_minus"]
            Q_str = data["p_plus"]
            k = int(data["k"])
            n = int(data["n"])
            C_str = str(k * (2 ** n))
            timestamp = data.get("timestamp_utc", "2026-11-12")
            source = "Phase 1 CATS search"
            origin_type = "discovered_in_repo"
            canonical_sha256 = data.get("sha256_hash", compute_canonical_json_sha256(data))

        else:
            raise ValueError(f"Unrecognized certificate schema: {cp}")

        # Mathematical sanity checks
        P_val = int(P_str)
        Q_val = int(Q_str)
        if P_val > Q_val:
            P_str, Q_str = Q_str, P_str
            P_val, Q_val = Q_val, P_val

        assert Q_val - P_val == 2, f"Diff is not 2 for {cp}"
        assert P_val % 2 != 0 and Q_val % 2 != 0, f"Values not odd for {cp}"

        # Attestation lookup
        att = attestations.get(cp.name) or attestations.get(canonical_sha256) or attestations.get(raw_hash)
        att_path = att["path"] if att else None
        att_status = att["verdict"] if att else "UNATTESTED"

        record = {
            "canonical_key": f"{P_str}:{Q_str}",
            "P": P_str,
            "Q": Q_str,
            "digits_P": len(P_str),
            "digits_Q": len(Q_str),
            "center_C": C_str,
            "phase": phase,
            "family": family,
            "discovery_timestamp": timestamp,
            "certificate_path": rel_cert_path,
            "attestation_path": att_path,
            "attestation_status": att_status,
            "raw_sha256": raw_hash,
            "canonical_payload_sha256": canonical_sha256,
            "source": source,
            "origin_type": origin_type
        }
        inventory.append(record)

    # Sort deterministically by digits ascending, then canonical key
    inventory.sort(key=lambda r: (r["digits_P"], r["canonical_key"]))
    return inventory

def main():
    inventory = build_inventory()
    out_dir = REPO_ROOT / "research" / "phase5_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = out_dir / "historical_inventory.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    inv_bytes = out_file.read_bytes()
    inv_sha256 = hashlib.sha256(inv_bytes).hexdigest()
    
    hash_file = out_dir / "historical_inventory.sha256"
    with open(hash_file, "w", encoding="utf-8") as f:
        f.write(f"{inv_sha256}  historical_inventory.json\n")

    # Also mirror into reports/phase5_audit for compliance with Deliverable A path
    reports_dir = REPO_ROOT / "reports" / "phase5_audit"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "historical_inventory.json", "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    with open(reports_dir / "historical_inventory.sha256", "w", encoding="utf-8") as f:
        f.write(f"{inv_sha256}  historical_inventory.json\n")

    print(f"Authoritative Historical Inventory generated: {len(inventory)} certificates")
    print(f"Output: {out_file}")
    print(f"SHA-256: {inv_sha256}")
    
    # Summary of digit bands
    by_phase = {}
    for r in inventory:
        by_phase.setdefault(r["phase"], []).append(r)
    for p, items in sorted(by_phase.items()):
        digits = [x["digits_P"] for x in items]
        print(f"  {p}: {len(items)} certs, digits range [{min(digits)}, {max(digits)}]")

if __name__ == "__main__":
    main()
