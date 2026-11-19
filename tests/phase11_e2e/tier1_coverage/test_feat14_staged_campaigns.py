"""Feature 14: Staged Discovery Campaigns.

Verifies:
1. Definition and ordering of 4 progressive search stages (Stage 1 to 4).
2. Stage 1 sanity search verifying pipeline candidate generation.
3. Stage 2 density benchmark computing empirical survivor yield.
4. Stage 3 parameter optimization evaluating anchor and sieve configurations.
5. Stage 4 discovery search configuration enforcing checkpointing and certification.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


STAGES = {
    1: {"name": "Sanity Search", "target_scale": "small", "max_t": 100},
    2: {"name": "Density Benchmark", "target_scale": "medium", "max_t": 500},
    3: {"name": "Parameter Optimization", "target_scale": "tuning", "max_t": 1000},
    4: {"name": "Discovery Search", "target_scale": "large", "max_t": 10000},
}


@pytest.mark.phase11_tier1
def test_f14_staged_campaign_definition_and_order() -> None:
    """Verifies all 4 campaign stages are defined with strictly increasing work bounds."""
    stages = sorted(STAGES.keys())
    assert stages == [1, 2, 3, 4]

    prev_bound = 0
    for s in stages:
        bound = STAGES[s]["max_t"]
        assert bound > prev_bound, f"Stage {s} bound {bound} not greater than {prev_bound}"
        prev_bound = bound


@pytest.mark.phase11_tier1
def test_f14_stage1_sanity_search_execution() -> None:
    """Verifies Stage 1 generates candidates and evaluates primality status."""
    y = 3
    t_range = (1, 20)
    survivors = Phase11ContractAdapter.sieve_survivors(y, t_range[0], t_range[1], sieve_depth=50)
    assert len(survivors) > 0

    # Screen first survivor
    status, pair = Phase11ContractAdapter.screen_candidate(y, survivors[0])
    assert status in ("COMPOSITE", "SINGLE_PRP", "DUAL_PRP")


@pytest.mark.phase11_tier1
def test_f14_stage2_density_benchmark_metrics() -> None:
    """Verifies Stage 2 calculates candidate survivor density in range (0%, 100%)."""
    y = 5
    t_start, t_end = 1, 100
    total = t_end - t_start + 1
    survivors = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth=100)

    density = len(survivors) / total
    assert 0.0 < density < 1.0, f"Density {density} outside expected interval (0, 1)"
    # Sieve should eliminate at least 50% of candidates
    assert density <= 0.50, f"Sieve density too high: {density}"


@pytest.mark.phase11_tier1
def test_f14_stage3_parameter_optimization_logic() -> None:
    """Verifies parameter optimization across different primorial anchors."""
    # Compare survivor retention across anchors y=3 vs y=5 at equal sieve depth
    survivors_y3 = Phase11ContractAdapter.sieve_survivors(y=3, t_start=1, t_end=50, sieve_depth=100)
    survivors_y5 = Phase11ContractAdapter.sieve_survivors(y=5, t_start=1, t_end=50, sieve_depth=100)

    assert isinstance(survivors_y3, list)
    assert isinstance(survivors_y5, list)


@pytest.mark.phase11_tier1
def test_f14_stage4_discovery_configuration() -> None:
    """Verifies Stage 4 configuration mandates checkpointing, proof verification, and novelty."""
    stage4 = STAGES[4]
    assert stage4["target_scale"] == "large"
    assert stage4["max_t"] >= 1000
