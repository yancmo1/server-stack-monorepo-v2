#!/bin/bash
# Deploy script: commit, push, SSH to server, pull, move nginx conf, and restart services
# Usage: ./scripts/deploy_tracker_and_nginx.sh

set -e

echo "=== STARTING DEPLOYMENT ==="

# 1. Force-add nginx config and other files
echo "--- STAGING FILES FOR COMMIT ---"
git add -f deploy/nginx/yancmo.xyz.conf || echo "nginx config not found, skipping"
git add -f deploy/docker-compose.yml
# Force add the docker-compose file specifically with status check
echo "Explicitly staging docker-compose.yml..."
git add deploy/docker-compose.yml
git status deploy/docker-compose.yml
# Add app and script files
git add -f apps/5k-tracker/app.py
git add -f apps/5k-tracker/list_users.py
git add -f apps/5k-tracker/init_and_run.sh
git add -f apps/5k-tracker/wait-for-it.sh || echo "wait-for-it.sh not found, skipping"
# Add this script itself
git add -f scripts/deploy_tracker_and_nginx.sh

# Show git status for debugging
echo "--- GIT STATUS BEFORE COMMIT ---"
git status

if ! git diff --cached --quiet; then
  echo "--- COMMITTING CHANGES ---"
  git commit -m "[deploy] $(date +'%Y-%m-%d %H:%M:%S') - Deploy tracker and nginx config: $(git diff --cached --name-only | xargs | sed 's/ /, /g')"
  echo "--- PUSHING TO REMOTE ---"
  git push origin main || { echo 'Git push failed!'; exit 1; }
else
  echo "No changes to commit, proceeding with deployment..."
fi

# 2. SSH to server and deploy
echo "--- CONNECTING TO SERVER ---"
ssh yancmo@ubuntumac << 'ENDSSH'
  set -e
  echo "=== ON SERVER: Starting deployment ==="
  
  cd /home/yancmo/apps/server-stack-monorepo-v2 
  
  echo "--- Pulling latest changes ---"
  git pull --no-rebase origin main || { echo "Git pull failed!"; exit 1; }
  
  echo "--- Fixing file permissions ---"
  chmod +x apps/5k-tracker/init_and_run.sh || echo "init_and_run.sh not found"
  chmod +x apps/5k-tracker/wait-for-it.sh || echo "wait-for-it.sh not found"
  
  echo "--- Updating nginx config ---"
  if [ -f deploy/nginx/yancmo.xyz.conf ]; then
    sudo cp deploy/nginx/yancmo.xyz.conf /etc/nginx/sites-available/yancmo.xyz.conf
    sudo ln -sf /etc/nginx/sites-available/yancmo.xyz.conf /etc/nginx/sites-enabled/yancmo.xyz.conf
    sudo nginx -t && sudo systemctl reload nginx
    echo "Nginx updated successfully"
  else
    echo "Nginx config not found, skipping nginx update"
  fi
  
  echo "--- Stopping existing containers ---"
  docker compose -f deploy/docker-compose.yml down || echo "No containers to stop"
  
  echo "--- Starting all services ---"
  docker compose -f deploy/docker-compose.yml up --build -d
  
  echo "--- Checking container status ---"
  docker compose -f deploy/docker-compose.yml ps
  
  echo "=== SERVER DEPLOYMENT COMPLETE ==="
ENDSSH

echo "=== DEPLOYMENT COMPLETE ==="
