"""
Phase 6: Search Ledger and Persistent Work Coordinator.
Manages atomic SQLite WAL state, work unit leases, checkpoint recovery,
canonical center deduplication, and cooperative campaign pause.
"""

import os
import time
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class SearchLedger:
    """
    Atomic SQLite WAL persistent ledger for Phase 6 campaigns.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS campaign_state (
                    campaign_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    found_pair INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS work_units (
                    unit_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    j_start INTEGER NOT NULL,
                    j_end INTEGER NOT NULL,
                    config_hash TEXT NOT NULL,
                    state TEXT NOT NULL, -- QUEUED, LEASED, COMPLETED, FAILED
                    lease_expire REAL,
                    candidates_tested INTEGER DEFAULT 0,
                    survivors_found INTEGER DEFAULT 0,
                    prp_hits INTEGER DEFAULT 0,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS candidates (
                    center_decimal TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    t INTEGER NOT NULL,
                    A TEXT NOT NULL,
                    B TEXT NOT NULL,
                    digits INTEGER NOT NULL,
                    status TEXT NOT NULL, -- PRP_BOTH, PROVEN, EXCLUDED_DUPLICATE
                    created_at REAL NOT NULL
                );
            """)

    def init_campaign(self, campaign_id: str, config: Dict[str, Any], total_units: List[Tuple[int, int]], config_hash: str) -> None:
        with self._get_connection() as conn:
            now = time.time()
            conn.execute(
                """INSERT OR IGNORE INTO campaign_state (campaign_id, status, config_json, found_pair, created_at, updated_at)
                   VALUES (?, 'RUNNING', ?, 0, ?, ?)""",
                (campaign_id, json.dumps(config), now, now)
            )
            for j_start, j_end in total_units:
                unit_id = f"{campaign_id}_{j_start}_{j_end}"
                conn.execute(
                    """INSERT OR IGNORE INTO work_units (unit_id, campaign_id, j_start, j_end, config_hash, state, updated_at)
                       VALUES (?, ?, ?, ?, ?, 'QUEUED', ?)""",
                    (unit_id, campaign_id, j_start, j_end, config_hash, now)
                )

    def lease_next_unit(self, campaign_id: str, lease_duration: float = 300.0) -> Optional[Tuple[str, int, int]]:
        with self._get_connection() as conn:
            now = time.time()
            # Recover stale leases
            conn.execute(
                """UPDATE work_units SET state = 'QUEUED', lease_expire = NULL
                   WHERE campaign_id = ? AND state = 'LEASED' AND lease_expire < ?""",
                (campaign_id, now)
            )
            cursor = conn.execute(
                """SELECT unit_id, j_start, j_end FROM work_units
                   WHERE campaign_id = ? AND state = 'QUEUED'
                   ORDER BY j_start ASC LIMIT 1""",
                (campaign_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            unit_id, j_start, j_end = row
            conn.execute(
                """UPDATE work_units SET state = 'LEASED', lease_expire = ?, updated_at = ?
                   WHERE unit_id = ?""",
                (now + lease_duration, now, unit_id)
            )
            return unit_id, j_start, j_end

    def complete_unit(self, unit_id: str, candidates: int, survivors: int, prps: int) -> None:
        with self._get_connection() as conn:
            now = time.time()
            conn.execute(
                """UPDATE work_units
                   SET state = 'COMPLETED', candidates_tested = ?, survivors_found = ?, prp_hits = ?, updated_at = ?, lease_expire = NULL
                   WHERE unit_id = ?""",
                (candidates, survivors, prps, now, unit_id)
            )

    def record_candidate(self, campaign_id: str, t: int, A: str, B: str, C: str, digits: int, status: str) -> None:
        with self._get_connection() as conn:
            now = time.time()
            conn.execute(
                """INSERT OR REPLACE INTO candidates (center_decimal, campaign_id, t, A, B, digits, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (C, campaign_id, t, A, B, digits, status, now)
            )

    def mark_pair_found(self, campaign_id: str) -> None:
        with self._get_connection() as conn:
            now = time.time()
            conn.execute(
                """UPDATE campaign_state SET found_pair = 1, status = 'COMPLETED', updated_at = ?
                   WHERE campaign_id = ?""",
                (now, campaign_id)
            )

    def set_campaign_status(self, campaign_id: str, status: str) -> None:
        with self._get_connection() as conn:
            now = time.time()
            conn.execute(
                """UPDATE campaign_state SET status = ?, updated_at = ? WHERE campaign_id = ?""",
                (status, now, campaign_id)
            )

    def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            state_row = conn.execute(
                "SELECT status, found_pair, updated_at FROM campaign_state WHERE campaign_id = ?",
                (campaign_id,)
            ).fetchone()
            if not state_row:
                return {"campaign_id": campaign_id, "status": "UNKNOWN"}

            stats = conn.execute(
                """SELECT
                    COUNT(*) as total_units,
                    SUM(CASE WHEN state = 'COMPLETED' THEN 1 ELSE 0 END) as completed_units,
                    SUM(candidates_tested) as total_candidates,
                    SUM(survivors_found) as total_survivors,
                    SUM(prp_hits) as total_prps
                   FROM work_units WHERE campaign_id = ?""",
                (campaign_id,)
            ).fetchone()

            proven_count = conn.execute(
                "SELECT COUNT(*) FROM candidates WHERE campaign_id = ? AND status = 'PROVEN'",
                (campaign_id,)
            ).fetchone()[0]

            return {
                "campaign_id": campaign_id,
                "status": state_row[0],
                "found_pair": bool(state_row[1]),
                "updated_at": state_row[2],
                "total_units": stats[0] or 0,
                "completed_units": stats[1] or 0,
                "candidates_tested": stats[2] or 0,
                "survivors_found": stats[3] or 0,
                "prp_hits": stats[4] or 0,
                "proven_pairs": proven_count
            }
