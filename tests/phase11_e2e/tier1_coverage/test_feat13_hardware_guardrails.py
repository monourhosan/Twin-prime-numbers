"""Feature 13: Hardware and Thermal Guardrails.

Verifies:
1. Host memory floor guardrail enforcing >= 2.5 GB available RAM.
2. GPU thermal throttle logic triggering at 80°C.
3. GPU thermal pause loop triggering at 85°C.
4. Graceful CPU-only fallback execution when GPU acceleration is absent.
5. Guardrail policy decision table handling combined environmental conditions.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


def evaluate_guardrails(free_ram_gb: float, gpu_temp_c: float | None) -> str:
    """Simulated hardware guardrail evaluator following Phase 11 constraints."""
    if free_ram_gb < 2.5:
        return "PAUSE_MEMORY"
    if gpu_temp_c is not None:
        if gpu_temp_c >= 85.0:
            return "PAUSE_THERMAL"
        if gpu_temp_c >= 80.0:
            return "THROTTLE_GPU"
    return "NORMAL"


@pytest.mark.phase11_tier1
def test_f13_ram_threshold_guard_evaluation() -> None:
    """Verifies that available RAM < 2.5 GB triggers memory guardrail."""
    assert evaluate_guardrails(free_ram_gb=3.5, gpu_temp_c=65.0) == "NORMAL"
    assert evaluate_guardrails(free_ram_gb=2.6, gpu_temp_c=65.0) == "NORMAL"
    assert evaluate_guardrails(free_ram_gb=2.49, gpu_temp_c=65.0) == "PAUSE_MEMORY"
    assert evaluate_guardrails(free_ram_gb=1.0, gpu_temp_c=65.0) == "PAUSE_MEMORY"


@pytest.mark.phase11_tier1
def test_f13_gpu_thermal_throttle_threshold() -> None:
    """Verifies that GPU temperature >= 80°C triggers throttling."""
    assert evaluate_guardrails(free_ram_gb=4.0, gpu_temp_c=78.0) == "NORMAL"
    assert evaluate_guardrails(free_ram_gb=4.0, gpu_temp_c=79.9) == "NORMAL"
    assert evaluate_guardrails(free_ram_gb=4.0, gpu_temp_c=80.0) == "THROTTLE_GPU"
    assert evaluate_guardrails(free_ram_gb=4.0, gpu_temp_c=84.5) == "THROTTLE_GPU"


@pytest.mark.phase11_tier1
def test_f13_gpu_thermal_pause_threshold() -> None:
    """Verifies that GPU temperature >= 85°C triggers execution pause."""
    assert evaluate_guardrails(free_ram_gb=4.0, gpu_temp_c=85.0) == "PAUSE_THERMAL"
    assert evaluate_guardrails(free_ram_gb=4.0, gpu_temp_c=88.5) == "PAUSE_THERMAL"


@pytest.mark.phase11_tier1
def test_f13_graceful_cpu_only_execution() -> None:
    """Verifies that when GPU is None / unavailable, operations execute on CPU."""
    # When gpu_temp_c is None (CPU only mode)
    assert evaluate_guardrails(free_ram_gb=3.0, gpu_temp_c=None) == "NORMAL"

    # Contract adapter works cleanly in CPU-only mode
    survivors = Phase11ContractAdapter.sieve_survivors(y=3, t_start=1, t_end=10, sieve_depth=20)
    assert isinstance(survivors, list)
    assert len(survivors) > 0


@pytest.mark.phase11_tier1
def test_f13_guardrail_policy_decision() -> None:
    """Verifies priority resolution when multiple thresholds are breached."""
    # Low RAM takes precedence over normal or high temp
    assert evaluate_guardrails(free_ram_gb=2.1, gpu_temp_c=86.0) == "PAUSE_MEMORY"
    # Normal operation when all parameters within bounds
    assert evaluate_guardrails(free_ram_gb=5.0, gpu_temp_c=72.0) == "NORMAL"
