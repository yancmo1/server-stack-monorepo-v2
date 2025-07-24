#!/bin/bash

# QSL Card Creator - Refresh Test Database Script
# This script safely copies the OneDrive database for local testing

ONEDRIVE_DB="/Users/yancyshepherd/Library/CloudStorage/OneDrive-GCGLLC/Yancy/Home/Family/Yancy/Ham/Log4OM/Log4OM db.SQLite"
LOCAL_DB="Log4OM db.SQLite"
BACKUP_DIR="database_backups"

echo "🗄️  QSL Card Creator - Database Refresh"
echo "==============================================="

# Check if OneDrive database exists
if [ ! -f "$ONEDRIVE_DB" ]; then
    echo "❌ Error: OneDrive database not found at: $ONEDRIVE_DB"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup current local database if it exists and has been modified
if [ -f "$LOCAL_DB" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/Log4OM_db_backup_$TIMESTAMP.SQLite"
    echo "📦 Backing up current test database to: $BACKUP_FILE"
    cp "$LOCAL_DB" "$BACKUP_FILE"
fi

# Copy fresh database from OneDrive
echo "📥 Copying fresh database from OneDrive..."
cp "$ONEDRIVE_DB" "$LOCAL_DB"

# Get file info
ONEDRIVE_SIZE=$(ls -lh "$ONEDRIVE_DB" | awk '{print $5}')
ONEDRIVE_DATE=$(ls -lh "$ONEDRIVE_DB" | awk '{print $6, $7, $8}')

echo "✅ Database refresh complete!"
echo "   Size: $ONEDRIVE_SIZE"
echo "   Modified: $ONEDRIVE_DATE"
echo ""
echo "📝 Note: This is a read-only copy for testing."
echo "   Your OneDrive database remains unchanged."
echo ""
echo "🐳 To apply changes to Docker container, run:"
echo "   ./rebuild_docker.sh"
