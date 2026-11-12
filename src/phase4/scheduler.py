"""
Phase 4 Task Scheduler and Interval Planner.
Generates deterministic, gap-free work units across configured exponents.
"""

import hashlib
from typing import List, Tuple
from .config import Phase4Config
from .storage import Phase4Storage

def compute_canonical_task_id(config_sha256: str, n: int, k_start: int, k_end: int, schema_version: str = "4.0") -> str:
    raw = f"{config_sha256}|{n}|{k_start}|{k_end}|{schema_version}"
    return f"task_{n}_{k_start}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"

class TaskScheduler:
    def __init__(self, config: Phase4Config, storage: Phase4Storage):
        self.config = config
        self.storage = storage
        self.config_sha256 = config.compute_sha256()

    def plan_and_register_tasks(self, num_windows_ahead: int = 20) -> int:
        """
        Plans next batch of windows across all configured exponents.
        Returns total number of newly registered tasks.
        """
        records = []
        k_span = self.config.window_k_span

        for n in self.config.exponents:
            two_n = 1 << n
            k_cur = self.config.k_start

            for _ in range(num_windows_ahead):
                k_next = k_cur + k_span
                if self.config.k_end is not None and k_cur >= self.config.k_end:
                    break
                if self.config.k_end is not None and k_next > self.config.k_end:
                    k_next = self.config.k_end

                # Enforce k < 2^n
                if k_cur >= two_n:
                    break
                if k_next > two_n:
                    k_next = two_n

                task_id = compute_canonical_task_id(self.config_sha256, n, k_cur, k_next, self.config.schema_version)
                records.append((task_id, self.config.campaign_id, n, k_cur, k_next))

                k_cur = k_next
                if self.config.k_end is not None and k_cur >= self.config.k_end:
                    break

        if records:
            self.storage.register_tasks_batch(records)
        return len(records)
