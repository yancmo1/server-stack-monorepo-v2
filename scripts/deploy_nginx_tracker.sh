#!/bin/bash
# Script to deploy the updated nginx config for yancmo.xyz to the server
# Usage: ./scripts/deploy_nginx_tracker.sh [user@host]

set -e

REMOTE=${1:-yancmo@ubuntumac}
LOCAL_CONF="$(dirname "$0")/../deploy/nginx/yancmo.xyz.conf"
REMOTE_CONF="/etc/nginx/sites-available/yancmo.xyz.conf"

# Copy the config file to the server
scp "$LOCAL_CONF" "$REMOTE:$REMOTE_CONF"

# Symlink to sites-enabled if not already
ssh "$REMOTE" "sudo ln -sf /etc/nginx/sites-available/yancmo.xyz.conf /etc/nginx/sites-enabled/yancmo.xyz.conf"

# Test nginx config and reload
ssh "$REMOTE" "sudo nginx -t && sudo systemctl reload nginx"

echo "Nginx config deployed and reloaded on $REMOTE."
