"""
Canonical JSON serialization and SHA-256 hash generation for Phase 6 certificates.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

SCHEMA_VERSION = "6.0"

def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """Serializes dictionary to canonical deterministic UTF-8 JSON bytes."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes SHA-256 digest of canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()

def build_certificate_payload(
    m: int,
    proof_data: Dict[str, Any],
    campaign_id: str = "gitcss_campaign"
) -> Dict[str, Any]:
    """Assembles authoritative Schema 6.0 certificate dictionary."""
    A = 6 * m - 1
    B = 6 * m + 1
    now_utc = datetime.now(timezone.utc).isoformat()
    
    payload = {
        "schema_version": SCHEMA_VERSION,
        "phase": "Phase 6",
        "method": "GITCSS (General-Integer Twin-Center Segmented Sieve)",
        "campaign_id": campaign_id,
        "timestamp_utc": now_utc,
        "pair": {
            "lower_prime_A": str(A),
            "upper_prime_B": str(B),
            "difference": str(B - A),
            "center_C": str(6 * m),
            "center_m": str(m),
            "digits_A": len(str(A)),
            "digits_B": len(str(B))
        },
        "novelty_audit": {
            "origin_type": "GENERAL_INTEGER",
            "repository_novelty": "NEW_TO_REPOSITORY",
            "global_novelty_status": "PENDING_EXTERNAL_REGISTRY_CHECK"
        },
        "proofs": proof_data
    }
    
    sha256_hash = compute_canonical_sha256(payload)
    payload["canonical_sha256"] = sha256_hash
    return payload

def save_certificate(
    payload: Dict[str, Any],
    out_dir: Path = Path("proofs/phase6/certificates")
) -> Path:
    """Saves certificate to disk with deterministic filename."""
    out_dir.mkdir(parents=True, exist_ok=True)
    digits = payload["pair"]["digits_A"]
    m_val = payload["pair"]["center_m"]
    # Filename format: cert_gitcss_m<m>_<digits>d.json
    filename = f"cert_gitcss_m{m_val}_{digits}d.json"
    file_path = out_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
        
    return file_path
