"""Phase 11 Staged Campaign Orchestrator, Atomic Checkpointing, and Telemetry Guardrails.

Implements:
  1. Atomic JSON checkpointing strictly compliant with 7-field schema.
  2. Crash-resilient resumption preventing duplicate work.
  3. Hardware RAM guardrails (>= 2.5 GB free) and GPU thermal guardrails (80°C / 85°C with 300s timeout).
  4. 4-stage progressive execution: sanity -> density -> optimize -> discovery.
"""

import json
import logging
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .screening import screen_candidate
from .sieve import sieve_survivors

logger = logging.getLogger(__name__)


def get_free_ram_gb() -> float:
    """Returns host available RAM in Gigabytes via psutil or ctypes fallback."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except (ImportError, AttributeError):
        pass

    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return stat.ullAvailPhys / (1024 ** 3)
    except (AttributeError, OSError, ValueError):
        pass

    return 4.0


def get_gpu_temperature() -> float | None:
    """Queries NVIDIA GPU temperature in Celsius via nvidia-smi."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            if lines:
                return float(lines[0])
    except (subprocess.SubprocessError, OSError, ValueError, IndexError):
        pass
    return None


def evaluate_guardrails(free_ram_gb: float, gpu_temp_c: float | None) -> str:
    """Evaluates hardware safety policy:

      - free_ram_gb < 2.5 -> 'PAUSE_MEMORY'
      - gpu_temp_c >= 85.0 -> 'PAUSE_THERMAL'
      - gpu_temp_c >= 80.0 -> 'THROTTLE_GPU'
      - otherwise -> 'NORMAL'
    """
    if free_ram_gb < 2.5:
        return "PAUSE_MEMORY"
    if gpu_temp_c is not None:
        if gpu_temp_c >= 85.0:
            return "PAUSE_THERMAL"
        if gpu_temp_c >= 80.0:
            return "THROTTLE_GPU"
    return "NORMAL"


class CampaignOrchestrator:
    """Executes staged campaigns with atomic persistence and safety guardrails."""

    def __init__(
        self,
        run_id: str,
        anchor_y: int,
        t_start: int,
        t_end: int,
        sieve_depth: int = 1000,
        batch_size: int = 500,
        output_dir: Path | None = None,
        stop_on_first_discovery: bool = False,
        enforce_ram_guardrail: bool = False,
    ):
        self.run_id = run_id
        self.anchor_y = anchor_y
        self.t_start = t_start
        self.t_end = t_end
        self.sieve_depth = sieve_depth
        self.batch_size = batch_size
        self.stop_on_first_discovery = stop_on_first_discovery
        self.enforce_ram_guardrail = enforce_ram_guardrail

        self.output_dir = output_dir or Path("runs/phase11")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.output_dir / f"{run_id}_checkpoint.json"

        self.current_t = t_start
        self.completed_intervals: list[list[int]] = []
        self.survivors: list[int] = []
        self.discoveries: list[dict[str, Any]] = []
        self.survivor_count = 0

    def load_checkpoint_if_exists(self) -> bool:
        """Loads and validates existing checkpoint, advancing current_t.

        Resilient against corrupted, truncated, empty, or schema-invalid files.
        Falls back to .bak backup if present and valid.
        """
        def _read_and_validate(path: Path) -> dict[str, Any] | None:
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if not content:
                    logger.warning("Checkpoint file is empty: %s", path)
                    return None
                data = json.loads(content)
                if not isinstance(data, dict):
                    logger.warning("Checkpoint JSON root is not a dict: %s", path)
                    return None
                for key in ("run_id", "anchor_y", "current_t", "completed_intervals", "survivor_count"):
                    if key not in data:
                        logger.warning("Checkpoint missing required field '%s': %s", key, path)
                        return None
                # Validate types and conversions
                _ = str(data["run_id"])
                _ = int(data["anchor_y"])
                _ = int(data["current_t"])
                _ = [list(i) for i in data["completed_intervals"]]
                _ = int(data["survivor_count"])
                return data
            except (json.JSONDecodeError, KeyError, ValueError, TypeError, OSError) as exc:
                logger.warning("Failed to parse checkpoint %s: %s", path, exc)
                return None

        data = _read_and_validate(self.checkpoint_file)
        if data is None and self.checkpoint_file.is_file():
            # Primary checkpoint exists but is invalid/corrupt. Try backup candidates.
            bak_candidates = [
                self.checkpoint_file.with_suffix(".bak"),
                self.checkpoint_file.with_name(self.checkpoint_file.name + ".bak"),
            ]
            for bak_p in bak_candidates:
                if bak_p.is_file():
                    logger.warning("Primary checkpoint invalid; attempting fallback to %s", bak_p)
                    data = _read_and_validate(bak_p)
                    if data is not None:
                        logger.info("Successfully recovered checkpoint from backup %s", bak_p)
                        break

        if data is None:
            return False

        self.run_id = str(data["run_id"])
        self.anchor_y = int(data["anchor_y"])
        self.current_t = int(data["current_t"])
        self.completed_intervals = [list(i) for i in data["completed_intervals"]]
        self.survivor_count = int(data["survivor_count"])
        return True

    def save_checkpoint(self) -> None:
        """Atomically persists checkpoint JSON matching 7 required schema fields."""
        state = {
            "run_id": self.run_id,
            "method_id": "OPQM_CRT_HYBRID_11",
            "anchor_y": self.anchor_y,
            "current_t": self.current_t,
            "completed_intervals": self.completed_intervals,
            "survivor_count": max(len(self.survivors), self.survivor_count),
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        tmp_file = self.checkpoint_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        # Update backup if current checkpoint exists
        if self.checkpoint_file.is_file():
            try:
                shutil.copy2(self.checkpoint_file, self.checkpoint_file.with_suffix(".bak"))
            except OSError:
                pass
        tmp_file.replace(self.checkpoint_file)

    def run_work_unit(self, b_start: int, b_end: int) -> list[int]:
        """Executes a single bounded work unit."""
        # Check for duplicated work
        for interval in self.completed_intervals:
            if interval[0] <= b_start and b_end <= interval[1]:
                return []

        survivors = sieve_survivors(self.anchor_y, b_start, b_end, self.sieve_depth, odd_only=True)
        self.survivors.extend(survivors)
        self.survivor_count = len(self.survivors)

        # Screen survivors
        for t in survivors:
            status, pair = screen_candidate(self.anchor_y, t)
            if status == "DUAL_PRP" and pair is not None:
                _C, A, B = pair
                discovery_record = {
                    "method_id": "OPQM_CRT_HYBRID_11",
                    "anchor_y": self.anchor_y,
                    "multiplier_t": t,
                    "lower_prime": str(A),
                    "upper_prime": str(B),
                    "digits": len(str(A)),
                    "timestamp_utc": datetime.now(UTC).isoformat(),
                }
                self.discoveries.append(discovery_record)
                if self.stop_on_first_discovery:
                    break

        self.completed_intervals.append([b_start, b_end])
        self.current_t = b_end
        self.save_checkpoint()
        return survivors

    def execute(self) -> dict[str, Any]:
        """Executes campaign from current_t to t_end under safety guardrails."""
        self.load_checkpoint_if_exists()
        if self.completed_intervals:
            cursor = max(interval[1] for interval in self.completed_intervals) + 1
        else:
            cursor = self.current_t

        while cursor <= self.t_end:
            # Check guardrails
            ram_gb = get_free_ram_gb()
            gpu_temp = get_gpu_temperature()
            status = evaluate_guardrails(ram_gb, gpu_temp)

            if status == "PAUSE_MEMORY":
                if self.enforce_ram_guardrail:
                    print(f"RAM Guardrail: Available RAM {ram_gb:.2f} GB < 2.5 GB. Pausing.")
                    self.save_checkpoint()
                    break
                else:
                    print(f"RAM Guardrail warning: Available RAM {ram_gb:.2f} GB < 2.5 GB (non-blocking).")
            elif status == "PAUSE_THERMAL":
                print(f"Thermal Guardrail: GPU temp {gpu_temp}°C >= 85°C. Waiting up to 300s for cooldown...")
                cooldown_start = time.time()
                cooled = False
                while time.time() - cooldown_start < 300:
                    time.sleep(5)
                    new_temp = get_gpu_temperature()
                    if new_temp is None or new_temp < 80.0:
                        cooled = True
                        break
                if not cooled:
                    print("Thermal cooldown timed out. Pausing campaign.")
                    self.save_checkpoint()
                    break
            elif status == "THROTTLE_GPU":
                time.sleep(2.0)

            b_start = cursor
            b_end = min(self.t_end, cursor + self.batch_size - 1)
            self.run_work_unit(b_start, b_end)
            cursor = b_end + 1

            if self.stop_on_first_discovery and len(self.discoveries) > 0:
                break

        return {
            "run_id": self.run_id,
            "anchor_y": self.anchor_y,
            "completed_intervals": self.completed_intervals,
            "survivors_found": len(self.survivors),
            "discoveries": self.discoveries,
        }
