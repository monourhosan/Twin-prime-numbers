"""
Durable Search Ledger and State Storage for Phase 3 (HDRSS).
Uses SQLite with Write-Ahead Logging (WAL) for atomic transactions,
granular task state (PENDING, CLAIMED, PARTIAL, COMPLETED), and crash recovery.
"""

import sqlite3
import time
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple

class Phase3Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                n INTEGER NOT NULL,
                k_start INTEGER NOT NULL,
                k_end INTEGER NOT NULL,
                next_unprocessed_k INTEGER NOT NULL,
                status TEXT NOT NULL, -- PENDING, CLAIMED, PARTIAL, COMPLETED, FAILED
                worker_id TEXT,
                raw_tested INTEGER DEFAULT 0,
                wheel_survivors INTEGER DEFAULT 0,
                sieve_survivors INTEGER DEFAULT 0,
                prp_survivors INTEGER DEFAULT 0,
                proven_pairs INTEGER DEFAULT 0,
                elapsed_seconds REAL DEFAULT 0.0,
                last_updated_utc TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS discoveries (
                artifact_sha256 TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                k INTEGER NOT NULL,
                n INTEGER NOT NULL,
                digits INTEGER NOT NULL,
                p_minus TEXT NOT NULL,
                p_plus TEXT NOT NULL,
                cert_path TEXT NOT NULL,
                utc_discovered TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS campaign_heartbeats (
                campaign_id TEXT PRIMARY KEY,
                pid INTEGER NOT NULL,
                worker_id TEXT NOT NULL,
                last_heartbeat_utc TEXT NOT NULL,
                active_task_id TEXT
            );
            """)
            conn.commit()

    def register_task(self, task_id: str, campaign_id: str, n: int, k_start: int, k_end: int):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO tasks (
                task_id, campaign_id, n, k_start, k_end, next_unprocessed_k, status, last_updated_utc
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?);
            """, (task_id, campaign_id, n, k_start, k_end, k_start, now))
            conn.commit()

    def claim_next_task(self, campaign_id: str, worker_id: str, lease_timeout_sec: float = 300.0) -> Optional[Dict[str, Any]]:
        now_ts = time.time()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts))
        stale_cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts - lease_timeout_sec))
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            # Reclaim stale/orphaned CLAIMED tasks whose workers abandoned or crashed
            conn.execute("""
            UPDATE tasks
            SET status = CASE WHEN next_unprocessed_k > k_start THEN 'PARTIAL' ELSE 'PENDING' END,
                worker_id = NULL
            WHERE campaign_id = ? AND status = 'CLAIMED' AND last_updated_utc < ?;
            """, (campaign_id, stale_cutoff))

            # Look for PARTIAL or PENDING
            cursor = conn.execute("""
            SELECT task_id, campaign_id, n, k_start, k_end, next_unprocessed_k, status
            FROM tasks
            WHERE campaign_id = ? AND status IN ('PENDING', 'PARTIAL')
            ORDER BY n ASC, k_start ASC
            LIMIT 1;
            """, (campaign_id,))
            row = cursor.fetchone()
            if not row:
                conn.commit()
                return None

            task_id, camp, n, k_start, k_end, next_k, status = row
            conn.execute("""
            UPDATE tasks
            SET status = 'CLAIMED', worker_id = ?, last_updated_utc = ?
            WHERE task_id = ?;
            """, (worker_id, now, task_id))
            conn.commit()

            return {
                "task_id": task_id,
                "campaign_id": camp,
                "n": n,
                "k_start": k_start,
                "k_end": k_end,
                "next_unprocessed_k": next_k,
                "status": "CLAIMED"
            }

    def update_task_progress(
        self,
        task_id: str,
        next_k: int,
        is_completed: bool,
        stats_delta: Dict[str, Any]
    ):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        new_status = "COMPLETED" if is_completed else "PARTIAL"
        with self._connection() as conn:
            conn.execute("""
            UPDATE tasks
            SET next_unprocessed_k = ?,
                status = ?,
                raw_tested = raw_tested + ?,
                wheel_survivors = wheel_survivors + ?,
                sieve_survivors = sieve_survivors + ?,
                prp_survivors = prp_survivors + ?,
                proven_pairs = proven_pairs + ?,
                elapsed_seconds = elapsed_seconds + ?,
                last_updated_utc = ?
            WHERE task_id = ?;
            """, (
                next_k,
                new_status,
                stats_delta.get("raw_tested", 0),
                stats_delta.get("wheel_survivors", 0),
                stats_delta.get("sieve_survivors", 0),
                stats_delta.get("prp_survivors", 0),
                stats_delta.get("proven_pairs", 0),
                stats_delta.get("elapsed_seconds", 0.0),
                now,
                task_id
            ))
            conn.commit()

    def record_discovery(
        self,
        artifact_sha256: str,
        campaign_id: str,
        task_id: str,
        k: int,
        n: int,
        digits: int,
        p_minus: str,
        p_plus: str,
        cert_path: str
    ):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO discoveries (
                artifact_sha256, campaign_id, task_id, k, n, digits, p_minus, p_plus, cert_path, utc_discovered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (artifact_sha256, campaign_id, task_id, k, n, digits, p_minus, p_plus, cert_path, now))
            conn.commit()

    def update_heartbeat(self, campaign_id: str, worker_id: str, active_task_id: Optional[str] = None):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pid = os.getpid()
        with self._connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO campaign_heartbeats (
                campaign_id, pid, worker_id, last_heartbeat_utc, active_task_id
            ) VALUES (?, ?, ?, ?, ?);
            """, (campaign_id, pid, worker_id, now, active_task_id))
            conn.commit()

    def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        with self._connection() as conn:
            # Summary of tasks
            cur = conn.execute("""
            SELECT
                COUNT(*),
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'PARTIAL' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'CLAIMED' THEN 1 ELSE 0 END),
                SUM(raw_tested),
                SUM(wheel_survivors),
                SUM(sieve_survivors),
                SUM(prp_survivors),
                SUM(proven_pairs),
                SUM(elapsed_seconds)
            FROM tasks
            WHERE campaign_id = ?;
            """, (campaign_id,))
            row = cur.fetchone()

            # Heartbeat check
            hb_cur = conn.execute("""
            SELECT pid, worker_id, last_heartbeat_utc, active_task_id
            FROM campaign_heartbeats
            WHERE campaign_id = ?;
            """, (campaign_id,))
            hb_row = hb_cur.fetchone()

            # Discoveries
            disc_cur = conn.execute("""
            SELECT k, n, digits, cert_path, utc_discovered
            FROM discoveries
            WHERE campaign_id = ?
            ORDER BY digits DESC;
            """, (campaign_id,))
            discoveries = [
                {"k": r[0], "n": r[1], "digits": r[2], "cert_path": r[3], "utc_discovered": r[4]}
                for r in disc_cur.fetchall()
            ]

        return {
            "campaign_id": campaign_id,
            "total_tasks": row[0] or 0,
            "completed_tasks": row[1] or 0,
            "partial_tasks": row[2] or 0,
            "claimed_tasks": row[3] or 0,
            "raw_tested": row[4] or 0,
            "wheel_survivors": row[5] or 0,
            "sieve_survivors": row[6] or 0,
            "prp_survivors": row[7] or 0,
            "proven_pairs": row[8] or 0,
            "total_cpu_seconds": row[9] or 0.0,
            "heartbeat": {
                "pid": hb_row[0],
                "worker_id": hb_row[1],
                "last_heartbeat_utc": hb_row[2],
                "active_task_id": hb_row[3]
            } if hb_row else None,
            "discoveries": discoveries
        }
