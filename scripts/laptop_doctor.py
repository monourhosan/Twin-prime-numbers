"""
Standalone Laptop Doctor Diagnostics Script for Intel i5-10210U + NVIDIA GeForce MX250.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
proj_root = Path(__file__).resolve().parent.parent
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

from src.phase4.laptop_accel.hardware_probe import probe_laptop_environment
from src.phase4.laptop_accel.safety_monitor import LaptopSafetyMonitor
from src.phase4.laptop_accel.cuda_driver import CUDADriverManager

def main():
    print("=" * 70)
    print("  Phase 4 Laptop Environment & Hardware Diagnostics (ADRS-4)")
    print("=" * 70)

    env = probe_laptop_environment()
    cpu = env["cpu"]
    mem = env["memory"]
    disk = env["disk"]
    pwr = env["power"]
    gpu = env["gpu"]
    sw = env["software"]

    print("\n[CPU & COMPUTE]")
    print(f"  Processor Model      : {cpu['model']}")
    print(f"  Physical Cores       : {cpu['physical_cores']}")
    print(f"  Logical Threads      : {cpu['logical_cpus']}")
    print(f"  Architecture         : {cpu['architecture']}")

    print("\n[SYSTEM MEMORY]")
    print(f"  Total Physical RAM   : {mem['total_ram_gb']:.2f} GB")
    print(f"  Available RAM        : {mem['avail_ram_gb']:.2f} GB")
    print(f"  Memory Load          : {mem['load_percent']}%")
    print(f"  Available Pagefile   : {mem.get('avail_pagefile_gb', 0):.2f} GB")

    print("\n[STORAGE]")
    for drive, d in disk.items():
        print(f"  Drive {drive}             : {d['free_gb']:.1f} GB free / {d['total_gb']:.1f} GB total ({d['used_gb']:.1f} GB used)")

    print("\n[POWER & BATTERY]")
    print(f"  AC Power Status      : {pwr['ac_status']}")
    print(f"  Battery Level        : {pwr['battery_percent']}%" if pwr['battery_percent'] is not None else "  Battery Level        : N/A")

    print("\n[NVIDIA GPU & CUDA DRIVER]")
    if gpu["present"]:
        print(f"  GPU Name             : {gpu['name']}")
        print(f"  Driver Version       : {gpu['driver_version']}")
        print(f"  Compute Capability   : {gpu.get('compute_capability', 'Unknown')} (Pascal sm_61)")
        print(f"  Total VRAM           : {gpu['vram_total_mb']} MB")
        print(f"  Free VRAM            : {gpu['vram_free_mb']} MB")
        print(f"  Used VRAM            : {gpu['vram_used_mb']} MB")
        print(f"  Temperature          : {gpu['temp_c']}°C")
        print(f"  GPU Utilization      : {gpu['util_gpu_percent']}%")
        print(f"  Memory Utilization   : {gpu['util_mem_percent']}%")
    else:
        print("  Dedicated GPU        : Not detected or offline")

    print("\n[SOFTWARE & ACCELERATION]")
    print(f"  Python Version       : {sw['python_version']} (64-bit)")
    print(f"  OS Build             : {sw['os_name']} {sw['os_version']}")
    print(f"  gmpy2 Acceleration   : {'ENABLED (v' + str(sw['gmpy2_version']) + ')' if sw['has_gmpy2'] else 'DISABLED'}")
    print(f"  NumPy Version        : {sw.get('numpy_version', 'N/A')}")
    print(f"  MSVC C++ Compiler    : {sw.get('msvc_cl_path') or 'Not Found'}")

    # Safety check
    monitor = LaptopSafetyMonitor()
    safe, messages, _ = monitor.check_safety()
    rec_workers = monitor.recommend_safe_worker_count(3)

    print("\n[SAFETY & SUSTAINABILITY VERDICT]")
    print(f"  Safety Status        : {'PASS - SAFE TO SEARCH' if safe else 'VIOLATION DETECTED'}")
    print(f"  Recommended Workers  : {rec_workers} (conservative mode on 15W TDP i5-10210U)")
    for msg in messages:
        prefix = "WARN" if "High" in msg or "pressure" in msg or "Low GPU" in msg else "CRIT"
        print(f"  [{prefix}] {msg}")
    print("=" * 70)

if __name__ == "__main__":
    main()
