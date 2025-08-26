#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
QSL_V2_DIR="$ROOT_DIR/qsl-auto-v2"

echo "==> Stopping qsl-auto-v2 compose services"
cd "$QSL_V2_DIR"
docker compose down

echo "✅ Stopped connector stack. If the GUI was started in a foreground terminal, stop it with Ctrl-C."
