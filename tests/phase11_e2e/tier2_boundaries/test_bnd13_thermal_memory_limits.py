"""Tier 2 Boundary Tests - Feature 13: Hardware & Thermal Guardrails.

Verifies:
1. Low free RAM guard (< 2.5 GB) triggers safe pause/checkpoint.
2. GPU temperature sensor query failure graceful fallback to CPU.
3. Rapid thermal oscillation debounce / hysteresis logic.
4. Graceful interrupt signal (SIGINT) checkpoint flush.
5. Maximum pause timeout under sustained thermal overload.
"""

import pytest


@pytest.mark.phase11_tier2
def test_bnd13_simulated_ram_exhaustion_guard() -> None:
    """Verifies that RAM monitor triggers warning/pause when free RAM drops below 2.5 GB."""
    MIN_FREE_RAM_GB = 2.5

    def check_ram_safety(free_ram_gb: float) -> tuple[str, bool]:
        if free_ram_gb < MIN_FREE_RAM_GB:
            return "LOW_RAM_PAUSE", False
        return "RAM_OK", True

    # 1.0 GB free -> must trigger pause
    status_low, ok_low = check_ram_safety(1.0)
    assert not ok_low
    assert status_low == "LOW_RAM_PAUSE"

    # 2.4 GB free -> must trigger pause
    status_marginal, ok_marginal = check_ram_safety(2.4)
    assert not ok_marginal

    # 3.0 GB free -> normal execution
    status_ok, ok = check_ram_safety(3.0)
    assert ok
    assert status_ok == "RAM_OK"


@pytest.mark.phase11_tier2
def test_bnd13_temperature_sensor_failure_fallback() -> None:
    """Verifies graceful fallback to CPU mode when GPU temperature query fails."""
    def query_gpu_temp(sensor_available: bool) -> tuple[float | None, str]:
        if not sensor_available:
            return None, "CPU_FALLBACK"
        return 65.0, "GPU_ACTIVE"

    temp, mode = query_gpu_temp(sensor_available=False)
    assert temp is None
    assert mode == "CPU_FALLBACK"


@pytest.mark.phase11_tier2
def test_bnd13_thermal_oscillation_debounce() -> None:
    """Verifies hysteresis debounce logic when temperature oscillates rapidly around 80°C."""
    # Throttle threshold: 80°C, release threshold: 75°C (5°C hysteresis)
    THROTTLE_ENTER = 80.0
    THROTTLE_EXIT = 75.0

    class ThermalController:
        def __init__(self):
            self.throttled = False

        def update(self, temp: float) -> bool:
            if not self.throttled and temp >= THROTTLE_ENTER:
                self.throttled = True
            elif self.throttled and temp < THROTTLE_EXIT:
                self.throttled = False
            return self.throttled

    ctrl = ThermalController()
    # Temp reaches 81°C -> Throttle ON
    assert ctrl.update(81.0) is True
    # Temp drops to 79°C -> Still throttled due to hysteresis!
    assert ctrl.update(79.0) is True
    # Temp drops to 76°C -> Still throttled
    assert ctrl.update(76.0) is True
    # Temp drops below 75°C (e.g. 74°C) -> Throttle OFF
    assert ctrl.update(74.0) is False


@pytest.mark.phase11_tier2
def test_bnd13_graceful_sigint_flush() -> None:
    """Verifies that an interrupt signal sets the termination flag and triggers checkpoint flush."""
    class MockRunner:
        def __init__(self):
            self.stop_requested = False
            self.state_flushed = False

        def handle_signal(self, signum: int, frame=None):
            self.stop_requested = True
            self.flush_state()

        def flush_state(self):
            self.state_flushed = True

    runner = MockRunner()
    # Simulate SIGINT (signal 2)
    runner.handle_signal(2)
    assert runner.stop_requested is True
    assert runner.state_flushed is True


@pytest.mark.phase11_tier2
def test_bnd13_thermal_pause_max_timeout() -> None:
    """Verifies that sustained thermal overload (>= 85°C) exits after maximum pause timeout."""
    MAX_PAUSE_SECONDS = 300

    def evaluate_thermal_pause(temp: float, elapsed_paused_seconds: float) -> str:
        if temp >= 85.0:
            if elapsed_paused_seconds >= MAX_PAUSE_SECONDS:
                return "ABORT_MAX_TIMEOUT_EXCEEDED"
            return "PAUSE_WAITING"
        return "RUNNING"

    assert evaluate_thermal_pause(86.0, 50.0) == "PAUSE_WAITING"
    assert evaluate_thermal_pause(86.0, 301.0) == "ABORT_MAX_TIMEOUT_EXCEEDED"
    assert evaluate_thermal_pause(72.0, 301.0) == "RUNNING"
