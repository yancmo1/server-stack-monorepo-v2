#!/bin/bash
# Development Environment Stop Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping Development Environment..."
echo "====================================="

# Stop and remove containers
docker compose -f docker-compose.dev.yml down

echo "🧹 Cleaning up unused Docker resources..."
docker system prune -f

echo "✅ Development environment stopped"
echo ""
echo "💡 To start again: ./start-dev.sh"
