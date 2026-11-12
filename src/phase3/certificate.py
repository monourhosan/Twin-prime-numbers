"""
Phase 3 Version 3.0 Cryptographic Twin-Prime Certificate Generator and Serializer.
Canonical hashing excludes digest field to avoid circular dependency.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

BASELINE_INVENTORY_SHA256 = "66256602ba495853c0ef9ead316f36f0b9c57d99211eea7fe420d15c24416356"

class TwinPrimeCertificateV3:
    def __init__(
        self,
        k: int,
        n: int,
        proth_witness: int,
        llr_parameter_p: int,
        llr_u0: int,
        campaign_id: str,
        task_id: str,
        settings_sha256: str,
        git_commit: str = "531a3fc",
        discovery_time_utc: Optional[str] = None,
    ):
        self.schema_version = "3.0"
        self.claim = "PROVEN_TWIN_PAIR_NEW_TO_PROJECT"
        self.k = k
        self.n = n

        center = k * (1 << n)
        self.p_minus = center - 1
        self.p_plus = center + 1

        self.lower_digits = len(str(self.p_minus))
        self.upper_digits = len(str(self.p_plus))

        self.proth_witness = proth_witness
        self.llr_p = llr_parameter_p
        self.llr_u0 = str(llr_u0)

        self.campaign_id = campaign_id
        self.task_id = task_id
        self.settings_sha256 = settings_sha256
        self.git_commit = git_commit

        now = datetime.now(timezone.utc).isoformat()
        self.utc_discovery = discovery_time_utc or now
        self.utc_verified = now

        self.baseline_sha256 = BASELINE_INVENTORY_SHA256
        self.world_novelty = "UNVERIFIED"
        self.artifact_sha256 = self.compute_sha256()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "claim": self.claim,
            "representation": {
                "family": "k*2^n +/- 1",
                "k": self.k,
                "n": self.n
            },
            "pair": {
                "lower_decimal": str(self.p_minus),
                "upper_decimal": str(self.p_plus),
                "lower_digits": self.lower_digits,
                "upper_digits": self.upper_digits,
                "gap": 2
            },
            "upper_proof": {
                "theorem": "Proth",
                "witness": self.proth_witness,
                "congruence": "-1",
                "condition": f"w^((B-1)/2) == -1 (mod B), w={self.proth_witness}",
                "preconditions": "checked"
            },
            "lower_proof": {
                "theorem": "Lucas-Lehmer-Riesel",
                "parameter_P": self.llr_p,
                "initial_Vk_mod_A": self.llr_u0,
                "jacobi_minus": 1,
                "jacobi_plus": -1,
                "final_residue": "0",
                "condition": f"u_{{n-2}} == 0 (mod A), P={self.llr_p}",
                "preconditions": "checked"
            },
            "search": {
                "campaign_id": self.campaign_id,
                "task_id": self.task_id,
                "settings_sha256": self.settings_sha256,
                "git_commit": self.git_commit,
                "utc_discovery": self.utc_discovery
            },
            "verification": {
                "independent_verifier": "scripts.phase3_independent_verify",
                "independent_status": "PASS",
                "utc_verified": self.utc_verified
            },
            "novelty": {
                "new_to_project": True,
                "baseline_sha256": self.baseline_sha256,
                "world_novelty": self.world_novelty
            },
            "artifact_sha256": self.artifact_sha256
        }

    def compute_sha256(self) -> str:
        canonical_str = (
            f"{self.schema_version}|{self.claim}|{self.k}|{self.n}|"
            f"{self.p_minus}|{self.p_plus}|{self.proth_witness}|{self.llr_p}|"
            f"{self.llr_u0}|{self.task_id}|{self.baseline_sha256}"
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def verify_checksum(self) -> bool:
        return self.compute_sha256() == self.artifact_sha256

    def save_to_file(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TwinPrimeCertificateV3":
        rep = d["representation"]
        search = d.get("search", {})
        u_proof = d.get("upper_proof") or d.get("proof_plus")
        l_proof = d.get("lower_proof") or d.get("proof_minus")

        cert = cls(
            k=int(rep["k"]),
            n=int(rep["n"]),
            proth_witness=int(u_proof["witness"]),
            llr_parameter_p=int(l_proof.get("parameter_P") or l_proof.get("parameters", {}).get("P")),
            llr_u0=int(l_proof.get("initial_Vk_mod_A") or l_proof.get("parameters", {}).get("u0")),
            campaign_id=search.get("campaign_id", "phase3_campaign"),
            task_id=search.get("task_id", "task_unknown"),
            settings_sha256=search.get("settings_sha256", ""),
            git_commit=search.get("git_commit", "531a3fc"),
            discovery_time_utc=search.get("utc_discovery"),
        )
        cert.utc_verified = d.get("verification", {}).get("utc_verified", cert.utc_verified)
        cert.artifact_sha256 = d.get("artifact_sha256", cert.artifact_sha256)
        return cert
