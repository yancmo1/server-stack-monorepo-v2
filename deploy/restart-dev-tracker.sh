#!/bin/bash
# Dev Tracker Restart Script - Stop, Build, and Restart the 5K Tracker PWA
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.dev.yml"
SERVICE="pwa-tracker"

echo "🔄 Dev Tracker: Stop → Build → Restart"
echo "========================================"

# Step 1: Stop the tracker service
echo "🛑 Stopping $SERVICE..."
docker compose -f "$COMPOSE_FILE" stop "$SERVICE" 2>/dev/null || echo "   (Service not running)"

# Step 2: Remove the container to ensure clean rebuild
echo "🗑️  Removing old container..."
docker compose -f "$COMPOSE_FILE" rm -f "$SERVICE" 2>/dev/null || echo "   (No container to remove)"

# Step 3: Build the tracker with no cache to ensure fresh build
echo "🏗️  Building $SERVICE (fresh build)..."
docker compose -f "$COMPOSE_FILE" build --no-cache "$SERVICE"

# Step 4: Start the tracker service
echo "🚀 Starting $SERVICE with hot reload..."
docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"

# Step 5: Wait and show status
echo "⏳ Waiting for service to start..."
sleep 5

echo "📊 Service Status:"
docker compose -f "$COMPOSE_FILE" ps "$SERVICE"

echo ""
echo "✅ Dev Tracker restarted successfully!"
echo "🌐 Tracker PWA: http://localhost:5555"
echo "🔥 Hot reload enabled - changes will auto-reload"
echo ""
echo "📋 To view logs: ./dev.sh logs pwa-tracker"