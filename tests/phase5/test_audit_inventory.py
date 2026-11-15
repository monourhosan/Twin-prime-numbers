"""
Regression tests for Audit Inventory and Historical Proof Immutability (P1-E, Rule 1).
Verifies:
- All published historical certificates have unchanged bytewise SHA-256 hashes.
- Audit reports unsupported formats and malformed artifacts without printing blanket PASS.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from src.phase5.cli import run_audit

def test_historical_certificate_bytes_unchanged():
    """Scenario 20: Published historical certificate hashes are identical to baseline inventory."""
    inv_file = Path("research/phase5_integrity/HISTORICAL_CERTIFICATE_INVENTORY.json")
    assert inv_file.exists(), "Baseline inventory must exist"
    
    with open(inv_file, "r", encoding="utf-8") as f:
        inventory = json.load(f)
        
    for item in inventory:
        p = Path(item["path"])
        assert p.exists(), f"Historical artifact missing: {p}"
        content = p.read_bytes()
        actual_sha = hashlib.sha256(content).hexdigest()
        assert actual_sha == item["sha256"], f"Historical artifact modified! {p}"

def test_audit_unsupported_format_and_strict_failure():
    """Scenario 19: Strict audit fails and reports when an artifact is unsupported or malformed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_repo = Path(tmpdir)
        p5_dir = tmp_repo / "proofs" / "phase5"
        p5_dir.mkdir(parents=True)
        
        # Write a malformed certificate
        bad_cert = p5_dir / "cert_malformed.json"
        with open(bad_cert, "w") as f:
            f.write("{invalid_json: true")
            
        class Args:
            repo = str(tmp_repo)
            strict = True
            report = str(tmp_repo / "report.json")
            
        with pytest.raises(SystemExit) as exc:
            run_audit(Args())
        assert exc.value.code == 1
        
        # Check generated report
        with open(Args.report) as rf:
            rep = json.load(rf)
            assert rep["summary"]["failed"] > 0
