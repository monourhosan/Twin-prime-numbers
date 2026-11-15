"""
PAQCS Standalone Verification Script (Phase 8).
Wrapper around scripts/phase8_paqcs_independent_verify.py.
"""
import sys
from pathlib import Path

# Add repo root to sys.path
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from scripts.phase8_paqcs_independent_verify import main

if __name__ == "__main__":
    main()
