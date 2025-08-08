#!/bin/bash
# Test Development Environment
set -e

echo "🧪 Testing Development Environment..."
echo "===================================="

cd "$(dirname "$0")"

# Function to test URL
test_url() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
        if [ "$response" = "$expected_status" ]; then
            echo "✅ OK ($response)"
            return 0
        else
            echo "❌ FAILED ($response)"
            return 1
        fi
    else
        echo "⚠️  SKIPPED (curl not available)"
        return 0
    fi
}

# Function to test port
test_port() {
    local name=$1
    local port=$2
    
    echo -n "Testing $name port $port... "
    
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$port" 2>/dev/null; then
            echo "✅ LISTENING"
            return 0
        else
            echo "❌ NOT LISTENING"
            return 1
        fi
    elif command -v telnet >/dev/null 2>&1; then
        if timeout 2 telnet localhost "$port" </dev/null >/dev/null 2>&1; then
            echo "✅ LISTENING"
            return 0
        else
            echo "❌ NOT LISTENING"
            return 1
        fi
    else
        echo "⚠️  SKIPPED (nc/telnet not available)"
        return 0
    fi
}

# Check if development environment is running
echo "📊 Checking container status..."
docker compose -f docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Testing ports..."
test_port "Dashboard" 5550
test_port "Tracker (PWA)" 5555
test_port "Cruise Check" 5551
test_port "Clan Map" 5552
test_port "QSL Creator" 5553
test_port "Database" 5433

echo ""
echo "🌐 Testing HTTP endpoints..."
test_url "Dashboard" "http://localhost:5550"
test_url "Dashboard Health" "http://localhost:5550/api/health"
test_url "Dashboard API Apps" "http://localhost:5550/api/apps"
test_url "Dashboard API System" "http://localhost:5550/api/system"
test_url "Tracker (PWA)" "http://localhost:5555"
test_url "Tracker (PWA) Health" "http://localhost:5555/health"

echo ""
echo "📋 Development URLs (if services are running):"
echo "  Dashboard:      http://localhost:5550"
echo "  Tracker (PWA):  http://localhost:5555"
echo "  Cruise Check:   http://localhost:5551"
echo "  Clan Map:       http://localhost:5552"
echo "  QSL Creator:    http://localhost:5553"
echo ""
echo "🔧 If any tests failed, try:"
echo "  ./start-dev.sh          # Start development environment"
echo "  docker compose -f docker-compose.dev.yml logs [service]  # Check logs"
echo ""
echo "✅ Test completed!"
