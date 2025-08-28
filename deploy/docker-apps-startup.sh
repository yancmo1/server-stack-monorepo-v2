#!/bin/bash
# Docker Compose Auto-Start Script for Server Applications
# This script ensures all applications start properly after system reboot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$SCRIPT_DIR"
LOG_FILE="/var/log/docker-apps-startup.log"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to wait for Docker to be ready
wait_for_docker() {
    log "Waiting for Docker daemon to be ready..."
    local retries=30
    while ! docker info >/dev/null 2>&1; do
        if [ $retries -eq 0 ]; then
            log "ERROR: Docker daemon not ready after 30 attempts"
            exit 1
        fi
        log "Docker not ready, waiting... (attempts left: $retries)"
        sleep 2
        ((retries--))
    done
    log "Docker daemon is ready"
}

# Function to start services
start_services() {
    log "Starting Docker Compose services..."
    cd "$COMPOSE_DIR"
    
    # Pull latest images (optional, only if you want to update)
    # docker compose pull --ignore-pull-failures
    
    # Start all services
    docker compose up -d
    
    if [ $? -eq 0 ]; then
        log "Docker Compose services started successfully"
        
        # Wait a bit for services to initialize
        sleep 10
        
        # Check service health
        log "Checking service status..."
        docker compose ps
        
        # Check if key services are healthy
        local services=("tracker" "tracker-db" "dashboard" "clan-map" "cruise-price-check" "qsl-card-creator")
        for service in "${services[@]}"; do
            if docker compose ps "$service" | grep -q "Up"; then
                log "✓ $service is running"
            else
                log "⚠ WARNING: $service might not be running properly"
            fi
        done
        
    else
        log "ERROR: Failed to start Docker Compose services"
        exit 1
    fi
}

# Function to ensure nginx is running
ensure_nginx() {
    log "Checking nginx status..."
    if systemctl is-active --quiet nginx; then
        log "✓ nginx is running"
    else
        log "Starting nginx..."
        sudo systemctl start nginx
        if systemctl is-active --quiet nginx; then
            log "✓ nginx started successfully"
        else
            log "⚠ WARNING: Failed to start nginx"
        fi
    fi
}

# Main execution
main() {
    log "=== Starting Docker Apps Auto-Start Script ==="
    log "Script directory: $SCRIPT_DIR"
    log "Compose directory: $COMPOSE_DIR"
    
    # Wait for Docker
    wait_for_docker
    
    # Start services
    start_services
    
    # Ensure nginx is running
    ensure_nginx
    
    log "=== Docker Apps Auto-Start Script Completed ==="
}

# Run main function
main "$@"
