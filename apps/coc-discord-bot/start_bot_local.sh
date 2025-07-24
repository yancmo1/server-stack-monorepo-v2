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

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Creating from template..."
    cat > .env.template << 'EOF'
DISCORD_BOT_TOKEN=your_dev_token_here
SUPERCELL_API_TOKEN=your_dev_api_token_here
CLAN_TAG=#PCRV2R2P
DISCORD_GUILD_ID=403910977302822913
ADMIN_DISCORD_ID=987654321098765432
POSTGRES_DB=devdb
POSTGRES_USER=devuser
POSTGRES_PASSWORD=devpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EOF
    cp .env.template .env
    echo "🔧 Please edit .env file with your development credentials"
else
    # Create template file even if .env exists (for reference)
    if [ ! -f .env.template ]; then
        cat > .env.template << 'EOF'
DISCORD_BOT_TOKEN=your_dev_token_here
SUPERCELL_API_TOKEN=your_dev_api_token_here
CLAN_TAG=#PCRV2R2P
DISCORD_GUILD_ID=403910977302822913
ADMIN_DISCORD_ID=987654321098765432
POSTGRES_DB=devdb
POSTGRES_USER=devuser
POSTGRES_PASSWORD=devpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EOF
        echo "📝 .env.template created for reference"
    fi
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