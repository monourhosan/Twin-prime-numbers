"""
Standalone Strict Independent Verifier Script for Phase 2 Certificates.
Usage:
  python scripts/phase2_verify.py proofs/phase2/
  python scripts/phase2_verify.py proofs/phase2/cert_k123_n340.json
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.phase2.independent_verifier import verify_certificate_strict

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/phase2_verify.py <proof_file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_dir():
        cert_files = sorted(target.glob("*.json"))
        if not cert_files:
            print(f"No JSON certificates found in {target}")
            sys.exit(0)
        print(f"Auditing {len(cert_files)} certificates in {target}...")
        all_passed = True
        for cf in cert_files:
            passed, messages = verify_certificate_strict(cf)
            if passed:
                print(f"  [PASS] {cf.name}")
            else:
                print(f"  [FAIL] {cf.name}:")
                for err in messages:
                    print(f"     - {err}")
                all_passed = False
        if all_passed:
            print("\n[SUCCESS] All Phase 2 certificates passed strict independent audit!")
            sys.exit(0)
        else:
            print("\n[FAILURE] One or more certificates failed verification!")
            sys.exit(1)
    else:
        passed, messages = verify_certificate_strict(target)
        if passed:
            print(f"[PASS] Certificate {target.name} verified successfully:")
            for m in messages:
                print(f"  + {m}")
            sys.exit(0)
        else:
            print(f"[FAIL] Certificate {target.name} failed verification:")
            for err in messages:
                print(f"  - {err}")
            sys.exit(1)

if __name__ == "__main__":
    main()
