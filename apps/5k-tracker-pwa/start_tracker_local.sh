#!/bin/bash
# Start 5K Tracker app and its DB for local development using Docker Compose
set -e
cd "$(dirname "$0")"

# Use the main deploy compose file, but only bring up tracker and db
COMPOSE_FILE="../../deploy/docker-compose.yml"

# Optional: check for .env
if [ ! -f ../../shared/config/.env ]; then
  echo "[DEV] WARNING: ../../shared/config/.env not found. You may need to create it."
fi

# Rebuild tracker for local changes

echo "[DEV] Building tracker image..."
docker compose -f $COMPOSE_FILE build tracker

echo "[DEV] Starting tracker and db containers (with code mount for live reload)..."
docker compose -f $COMPOSE_FILE up -d db tracker

echo "[DEV] Tracker app is running!"
echo "- App: http://localhost:5554/"
echo "- DB: internal only (db:5432)"
echo "- To stop: docker compose -f $COMPOSE_FILE down"
