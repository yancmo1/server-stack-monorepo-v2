#!/bin/bash

# QSL Card Creator Database Manager
# This script helps manage the Docker container to prevent database locks

CONTAINER_NAME="qsl-card-creator"
DB_PATH="/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite"

case "$1" in
    "stop")
        echo "🛑 Stopping QSL Card Creator for Log4OM access..."
        docker stop $CONTAINER_NAME
        echo "✅ Safe to use Log4OM now!"
        echo "💡 Run './db_manager.sh start' when done with Log4OM"
        ;;
    "start")
        echo "🚀 Starting QSL Card Creator..."
        docker start $CONTAINER_NAME
        sleep 2
        echo "✅ QSL Card Creator running at http://localhost:5001"
        ;;
    "restart")
        echo "🔄 Restarting QSL Card Creator..."
        docker stop $CONTAINER_NAME
        sleep 1
        docker start $CONTAINER_NAME
        sleep 2
        echo "✅ QSL Card Creator restarted at http://localhost:5001"
        ;;
    "status")
        if docker ps | grep -q $CONTAINER_NAME; then
            echo "✅ QSL Card Creator is running"
            echo "🌐 Access at: http://localhost:5001"
        else
            echo "❌ QSL Card Creator is stopped"
            echo "💡 Run './db_manager.sh start' to start it"
        fi
        ;;
    "logs")
        echo "📋 Recent logs:"
        docker logs $CONTAINER_NAME --tail 20
        ;;
    *)
        echo "🔧 QSL Card Creator Database Manager"
        echo ""
        echo "Usage: $0 {stop|start|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  stop    - Stop container before using Log4OM"
        echo "  start   - Start container after Log4OM changes"
        echo "  restart - Quick restart of container"
        echo "  status  - Check if container is running"
        echo "  logs    - Show recent container logs"
        echo ""
        echo "💡 Workflow:"
        echo "  1. ./db_manager.sh stop    (before Log4OM changes)"
        echo "  2. Make changes in Log4OM"
        echo "  3. ./db_manager.sh start   (after Log4OM changes)"
        ;;
esac
