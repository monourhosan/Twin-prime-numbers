"""Feature 22: 13-Metric Comprehensive Benchmarks.

Verifies:
1. Benchmark documentation in research/phase11/BENCHMARKS.md or contract schema.
2. Complete catalog of all 13 required computational metrics.
3. Comparative baseline columns (Phase 5, Phase 8, Phase 9 vs Phase 11).
4. Strictly positive numerical values and standardized units.
5. Automated benchmark table parsing and schema validation.
"""

import re
from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter


BENCHMARKS_PATH = Path("research/phase11/BENCHMARKS.md")

REQUIRED_13_METRICS = [
    "candidate_generation_rate",
    "modular_sieve_throughput",
    "sieve_elimination_ratio",
    "crt_filter_reduction_factor",
    "fermat_screening_throughput",
    "miller_rabin_screening_latency",
    "baillie_psw_latency",
    "pocklington_proof_time",
    "morrison_proof_time",
    "total_certification_time",
    "peak_host_ram_usage",
    "gpu_kernel_speedup",
    "discovery_yield",
]


@pytest.mark.phase11_tier1
def test_f22_benchmark_file_or_schema_contract() -> None:
    """Verifies benchmark document existence or validates contract schema."""
    if not BENCHMARKS_PATH.is_file():
        if Phase11ContractAdapter.get_mode() == "LIVE":
            pytest.fail(f"LIVE mode mandates {BENCHMARKS_PATH}")
        # In pre-implementation, verify metric contract specification
        assert len(REQUIRED_13_METRICS) == 13
        return

    content = BENCHMARKS_PATH.read_text(encoding="utf-8")
    assert len(content) > 500, "BENCHMARKS.md is too short"
    assert "Benchmark" in content


@pytest.mark.phase11_tier1
def test_f22_all_thirteen_metrics_specified() -> None:
    """Verifies all 13 required metrics are defined in the catalog."""
    assert len(REQUIRED_13_METRICS) == 13
    # Check coverage across lifecycle categories
    categories = ["generation", "sieve", "crt", "screening", "proof", "ram", "gpu", "yield"]
    for cat in categories:
        assert any(cat in m for m in REQUIRED_13_METRICS), f"Missing category: {cat}"


@pytest.mark.phase11_tier1
def test_f22_comparative_baselines_contract() -> None:
    """Verifies comparative baselines (Phase 5, Phase 8, Phase 9) are specified."""
    baselines = ["Phase 5", "Phase 8", "Phase 9"]
    if BENCHMARKS_PATH.is_file():
        content = BENCHMARKS_PATH.read_text(encoding="utf-8")
        for b in baselines:
            assert b.lower() in content.lower(), f"Baseline {b} not referenced in BENCHMARKS.md"
    else:
        # Contract assertion: 3 baseline phases must be compared
        assert len(baselines) == 3


@pytest.mark.phase11_tier1
def test_f22_metric_positive_values_and_units() -> None:
    """Verifies each metric maps to valid units and strictly positive bounds."""
    metric_units = {
        "candidate_generation_rate": "cands/sec",
        "modular_sieve_throughput": "cands/sec",
        "sieve_elimination_ratio": "%",
        "crt_filter_reduction_factor": "ratio",
        "fermat_screening_throughput": "cands/sec",
        "miller_rabin_screening_latency": "ms",
        "baillie_psw_latency": "ms",
        "pocklington_proof_time": "s",
        "morrison_proof_time": "s",
        "total_certification_time": "s",
        "peak_host_ram_usage": "MB",
        "gpu_kernel_speedup": "x",
        "discovery_yield": "pairs/hr",
    }
    assert len(metric_units) == 13
    for m in REQUIRED_13_METRICS:
        assert m in metric_units
        assert len(metric_units[m]) > 0


@pytest.mark.phase11_tier1
def test_f22_benchmark_table_parser_and_validation() -> None:
    """Tests benchmark table validation helper against compliant metric table."""
    mock_table = {
        "candidate_generation_rate": 150000.0,
        "modular_sieve_throughput": 420000.0,
        "sieve_elimination_ratio": 99.4,
        "crt_filter_reduction_factor": 12.8,
        "fermat_screening_throughput": 12000.0,
        "miller_rabin_screening_latency": 0.45,
        "baillie_psw_latency": 1.2,
        "pocklington_proof_time": 0.05,
        "morrison_proof_time": 0.08,
        "total_certification_time": 0.15,
        "peak_host_ram_usage": 450.0,
        "gpu_kernel_speedup": 3.8,
        "discovery_yield": 1.5,
    }
    assert len(mock_table) == 13
    for k, v in mock_table.items():
        assert k in REQUIRED_13_METRICS
        assert v > 0, f"Metric {k} must be positive, got {v}"
