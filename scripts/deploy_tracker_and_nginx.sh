#!/bin/bash
# Deploy script: commit, push, SSH to server, pull, move nginx conf, and restart services
# Usage: ./scripts/deploy_tracker_and_nginx.sh

set -e

# 1. Force-add nginx config and other files
# This ensures the nginx config is always staged, even if previously ignored or unchanged
# Add any other files you want to include
git add -f deploy/nginx/yancmo.xyz.conf
# Add app and script files as well
git add -f apps/5k-tracker/app.py scripts/deploy_nginx_tracker.sh
# Add user listing and init scripts
git add -f apps/5k-tracker/list_users.py apps/5k-tracker/init_and_run.sh
# Add all new/untracked files in 5k-tracker
git add -f apps/5k-tracker/* || true
# Show git status for debugging
echo "--- GIT STATUS BEFORE COMMIT ---"
git status
ls -l apps/5k-tracker/

if ! git diff --cached --quiet; then
  echo "--- COMMITTING CHANGES ---"
  git commit -m "[deploy] $(date +'%Y-%m-%d %H:%M:%S') - Deploy tracker and nginx config: $(git diff --cached --name-only | xargs | sed 's/ /, /g')"
else
  echo "No changes to commit."
fi

git push origin main || { echo 'Git push failed!'; exit 1; }

# 2. SSH to server and deploy
ssh yancmo@ubuntumac << 'ENDSSH'
  set -e
  cd /home/yancmo/apps/server-stack-monorepo-v2 
  git pull origin main
  sudo cp deploy/nginx/yancmo.xyz.conf /etc/nginx/sites-available/yancmo.xyz.conf
  sudo ln -sf /etc/nginx/sites-available/yancmo.xyz.conf /etc/nginx/sites-enabled/yancmo.xyz.conf
  sudo nginx -t && sudo systemctl reload nginx
  docker compose -f deploy/docker-compose.yml up --build -d tracker
ENDSSH

echo "Deployment complete!"
