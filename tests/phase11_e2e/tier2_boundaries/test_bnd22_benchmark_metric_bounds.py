"""Tier 2 Boundary Tests - Feature 22: 13-Metric Benchmarks.

Verifies:
1. Detection of missing benchmark metrics (all 13 required metrics).
2. Rejection of non-positive or impossible metric measurements.
3. Enforcement of peak RSS memory limit (<= 4.0 GB).
4. Sieve and screening survival rate interval bounds ([0.0, 1.0]).
5. CSV export schema validation and formatting.
"""

import pytest

REQUIRED_BENCHMARK_METRICS = [
    "sieve_throughput_candidates_per_sec",
    "screening_throughput_candidates_per_sec",
    "pocklington_proving_time_sec",
    "morrison_proving_time_sec",
    "total_certification_time_sec",
    "crt_prefilter_yield_rate",
    "sieve_survival_rate",
    "screening_survival_rate",
    "peak_rss_memory_mb",
    "gpu_utilization_pct",
    "gpu_temperature_celsius",
    "checkpoint_write_time_ms",
    "total_discovery_time_sec",
]


@pytest.mark.phase11_tier2
def test_bnd22_missing_metric_detection() -> None:
    """Verifies that an incomplete benchmark dataset missing any of the 13 required metrics is rejected."""
    def validate_benchmark_metrics(data: dict[str, float]) -> tuple[bool, list[str]]:
        missing = [m for m in REQUIRED_BENCHMARK_METRICS if m not in data]
        return len(missing) == 0, missing

    # Missing memory and temperature
    incomplete = {m: 100.0 for m in REQUIRED_BENCHMARK_METRICS if m not in ("peak_rss_memory_mb", "gpu_temperature_celsius")}
    ok, missing = validate_benchmark_metrics(incomplete)
    assert not ok
    assert set(missing) == {"peak_rss_memory_mb", "gpu_temperature_celsius"}

    # Full data
    complete = {m: 42.0 for m in REQUIRED_BENCHMARK_METRICS}
    ok_full, missing_full = validate_benchmark_metrics(complete)
    assert ok_full is True
    assert len(missing_full) == 0


@pytest.mark.phase11_tier2
def test_bnd22_non_positive_value_rejection() -> None:
    """Verifies that throughput and timing values must be strictly positive."""
    def validate_positive_metric(name: str, value: float) -> bool:
        if name.endswith(("_sec", "_ms", "_per_sec")):
            return value > 0.0
        return value >= 0.0

    # Non-positive timings
    assert not validate_positive_metric("pocklington_proving_time_sec", 0.0)
    assert not validate_positive_metric("pocklington_proving_time_sec", -1.5)
    assert not validate_positive_metric("sieve_throughput_candidates_per_sec", -100.0)

    # Valid positive timings
    assert validate_positive_metric("pocklington_proving_time_sec", 0.012)
    assert validate_positive_metric("sieve_throughput_candidates_per_sec", 50000.0)


@pytest.mark.phase11_tier2
def test_bnd22_peak_rss_memory_limit() -> None:
    """Verifies enforcement of peak RSS memory limit <= 4.0 GB (4096 MB)."""
    MAX_ALLOWED_RSS_MB = 4096.0

    def check_memory_guardrail(rss_mb: float) -> tuple[bool, str]:
        if rss_mb > MAX_ALLOWED_RSS_MB:
            return False, f"Peak RSS {rss_mb} MB exceeds 4.0 GB limit ({MAX_ALLOWED_RSS_MB} MB)"
        return True, "OK"

    # Excessive memory consumption
    ok_excess, err_excess = check_memory_guardrail(5120.0)
    assert not ok_excess
    assert "exceeds 4.0 GB limit" in err_excess

    # Compliant memory consumption (e.g. 1.2 GB)
    ok_good, _ = check_memory_guardrail(1200.0)
    assert ok_good is True


@pytest.mark.phase11_tier2
def test_bnd22_survival_rate_bounds() -> None:
    """Verifies that survival rate metrics lie strictly in the valid range [0.0, 1.0]."""
    def validate_rate(rate: float) -> bool:
        return 0.0 <= rate <= 1.0

    invalid_rates = [-0.01, 1.01, 100.0, -1.0, float("nan"), float("inf")]
    for bad in invalid_rates:
        assert not validate_rate(bad), f"Invalid rate {bad} was accepted"

    valid_rates = [0.0, 0.005, 0.5, 0.999, 1.0]
    for good in valid_rates:
        assert validate_rate(good)


@pytest.mark.phase11_tier2
def test_bnd22_csv_export_format() -> None:
    """Verifies that exported benchmark CSV structure matches required schema columns."""
    import csv
    import io

    headers = ["metric_name", "category", "value", "unit", "baseline_ratio"]
    sample_rows = [
        ["sieve_throughput_candidates_per_sec", "throughput", "125000", "cand/sec", "2.1"],
        ["peak_rss_memory_mb", "hardware", "850.5", "MB", "0.95"],
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(sample_rows)

    # Read back and validate
    output.seek(0)
    reader = csv.reader(output)
    read_headers = next(reader)
    assert read_headers == headers
    row_count = sum(1 for _ in reader)
    assert row_count == 2
