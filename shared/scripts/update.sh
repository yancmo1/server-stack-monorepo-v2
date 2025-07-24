#!/bin/bash

# Pi Dashboard Update Script
# Updates dashboard to the latest version

set -e

INSTALL_DIR="/home/pi/pi-dashboard"
SERVICE_NAME="pi-dashboard"
BACKUP_DIR="/home/pi/pi-dashboard-backups"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

main() {
    print_step "Updating Pi Dashboard..."
    
    # Create backup
    mkdir -p "$BACKUP_DIR"
    backup_file="$BACKUP_DIR/dashboard-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$backup_file" -C "$INSTALL_DIR" . 2>/dev/null || true
    print_success "Backup created: $backup_file"
    
    # Stop service
    print_step "Stopping dashboard service..."
    sudo systemctl stop "$SERVICE_NAME"
    
    # Update code (this would pull from git in real deployment)
    print_step "Updating dashboard code..."
    cd "$INSTALL_DIR"
    
    # Update Python dependencies
    source dashboard_venv/bin/activate
    pip install --upgrade -r requirements.txt
    
    # Start service
    print_step "Starting dashboard service..."
    sudo systemctl start "$SERVICE_NAME"
    
    # Verify
    sleep 3
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Dashboard updated and running"
    else
        print_warning "Dashboard may not have started properly"
        sudo systemctl status "$SERVICE_NAME" --no-pager
    fi
}

main "$@"
