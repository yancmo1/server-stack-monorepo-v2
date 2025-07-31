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
check_port 5554 || exit 1  # Tracker
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
echo "  Dashboard:      http://localhost:5550"
echo "  Tracker:        http://localhost:5554"
echo "  Cruise Check:   http://localhost:5551"
echo "  Clan Map:       http://localhost:5552"
echo "  QSL Creator:    http://localhost:5553"
echo "  Database:       localhost:5433"
echo ""
echo "📱 Health Check URLs:"
echo "  Tracker Health: http://localhost:5554/health"
echo ""
echo "🛠️  Management Commands:"
echo "  View logs:      docker compose -f docker-compose.dev.yml logs -f [service]"
echo "  Stop all:       docker compose -f docker-compose.dev.yml down"
echo "  Restart:        docker compose -f docker-compose.dev.yml restart [service]"
echo ""
echo "✅ Development environment is ready!"
