#!/bin/bash
# Development Environment Management Script
# Usage: ./dev.sh [start|stop|restart|test|logs|clean]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.dev.yml"

show_help() {
    echo "🚀 Development Environment Manager"
    echo "=================================="
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start     Start all development services"
    echo "  stop      Stop all development services"
    echo "  restart   Restart all development services"
    echo "  test      Run health checks on all services"
    echo "  logs      Show logs (add service name for specific service)"
    echo "  status    Show container status"
    echo "  clean     Stop and remove all containers/volumes"
    echo "  help      Show this help message"
    echo ""
    echo "📝 Note: Discord bot excluded from development environment"
    echo "   Use: ./deploy.sh bot  (for bot development/testing)"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh start"
    echo "  ./dev.sh logs tracker"
    echo "  ./dev.sh restart dashboard"
}

check_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use!"
        echo "   Kill with: kill -9 \$(lsof -ti:$port)"
        return 1
    fi
    return 0
}

start_dev() {
    echo "🚀 Starting Development Environment..."
    
    # Check critical ports
    echo "🔍 Checking ports..."
    check_port 5550 || exit 1  # Dashboard
    check_port 5555 || exit 1  # Tracker (PWA)
    check_port 5433 || exit 1  # Database
    
    echo "✅ All ports available"
    
    # Start services
    docker compose -f "$COMPOSE_FILE" up -d
    
    echo "⏳ Waiting for services..."
    sleep 10
    
    echo "📊 Service Status:"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "🎯 Development URLs:"
    echo "  Dashboard:      https://dashboard.yancmo.xyz"
    echo "  Tracker:        https://tracker.yancmo.xyz"
    echo "  Crumb:          https://crumb.yancmo.xyz"
    echo "  Cruise Check:   https://cruise.yancmo.xyz"
    echo "  Clash Map:      https://clashmap.yancmo.xyz"
    echo "  QSL Creator:    http://localhost:5553"
    echo ""
    echo "✅ Development environment ready!"
}

stop_dev() {
    echo "🛑 Stopping Development Environment..."
    docker compose -f "$COMPOSE_FILE" down
    echo "✅ Development environment stopped"
}

restart_dev() {
    local service=$1
    if [ -n "$service" ]; then
        echo "🔄 Restarting $service..."
        docker compose -f "$COMPOSE_FILE" restart "$service"
    else
        echo "🔄 Restarting all services..."
        stop_dev
        start_dev
    fi
}

test_dev() {
    echo "🧪 Testing Development Environment..."
    ./test-dev.sh
}

logs_dev() {
    local service=$1
    if [ -n "$service" ]; then
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

status_dev() {
    echo "📊 Development Environment Status:"
    docker compose -f "$COMPOSE_FILE" ps
}

clean_dev() {
    echo "🧹 Cleaning Development Environment..."
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
    docker system prune -f
    echo "✅ Development environment cleaned"
}

# Main command handling
case "${1:-help}" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    restart)
        restart_dev "$2"
        ;;
    test)
        test_dev
        ;;
    logs)
        logs_dev "$2"
        ;;
    status)
        status_dev
        ;;
    clean)
        clean_dev
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
