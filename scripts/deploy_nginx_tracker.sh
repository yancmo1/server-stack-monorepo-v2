#!/bin/bash
# Script to deploy the updated nginx config for yancmo.xyz to the server
# Usage: ./scripts/deploy_nginx_tracker.sh [user@host]

set -e

REMOTE=${1:-yancmo@ubuntumac}
LOCAL_CONF="$(dirname "$0")/../deploy/nginx/yancmo.xyz.conf"
REMOTE_CONF="/etc/nginx/sites-available/yancmo.xyz.conf"

# Copy the config file to the server
	   # Copy the config file to the user's home directory on the server
	   scp "$LOCAL_CONF" "$REMOTE:~/yancmo.xyz.conf"

	   # Move the config into /etc/nginx/sites-available/ with sudo, symlink, test, and reload
	   ssh "$REMOTE" "sudo mv ~/yancmo.xyz.conf /etc/nginx/sites-available/yancmo.xyz.conf && \
		   sudo ln -sf /etc/nginx/sites-available/yancmo.xyz.conf /etc/nginx/sites-enabled/yancmo.xyz.conf && \
		   sudo nginx -t && sudo systemctl reload nginx"

# Symlink to sites-enabled if not already

# Test nginx config and reload

echo "Nginx config deployed and reloaded on $REMOTE."
	   echo "Nginx config deployed and reloaded on $REMOTE."
