#!/bin/bash

# Pi Dashboard Backup Script
# Creates backups of dashboard configuration and data

set -e

INSTALL_DIR="/home/pi/pi-dashboard"
BACKUP_DIR="/home/pi/pi-dashboard-backups"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

main() {
    print_step "Creating dashboard backup..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Create backup filename
    backup_file="$BACKUP_DIR/dashboard-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    # Create backup
    tar -czf "$backup_file" \
        -C "$INSTALL_DIR" \
        config/ \
        logs/ \
        dashboard.py \
        requirements.txt \
        2>/dev/null || true
    
    print_success "Backup created: $backup_file"
    
    # Cleanup old backups
    print_step "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    find "$BACKUP_DIR" -name "dashboard-backup-*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    print_success "Backup complete"
}

main "$@"
