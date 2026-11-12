"""
Phase 4 Coverage and Interval Union Auditor.
Reconstructs exact intervals from database records, detects gaps, overlaps,
and certifies verified numerical coverage per exponent.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
from .storage import Phase4Storage

def audit_coverage(storage: Phase4Storage, campaign_id: str) -> Dict[str, Any]:
    with storage._connection() as conn:
        cursor = conn.execute("""
        SELECT n, k_start, k_end, next_unprocessed_k, status
        FROM tasks
        WHERE campaign_id = ?
        ORDER BY n ASC, k_start ASC;
        """, (campaign_id,))
        rows = cursor.fetchall()

    per_exponent: Dict[int, List[Dict[str, Any]]] = {}
    for n, ks, ke, next_k, status in rows:
        if n not in per_exponent:
            per_exponent[n] = []
        per_exponent[n].append({
            "k_start": ks,
            "k_end": ke,
            "next_unprocessed_k": next_k,
            "status": status
        })

    summary: Dict[int, Dict[str, Any]] = {}
    for n, tasks in per_exponent.items():
        completed_spans = []
        partial_spans = []
        gaps = []
        overlaps = []

        last_end = None
        total_covered_span = 0

        for t in tasks:
            ks = t["k_start"]
            ke = t["k_end"]
            nk = t["next_unprocessed_k"]
            st = t["status"]

            if last_end is not None:
                if ks > last_end:
                    gaps.append((last_end, ks))
                elif ks < last_end:
                    overlaps.append((ks, last_end))

            if st == "COMPLETED":
                completed_spans.append((ks, ke))
                total_covered_span += (ke - ks)
                last_end = ke
            elif st == "PARTIAL":
                partial_spans.append((ks, nk, ke))
                total_covered_span += (nk - ks)
                last_end = ke
            else:
                last_end = ke

        summary[n] = {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_spans),
            "partial_tasks": len(partial_spans),
            "total_covered_k_span": total_covered_span,
            "gaps": gaps,
            "overlaps": overlaps,
            "is_gap_free": len(gaps) == 0
        }

    return summary
