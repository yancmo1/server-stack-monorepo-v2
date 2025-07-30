#!/bin/bash
# Deploy script: commit, push, SSH to server, pull, move nginx conf, and restart services
# Usage: ./scripts/deploy_tracker_and_nginx.sh

set -e

# 1. Force-add nginx config and other files
# This ensures the nginx config is always staged, even if previously ignored or unchanged
# Add any other files you want to include
git add -f deploy/nginx/yancmo.xyz.conf
# Add app and script files as well
git add apps/5k-tracker/app.py scripts/deploy_nginx_tracker.sh
if ! git diff --cached --quiet; then
  git commit -m "$(git diff --cached --name-only | xargs | sed 's/ /, /g')"
fi
git push origin main

# 2. SSH to server and deploy
ssh yancmo@ubuntumac << 'ENDSSH'
  set -e
  cd /home/yancmo/apps/server-stack-monorepo-v2  # <-- CHANGE THIS to your actual project path
  git pull origin main
  sudo cp deploy/nginx/yancmo.xyz.conf /etc/nginx/sites-available/yancmo.xyz.conf
  sudo ln -sf /etc/nginx/sites-available/yancmo.xyz.conf /etc/nginx/sites-enabled/yancmo.xyz.conf
  sudo nginx -t && sudo systemctl reload nginx
  docker compose -f deploy/docker-compose.yml up --build -d tracker
ENDSSH

echo "Deployment complete!"
