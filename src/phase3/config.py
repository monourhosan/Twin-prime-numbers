"""
Typed Configuration Schema and Canonical Hasher for Phase 3.
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

@dataclass
class Phase3Config:
    version: str = "3.0.0"
    campaign_id: str = "phase3_campaign"
    min_digits: int = 300
    exponents: List[int] = field(default_factory=lambda: [1024])
    k_start: int = 3
    k_end: Optional[int] = None # None means open-ended progressive
    window_size: int = 100_000
    sieve_depth: int = 50_000
    stride_cutoff: int = 10_000 # For Strategy S2
    algorithm: str = "hybrid" # s0_phase2, s1_segmented, s2_hybrid
    workers: int = 1
    max_wall_hours: float = 0.0 # 0.0 means unlimited
    until_proven_pairs: int = 1
    checkpoint_dir: str = "runs/phase3"
    checkpoint_frequency_sec: float = 30.0
    memory_limit_mb: int = 2048
    prp_bases: List[int] = field(default_factory=lambda: [2, 3])
    proth_witness_pool: List[int] = field(default_factory=lambda: [3, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47])
    llr_parameter_pool: List[int] = field(default_factory=lambda: [3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22, 24])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    def compute_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_file(cls, path: Path) -> "Phase3Config":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def save_to_file(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
