#!/bin/bash
# Production Deployment Script
# Usage: ./deploy.sh [service|all] [message]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

SERVER_USER="yancmo"
SERVER_HOST="ubuntumac"
SERVER_PATH="/home/yancmo/apps/server-stack-monorepo-v2"

show_help() {
    echo "🚀 Production Deployment Script"
    echo "==============================="
    echo ""
    echo "Usage: ./deploy.sh [service] [message]"
    echo ""
    echo "Services:"
    echo "  all               Deploy all services (default)"
    echo "  tracker           Deploy only tracker (5K tracker)"
    echo "  crumb             Deploy only crumb"
    echo "  dashboard         Deploy only dashboard"
    echo "  bot               Deploy only coc-discord-bot"
    echo "  bot-nocache       Rebuild bot without cache and restart"
    echo "  no-bot           Deploy all except coc-discord-bot"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh                           # Deploy all with auto message"
    echo "  ./deploy.sh all \"Updated dashboard\"   # Deploy all with custom message"
    echo "  ./deploy.sh tracker \"Fix login bug\"   # Deploy only tracker"
    echo "  ./deploy.sh crumb \"Fix login bug\"     # Deploy only crumb"
    echo "  ./deploy.sh bot \"Updated bot commands\" # Deploy only coc-discord-bot"
    echo "  ./deploy.sh no-bot                   # Deploy without bot"
}

commit_and_push() {
    local message="$1"
    
    if [ -z "$message" ]; then
        local changed_files=$(git status --porcelain | wc -l | tr -d ' ')
        message="Deploy: $(date '+%Y-%m-%d %H:%M:%S') - $changed_files file(s) updated"
    fi
    
    echo "📝 Committing changes..."
    git add -A
    
    if git diff --cached --quiet; then
        echo "ℹ️  No changes to commit"
        return 0
    fi
    
    git commit -m "$message"
    echo "📤 Pushing to remote..."
    git push origin main
    echo "✅ Code pushed successfully"
}

deploy_to_server() {
    local service="$1"
    
    echo "🌐 Deploying to server..."
    
    ssh "${SERVER_USER}@${SERVER_HOST}" << ENDSSH
        set -e
        echo "=== Server Deployment Started ==="
        
        cd "$SERVER_PATH"
        
        echo "📥 Pulling latest changes..."
        git pull origin main
        
        echo "🔧 Setting permissions..."
        find . -name "*.sh" -exec chmod +x {} \;
        
        echo "� Installing nginx config (yancmo.xyz.conf)..."
        if [ -f "deploy/nginx/yancmo.xyz.conf" ]; then
            sudo cp deploy/nginx/yancmo.xyz.conf /etc/nginx/sites-available/yancmo.xyz
            if [ ! -L "/etc/nginx/sites-enabled/yancmo.xyz" ]; then
                sudo ln -s /etc/nginx/sites-available/yancmo.xyz /etc/nginx/sites-enabled/yancmo.xyz || true
            fi
        else
            echo "⚠️  nginx config deploy/nginx/yancmo.xyz.conf not found in repo on server"
        fi

        echo "�🐳 Deploying containers..."
        cd deploy
        
        if [ "$service" = "no-bot" ]; then
            echo "Deploying all services except bot and crumb (temporarily)..."
            docker compose up -d --build dashboard tracker cruise-price-check
        elif [ "$service" = "bot" ]; then
            echo "Deploying coc-discord-bot only..."
            docker compose up -d --build coc-discord-bot
        elif [ "$service" = "bot-nocache" ]; then
            echo "Rebuilding coc-discord-bot without cache and restarting..."
            docker compose build --no-cache coc-discord-bot
            docker compose up -d --no-deps --force-recreate coc-discord-bot
        elif [ "$service" = "all" ] || [ -z "$service" ]; then
            echo "Deploying all services..."
            docker compose down
            docker compose up -d --build
        else
            echo "Deploying service: $service"
            docker compose up -d --build "$service"
        fi
        
        echo "📊 Checking status..."
        docker compose ps

        echo "🔄 Reloading nginx to apply latest config..."
        sudo nginx -t && sudo systemctl reload nginx || sudo systemctl restart nginx || true
        
    echo "🧪 Post-deploy diagnostics (qsl and connector)"
    echo "— Listening on ports 5553/5557:"
    (sudo ss -ltnp 2>/dev/null | grep -E ':5553|:5557' || true)
    echo "— Container health:"
    (docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'qsl|connector' || true)
    echo "— Curl upstreams (localhost):"
    (curl -sS http://localhost:5557/ | head -c 200; echo) || true
    (curl -sS http://localhost:5553/status | head -c 200; echo) || true
    echo "— Curl via nginx (https://localhost/qsl/status):"
    (curl -skS https://localhost/qsl/status | head -c 200; echo) || true

        echo "=== Server Deployment Complete ==="
ENDSSH
    
    echo "✅ Deployment completed successfully!"
}

check_status() {
    echo "🔍 Checking server status..."
    ssh "${SERVER_USER}@${SERVER_HOST}" "cd $SERVER_PATH/deploy && docker compose ps"
}

# Main execution
case "${1:-all}" in
    all|"")
        commit_and_push "$2"
        deploy_to_server "all"
        ;;
    tracker|dashboard|clan-map|cruise-price-check|qsl-card-creator|connector|bot|bot-nocache)
        commit_and_push "$2"
        deploy_to_server "$1"
        ;;
    no-bot)
        commit_and_push "$2"
        deploy_to_server "no-bot"
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown service: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
