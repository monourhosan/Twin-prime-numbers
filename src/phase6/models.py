"""
Data models and schemas for Phase 6 GITCSS pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True)
class IntervalMapping:
    """Exact mapping between p-interval and center m-interval."""
    p_min: int
    p_max: int
    m_min: int
    m_max: int
    total_m_candidates: int

    @classmethod
    def from_p_range(cls, p_min: int, p_max: int) -> "IntervalMapping":
        if p_min > p_max:
            raise ValueError(f"p_min ({p_min}) cannot exceed p_max ({p_max})")
        # Exact integer division: m_min = ceil((p_min + 1) / 6), m_max = floor((p_max + 1) / 6)
        m_min = (p_min + 1 + 5) // 6
        m_max = (p_max + 1) // 6
        total = max(0, m_max - m_min + 1)
        return cls(p_min=p_min, p_max=p_max, m_min=m_min, m_max=m_max, total_m_candidates=total)

@dataclass(frozen=True)
class CandidatePair:
    """A twin prime candidate pair generated from center index m."""
    m: int
    A: int # 6m - 1
    B: int # 6m + 1
    digits: int

    @classmethod
    def from_m(cls, m: int) -> "CandidatePair":
        A = 6 * m - 1
        B = 6 * m + 1
        return cls(m=m, A=A, B=B, digits=len(str(A)))

@dataclass
class ScreeningResult:
    """Results of multi-stage probable prime screening."""
    candidate: CandidatePair
    is_left_prp: bool = False
    is_right_prp: bool = False
    is_dual_prp: bool = False
    stage_passed: str = "NONE" # "NONE", "DIVISIBILITY", "FERMAT", "MILLER_RABIN", "LUCAS"
    rejection_reason: Optional[str] = None
    elapsed_ms: float = 0.0

@dataclass
class SegmentSummary:
    """Summary metrics for a completed segment of m values."""
    segment_id: int
    m_start: int
    m_end: int # exclusive
    total_centers: int
    wheel_survivors: int
    sieve_survivors: int
    dual_prps: int
    proven_pairs: int
    sieve_time_ms: float
    screen_time_ms: float
    status: str = "COMPLETED"
