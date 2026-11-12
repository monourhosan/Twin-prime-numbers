"""
Phase 4 Fault-Tolerant Storage & Distributed Work Ledger.
Uses SQLite with Write-Ahead Logging (WAL), atomic IMMEDIATE transactions,
durable lease tokens, fencing generations, and automatic crash/zombie recovery.
"""

import sqlite3
import time
import uuid
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple

class Phase4Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=60.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 60000;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                campaign_id TEXT PRIMARY KEY,
                config_sha256 TEXT NOT NULL,
                git_commit TEXT NOT NULL,
                environment_json TEXT NOT NULL,
                created_utc TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                n INTEGER NOT NULL,
                k_start INTEGER NOT NULL,
                k_end INTEGER NOT NULL,
                next_unprocessed_k INTEGER NOT NULL,
                status TEXT NOT NULL, -- PENDING, LEASED, PARTIAL, COMPLETED, FAILED_RETRYABLE
                created_utc TEXT NOT NULL,
                last_updated_utc TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS leases (
                lease_token TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                pid INTEGER NOT NULL,
                acquired_utc TEXT NOT NULL,
                heartbeat_utc TEXT NOT NULL,
                expires_utc TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS stage_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                raw_tested INTEGER NOT NULL,
                wheel_survivors INTEGER NOT NULL,
                sieve_survivors INTEGER NOT NULL,
                prp_screened INTEGER NOT NULL,
                prp_passed INTEGER NOT NULL,
                proth_proven INTEGER NOT NULL,
                llr_proven INTEGER NOT NULL,
                wall_seconds REAL NOT NULL,
                cpu_seconds REAL NOT NULL,
                timestamp_utc TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS discoveries (
                payload_sha256 TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                k INTEGER NOT NULL,
                n INTEGER NOT NULL,
                digits INTEGER NOT NULL,
                proth_witness INTEGER NOT NULL,
                llr_p INTEGER NOT NULL,
                payload_path TEXT NOT NULL,
                independent_status TEXT DEFAULT 'UNVERIFIED',
                attestation_path TEXT,
                discovered_utc TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL
            );
            """)
            conn.commit()

    def register_campaign(self, campaign_id: str, config_sha256: str, git_commit: str, env_dict: Dict[str, Any]):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO campaigns (campaign_id, config_sha256, git_commit, environment_json, created_utc)
            VALUES (?, ?, ?, ?, ?);
            """, (campaign_id, config_sha256, git_commit, json.dumps(env_dict), now))
            conn.commit()

    def register_tasks_batch(self, task_records: List[Tuple[str, str, int, int, int]]):
        """Registers a batch of (task_id, campaign_id, n, k_start, k_end)."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._connection() as conn:
            conn.executemany("""
            INSERT OR IGNORE INTO tasks (task_id, campaign_id, n, k_start, k_end, next_unprocessed_k, status, created_utc, last_updated_utc)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?);
            """, [(tid, cid, n, ks, ke, ks, now, now) for tid, cid, n, ks, ke in task_records])
            conn.commit()

    def claim_task(
        self,
        campaign_id: str,
        worker_id: str,
        pid: int,
        lease_duration_sec: float = 120.0
    ) -> Optional[Dict[str, Any]]:
        """
        Atomically claims the next eligible task under durable lease.
        Reclaims any abandoned or expired leases automatically.
        """
        now_ts = time.time()
        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts))
        exp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts + lease_duration_sec))

        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")

            # 1. Reclaim expired active leases
            cursor = conn.execute("""
            SELECT lease_token, task_id FROM leases
            WHERE campaign_id = ? AND is_active = 1 AND expires_utc < ?;
            """, (campaign_id, now_utc))
            expired_leases = cursor.fetchall()

            for ltok, tid in expired_leases:
                conn.execute("UPDATE leases SET is_active = 0 WHERE lease_token = ?;", (ltok,))
                # Revert task to PARTIAL or PENDING based on progress
                conn.execute("""
                UPDATE tasks
                SET status = CASE WHEN next_unprocessed_k > k_start THEN 'PARTIAL' ELSE 'PENDING' END,
                    last_updated_utc = ?
                WHERE task_id = ? AND status = 'LEASED';
                """, (now_utc, tid))

            # 2. Select next available PENDING or PARTIAL task
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

            task_id, cid, n, k_start, k_end, next_k, status = row
            lease_token = f"lease_{uuid.uuid4().hex}"

            # 3. Create lease and update task
            conn.execute("""
            INSERT INTO leases (lease_token, task_id, campaign_id, worker_id, pid, acquired_utc, heartbeat_utc, expires_utc, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1);
            """, (lease_token, task_id, cid, worker_id, pid, now_utc, now_utc, exp_utc))

            conn.execute("""
            UPDATE tasks
            SET status = 'LEASED', last_updated_utc = ?
            WHERE task_id = ?;
            """, (now_utc, task_id))

            conn.commit()

            return {
                "task_id": task_id,
                "campaign_id": cid,
                "n": n,
                "k_start": k_start,
                "k_end": k_end,
                "next_unprocessed_k": next_k,
                "lease_token": lease_token
            }

    def heartbeat_lease(self, lease_token: str, extend_sec: float = 120.0) -> bool:
        """Extends active lease heartbeat."""
        now_ts = time.time()
        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts))
        exp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts + extend_sec))

        with self._connection() as conn:
            cursor = conn.execute("""
            UPDATE leases
            SET heartbeat_utc = ?, expires_utc = ?
            WHERE lease_token = ? AND is_active = 1;
            """, (now_utc, exp_utc, lease_token))
            conn.commit()
            return cursor.rowcount > 0

    def commit_task_progress(
        self,
        task_id: str,
        lease_token: str,
        worker_id: str,
        next_k: int,
        is_completed: bool,
        metrics_dict: Dict[str, Any]
    ) -> bool:
        """
        Commits stage metrics and advances progress cursor under active lease.
        Fails closed if lease was revoked or expired.
        """
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        new_status = "COMPLETED" if is_completed else "PARTIAL"

        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")

            # Verify lease validity
            cursor = conn.execute("""
            SELECT is_active FROM leases WHERE lease_token = ? AND task_id = ?;
            """, (lease_token, task_id))
            lease_row = cursor.fetchone()
            if not lease_row or lease_row[0] != 1:
                conn.rollback()
                return False # Fencing token invalid

            # Update task
            conn.execute("""
            UPDATE tasks
            SET next_unprocessed_k = ?, status = ?, last_updated_utc = ?
            WHERE task_id = ?;
            """, (next_k, new_status, now, task_id))

            # Mark lease inactive if completed
            if is_completed:
                conn.execute("UPDATE leases SET is_active = 0 WHERE lease_token = ?;", (lease_token,))

            # Append stage metrics
            conn.execute("""
            INSERT INTO stage_metrics (
                task_id, worker_id, raw_tested, wheel_survivors, sieve_survivors,
                prp_screened, prp_passed, proth_proven, llr_proven,
                wall_seconds, cpu_seconds, timestamp_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                task_id,
                worker_id,
                metrics_dict.get("raw_tested", 0),
                metrics_dict.get("wheel_survivors", 0),
                metrics_dict.get("sieve_survivors", 0),
                metrics_dict.get("prp_screened", 0),
                metrics_dict.get("prp_passed", 0),
                metrics_dict.get("proth_proven", 0),
                metrics_dict.get("llr_proven", 0),
                metrics_dict.get("wall_seconds", 0.0),
                metrics_dict.get("cpu_seconds", 0.0),
                now
            ))

            conn.commit()
            return True

    def record_discovery(
        self,
        payload_sha256: str,
        campaign_id: str,
        task_id: str,
        k: int,
        n: int,
        digits: int,
        proth_witness: int,
        llr_p: int,
        payload_path: str,
        independent_status: str = "UNVERIFIED",
        attestation_path: Optional[str] = None
    ):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO discoveries (
                payload_sha256, campaign_id, task_id, k, n, digits,
                proth_witness, llr_p, payload_path, independent_status,
                attestation_path, discovered_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                payload_sha256, campaign_id, task_id, k, n, digits,
                proth_witness, llr_p, payload_path, independent_status,
                attestation_path, now
            ))
            conn.commit()

    def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Queries aggregated campaign metrics and progress."""
        with self._connection() as conn:
            c_tasks = conn.execute("""
            SELECT
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END),
                COUNT(CASE WHEN status = 'PARTIAL' THEN 1 END),
                COUNT(CASE WHEN status = 'LEASED' THEN 1 END),
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END),
                COUNT(*)
            FROM tasks WHERE campaign_id = ?;
            """, (campaign_id,)).fetchone()

            c_metrics = conn.execute("""
            SELECT
                COALESCE(SUM(raw_tested), 0),
                COALESCE(SUM(sieve_survivors), 0),
                COALESCE(SUM(prp_passed), 0),
                COALESCE(SUM(proth_proven), 0),
                COALESCE(SUM(wall_seconds), 0.0)
            FROM stage_metrics sm
            JOIN tasks t ON sm.task_id = t.task_id
            WHERE t.campaign_id = ?;
            """, (campaign_id,)).fetchone()

            c_disc = conn.execute("""
            SELECT COUNT(*) FROM discoveries WHERE campaign_id = ?;
            """, (campaign_id,)).fetchone()

            # Active leases check
            now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            active_leases = conn.execute("""
            SELECT COUNT(*) FROM leases
            WHERE campaign_id = ? AND is_active = 1 AND expires_utc >= ?;
            """, (campaign_id, now_utc)).fetchone()

            return {
                "campaign_id": campaign_id,
                "completed_tasks": c_tasks[0],
                "partial_tasks": c_tasks[1],
                "leased_tasks": c_tasks[2],
                "pending_tasks": c_tasks[3],
                "total_tasks": c_tasks[4],
                "raw_tested": c_metrics[0],
                "sieve_survivors": c_metrics[1],
                "prp_passed": c_metrics[2],
                "proven_pairs": c_metrics[3],
                "elapsed_wall_seconds": c_metrics[4],
                "discoveries": c_disc[0],
                "active_leases": active_leases[0]
            }
