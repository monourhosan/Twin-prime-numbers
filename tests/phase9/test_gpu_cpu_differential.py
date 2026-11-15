"""
Differential tests between NVIDIA GeForce MX250 GPU Sieve and CPU Reference Sieve.
Verifies bit-for-bit equivalence of surviving candidate sets across multiple windows.
"""

import pytest
from src.phase9.anchor import PrimorialAnchor
from src.phase9.cpu_sieve import prepare_sieve_plan, CPUSieve
from src.phase9.gpu_sieve import GPUSieveMX250
from src.phase4.laptop_accel.cuda_driver import CUDADriverManager


@pytest.fixture(scope="module")
def sieve_setup():
    anchor = PrimorialAnchor(y=11)
    plan = prepare_sieve_plan(anchor.S_y, anchor.y, Q_bound=1000)
    cpu_sieve = CPUSieve(plan)
    gpu_sieve = GPUSieveMX250(plan, cross_check_cpu=True)
    return cpu_sieve, gpu_sieve


def test_gpu_available():
    mgr = CUDADriverManager.get_instance()
    assert mgr.is_available, "NVIDIA GPU Driver API (nvcuda.dll) is unavailable on this laptop"
    assert "MX250" in mgr.device_name or mgr.compute_capability == (6, 1)


def test_gpu_cpu_equivalence_small(sieve_setup):
    cpu_sieve, gpu_sieve = sieve_setup
    if not gpu_sieve.gpu_ready:
        pytest.skip("GPU not initialized")

    windows = [
        (1, 101),
        (103, 301),
        (501, 1501),
        (2001, 3001),
        (9999, 12001)
    ]
    for t_start, t_end in windows:
        cpu_res = cpu_sieve.sieve_segment(t_start, t_end)
        gpu_res = gpu_sieve.sieve_segment(t_start, t_end)
        assert cpu_res == gpu_res, f"GPU/CPU mismatch on [{t_start}, {t_end}]: CPU {len(cpu_res)}, GPU {len(gpu_res)}"


def test_gpu_cpu_equivalence_unaligned(sieve_setup):
    cpu_sieve, gpu_sieve = sieve_setup
    if not gpu_sieve.gpu_ready:
        pytest.skip("GPU not initialized")

    # Non-power-of-two window sizes
    windows = [
        (11, 23),
        (37, 37),
        (101, 103),
        (777, 1333),
        (5001, 7891)
    ]
    for t_start, t_end in windows:
        cpu_res = cpu_sieve.sieve_segment(t_start, t_end)
        gpu_res = gpu_sieve.sieve_segment(t_start, t_end)
        assert cpu_res == gpu_res, f"Unaligned mismatch on [{t_start}, {t_end}]"
