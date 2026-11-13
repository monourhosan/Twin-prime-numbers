"""
Auditable search coverage tracker and resumption manager for Phase 6 campaigns.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

class CoverageManager:
    """Manages interval coverage, resume points, and segment manifests."""
    def __init__(self, db_path: Path, manifest_path: Optional[Path] = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path = Path(manifest_path) if manifest_path else Path("data/phase6_coverage_manifest.json")
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS completed_segments (
                    segment_id INTEGER PRIMARY KEY,
                    m_start TEXT NOT NULL,
                    m_end TEXT NOT NULL,
                    segment_size INTEGER NOT NULL,
                    survivors_count INTEGER NOT NULL,
                    dual_prp_count INTEGER NOT NULL,
                    proven_count INTEGER NOT NULL,
                    elapsed_seconds REAL NOT NULL,
                    completed_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_m_range ON completed_segments(m_start, m_end);
                """)
        finally:
            conn.close()

    def get_max_completed_m(self) -> int:
        """Returns the maximum m_end completed so far, or 0 if none."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT m_end FROM completed_segments")
            rows = cursor.fetchall()
            if not rows:
                return 0
            return max(int(r[0]) for r in rows)
        finally:
            conn.close()

    def record_completed_segment(
        self,
        segment_id: int,
        m_start: int,
        m_end: int,
        survivors: int,
        dual_prps: int,
        proven: int,
        elapsed_sec: float,
        timestamp_utc: str
    ):
        """Records completed segment and updates JSON manifest atomically."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                INSERT OR REPLACE INTO completed_segments (
                    segment_id, m_start, m_end, segment_size,
                    survivors_count, dual_prp_count, proven_count,
                    elapsed_seconds, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    segment_id, str(m_start), str(m_end), m_end - m_start,
                    survivors, dual_prps, proven, elapsed_sec, timestamp_utc
                ))
        finally:
            conn.close()

        self._export_manifest()

    def _export_manifest(self):
        """Exports full coverage manifest to JSON."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM completed_segments ORDER BY segment_id ASC")
            rows = cursor.fetchall()
            segments = [dict(r) for r in rows]
        finally:
            conn.close()

        manifest = {
            "schema_version": "6.0",
            "phase": "Phase 6",
            "total_segments_completed": len(segments),
            "max_m_completed": self.get_max_completed_m(),
            "segments": segments
        }

        temp_file = self.manifest_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        temp_file.replace(self.manifest_path)
