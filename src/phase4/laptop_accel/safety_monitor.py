"""
Laptop Safety Monitor and Thermal/Resource Guardrails.
Guarantees sustainable execution on Intel i5-10210U + NVIDIA MX250:
- Enforces AC line power requirement (prevents battery discharge degradation).
- Monitors available system RAM (minimum threshold 2.0 - 2.5 GB).
- Monitors disk space on system and project drives (minimum threshold 30 GB).
- Reads GPU temperature and enforces soft (78-80C) and hard pause (85C) limits.
- Manages fallback conservative worker budgeting when CPU thermal sensors are restricted.
"""

from typing import Dict, Any, Tuple, List
from .hardware_probe import get_memory_info, get_disk_info, get_power_info, get_gpu_info

class LaptopSafetyMonitor:
    def __init__(
        self,
        require_ac_power: bool = True,
        min_available_ram_gb: float = 2.5,
        min_free_disk_gb: float = 30.0,
        gpu_soft_temp_c: int = 80,
        gpu_pause_temp_c: int = 85,
        cpu_soft_temp_c: int = 85,
        cpu_pause_temp_c: int = 92,
        if_temp_monitoring_unavailable: str = "conservative_mode"
    ):
        self.require_ac_power = require_ac_power
        self.min_available_ram_gb = min_available_ram_gb
        self.min_free_disk_gb = min_free_disk_gb
        self.gpu_soft_temp_c = gpu_soft_temp_c
        self.gpu_pause_temp_c = gpu_pause_temp_c
        self.cpu_soft_temp_c = cpu_soft_temp_c
        self.cpu_pause_temp_c = cpu_pause_temp_c
        self.if_temp_monitoring_unavailable = if_temp_monitoring_unavailable

    def check_safety(self) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Evaluates current physical status against all safety constraints.
        Returns: (is_safe, list_of_violations_or_warnings, current_snapshot)
        """
        violations = []
        warnings = []
        snapshot = {}

        # 1. Power
        pwr = get_power_info()
        snapshot["power"] = pwr
        if self.require_ac_power and not pwr.get("is_ac_online", True):
            violations.append(f"AC power unplugged! Operating on battery ({pwr.get('battery_percent', '?')}%). Sustained search forbidden on battery.")

        # 2. RAM
        mem = get_memory_info()
        snapshot["memory"] = mem
        avail_ram = mem.get("avail_ram_gb", 0.0)
        if avail_ram < self.min_available_ram_gb:
            violations.append(f"Low system memory! Available: {avail_ram:.2f} GB (minimum threshold {self.min_available_ram_gb:.2f} GB). Risk of paging thrash.")
        elif avail_ram < self.min_available_ram_gb + 1.0:
            warnings.append(f"Moderate memory pressure: {avail_ram:.2f} GB available.")

        # 3. Disk
        disk = get_disk_info()
        snapshot["disk"] = disk
        for drive, dinfo in disk.items():
            free_gb = dinfo.get("free_gb", 0.0)
            if free_gb < self.min_free_disk_gb:
                violations.append(f"Low disk space on {drive}! Free: {free_gb:.1f} GB (minimum threshold {self.min_free_disk_gb:.1f} GB).")

        # 4. GPU Thermals & VRAM
        gpu = get_gpu_info()
        snapshot["gpu"] = gpu
        if gpu.get("present"):
            temp = gpu.get("temp_c")
            if temp is not None:
                if temp >= self.gpu_pause_temp_c:
                    violations.append(f"CRITICAL GPU OVERHEAT: GPU temperature is {temp}°C (pause threshold: {self.gpu_pause_temp_c}°C).")
                elif temp >= self.gpu_soft_temp_c:
                    warnings.append(f"High GPU temperature: {temp}°C (soft threshold: {self.gpu_soft_temp_c}°C).")

            free_vram = gpu.get("vram_free_mb")
            if free_vram is not None and free_vram < 256.0:
                warnings.append(f"Low GPU VRAM: {free_vram:.0f} MB free.")

        is_safe = (len(violations) == 0)
        all_messages = violations + warnings
        return is_safe, all_messages, snapshot

    def recommend_safe_worker_count(self, requested: int = 3) -> int:
        """
        Determines the maximum sustainable worker count on the i5-10210U (4c/8t, 15W TDP).
        Under conservative mode, limits workers to 2-3 to avoid severe thermal throttling.
        """
        logical = 8
        if self.if_temp_monitoring_unavailable == "conservative_mode":
            # 4 physical cores, 15W TDP. Pegging 4+ cores causes clock throttling from 2.1 GHz to ~1.6 GHz.
            # 2 to 3 workers maintains sustained high boost (~2.4-2.8 GHz) without thermal saturation.
            return max(1, min(requested, 3))
        return max(1, min(requested, logical - 1))
