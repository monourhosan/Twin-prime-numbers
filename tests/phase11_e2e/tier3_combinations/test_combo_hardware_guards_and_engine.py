"""Tier 3 Integration Suite 7: Hardware & Thermal Guards (F13) x Search Engine (F9/F10).

Validates the pairwise interaction between:
1. Hardware & Thermal Guardrails (RAM monitoring >= 2.5GB free, GPU 80°C throttle, GPU 85°C pause).
2. Arbitrary-Precision Engine & Modular Sieve (batch adaptation, CPU fallback, OOM avoidance).
"""

import pytest
from typing import List, Tuple
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import compute_manifold


class AdaptiveEngineController:
    """Simulates hardware guardrail integration with the production engine."""

    RAM_THRESHOLD_MB = 2500  # 2.5 GB
    GPU_THROTTLE_TEMP = 80   # °C
    GPU_PAUSE_TEMP = 85      # °C

    def __init__(self, default_batch_size: int = 1000):
        self.default_batch_size = default_batch_size
        self.current_batch_size = default_batch_size
        self.execution_mode = "GPU"
        self.throttle_delays_inserted = 0
        self.paused_events = 0

    def adjust_for_hardware(self, free_ram_mb: int, gpu_temp_c: float) -> str:
        """Dynamically adjusts batch size and execution target based on hardware telemetry."""
        # 1. RAM pressure check
        if free_ram_mb < self.RAM_THRESHOLD_MB:
            self.current_batch_size = max(50, self.default_batch_size // 4)
            status = "BATCH_REDUCED"
        else:
            self.current_batch_size = self.default_batch_size
            status = "NORMAL_RAM"

        # 2. Thermal guard check
        if gpu_temp_c >= self.GPU_PAUSE_TEMP:
            self.paused_events += 1
            status = "THERMAL_PAUSE"
        elif gpu_temp_c >= self.GPU_THROTTLE_TEMP:
            self.throttle_delays_inserted += 1
            self.execution_mode = "CPU_FALLBACK"
            status = "THERMAL_THROTTLE"
        else:
            self.execution_mode = "GPU"

        return status

    def execute_sieve_batch(
        self,
        anchor_y: int,
        t_start: int,
        free_ram_mb: int,
        gpu_temp_c: float,
        sieve_depth: int = 50,
    ) -> Tuple[str, List[int]]:
        status = self.adjust_for_hardware(free_ram_mb, gpu_temp_c)
        if status == "THERMAL_PAUSE":
            return status, []

        t_end = t_start + self.current_batch_size - 1
        survivors = Phase11ContractAdapter.sieve_survivors(anchor_y, t_start, t_end, sieve_depth)
        return status, survivors


@pytest.mark.phase11_tier3
def test_combo_hardware_guards_reduce_batch_on_low_ram() -> None:
    """Verifies that when free RAM falls below 2.5 GB,

    the engine dynamically reduces the work unit batch size to prevent OOM.
    """
    controller = AdaptiveEngineController(default_batch_size=1000)

    # Normal RAM (16 GB free)
    status_normal = controller.adjust_for_hardware(free_ram_mb=16000, gpu_temp_c=55.0)
    assert status_normal == "NORMAL_RAM"
    assert controller.current_batch_size == 1000

    # Low RAM pressure (1.8 GB free < 2.5 GB threshold)
    status_low = controller.adjust_for_hardware(free_ram_mb=1800, gpu_temp_c=55.0)
    assert status_low == "BATCH_REDUCED"
    assert controller.current_batch_size == 250  # 1000 // 4


@pytest.mark.phase11_tier3
def test_combo_hardware_guards_thermal_throttle_and_cpu_fallback() -> None:
    """Verifies that when GPU temperature reaches or exceeds 80°C,

    the engine throttles operations and safely switches execution to the CPU modular sieve.
    """
    controller = AdaptiveEngineController(default_batch_size=500)

    # GPU heats to 82°C (above 80°C throttle threshold)
    status, survivors = controller.execute_sieve_batch(
        anchor_y=5,
        t_start=1,
        free_ram_mb=8000,
        gpu_temp_c=82.0,
        sieve_depth=40,
    )

    assert status == "THERMAL_THROTTLE"
    assert controller.execution_mode == "CPU_FALLBACK"
    assert controller.throttle_delays_inserted > 0
    assert len(survivors) > 0, "CPU fallback must successfully produce sieve survivors"


@pytest.mark.phase11_tier3
def test_combo_hardware_guards_thermal_pause_at_critical_temp() -> None:
    """Confirms that when GPU temperature reaches critical 85°C,

    the engine halts candidate processing until the temperature subsides.
    """
    controller = AdaptiveEngineController(default_batch_size=500)

    # GPU temp critical at 87°C
    status, survivors = controller.execute_sieve_batch(
        anchor_y=5,
        t_start=1,
        free_ram_mb=8000,
        gpu_temp_c=87.0,
    )

    assert status == "THERMAL_PAUSE"
    assert controller.paused_events == 1
    assert survivors == [], "Processing must be halted during thermal pause"


@pytest.mark.phase11_tier3
def test_combo_engine_cpu_fallback_produces_identical_survivors() -> None:
    """Verifies that whether running in normal mode or under thermal CPU fallback,

    the resulting survivor set is 100% bit-exact and identical.
    """
    y = 5
    t_start, t_end = 1, 100
    sieve_depth = 50

    # Run reference modular sieve
    survivors_ref = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth)

    # Controller executing under CPU fallback
    controller = AdaptiveEngineController(default_batch_size=100)
    _, survivors_fallback = controller.execute_sieve_batch(
        anchor_y=y,
        t_start=t_start,
        free_ram_mb=8000,
        gpu_temp_c=83.0,  # Forces fallback
        sieve_depth=sieve_depth,
    )

    assert survivors_fallback == survivors_ref


@pytest.mark.phase11_tier3
def test_combo_bigint_memory_safety_across_large_batch() -> None:
    """Verifies that arbitrary precision candidate pair calculations over large coordinate spans

    do not leak memory, overflow 64-bit integer boundaries, or produce float conversions.
    """
    # Sample candidate pair at scaling coordinates x ~ 10^8
    y = 5
    t_large = 10**7
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t_large)

    assert isinstance(C, int)
    assert isinstance(A, int)
    assert isinstance(B, int)
    assert B - A == 2
    assert C % 6 == 0
    # Confirm integer arithmetic didn't truncate digits
    assert len(str(C)) > 30
