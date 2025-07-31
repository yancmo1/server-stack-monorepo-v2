#!/bin/bash
# Clean up old/redundant scripts and organize the workspace
# This script moves old scripts to archive and keeps only the essential ones

set -e

echo "🧹 Cleaning up scripts and tasks..."

ARCHIVE_DIR="archive/old-scripts"
mkdir -p "$ARCHIVE_DIR"

# Scripts to archive (redundant or replaced by new unified scripts)
OLD_SCRIPTS=(
    "scripts/deploy_tracker_and_nginx.sh"
    "scripts/commit_and_push_all.sh"
    "scripts/commit_all_apps.sh"
    "scripts/commit_all_git_repos.sh"
    "deploy/deploy_no_bot.sh"
    "deploy/start-dev.sh"
    "deploy/stop-dev.sh"
    "scripts/deploy-website.sh"
    "scripts/install_website.sh"
    "scripts/fix-nginx-now.sh"
    "scripts/deploy_nginx_tracker.sh"
)

echo "📦 Archiving old scripts..."
for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "  Moving $script -> $ARCHIVE_DIR/"
        mv "$script" "$ARCHIVE_DIR/"
    else
        echo "  ⚠️  $script not found, skipping"
    fi
done

# Keep important scripts
KEEP_SCRIPTS=(
    "scripts/backup_to_meganz.sh"
    "scripts/server_audit.sh"
    "scripts/send_backup_log_test_email.py"
    "deploy/docker-apps-startup.sh"
    "deploy/setup-autostart.sh"
    "deploy/nginx-delayed-start.sh"
)

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Scripts organization:"
echo "  Essential scripts:     deploy/dev.sh, deploy/deploy.sh"
echo "  Development:          deploy/test-dev.sh"
echo "  System/backup:        scripts/ (${#KEEP_SCRIPTS[@]} scripts kept)"
echo "  Archived:             $ARCHIVE_DIR/ (${#OLD_SCRIPTS[@]} scripts moved)"
echo ""
echo "🎯 New workflow:"
echo "  Development:    ./deploy/dev.sh [start|stop|test|logs]"
echo "  Deployment:     ./deploy/deploy.sh [all|service] [message]"
echo "  VS Code Tasks:  Use Command Palette -> Tasks: Run Task"
