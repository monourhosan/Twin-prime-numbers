"""
Durable, crash-safe checkpointing and progress logging for Phase 2 search campaigns.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

class SearchCheckpoint:
    """
    Manages atomic persistence of search progress, completed windows,
    PRP candidate hits, and discovered proof certificates.
    """

    def __init__(self, checkpoint_dir: Path, session_id: Optional[str] = None):
        self.dir = Path(checkpoint_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or f"phase2_session_{int(time.time())}"
        self.state_file = self.dir / "checkpoint_state.json"
        self.completed_windows: Set[str] = set()
        self.stats = {
            "total_candidates_screened": 0,
            "wheel_survivors": 0,
            "sieve_survivors": 0,
            "prp_hits": 0,
            "proven_pairs": 0,
            "cpu_seconds_accumulated": 0.0,
            "last_updated_utc": None,
        }
        self.load()

    def _window_key(self, n: int, k_start: int, k_end: int) -> str:
        return f"n{n}_k{k_start}_{k_end}"

    def is_window_completed(self, n: int, k_start: int, k_end: int) -> bool:
        return self._window_key(n, k_start, k_end) in self.completed_windows

    def mark_window_completed(self, n: int, k_start: int, k_end: int, stats_delta: Dict[str, Any]):
        self.completed_windows.add(self._window_key(n, k_start, k_end))
        for k, v in stats_delta.items():
            if k in self.stats:
                self.stats[k] += v
        self.stats["last_updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.save()

    def save(self):
        payload = {
            "session_id": self.session_id,
            "stats": self.stats,
            "completed_windows": sorted(list(self.completed_windows)),
        }
        # Atomic write: write to temp file then atomic replace
        temp_file = self.dir / f"checkpoint_state.tmp.{os.getpid()}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        temp_file.replace(self.state_file)

    def load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.session_id = data.get("session_id", self.session_id)
                self.stats = data.get("stats", self.stats)
                self.completed_windows = set(data.get("completed_windows", []))
            except Exception as e:
                print(f"Warning: Failed to load checkpoint {self.state_file}: {e}")
        return {
            "session_id": self.session_id,
            "stats": self.stats,
            "completed_windows": sorted(list(self.completed_windows)),
        }

    def record_completed_window(self, task_id: str, info: Dict[str, Any]):
        self.completed_windows.add(task_id)
        if "raw_tested" in info:
            self.stats["total_candidates_screened"] += info["raw_tested"]
        if "survivors" in info:
            self.stats["sieve_survivors"] += info["survivors"]
        if "discovered" in info:
            self.stats["proven_pairs"] += info["discovered"]
        if "elapsed_sec" in info:
            self.stats["cpu_seconds_accumulated"] += info["elapsed_sec"]
        self.stats["last_updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.save()

CheckpointManager = SearchCheckpoint

