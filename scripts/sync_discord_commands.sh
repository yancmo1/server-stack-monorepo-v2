#!/bin/bash

# Discord Bot Command Sync Script
# This script manually syncs Discord slash commands on the production server

set -e

echo "🔄 Discord Bot Command Sync"
echo "=========================="

# Check if we can reach the server
echo "📡 Connecting to server..."
if ! ssh -o ConnectTimeout=10 yancmo@ubuntumac "echo 'Connection test successful'" > /dev/null 2>&1; then
    echo "❌ Failed to connect to server"
    exit 1
fi

# Check if the bot container is running
echo "🐳 Checking bot container status..."
CONTAINER_STATUS=$(ssh yancmo@ubuntumac "docker ps --filter 'name=deploy-coc-discord-bot-1' --format '{{.Status}}'" 2>/dev/null || echo "not found")

if [[ "$CONTAINER_STATUS" == "not found" ]] || [[ "$CONTAINER_STATUS" == "" ]]; then
    echo "❌ Bot container is not running"
    echo "💡 Try running: ./deploy/deploy.sh bot"
    exit 1
fi

echo "✅ Bot container is running: $CONTAINER_STATUS"

# Execute command sync in the container
echo "🔄 Syncing Discord commands..."
echo "⏳ Using guild-only sync to avoid rate limits..."

# Run the sync command with gtimeout (if available) or fallback to regular ssh
if command -v gtimeout >/dev/null 2>&1; then
    # Use gtimeout on macOS (install with: brew install coreutils)
    if gtimeout 60 ssh yancmo@ubuntumac "docker exec deploy-coc-discord-bot-1 python bot.py --sync-commands" 2>&1; then
        echo "✅ Discord commands synced successfully!"
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo "⚠️  Command sync timed out after 60 seconds"
            echo "💡 This might still have worked - check Discord for new commands"
        else
            echo "❌ Command sync failed with exit code: $exit_code"
            echo "💡 Check bot logs: ssh yancmo@ubuntumac 'docker logs deploy-coc-discord-bot-1 --tail 20'"
            exit 1
        fi
    fi
elif command -v timeout >/dev/null 2>&1; then
    # Use timeout on Linux
    if timeout 60 ssh yancmo@ubuntumac "docker exec deploy-coc-discord-bot-1 python bot.py --sync-commands" 2>&1; then
        echo "✅ Discord commands synced successfully!"
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo "⚠️  Command sync timed out after 60 seconds"
            echo "💡 This might still have worked - check Discord for new commands"
        else
            echo "❌ Command sync failed with exit code: $exit_code"
            echo "💡 Check bot logs: ssh yancmo@ubuntumac 'docker logs deploy-coc-discord-bot-1 --tail 20'"
            exit 1
        fi
    fi
else
    # No timeout available - run without timeout
    echo "⚠️  No timeout command available - running without timeout"
    if ssh yancmo@ubuntumac "docker exec deploy-coc-discord-bot-1 python bot.py --sync-commands" 2>&1; then
        echo "✅ Discord commands synced successfully!"
    else
        echo "❌ Command sync failed"
        echo "💡 Check bot logs: ssh yancmo@ubuntumac 'docker logs deploy-coc-discord-bot-1 --tail 20'"
        exit 1
    fi
fi

echo ""
echo "📝 Commands should now be available in Discord:"
echo "   • /test_cwl_notification"
echo "   • /sync_cwl_commands"
echo ""
echo "💡 It may take 1-2 minutes for commands to appear in Discord"
