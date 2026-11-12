"""
Phase 4 Version 4.0 Primality Certificate & Proof Payload Generator.
Adheres strictly to the two-tier immutable artifact design:
- Tier A: Immutable Proof Payload (claim_level: PROOF_GENERATED_UNVERIFIED)
- Tier B: Independent Verification Attestation (linked via proof_payload_sha256)
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

class TwinPrimeCertificateV4:
    def __init__(
        self,
        k: int,
        n: int,
        proth_witness: int,
        llr_p: int,
        llr_u0: int,
        campaign_id: str,
        task_id: str,
        config_sha256: str,
        git_commit: Optional[str] = None,
        utc_found: Optional[str] = None,
        claim_level: str = "PROOF_GENERATED_UNVERIFIED"
    ):
        self.schema_version = "4.0"
        self.family = "k*2^n +/- 1"
        self.k = k
        self.n = n

        center = k * (1 << n)
        self.p_minus = center - 1
        self.p_plus = center + 1

        self.lower_digits = len(str(self.p_minus))
        self.upper_digits = len(str(self.p_plus))

        self.proth_witness = proth_witness
        self.llr_p = llr_p
        self.llr_u0 = str(llr_u0)

        self.campaign_id = campaign_id
        self.task_id = task_id
        self.config_sha256 = config_sha256

        if not git_commit:
            try:
                import subprocess
                res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2)
                self.git_commit = res.stdout.strip()[:10] if res.returncode == 0 else "unknown"
            except Exception:
                self.git_commit = "unknown"
        else:
            self.git_commit = git_commit

        self.utc_found = utc_found or datetime.now(timezone.utc).isoformat()
        self.claim_level = claim_level

    def to_dict(self) -> Dict[str, Any]:
        """Builds immutable proof payload dictionary."""
        return {
            "schema_version": self.schema_version,
            "family": self.family,
            "representation": {
                "k": str(self.k),
                "n": self.n
            },
            "pair": {
                "lower_decimal": str(self.p_minus),
                "upper_decimal": str(self.p_plus),
                "gap": 2,
                "lower_digits": self.lower_digits,
                "upper_digits": self.upper_digits
            },
            "upper_proof": {
                "theorem": "Proth",
                "witness": str(self.proth_witness),
                "modular_result": "-1"
            },
            "lower_proof": {
                "theorem": "Lucas-Lehmer-Riesel/Rodseth",
                "P": str(self.llr_p),
                "jacobi_P_minus_2": 1,
                "jacobi_P_plus_2": -1,
                "initial_Vk_mod_A": str(self.llr_u0),
                "final_residue": "0"
            },
            "search_evidence": {
                "campaign_id": self.campaign_id,
                "task_id": self.task_id,
                "config_sha256": self.config_sha256,
                "git_commit": self.git_commit,
                "utc_found": self.utc_found
            },
            "claim_level": self.claim_level
        }

    def canonical_json(self) -> str:
        """Produces canonical JSON serialization (sorted keys, compact separators)."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    def compute_payload_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def save_payload_file(self, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload_data = self.to_dict()
        digest = self.compute_payload_sha256()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload_data, f, indent=2)
        return digest

    @classmethod
    def from_file(cls, path: Path) -> "TwinPrimeCertificateV4":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        rep = d["representation"]
        search = d.get("search_evidence", {})
        u_proof = d["upper_proof"]
        l_proof = d["lower_proof"]

        return cls(
            k=int(rep["k"]),
            n=int(rep["n"]),
            proth_witness=int(u_proof["witness"]),
            llr_p=int(l_proof["P"]),
            llr_u0=int(l_proof["initial_Vk_mod_A"]),
            campaign_id=search.get("campaign_id", ""),
            task_id=search.get("task_id", ""),
            config_sha256=search.get("config_sha256", ""),
            git_commit=search.get("git_commit", ""),
            utc_found=search.get("utc_found"),
            claim_level=d.get("claim_level", "PROOF_GENERATED_UNVERIFIED")
        )
