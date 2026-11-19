"""Feature 15: Twin-Prime Pair Discovery.

Verifies:
1. Exact twin prime difference B - A = 2 for discovered pairs.
2. Both members are odd integers strictly greater than 3.
3. Complete provenance and execution parameters are recorded.
4. Exact parameter reconstruction reproduces candidate coordinates.
5. Proof certificate generation produces valid canonical SHA-256.
"""

from pathlib import Path
import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import compute_primorial_anchor, compute_manifold
from tests.phase11_e2e.contracts.schemas import compute_canonical_sha256, validate_certificate_schema


@pytest.fixture
def discovery_cert() -> dict:
    """Generates a reference discovery certificate for testing."""
    return Phase11ContractAdapter.prove_pair(y=3, t=21, run_id="discovery_feat15")


@pytest.mark.phase11_tier1
def test_f15_twin_gap_exact_two(discovery_cert: dict) -> None:
    """Verifies that the discovered pair has exact difference B - A = 2."""
    A = int(discovery_cert["lower_prime"])
    B = int(discovery_cert["upper_prime"])
    assert B - A == 2
    assert int(discovery_cert["difference"]) == 2


@pytest.mark.phase11_tier1
def test_f15_both_members_odd_primes_above_3(discovery_cert: dict) -> None:
    """Verifies both candidate members are odd and strictly greater than 3."""
    A = int(discovery_cert["lower_prime"])
    B = int(discovery_cert["upper_prime"])
    assert A > 3
    assert B > 3
    assert A % 2 == 1
    assert B % 2 == 1


@pytest.mark.phase11_tier1
def test_f15_complete_provenance_recorded(discovery_cert: dict) -> None:
    """Verifies discovery record contains complete provenance metadata."""
    assert discovery_cert["method_id"] == "OPQM_CRT_HYBRID_11"
    assert discovery_cert["run_id"] == "discovery_feat15"
    assert "timestamp_utc" in discovery_cert
    assert "hardware" in discovery_cert
    assert "parameters" in discovery_cert
    params = discovery_cert["parameters"]
    assert "y" in params and "t" in params and "x" in params


@pytest.mark.phase11_tier1
def test_f15_exact_parameter_reconstruction(discovery_cert: dict) -> None:
    """Verifies coordinates are reconstructed exactly from anchor y and multiplier t."""
    params = discovery_cert["parameters"]
    y = int(params["y"])
    t = int(params["t"])

    Sy, _ = compute_primorial_anchor(y)
    x = Sy * t
    assert int(params["x"]) == x

    C, A, B = compute_manifold(x)
    assert int(discovery_cert["lower_prime"]) == A
    assert int(discovery_cert["upper_prime"]) == B


@pytest.mark.phase11_tier1
def test_f15_discovery_certificate_generation_and_hash(discovery_cert: dict) -> None:
    """Verifies canonical SHA-256 hash matches the certificate payload."""
    is_valid, errors = validate_certificate_schema(discovery_cert, verify_hash=True)
    assert is_valid, f"Certificate validation failed: {errors}"
    expected_hash = compute_canonical_sha256(discovery_cert)
    assert discovery_cert["certificate_sha256"] == expected_hash
