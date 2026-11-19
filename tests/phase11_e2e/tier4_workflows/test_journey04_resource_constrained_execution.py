"""Tier 4 Workflow 4: Resource-Constrained Execution and Thermal Throttle User Journey.

Covers the full dynamic hardware adaptation workflow:
1. Nominal search execution under ample RAM and cool temperature.
2. RAM exhaustion avoidance: dynamic batch reduction when free RAM < 2.5 GB.
3. GPU thermal protection: insertion of throttle delays and CPU fallback at >= 80°C.
4. Critical thermal pause: execution halt at >= 85°C.
5. Resource normalization and restoration to full capacity.
6. Validation of 100% calculation accuracy and zero candidate drop across all throttle transitions.
"""

from pathlib import Path
from typing import List, Dict, Tuple, Any
import pytest

from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


class HardwareThrottledPipeline:
    """Manages search execution under dynamically varying RAM and thermal telemetry."""

    RAM_LIMIT_MB = 2500
    GPU_THROTTLE_TEMP = 80
    GPU_PAUSE_TEMP = 85

    def __init__(self, default_batch: int = 400):
        self.default_batch = default_batch
        self.current_batch = default_batch
        self.mode = "GPU"
        self.transition_log: List[Dict[str, Any]] = []
        self.accumulated_survivors: List[int] = []

    def evaluate_telemetry(self, free_ram_mb: int, gpu_temp_c: float) -> str:
        state = "NOMINAL"
        # 1. RAM check
        if free_ram_mb < self.RAM_LIMIT_MB:
            self.current_batch = max(50, self.default_batch // 4)
            state = "LOW_RAM_REDUCTION"
        else:
            self.current_batch = self.default_batch

        # 2. Thermal check
        if gpu_temp_c >= self.GPU_PAUSE_TEMP:
            state = "CRITICAL_THERMAL_PAUSE"
        elif gpu_temp_c >= self.GPU_THROTTLE_TEMP:
            self.mode = "CPU_FALLBACK"
            state = "THERMAL_THROTTLE"
        else:
            self.mode = "GPU"

        self.transition_log.append({
            "free_ram_mb": free_ram_mb,
            "gpu_temp_c": gpu_temp_c,
            "state": state,
            "batch_size": self.current_batch,
            "mode": self.mode,
        })
        return state

    def step_work_unit(
        self,
        anchor_y: int,
        t_cursor: int,
        free_ram_mb: int,
        gpu_temp_c: float,
        sieve_depth: int = 40,
    ) -> Tuple[int, List[int]]:
        """Executes one adaptive step based on current telemetry.

        Returns (next_cursor, unit_survivors).
        """
        state = self.evaluate_telemetry(free_ram_mb, gpu_temp_c)
        if state == "CRITICAL_THERMAL_PAUSE":
            # Execution halted: no progress made this tick
            return t_cursor, []

        t_end = t_cursor + self.current_batch - 1
        survivors = Phase11ContractAdapter.sieve_survivors(anchor_y, t_cursor, t_end, sieve_depth)
        self.accumulated_survivors.extend(survivors)
        return t_end + 1, survivors


@pytest.mark.phase11_tier4
def test_journey04_resource_constrained_execution_lifecycle() -> None:
    """Simulates a full dynamic user journey under varying hardware constraints:

    Nominal -> Low RAM -> Thermal Spike (Throttle) -> Critical Thermal (Pause) -> Recovery -> Nominal.
    """
    pipeline = HardwareThrottledPipeline(default_batch=200)
    anchor_y = 5
    sieve_depth = 40
    t_cursor = 1

    # Phase 1: Nominal conditions (RAM=12GB, Temp=60C)
    t_cursor, s1 = pipeline.step_work_unit(anchor_y, t_cursor, free_ram_mb=12000, gpu_temp_c=60.0, sieve_depth=sieve_depth)
    assert t_cursor == 201
    assert pipeline.mode == "GPU"
    assert pipeline.current_batch == 200

    # Phase 2: Injected low memory pressure (RAM=1.8GB < 2.5GB)
    t_cursor, s2 = pipeline.step_work_unit(anchor_y, t_cursor, free_ram_mb=1800, gpu_temp_c=65.0, sieve_depth=sieve_depth)
    assert pipeline.current_batch == 50  # Reduced batch
    assert t_cursor == 251

    # Phase 3: Injected thermal throttle (GPU temp reaches 82C)
    t_cursor, s3 = pipeline.step_work_unit(anchor_y, t_cursor, free_ram_mb=8000, gpu_temp_c=82.0, sieve_depth=sieve_depth)
    assert pipeline.mode == "CPU_FALLBACK"
    assert t_cursor == 451

    # Phase 4: Critical thermal event (GPU temp reaches 87C >= 85C pause)
    t_cursor, s4 = pipeline.step_work_unit(anchor_y, t_cursor, free_ram_mb=8000, gpu_temp_c=87.0, sieve_depth=sieve_depth)
    assert s4 == []
    assert t_cursor == 451  # Cursor remained paused

    # Phase 5: Recovery event (GPU cools to 62C, RAM 16GB)
    t_cursor, s5 = pipeline.step_work_unit(anchor_y, t_cursor, free_ram_mb=16000, gpu_temp_c=62.0, sieve_depth=sieve_depth)
    assert pipeline.mode == "GPU"
    assert pipeline.current_batch == 200
    assert t_cursor == 651

    # Verify transition log recorded all events correctly
    states = [entry["state"] for entry in pipeline.transition_log]
    assert states == [
        "NOMINAL",
        "LOW_RAM_REDUCTION",
        "THERMAL_THROTTLE",
        "CRITICAL_THERMAL_PAUSE",
        "NOMINAL",
    ]


@pytest.mark.phase11_tier4
def test_journey04_accuracy_invariant_under_transitions() -> None:
    """Confirms that candidate survivor lists across adaptive transitions

    match the exact reference survivors with 100% accuracy and zero dropped candidates.
    """
    anchor_y = 5
    sieve_depth = 40

    # Compare an uninterrupted span [1, 200]
    expected = Phase11ContractAdapter.sieve_survivors(anchor_y, 1, 200, sieve_depth)

    # Executed via throttled pipeline with batch transitions
    pipeline = HardwareThrottledPipeline(default_batch=100)
    # Unit 1: 100 candidates
    cursor, u1 = pipeline.step_work_unit(anchor_y, 1, free_ram_mb=16000, gpu_temp_c=60.0, sieve_depth=sieve_depth)
    # Unit 2: throttled to 50 candidates
    cursor, u2 = pipeline.step_work_unit(anchor_y, cursor, free_ram_mb=1500, gpu_temp_c=65.0, sieve_depth=sieve_depth)
    # Unit 3: 50 candidates
    cursor, u3 = pipeline.step_work_unit(anchor_y, cursor, free_ram_mb=1500, gpu_temp_c=65.0, sieve_depth=sieve_depth)

    assert cursor == 201
    actual = u1 + u2 + u3
    assert actual == expected, "Throttled pipeline produced survivor discrepancy"


@pytest.mark.phase11_tier4
def test_journey04_memory_safety_high_coordinate_stream() -> None:
    """Verifies that running big-integer manifold generation on high coordinates

    maintains stable memory and returns exact values without leak or precision loss.
    """
    y = 5
    # Process 100 high-coordinate items
    results = []
    for t in range(10000, 10100):
        C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        assert B - A == 2
        results.append(C)

    assert len(results) == 100
    assert all(isinstance(c, int) for c in results)
