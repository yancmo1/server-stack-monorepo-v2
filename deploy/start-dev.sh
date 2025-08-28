#!/bin/bash
# Development Environment Startup Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Development Environment..."
echo "=================================="

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use!"
        echo "   Kill the process with: kill -9 \$(lsof -ti:$port)"
        return 1
    fi
    return 0
}

# Check critical ports
echo "🔍 Checking ports..."
check_port 5550 || exit 1  # Dashboard
check_port 5555 || exit 1  # Tracker
check_port 5554 || exit 1  # Crumb
check_port 5433 || exit 1  # Database

echo "✅ All ports are available"

# Start services
echo "🐳 Starting Docker Compose services..."
docker compose -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker compose -f docker-compose.dev.yml ps

echo ""
echo "🎯 Development URLs:"
echo "  Dashboard:      https://dashboard.yancmo.xyz"
echo "  Tracker:        https://tracker.yancmo.xyz"
echo "  Crumb:          https://crumb.yancmo.xyz"
echo "  Cruise Check:   https://cruise.yancmo.xyz"
echo "  Clash Map:      https://clashmap.yancmo.xyz"
echo "  QSL Creator:    https://qsl.yancmo.xyz"
echo "  Database:       localhost:5433"
echo ""
echo "📱 Health Check URLs:"
echo "  Tracker Health: http://localhost:5555/health"
echo "  Crumb Health: http://localhost:5554/health"
echo ""
echo "🛠️  Management Commands:"
echo "  View logs:      docker compose -f docker-compose.dev.yml logs -f [service]"
echo "  Stop all:       docker compose -f docker-compose.dev.yml down"
echo "  Restart:        docker compose -f docker-compose.dev.yml restart [service]"
echo ""
echo "✅ Development environment is ready!"
