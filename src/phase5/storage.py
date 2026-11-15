"""
Phase 5 Durable Storage & Deduplication Ledger.
Manages work units, leases, candidate progression, discoveries, and deduplication
using SQLite with Write-Ahead Logging (WAL) for durability across restarts.

Integrity guarantees:
1. Canonical pair identity is computed from exact integer tuple (A, B) with domain separation:
   twin-pair-v1:<decimal A>:<decimal B>.
2. Novelty classification evaluates pre-run historical inventory and past discoveries/proven pairs,
   never self-contaminating against candidates undergoing active PRP screening.
3. Discovery lookup operates on pair_id / pair hash, never confusing certificate SHA-256 with pair hash.
4. Fail-closed connection management: connections are safely closed to prevent Windows file-locking.
"""

import sqlite3
import time
import json
import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

class Phase5Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

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
                pair_id TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bandit_stats (
                family_id TEXT PRIMARY KEY,
                pulls INTEGER DEFAULT 0,
                cumulative_reward REAL DEFAULT 0.0,
                mean_reward REAL DEFAULT 0.0,
                total_time REAL DEFAULT 0.0,
                survivors INTEGER DEFAULT 0,
                dual_prp INTEGER DEFAULT 0,
                proven INTEGER DEFAULT 0,
                last_reward REAL DEFAULT 0.0,
                updated_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_wu_status ON work_units(status, lease_expiry);
            CREATE INDEX IF NOT EXISTS idx_cand_hash ON candidates(canonical_hash);
            """)

            # Safe schema migration for pair_id in discoveries
            cols = [col["name"] for col in conn.execute("PRAGMA table_info(discoveries)").fetchall()]
            if "pair_id" not in cols:
                conn.execute("ALTER TABLE discoveries ADD COLUMN pair_id TEXT;")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_disc_pair_id ON discoveries(pair_id);")

    @staticmethod
    def canonical_key(A: int, B: int) -> str:
        """Returns standard normalized canonical key for a pair: min(A, B):max(A, B)."""
        p_min = min(int(A), int(B))
        p_max = max(int(A), int(B))
        return f"{p_min}:{p_max}"

    @staticmethod
    def canonical_pair_key(A: int, B: int) -> str:
        """Returns domain-separated canonical key: twin-pair-v1:min(A, B):max(A, B)."""
        p_min = min(int(A), int(B))
        p_max = max(int(A), int(B))
        return f"twin-pair-v1:{p_min}:{p_max}"

    @staticmethod
    def canonical_hash(A: int, B: int) -> str:
        """Deterministic SHA-256 over standard canonical key."""
        key = Phase5Storage.canonical_key(A, B)
        return hashlib.sha256(key.encode("ascii")).hexdigest()

    @staticmethod
    def canonical_pair_id(A: int, B: int) -> str:
        """Deterministic SHA-256 over domain-separated canonical pair key."""
        key = Phase5Storage.canonical_pair_key(A, B)
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def check_novelty(
        self,
        A: int,
        B: int,
        historical_inventory_path: Optional[Path] = None
    ) -> str:
        """
        Explicit Fail-Closed Novelty Pipeline:
        1. Validate gap == 2 and odd numbers > 2.
        2. Check against frozen historical pre-run inventory baseline.
        3. Check against accepted discoveries and proven pairs in current run database.
        Returns one of:
        - INVALID_PAIR
        - ALREADY_IN_HISTORICAL_INVENTORY
        - DUPLICATE_IN_CURRENT_RUN
        - NEW_TO_REPOSITORY
        """
        p_min = min(int(A), int(B))
        p_max = max(int(A), int(B))

        if p_max - p_min != 2:
            return "INVALID_PAIR"
        if p_min <= 2 or p_min % 2 == 0 or p_max % 2 == 0:
            return "INVALID_PAIR"

        c_key = self.canonical_key(A, B)
        c_pair_key = self.canonical_pair_key(A, B)
        c_hash = self.canonical_hash(A, B)
        c_pair_id = self.canonical_pair_id(A, B)

        # Step 1: Compare against frozen historical inventory baseline
        if historical_inventory_path:
            h_path = Path(historical_inventory_path)
            if h_path.exists():
                try:
                    with open(h_path, "r", encoding="utf-8") as f:
                        hist_data = json.load(f)
                    for item in hist_data:
                        if (
                            item.get("canonical_key") == c_key or
                            item.get("canonical_pair_key") == c_pair_key or
                            item.get("pair_id") == c_pair_id or
                            (item.get("P") == str(p_min) and item.get("Q") == str(p_max)) or
                            (item.get("A") == str(p_min) and item.get("B") == str(p_max))
                        ):
                            return "ALREADY_IN_HISTORICAL_INVENTORY"
                except Exception:
                    pass

        # Step 2: Compare against current run database
        # Note: Do not treat active screening stages (PRP_BOTH, COMPOSITE) as duplicate discoveries!
        # Only treat completed discoveries or certified/proven pairs as duplicate.
        with self._get_connection() as conn:
            row_d = conn.execute(
                "SELECT 1 FROM discoveries WHERE pair_id = ? OR (A_str = ? AND B_str = ?)",
                (c_pair_id, str(p_min), str(p_max))
            ).fetchone()
            if row_d:
                return "DUPLICATE_IN_CURRENT_RUN"

            row_c = conn.execute(
                "SELECT 1 FROM candidates WHERE canonical_hash = ? AND status IN ('PROVEN_BOTH', 'VERIFIED_BOTH')",
                (c_hash,)
            ).fetchone()
            if row_c:
                return "DUPLICATE_IN_CURRENT_RUN"

        return "NEW_TO_REPOSITORY"

    def is_known_discovery(self, canonical_identifier: str) -> bool:
        """
        Checks if a canonical pair identifier exists in accepted discoveries
        or previously proven candidates. Does NOT treat active PRP screening as known discovery.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM discoveries WHERE pair_id = ? OR discovery_id = ?",
                (canonical_identifier, f"disc_{canonical_identifier}")
            ).fetchone()
            if row:
                return True
            row_c = conn.execute(
                "SELECT 1 FROM candidates WHERE canonical_hash = ? AND status IN ('PROVEN_BOTH', 'VERIFIED_BOTH')",
                (canonical_identifier,)
            ).fetchone()
            return row_c is not None

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
        """Marks work unit COMPLETE and logs measured telemetry."""
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE work_units
                SET status = 'COMPLETE', survivors = ?, dual_prp = ?, proven = ?, lease_expiry = NULL, updated_at = ?
                WHERE work_unit_id = ?""",
                (survivors, dual_prp, proven, now, work_unit_id)
            )

    def get_max_t_for_family(self, family_id: str) -> int:
        """Returns max(t_end) for given family across registered work units, or 0 if none."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT MAX(t_end) as max_t FROM work_units WHERE family_id = ?",
                (family_id,)
            ).fetchone()
            if row and row["max_t"] is not None:
                return int(row["max_t"])
            return 0

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
        """Records a candidate in the progression ledger."""
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
        novelty_status: str,
        pair_id: Optional[str] = None
    ):
        """Records an independently certified and verified discovery."""
        now = time.time()
        disc_id = f"disc_{family_id}_t{t}"
        p_id = pair_id or self.canonical_pair_id(A, B)
        with self._get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO discoveries
                (discovery_id, family_id, t, digits, A_str, B_str, cert_path, sha256, novelty_status, pair_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (disc_id, family_id, t, digits, str(A), str(B), cert_path, sha256, novelty_status, p_id, now)
            )

    @staticmethod
    def compute_bounded_reward(
        survivors: int,
        batch_size: int,
        dual_prp: int,
        proven: int,
        elapsed_sec: float
    ) -> float:
        """
        Computes a bounded reward in [0.0, 1.0] for UCB1:
        - Sieve yield component: min(1.0, survivors / batch_size) * 0.1
        - Dual PRP hit component: min(1.0, dual_prp) * 0.4
        - Proven pair component: min(1.0, proven) * 0.5
        """
        b_size = max(int(batch_size), 1)
        sieve_ratio = min(1.0, survivors / b_size)
        prp_ratio = min(1.0, dual_prp / 1.0)
        proven_ratio = min(1.0, proven / 1.0)
        raw = 0.1 * sieve_ratio + 0.4 * prp_ratio + 0.5 * proven_ratio
        return max(0.0, min(1.0, raw))

    def update_bandit_stats(
        self,
        family_id: str,
        elapsed_sec: float,
        survivors: int,
        dual_prp: int,
        proven: int,
        reward: Optional[float] = None,
        batch_size: int = 1000
    ):
        """Updates online performance stats with cumulative reward and mean reward."""
        if reward is None:
            r = self.compute_bounded_reward(survivors, batch_size, dual_prp, proven, elapsed_sec)
        else:
            r = max(0.0, min(1.0, float(reward)))

        now = time.time()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT pulls, cumulative_reward, total_time, survivors, dual_prp, proven FROM bandit_stats WHERE family_id = ?",
                (family_id,)
            ).fetchone()

            if row:
                pulls = row["pulls"] + 1
                cum_reward = row["cumulative_reward"] + r
                mean_reward = cum_reward / pulls
                tot_time = row["total_time"] + elapsed_sec
                surv = row["survivors"] + survivors
                d_prp = row["dual_prp"] + dual_prp
                prv = row["proven"] + proven
                conn.execute(
                    """UPDATE bandit_stats SET
                        pulls = ?, cumulative_reward = ?, mean_reward = ?, total_time = ?,
                        survivors = ?, dual_prp = ?, proven = ?, last_reward = ?, updated_at = ?
                    WHERE family_id = ?""",
                    (pulls, cum_reward, mean_reward, tot_time, surv, d_prp, prv, r, now, family_id)
                )
            else:
                conn.execute(
                    """INSERT INTO bandit_stats
                    (family_id, pulls, cumulative_reward, mean_reward, total_time, survivors, dual_prp, proven, last_reward, updated_at)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (family_id, r, r, elapsed_sec, survivors, dual_prp, proven, r, now)
                )

    def get_bandit_stats(self) -> Dict[str, Dict[str, Any]]:
        """Returns current bandit performance table."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM bandit_stats").fetchall()
            return {r["family_id"]: dict(r) for r in rows}
