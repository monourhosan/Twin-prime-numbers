"""
Phase 4 Hardware Environment Profiler and Laptop Safety Guardrails.
Inspects CPU, RAM, OS, and multiprecision libraries, providing conservative
concurrency and resource budgets for laptop sustainability.
"""

import os
import sys
import platform
import multiprocessing
from typing import Dict, Any

def get_hardware_profile() -> Dict[str, Any]:
    logical_cpus = multiprocessing.cpu_count()
    profile = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "logical_cpus": logical_cpus,
        "recommended_workers": max(1, min(logical_cpus - 1, 2)),
        "has_gmpy2": False,
        "gmpy2_version": None,
        "numpy_version": None,
        "sympy_version": None
    }

    try:
        import numpy
        profile["numpy_version"] = numpy.__version__
    except ImportError:
        pass

    try:
        import sympy
        profile["sympy_version"] = sympy.__version__
    except ImportError:
        pass

    try:
        import gmpy2
        profile["has_gmpy2"] = True
        profile["gmpy2_version"] = getattr(gmpy2, "__version__", "installed")
    except ImportError:
        profile["has_gmpy2"] = False

    return profile

def get_safe_worker_count(requested: int) -> int:
    """Clamps worker count within safe hardware bounds to prevent thermal throttling or freeze."""
    try:
        from .laptop_accel.safety_monitor import LaptopSafetyMonitor
        safe_max = LaptopSafetyMonitor().recommend_safe_worker_count(requested)
        return safe_max
    except Exception:
        logical = multiprocessing.cpu_count()
        safe_max = max(1, min(logical - 1, 3))
        if requested > safe_max:
            return safe_max
        return max(1, requested)
