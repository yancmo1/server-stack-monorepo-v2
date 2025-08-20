#!/bin/bash
# Fix login issue - Start database service
echo "🔧 Fixing 5K Tracker login issue..."
echo "   Issue: Database service not running"
echo ""

cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "   Please start Docker Desktop first"
    exit 1
fi

# Start database service
echo "🚀 Starting database service..."
docker compose -f docker-compose.dev.yml up -d db

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check status
echo "📊 Current services:"
docker compose -f docker-compose.dev.yml ps

echo ""
echo "✅ Database service started!"
echo "🌐 You can now log in to: http://localhost:5555"
echo ""
echo "🔑 Default login credentials:"
echo "   Email: admin@example.com"
echo "   Password: test123"