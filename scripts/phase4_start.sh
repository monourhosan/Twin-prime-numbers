#!/usr/bin/env bash
# Phase 4 ADRS-4 Start Launcher for Unix / macOS
set -euo pipefail

CONFIG="${1:-configs/phase4/target_1000.json}"
WORKERS="${2:-1}"

echo "=== Starting Phase 4 ADRS-4 Twin-Prime Search ==="
echo "Config: ${CONFIG}"
echo "Workers: ${WORKERS}"

python3 -m src.phase4 search --config "${CONFIG}" --workers "${WORKERS}"
