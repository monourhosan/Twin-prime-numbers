"""
Phase 4 Configuration Schema (Schema 4.0).
Provides typed, validated, and canonically hashed campaign configurations.
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

@dataclass
class Phase4Config:
    schema_version: str = "4.0"
    campaign_id: str = "target_1000"
    family: str = "odd_k_divisible_by_3_times_2_power_plus_minus_1"
    min_digits: int = 1000
    exponents: List[int] = field(default_factory=lambda: [3328])
    k_start: int = 3
    k_end: Optional[int] = None # None means progressive open-ended
    window_k_span: int = 120_000
    sieve_strategy: str = "r1_tspace" # "r0_s1_baseline", "r1_tspace", "r2_adaptive"
    sieve_depth: int = 50_000
    sieve_depth_candidates: List[int] = field(default_factory=lambda: [10000, 30000, 100000, 300000])
    prp_bases: List[int] = field(default_factory=lambda: [2, 3, 5])
    proth_witness_pool: List[int] = field(default_factory=lambda: [3, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47])
    llr_parameter_pool: List[int] = field(default_factory=lambda: [3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22, 24])
    workers: int = 1
    max_wall_hours_per_session: float = 0.0
    checkpoint_seconds: float = 30.0
    lease_timeout_seconds: float = 120.0
    stop_after_verified_pairs: int = 1
    require_independent_verification: bool = True
    checkpoint_dir: str = "runs/phase4/target_1000"
    proofs_dir: str = "proofs/phase4"
    allow_auto_start: bool = False
    use_gmpy2: bool = True

    def validate(self):
        if self.schema_version != "4.0":
            raise ValueError(f"Unsupported schema version: {self.schema_version}")
        if self.min_digits < 1:
            raise ValueError(f"min_digits must be positive, got {self.min_digits}")
        if not self.exponents:
            raise ValueError("Exponents list cannot be empty")
        for n in self.exponents:
            if n < 2:
                raise ValueError(f"Exponent n must be >= 2, got {n}")
        if self.k_start <= 0 or self.k_start % 2 == 0:
            raise ValueError(f"k_start must be positive odd integer, got {self.k_start}")
        if self.k_start % 3 != 0:
            raise ValueError(f"k_start must be divisible by 3 (k=6t+3 family), got {self.k_start}")
        if self.k_end is not None:
            if self.k_end <= self.k_start:
                raise ValueError(f"k_end ({self.k_end}) must be > k_start ({self.k_start})")
        if self.window_k_span <= 0:
            raise ValueError(f"window_k_span must be positive, got {self.window_k_span}")
        if self.sieve_depth <= 0:
            raise ValueError(f"sieve_depth must be positive, got {self.sieve_depth}")
        if self.workers < 1:
            raise ValueError(f"workers must be >= 1, got {self.workers}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    def compute_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Phase4Config":
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        cfg = cls(**filtered)
        cfg.validate()
        return cfg

    @classmethod
    def from_file(cls, path: Path) -> "Phase4Config":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
