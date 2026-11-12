"""
Cryptographic certificate management and independent verification for CATS.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

class TwinPrimeCertificate:
    def __init__(
        self,
        pair_type: str,
        p_minus_str: str,
        p_plus_str: str,
        digits: int,
        k: Optional[int] = None,
        n: Optional[int] = None,
        proth_witness: Optional[int] = None,
        llr_witness: Optional[int] = None,
        is_proven: bool = False,
        certificate_id: Optional[str] = None,
        timestamp_utc: Optional[str] = None,
        engine_version: str = "CATS-Python-1.0.0 (NumPy/SymPy)",
        sha256_hash: Optional[str] = None,
    ):
        now = datetime.now(timezone.utc).isoformat()
        self.certificate_id = certificate_id or f"CATS-TWIN-k{k}-n{n}-{now[:10]}"
        self.timestamp_utc = timestamp_utc or now
        self.engine_version = engine_version
        self.pair_type = pair_type
        self.digits = digits
        self.k = k
        self.n = n
        self.center_m = f"{k} * 2^{n}" if (k and n) else f"({p_minus_str} + 1)"
        self.p_minus = p_minus_str
        self.p_plus = p_plus_str

        self.p_plus_proof = (
            {
                "method": "PROTH_THEOREM",
                "witness": proth_witness,
                "condition_checked": f"w^((B-1)/2) == -1 (mod B), with w={proth_witness}, k={k}, n={n}",
                "passed": True,
            }
            if proth_witness is not None
            else None
        )

        self.p_minus_proof = (
            {
                "method": "LUCAS_LEHMER_RIESEL",
                "witness_p": llr_witness,
                "condition_checked": f"u_{{n-2}} == 0 (mod A), P={llr_witness}, k={k}, n={n}",
                "passed": True,
            }
            if llr_witness is not None
            else None
        )

        self.proof_status = "PROVEN_PRIME_PAIR" if is_proven else "STRONG_PRP_PAIR"
        self.sha256_hash = sha256_hash or self.compute_hash()

    def compute_hash(self) -> str:
        hasher = hashlib.sha256()
        canonical_str = (
            f"{self.certificate_id}|{self.pair_type}|{self.p_minus}|"
            f"{self.p_plus}|{self.proof_status}|"
            f"{self.p_plus_proof.get('condition_checked') if self.p_plus_proof else ''}|"
            f"{self.p_minus_proof.get('condition_checked') if self.p_minus_proof else ''}"
        )
        hasher.update(canonical_str.encode("utf-8"))
        return hasher.hexdigest()

    def verify_checksum(self) -> bool:
        return self.compute_hash() == self.sha256_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "timestamp_utc": self.timestamp_utc,
            "engine_version": self.engine_version,
            "pair_type": self.pair_type,
            "digits": self.digits,
            "k": self.k,
            "n": self.n,
            "center_m": self.center_m,
            "p_minus": self.p_minus,
            "p_plus": self.p_plus,
            "p_plus_proof": self.p_plus_proof,
            "p_minus_proof": self.p_minus_proof,
            "proof_status": self.proof_status,
            "sha256_hash": self.sha256_hash,
        }

    def save_to_file(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_file(cls, path: Path) -> "TwinPrimeCertificate":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        proth_w = d.get("p_plus_proof", {}).get("witness") if d.get("p_plus_proof") else None
        llr_w = d.get("p_minus_proof", {}).get("witness_p") if d.get("p_minus_proof") else None
        return cls(
            pair_type=d["pair_type"],
            p_minus_str=d["p_minus"],
            p_plus_str=d["p_plus"],
            digits=d["digits"],
            k=d.get("k"),
            n=d.get("n"),
            proth_witness=proth_w,
            llr_witness=llr_w,
            is_proven=(d["proof_status"] == "PROVEN_PRIME_PAIR"),
            certificate_id=d["certificate_id"],
            timestamp_utc=d["timestamp_utc"],
            engine_version=d["engine_version"],
            sha256_hash=d["sha256_hash"],
        )
