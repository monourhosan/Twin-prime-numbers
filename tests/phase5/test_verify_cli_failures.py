"""
Regression tests for Phase 5 Independent Verifier CLI and Mutation Rejection (P0-C, P1-G).
Verifies:
- Verify on empty directory returns nonzero exit code (exit code 2).
- Verify on missing file returns nonzero exit code (exit code 1).
- Mutations to witness, arithmetic parameters, or (B-A) are strictly rejected.
"""

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from scripts.phase5_independent_verify import verify_file, verify_certificate_v5_payload

def test_verify_empty_directory_nonzero_exit():
    """Scenario 8: verify on an empty directory returns nonzero exit code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        res = subprocess.run(
            [sys.executable, "scripts/phase5_independent_verify.py", tmpdir],
            capture_output=True,
            text=True
        )
        assert res.returncode == 2
        assert "No certificate files" in res.stderr

def test_verify_missing_file_nonzero_exit():
    """Scenario 9: verify on a missing file returns nonzero exit code."""
    res = subprocess.run(
        [sys.executable, "scripts/phase5_independent_verify.py", "nonexistent_cert.json"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
    assert "does not exist" in res.stderr

def test_mutation_gap_tampered_fails():
    """Scenario 10a: B - A != 2 is strictly rejected."""
    base_cert = Path("proofs/phase5/cert_scca_smoke_p2e3_p3e4_p5e2_p7e1_t4_6d.json")
    with open(base_cert) as f:
        data = json.load(f)
        
    mutated = copy.deepcopy(data)
    mutated["upper_decimal"] = str(int(mutated["upper_decimal"]) + 2) # Gap becomes 4
    
    is_valid, errors, _ = verify_certificate_v5_payload(mutated)
    assert not is_valid
    assert any("Gap is not 2" in e for e in errors)

def test_mutation_lower_morrison_parameter_tampered_fails():
    """Scenario 10b: Tampered Morrison parameter P is rejected."""
    base_cert = Path("proofs/phase5/cert_scca_smoke_p2e3_p3e4_p5e2_p7e1_t4_6d.json")
    with open(base_cert) as f:
        data = json.load(f)
        
    mutated = copy.deepcopy(data)
    # Tamper with parameter P
    mutated["primality_proofs"]["lower"]["parameter_P"] = 5 # Changed P
    
    is_valid, errors, _ = verify_certificate_v5_payload(mutated)
    assert not is_valid
    assert any("Morrison" in e for e in errors)

def test_mutation_upper_pocklington_witness_tampered_fails():
    """Scenario 10c: Tampered Pocklington witness base a is rejected."""
    base_cert = Path("proofs/phase5/cert_scca_smoke_p2e3_p3e4_p5e2_p7e1_t4_6d.json")
    with open(base_cert) as f:
        data = json.load(f)
        
    mutated = copy.deepcopy(data)
    # Set invalid witness a = 1
    mutated["primality_proofs"]["upper"]["witness_base_a"] = 1
    
    is_valid, errors, _ = verify_certificate_v5_payload(mutated)
    assert not is_valid
    assert any("Invalid witness base" in e for e in errors)

def test_mutation_smooth_center_parameter_t_tampered_fails():
    """Scenario 10d: Tampered parameter t causing reconstructed mismatch is rejected."""
    base_cert = Path("proofs/phase5/cert_scca_smoke_p2e3_p3e4_p5e2_p7e1_t4_6d.json")
    with open(base_cert) as f:
        data = json.load(f)
        
    mutated = copy.deepcopy(data)
    mutated["parameters"]["t"] = "5" # Was 4
    
    is_valid, errors, _ = verify_certificate_v5_payload(mutated)
    assert not is_valid
    assert any("mismatch" in e for e in errors)
