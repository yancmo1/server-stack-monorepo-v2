#!/bin/bash
# Verify clan-map dev environment (mounted code, routes, map regeneration capability)
set -e
COMPOSE="docker compose -f deploy/docker-compose.dev.yml"
SERVICE=clan-map

echo "[1] Checking container running..."
$COMPOSE ps --status running | grep -q clan-map-dev || { echo "Clan-map dev container not running"; exit 1; }

echo "[2] Verifying code mount (looking for DEV_SENTINEL marker)..."
MARKER="apps/clan-map/DEV_SENTINEL.txt"
if [ ! -f "$MARKER" ]; then
  echo "Creating sentinel file at $MARKER"
  touch "$MARKER"
fi
$COMPOSE exec -T $SERVICE ls -1 /app/DEV_SENTINEL.txt >/dev/null 2>&1 && echo "Mount OK" || { echo "Mount missing /app/DEV_SENTINEL.txt"; exit 1; }

echo "[3] Hitting /dev/info endpoint..."
curl -s http://localhost:5552/dev/info | python -c 'import sys,json; d=json.load(sys.stdin); print("dev/info:", d)' || echo "Could not fetch /dev/info"

echo "[4] Forcing regeneration..."
curl -s http://localhost:5552/dev/regen-map | python -c 'import sys,json; d=json.load(sys.stdin); print("regen:", d)' || echo "Could not run regen"

echo "[5] Cache-buster test..."
curl -Is http://localhost:5552/clan-map/static/folium_map.html?cb=$(date +%s) | head -n1

echo "✅ Verification sequence complete"
