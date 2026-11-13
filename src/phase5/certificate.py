"""
Phase 5 Version 5.0 Twin-Prime Proof Certificate Generator.
Implements the canonical Schema 5.0 structure for Smooth-Center Twin Primes.
Ensures two-tier integrity:
1. Immutable Proof Payload with canonical SHA-256 digest.
2. Complete mathematical verification traces for both lower (Morrison) and upper (Pocklington) members.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from .candidates import TwinPairCandidate

def compute_canonical_sha256(data: Dict[str, Any]) -> str:
    """Computes canonical SHA-256 over a JSON dictionary excluding any existing sha256 field."""
    clean_dict = {k: v for k, v in data.items() if k != "sha256"}
    canonical_json = json.dumps(clean_dict, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

class TwinPrimeCertificateV5:
    """Represents a Phase 5 Schema 5.0 deterministic proof certificate."""
    def __init__(
        self,
        candidate: TwinPairCandidate,
        lower_proof: Dict[str, Any],
        upper_proof: Dict[str, Any],
        search_provenance: Dict[str, Any],
        status: str = "PROVEN_BOTH",
        novelty_status: str = "NEW_TO_REPO_ONLY",
        created_at: Optional[str] = None
    ):
        self.schema_version = "5.0"
        self.family = "smooth_center"
        self.candidate = candidate
        self.lower_proof = lower_proof
        self.upper_proof = upper_proof
        self.search_provenance = search_provenance
        self.status = status
        self.novelty_status = novelty_status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Constructs canonical certificate dictionary."""
        fam = self.candidate.family
        data: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "status": self.status,
            "family": self.family,
            "family_id": fam.family_id,
            "parameters": {
                "exponents": {str(p): e for p, e in sorted(fam.exponents.items())},
                "t": str(self.candidate.t),
                "F_decimal": str(fam.F),
                "F_odd_decimal": str(fam.F_odd),
                "odd_prime_factors": fam.odd_prime_factors
            },
            "center_decimal": str(self.candidate.C),
            "lower_decimal": str(self.candidate.A),
            "upper_decimal": str(self.candidate.B),
            "digits_lower": self.candidate.digits_A,
            "digits_upper": self.candidate.digits_B,
            "difference_proof": {
                "expression": "B - A = (C + 1) - (C - 1) = 2",
                "exact_difference": self.candidate.B - self.candidate.A
            },
            "primality_proofs": {
                "lower": self.lower_proof,
                "upper": self.upper_proof
            },
            "search_provenance": self.search_provenance,
            "novelty_status": self.novelty_status,
            "created_at": self.created_at
        }
        data["sha256"] = compute_canonical_sha256(data)
        return data

    def save(self, output_dir: Path) -> Path:
        """Saves certificate to JSON file."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"cert_{self.candidate.family.family_id}_t{self.candidate.t}_{self.candidate.digits_A}d.json"
        out_path = output_dir / filename
        data = self.to_dict()
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return out_path
