"""
Laptop Hardware and Safety Environment Probe for Intel i5-10210U + NVIDIA GeForce MX250.
Collects OS, CPU, RAM, Disk, AC Power, GPU, CUDA Driver API, and Multiprecision libraries.
"""

import os
import sys
import shutil
import platform
import subprocess
import ctypes
from ctypes import wintypes
from typing import Dict, Any, Optional

def get_cpu_info() -> Dict[str, Any]:
    logical_cpus = os.cpu_count() or 1
    # Try to query CPU name via Windows registry or wmic / powershell
    cpu_name = platform.processor() or "Unknown x86_64"
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            cpu_name = res.stdout.strip()
    except Exception:
        pass

    # Physical cores
    physical_cores = max(1, logical_cpus // 2) if "Intel" in cpu_name else logical_cpus
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).NumberOfCores"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip().isdigit():
            physical_cores = int(res.stdout.strip())
    except Exception:
        pass

    return {
        "model": cpu_name,
        "physical_cores": physical_cores,
        "logical_cpus": logical_cpus,
        "architecture": platform.machine()
    }

def get_memory_info() -> Dict[str, Any]:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ('dwLength', wintypes.DWORD),
            ('dwMemoryLoad', wintypes.DWORD),
            ('ullTotalPhys', ctypes.c_uint64),
            ('ullAvailPhys', ctypes.c_uint64),
            ('ullTotalPageFile', ctypes.c_uint64),
            ('ullAvailPageFile', ctypes.c_uint64),
            ('ullTotalVirtual', ctypes.c_uint64),
            ('ullAvailVirtual', ctypes.c_uint64),
            ('ullAvailExtendedVirtual', ctypes.c_uint64),
        ]
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            gb = 1024 ** 3
            return {
                "total_ram_gb": round(stat.ullTotalPhys / gb, 2),
                "avail_ram_gb": round(stat.ullAvailPhys / gb, 2),
                "load_percent": stat.dwMemoryLoad,
                "total_pagefile_gb": round(stat.ullTotalPageFile / gb, 2),
                "avail_pagefile_gb": round(stat.ullAvailPageFile / gb, 2),
            }
    except Exception:
        pass
    return {"total_ram_gb": 0.0, "avail_ram_gb": 0.0, "load_percent": 0}

def get_disk_info() -> Dict[str, Any]:
    disks = {}
    for d in ("C:\\", "D:\\"):
        try:
            usage = shutil.disk_usage(d)
            gb = 1024 ** 3
            disks[d[:2]] = {
                "total_gb": round(usage.total / gb, 2),
                "free_gb": round(usage.free / gb, 2),
                "used_gb": round(usage.used / gb, 2)
            }
        except Exception:
            pass
    return disks

def get_power_info() -> Dict[str, Any]:
    class SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [
            ('ACLineStatus', wintypes.BYTE),
            ('BatteryFlag', wintypes.BYTE),
            ('BatteryLifePercent', wintypes.BYTE),
            ('SystemStatusFlag', wintypes.BYTE),
            ('BatteryLifeTime', wintypes.DWORD),
            ('BatteryFullLifeTime', wintypes.DWORD),
        ]
    try:
        sps = SYSTEM_POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
            ac_map = {0: "OFFLINE (Battery)", 1: "ONLINE (Plugged In)", 255: "UNKNOWN"}
            return {
                "ac_status": ac_map.get(sps.ACLineStatus, "UNKNOWN"),
                "is_ac_online": sps.ACLineStatus == 1,
                "battery_percent": sps.BatteryLifePercent if sps.BatteryLifePercent != 255 else None,
                "raw_ac_code": sps.ACLineStatus
            }
    except Exception:
        pass
    return {"ac_status": "UNKNOWN", "is_ac_online": True, "battery_percent": None, "raw_ac_code": 255}

def get_gpu_info() -> Dict[str, Any]:
    gpu_info = {
        "present": False,
        "name": None,
        "driver_version": None,
        "cuda_version_supported": None,
        "temp_c": None,
        "util_gpu_percent": None,
        "util_mem_percent": None,
        "vram_total_mb": None,
        "vram_free_mb": None,
        "vram_used_mb": None,
        "driver_api_available": False,
        "compute_capability": None
    }

    # Query via nvidia-smi
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=name,driver_version,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used",
            "--format=csv,noheader,nounits"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            if len(parts) >= 8:
                gpu_info["present"] = True
                gpu_info["name"] = parts[0]
                gpu_info["driver_version"] = parts[1]
                gpu_info["temp_c"] = int(parts[2]) if parts[2].isdigit() else None
                gpu_info["util_gpu_percent"] = int(parts[3]) if parts[3].isdigit() else None
                gpu_info["util_mem_percent"] = int(parts[4]) if parts[4].isdigit() else None
                gpu_info["vram_total_mb"] = float(parts[5]) if parts[5].replace('.', '').isdigit() else None
                gpu_info["vram_free_mb"] = float(parts[6]) if parts[6].replace('.', '').isdigit() else None
                gpu_info["vram_used_mb"] = float(parts[7]) if parts[7].replace('.', '').isdigit() else None
    except Exception:
        pass

    # Check CUDA Driver API directly
    try:
        cuda = ctypes.WinDLL("nvcuda.dll")
        if cuda.cuInit(0) == 0:
            gpu_info["driver_api_available"] = True
            dev = ctypes.c_int()
            if cuda.cuDeviceGet(ctypes.byref(dev), 0) == 0:
                major = ctypes.c_int()
                minor = ctypes.c_int()
                cuda.cuDeviceComputeCapability(ctypes.byref(major), ctypes.byref(minor), dev.value)
                gpu_info["compute_capability"] = f"{major.value}.{minor.value}"
    except Exception:
        pass

    return gpu_info

def get_software_env() -> Dict[str, Any]:
    env = {
        "python_version": sys.version.split()[0],
        "os_name": platform.system(),
        "os_version": platform.version(),
        "has_gmpy2": False,
        "gmpy2_version": None,
        "numpy_version": None,
        "scipy_version": None,
        "sympy_version": None,
        "pytest_version": None,
        "msvc_cl_path": None
    }
    try:
        import gmpy2
        env["has_gmpy2"] = True
        env["gmpy2_version"] = getattr(gmpy2, "__version__", "installed")
    except ImportError:
        pass

    try:
        import numpy
        env["numpy_version"] = numpy.__version__
    except ImportError:
        pass

    try:
        import scipy
        env["scipy_version"] = scipy.__version__
    except ImportError:
        pass

    try:
        import sympy
        env["sympy_version"] = sympy.__version__
    except ImportError:
        pass

    try:
        import pytest
        env["pytest_version"] = pytest.__version__
    except ImportError:
        pass

    # Find MSVC cl.exe
    default_cl = r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.52.37025\bin\Hostx64\x64\cl.exe"
    if os.path.exists(default_cl):
        env["msvc_cl_path"] = default_cl
    else:
        cl_found = shutil.which("cl.exe")
        if cl_found:
            env["msvc_cl_path"] = cl_found

    return env

def probe_laptop_environment() -> Dict[str, Any]:
    """Aggregates comprehensive hardware and environment metrics."""
    return {
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "power": get_power_info(),
        "gpu": get_gpu_info(),
        "software": get_software_env()
    }
