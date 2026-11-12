"""
Automated Test Suite for Laptop CPU + NVIDIA GeForce MX250 Acceleration Pipeline.
Tests:
- Hardware diagnostics and environment probe.
- Safety guardrails and thermal monitoring.
- CUDA driver API initialization and PTX compilation on sm_61.
- Bit-for-bit equivalence between GPU CUDASieveMX250 and CPU SieveR1_TSpace across exponents and window shapes.
- Config schema validation for laptop profiles.
- Resumability and checkpoint recovery.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from src.phase4.laptop_accel.hardware_probe import probe_laptop_environment, get_cpu_info, get_memory_info, get_gpu_info, get_power_info
from src.phase4.laptop_accel.safety_monitor import LaptopSafetyMonitor
from src.phase4.laptop_accel.cuda_driver import CUDADriverManager
from src.phase4.laptop_accel.cuda_sieve import CUDASieveMX250
from src.phase4.t_sieve import SieveR1_TSpace
from src.phase4.config import Phase4Config
from src.phase4.storage import Phase4Storage

def test_hardware_probe():
    env = probe_laptop_environment()
    assert "cpu" in env and "memory" in env and "disk" in env and "gpu" in env
    assert env["cpu"]["logical_cpus"] >= 4
    assert env["memory"]["total_ram_gb"] > 4.0
    assert "C:" in env["disk"]
    assert env["power"]["ac_status"] in ("ONLINE (Plugged In)", "OFFLINE (Battery)", "UNKNOWN")

def test_safety_monitor_thresholds():
    monitor = LaptopSafetyMonitor(
        require_ac_power=False,
        min_available_ram_gb=1.0,
        min_free_disk_gb=5.0
    )
    safe, messages, snapshot = monitor.check_safety()
    assert isinstance(safe, bool)
    assert isinstance(messages, list)
    assert "memory" in snapshot

    # Conservative worker recommendation on 15W TDP processor
    rec = monitor.recommend_safe_worker_count(requested=8)
    assert rec <= 3, f"Recommended workers on 15W package must not exceed 3, got {rec}"

def test_cuda_driver_availability():
    driver = CUDADriverManager.get_instance()
    if not driver.is_available:
        pytest.skip("NVIDIA GPU driver not available on this host.")

    assert "MX250" in driver.device_name or "GeForce" in driver.device_name or "NVIDIA" in driver.device_name
    major, minor = driver.compute_capability
    assert major >= 6, f"Expected compute capability >= 6.0, got {major}.{minor}"

def test_cuda_sieve_bit_exact_against_cpu_r1():
    driver = CUDADriverManager.get_instance()
    if not driver.is_available:
        pytest.skip("NVIDIA CUDA driver unavailable.")

    n = 3328
    sieve_depth = 30_000
    k_start = 3
    k_end = 60_003

    cpu_sieve = SieveR1_TSpace(n, sieve_depth)
    cpu_survivors = cpu_sieve.sieve_window(k_start, k_end)

    gpu_sieve = CUDASieveMX250(n, sieve_depth, cross_check_cpu=True)
    gpu_survivors = gpu_sieve.sieve_window(k_start, k_end)
    gpu_sieve.close()

    assert gpu_survivors == cpu_survivors, f"GPU survivors ({len(gpu_survivors)}) != CPU survivors ({len(cpu_survivors)})"
    assert len(gpu_survivors) > 0

@pytest.mark.parametrize("n", [4992, 6656, 8192])
def test_cuda_sieve_various_exponents(n):
    driver = CUDADriverManager.get_instance()
    if not driver.is_available:
        pytest.skip("NVIDIA CUDA driver unavailable.")

    sieve_depth = 20_000
    k_start = 3
    k_end = 30_003

    cpu_sieve = SieveR1_TSpace(n, sieve_depth)
    cpu_survivors = cpu_sieve.sieve_window(k_start, k_end)

    gpu_sieve = CUDASieveMX250(n, sieve_depth, cross_check_cpu=False)
    gpu_survivors = gpu_sieve.sieve_window(k_start, k_end)
    gpu_sieve.close()

    assert gpu_survivors == cpu_survivors

def test_cuda_sieve_misaligned_boundaries():
    driver = CUDADriverManager.get_instance()
    if not driver.is_available:
        pytest.skip("NVIDIA CUDA driver unavailable.")

    n = 3328
    sieve_depth = 10_000
    gpu_sieve = CUDASieveMX250(n, sieve_depth, cross_check_cpu=False)

    # Even boundary start
    w_even = gpu_sieve.sieve_window(4, 1000)
    # Odd non-3 start
    w_non3 = gpu_sieve.sieve_window(5, 1000)
    # Valid k=6t+3 start
    w_valid = gpu_sieve.sieve_window(9, 1000)
    gpu_sieve.close()

    assert w_even == w_valid
    assert w_non3 == w_valid

def test_laptop_profile_config_parsing():
    cfg_path = Path("configs/laptop_i5_10210u_mx250.json")
    assert cfg_path.exists()

    cfg = Phase4Config.from_file(cfg_path)
    assert cfg.campaign_id == "laptop_2k_exploration"
    assert cfg.workers == 3
    assert cfg.sieve_strategy == "r3_gpu_mx250"
    assert 6656 in cfg.exponents
    assert cfg.sieve_depth == 50_000
    assert cfg.laptop_profile is not None

def test_storage_task_claiming_and_crash_recovery():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_recovery.sqlite"
        storage = Phase4Storage(db_path)

        storage.register_campaign("test_camp", "0"*64, "head", {})
        storage.register_tasks_batch([
            ("task_01", "test_camp", 6656, 3, 120003),
        ])

        # Worker 1 claims task_01 with 1s lease
        t1 = storage.claim_task("test_camp", worker_id="w1", pid=123, lease_duration_sec=1.0)
        assert t1 is not None and t1["task_id"] == "task_01"

        # Worker 2 tries to claim while lease active -> should find nothing
        t_none = storage.claim_task("test_camp", worker_id="w2", pid=456, lease_duration_sec=60.0)
        assert t_none is None, "Active leased task must not be claimed by another worker"

        # Wait for 1s lease to expire (second-resolution timestamp boundary)
        import time
        time.sleep(2.1)

        # Worker 2 should now reclaim the expired task_01
        t2 = storage.claim_task("test_camp", worker_id="w2", pid=456, lease_duration_sec=60.0)
        assert t2 is not None and t2["task_id"] == "task_01", "Expired leased task must be recovered idempotently"
