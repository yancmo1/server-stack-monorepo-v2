#!/bin/bash

echo "🧪 Starting COC Discord Bot in Development Mode..."

# Check for test mode
if [ "$1" = "--test" ]; then
    echo "🧪 Running in test mode (no Docker operations)"
    TEST_MODE=true
else
    TEST_MODE=false
fi

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Create development environment flag
touch .development

# Remove production flag if it exists
rm -f .production

echo "🔍 Environment: Development"
echo "🔍 Current directory: $(pwd)"



# Load environment variables from ~/config/.env for Docker Compose
if [ -f "$HOME/config/.env" ]; then
    set -a
    source "$HOME/config/.env"
    set +a
    echo "[INFO] Loaded environment variables from $HOME/config/.env (global config)"
else
    echo "[WARNING] $HOME/config/.env file not found."
fi

if [ "$TEST_MODE" = "false" ]; then
    echo "🐳 Starting Docker containers for development..."

    # Stop any existing containers
    docker compose down

    # Start development environment
    docker compose up -d --build

    echo "🎯 Waiting for containers to start..."
    sleep 10

    echo "📊 Container Status:"
    docker compose ps

    echo "📝 Bot Logs:"
    docker compose logs coc-discord-bot --tail=20

    echo "✅ Development environment started!"
    echo "🔍 To view logs: docker compose logs -f coc-discord-bot"
    echo "🛑 To stop: docker compose down"
else
    echo "✅ Test mode completed successfully"
fi