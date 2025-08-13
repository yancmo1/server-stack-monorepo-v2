#!/usr/bin/env bash
set -euo pipefail

# cruise_all.sh: Run all major cruise dev actions in sequence
# Usage: ./scripts/cruise_all.sh [--no-rebuild]
# By default, rebuilds image, starts service, runs check, summary, and tails logs.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRUISE_DEV="$SCRIPT_DIR/cruise_dev.sh"

NO_REBUILD=0
if [[ "${1:-}" == "--no-rebuild" ]]; then
  NO_REBUILD=1
fi

if [[ $NO_REBUILD -eq 0 ]]; then
  echo "[cruise_all] Rebuilding image and starting service..."
  "$CRUISE_DEV" rebuild
else
  echo "[cruise_all] Starting service without rebuild..."
  "$CRUISE_DEV" up
fi

echo "[cruise_all] Running one-off price check..."
"$CRUISE_DEV" check

echo "[cruise_all] Running 7-day summary..."
"$CRUISE_DEV" summary

echo "[cruise_all] Tailing logs (Ctrl+C to exit)..."
"$CRUISE_DEV" logs
