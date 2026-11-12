"""
Deterministic Task Partitioning and Scheduling Planner for Phase 3.
Ensures zero-overlap and gapless coverage across multi-exponent campaigns.
"""

from typing import List, Dict, Any, Optional
from .config import Phase3Config
from .storage import Phase3Storage

class TaskScheduler:
    def __init__(self, config: Phase3Config, storage: Phase3Storage):
        self.config = config
        self.storage = storage

    def plan_and_register_tasks(self, num_windows_ahead: int = 20) -> List[str]:
        """
        Plans progressive tasks according to configuration and registers them.
        """
        registered_ids = []
        w_size = self.config.window_size

        for n in self.config.exponents:
            k_curr = self.config.k_start
            k_limit = self.config.k_end or (k_curr + w_size * num_windows_ahead)

            while k_curr < k_limit:
                k_next = min(k_curr + w_size, k_limit)
                task_id = f"task_{self.config.campaign_id}_n{n}_k{k_curr}_{k_next}"
                self.storage.register_task(
                    task_id=task_id,
                    campaign_id=self.config.campaign_id,
                    n=n,
                    k_start=k_curr,
                    k_end=k_next
                )
                registered_ids.append(task_id)
                k_curr = k_next

        return registered_ids
