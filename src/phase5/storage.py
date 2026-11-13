"""
Phase 5 Durable Storage & Deduplication Ledger.
Manages work units, leases, candidate progression, discoveries, and deduplication
using SQLite with Write-Ahead Logging (WAL) for durability across restarts.
"""

import sqlite3
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

class Phase5Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS work_units (
                work_unit_id TEXT PRIMARY KEY,
                family_id TEXT NOT NULL,
                family_config TEXT NOT NULL,
                t_start INTEGER NOT NULL,
                t_end INTEGER NOT NULL,
                sieve_limit INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                worker_id TEXT,
                lease_expiry REAL,
                survivors INTEGER DEFAULT 0,
                dual_prp INTEGER DEFAULT 0,
                proven INTEGER DEFAULT 0,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                family_id TEXT NOT NULL,
                t INTEGER NOT NULL,
                A_str TEXT NOT NULL,
                B_str TEXT NOT NULL,
                digits INTEGER NOT NULL,
                status TEXT NOT NULL,
                canonical_hash TEXT NOT NULL UNIQUE,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discoveries (
                discovery_id TEXT PRIMARY KEY,
                family_id TEXT NOT NULL,
                t INTEGER NOT NULL,
                digits INTEGER NOT NULL,
                A_str TEXT NOT NULL,
                B_str TEXT NOT NULL,
                cert_path TEXT NOT NULL,
                sha256 TEXT NOT NULL UNIQUE,
                novelty_status TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bandit_stats (
                family_id TEXT PRIMARY KEY,
                pulls INTEGER DEFAULT 0,
                total_time REAL DEFAULT 0.0,
                survivors INTEGER DEFAULT 0,
                dual_prp INTEGER DEFAULT 0,
                proven INTEGER DEFAULT 0,
                last_reward REAL DEFAULT 0.0
            );

            CREATE INDEX IF NOT EXISTS idx_wu_status ON work_units(status, lease_expiry);
            CREATE INDEX IF NOT EXISTS idx_cand_hash ON candidates(canonical_hash);
            """)

    def register_work_unit(
        self,
        work_unit_id: str,
        family_id: str,
        family_config: Dict[str, Any],
        t_start: int,
        t_end: int,
        sieve_limit: int
    ) -> bool:
        """Registers a new work unit if not already registered."""
        now = time.time()
        config_str = json.dumps(family_config, sort_keys=True)
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO work_units 
                (work_unit_id, family_id, family_config, t_start, t_end, sieve_limit, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)""",
                (work_unit_id, family_id, config_str, t_start, t_end, sieve_limit, now)
            )
            return cursor.rowcount > 0

    def lease_work_unit(self, worker_id: str, lease_duration_sec: float = 60.0) -> Optional[Dict[str, Any]]:
        """
        Atomically leases a PENDING or expired work unit.
        Returns the leased work unit dict or None if no work is available.
        """
        now = time.time()
        expiry = now + lease_duration_sec
        with self._get_connection() as conn:
            # Reclaim expired leases or acquire pending
            row = conn.execute(
                """SELECT work_unit_id, family_id, family_config, t_start, t_end, sieve_limit
                FROM work_units
                WHERE status = 'PENDING' OR (status = 'LEASED' AND lease_expiry < ?)
                ORDER BY t_start ASC LIMIT 1""",
                (now,)
            ).fetchone()

            if row is None:
                return None

            wu_id = row["work_unit_id"]
            conn.execute(
                """UPDATE work_units 
                SET status = 'LEASED', worker_id = ?, lease_expiry = ?, updated_at = ?
                WHERE work_unit_id = ?""",
                (worker_id, expiry, now, wu_id)
            )
            res = dict(row)
            res["family_config"] = json.loads(res["family_config"])
            return res

    def complete_work_unit(self, work_unit_id: str, survivors: int, dual_prp: int, proven: int):
        """Marks work unit COMPLETE and logs telemetry."""
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE work_units
                SET status = 'COMPLETE', survivors = ?, dual_prp = ?, proven = ?, lease_expiry = NULL, updated_at = ?
                WHERE work_unit_id = ?""",
                (survivors, dual_prp, proven, now, work_unit_id)
            )

    def record_candidate(
        self,
        family_id: str,
        t: int,
        A: int,
        B: int,
        digits: int,
        status: str,
        canonical_hash: str
    ):
        """Records a candidate in the ledger."""
        now = time.time()
        cand_id = f"{family_id}_t{t}"
        with self._get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO candidates
                (candidate_id, family_id, t, A_str, B_str, digits, status, canonical_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cand_id, family_id, t, str(A), str(B), digits, status, canonical_hash, now)
            )

    def record_discovery(
        self,
        family_id: str,
        t: int,
        digits: int,
        A: int,
        B: int,
        cert_path: str,
        sha256: str,
        novelty_status: str
    ):
        """Records an independently certified discovery."""
        now = time.time()
        disc_id = f"disc_{family_id}_t{t}"
        with self._get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO discoveries
                (discovery_id, family_id, t, digits, A_str, B_str, cert_path, sha256, novelty_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (disc_id, family_id, t, digits, str(A), str(B), cert_path, sha256, novelty_status, now)
            )

    def update_bandit_stats(
        self,
        family_id: str,
        elapsed_sec: float,
        survivors: int,
        dual_prp: int,
        proven: int
    ):
        """Updates online performance stats for Method S2 bandit scheduler."""
        reward = (survivors * 0.1 + dual_prp * 10.0 + proven * 1000.0) / max(elapsed_sec, 0.001)
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO bandit_stats (family_id, pulls, total_time, survivors, dual_prp, proven, last_reward)
                VALUES (?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(family_id) DO UPDATE SET
                    pulls = pulls + 1,
                    total_time = total_time + excluded.total_time,
                    survivors = survivors + excluded.survivors,
                    dual_prp = dual_prp + excluded.dual_prp,
                    proven = proven + excluded.proven,
                    last_reward = excluded.last_reward""",
                (family_id, elapsed_sec, survivors, dual_prp, proven, reward)
            )

    def get_bandit_stats(self) -> Dict[str, Dict[str, Any]]:
        """Returns current bandit performance table."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM bandit_stats").fetchall()
            return {r["family_id"]: dict(r) for r in rows}

    def is_known_discovery(self, canonical_hash: str) -> bool:
        """Checks if a canonical hash already exists in discoveries or candidates."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT 1 FROM candidates WHERE canonical_hash = ?", (canonical_hash,)).fetchone()
            if row:
                return True
            row = conn.execute("SELECT 1 FROM discoveries WHERE sha256 = ?", (canonical_hash,)).fetchone()
            return row is not None
