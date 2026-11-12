"""
Version 2.0 Cryptographic Twin-Prime Certificate Generator and Serializer.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

BASELINE_INVENTORY_SHA256 = "b27e24a1ab320b9882e720e95a1336c1d768fa4c792383dfb245e383e2dcf554"

class TwinPrimeCertificateV2:
    def __init__(
        self,
        k: int,
        n: int,
        proth_witness: int,
        llr_parameter_p: int,
        llr_u0: int,
        work_unit_id: str,
        run_id: str,
        generator_commit: str,
        discovery_time_utc: Optional[str] = None,
    ):
        self.schema_version = "2.0"
        self.claim_type = "new_to_project_proven_twin_pair"
        self.k = k
        self.n = n

        two_pow_n = 1 << n
        center = k * two_pow_n
        self.p_minus = center - 1
        self.p_plus = center + 1

        self.digits_p_minus = len(str(self.p_minus))
        self.digits_p_plus = len(str(self.p_plus))

        self.proth_witness = proth_witness
        self.llr_p = llr_parameter_p
        self.llr_u0 = str(llr_u0)

        self.work_unit_id = work_unit_id
        self.run_id = run_id
        self.generator_commit = generator_commit
        self.baseline_inventory_sha256 = BASELINE_INVENTORY_SHA256

        now = datetime.now(timezone.utc).isoformat()
        self.utc_discovery_time = discovery_time_utc or now
        self.utc_verification_time = now
        self.verification_status = "PROVEN_TWIN_PAIR"

        self.artifact_sha256 = self.compute_sha256()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "claim_type": self.claim_type,
            "p_minus": str(self.p_minus),
            "p_plus": str(self.p_plus),
            "representation": {
                "family": "k*2^n+/-1",
                "k": self.k,
                "n": self.n
            },
            "digits_p_minus": self.digits_p_minus,
            "digits_p_plus": self.digits_p_plus,
            "proof_minus": {
                "method": "LUCAS_LEHMER_RIESEL",
                "parameters": {
                    "P": self.llr_p,
                    "u0": self.llr_u0
                },
                "condition_checked": f"u_{{n-2}} == 0 (mod A), P={self.llr_p}, k={self.k}, n={self.n}",
                "verifier": "phase2_strict_verifier"
            },
            "proof_plus": {
                "method": "PROTH_THEOREM",
                "witness": self.proth_witness,
                "condition_checked": f"w^((B-1)/2) == -1 (mod B), with w={self.proth_witness}, k={self.k}, n={self.n}",
                "verifier": "phase2_strict_verifier"
            },
            "search_work_unit_id": self.work_unit_id,
            "search_run_id": self.run_id,
            "generator_commit": self.generator_commit,
            "original_baseline_inventory_sha256": self.baseline_inventory_sha256,
            "utc_discovery_time": self.utc_discovery_time,
            "utc_verification_time": self.utc_verification_time,
            "verification_status": self.verification_status,
            "artifact_sha256": self.artifact_sha256,
        }

    def compute_sha256(self) -> str:
        hasher = hashlib.sha256()
        canonical_str = (
            f"{self.schema_version}|{self.claim_type}|{self.k}|{self.n}|"
            f"{self.p_minus}|{self.p_plus}|{self.proth_witness}|{self.llr_p}|"
            f"{self.work_unit_id}|{self.baseline_inventory_sha256}"
        )
        hasher.update(canonical_str.encode("utf-8"))
        return hasher.hexdigest()

    def verify_checksum(self) -> bool:
        return self.compute_sha256() == self.artifact_sha256

    def save_to_file(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TwinPrimeCertificateV2":
        rep = d["representation"]
        cert = cls(
            k=int(rep["k"]),
            n=int(rep["n"]),
            proth_witness=int(d["proof_plus"]["witness"]),
            llr_parameter_p=int(d["proof_minus"]["parameters"]["P"]),
            llr_u0=int(d["proof_minus"]["parameters"]["u0"]),
            work_unit_id=d["search_work_unit_id"],
            run_id=d["search_run_id"],
            generator_commit=d["generator_commit"],
            discovery_time_utc=d["utc_discovery_time"],
        )
        cert.utc_verification_time = d["utc_verification_time"]
        cert.artifact_sha256 = d["artifact_sha256"]
        return cert

    @classmethod
    def from_file(cls, path: Path) -> "TwinPrimeCertificateV2":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dict(d)
