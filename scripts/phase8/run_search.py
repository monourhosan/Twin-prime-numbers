"""
PAQCS Search Campaign Runner (Phase 8).
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from src.phase8.paqcs_cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(["search", "--config", "configs/phase8/paqcs_primary_1511d.json"])
    main()
