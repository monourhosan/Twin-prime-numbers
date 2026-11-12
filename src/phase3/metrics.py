"""
Performance Metrics and Monotonic Instrumentation for Phase 3 (HDRSS).
Maintains exact stage timings, survivor counts, rates, and memory tracking.
"""

import time
import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class WindowMetrics:
    raw_odd_k: int = 0
    wheel_survivors: int = 0
    sieve_survivors: int = 0
    prp_B_pass: int = 0
    prp_A_pass: int = 0
    prp_pair_pass: int = 0
    proth_proven: int = 0
    llr_proven: int = 0
    pair_verified: int = 0

    # Milliseconds per stage
    wheel_ms: float = 0.0
    sieve_ms: float = 0.0
    prp_ms: float = 0.0
    proof_ms: float = 0.0
    verify_ms: float = 0.0
    io_ms: float = 0.0

    # Overall timings
    wall_seconds: float = 0.0
    process_cpu_seconds: float = 0.0
    peak_rss_mb: float = 0.0

    def raw_rate(self) -> float:
        if self.wall_seconds > 0:
            return self.raw_odd_k / self.wall_seconds
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_odd_k": self.raw_odd_k,
            "wheel_survivors": self.wheel_survivors,
            "sieve_survivors": self.sieve_survivors,
            "prp_pair_pass": self.prp_pair_pass,
            "proth_proven": self.proth_proven,
            "llr_proven": self.llr_proven,
            "pair_verified": self.pair_verified,
            "timings_ms": {
                "wheel": round(self.wheel_ms, 2),
                "sieve": round(self.sieve_ms, 2),
                "prp": round(self.prp_ms, 2),
                "proof": round(self.proof_ms, 2),
                "verify": round(self.verify_ms, 2),
                "io": round(self.io_ms, 2),
            },
            "wall_seconds": round(self.wall_seconds, 4),
            "candidates_per_sec": round(self.raw_rate(), 1)
        }
