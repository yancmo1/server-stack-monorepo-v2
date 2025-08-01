#!/bin/bash
# scripts/deploy_pwa_tracker.sh
# Deploys only the pwa-tracker service: commit, push, ssh, pull, rebuild, restart

set -e

# Commit and push changes
BRANCH=$(git rev-parse --abbrev-ref HEAD)
CHANGED=$(git status --porcelain)
if [ -z "$CHANGED" ]; then
  echo "No changes to commit. Proceeding to remote deploy."
else
  MSG="Auto-commit: $(date '+%Y-%m-%d %H:%M') - $(git status -s | wc -l) file(s) changed [pwa-tracker deploy]"
  git add .
  git commit -m "$MSG"
  git push origin "$BRANCH"
  echo "Committed and pushed to $BRANCH with message: $MSG"
fi

# SSH, pull, rebuild, and restart only pwa-tracker
ssh yancmo@ubuntumac '
  cd /home/yancmo/apps/server-stack-monorepo-v2 && \
  git pull && \
  cd deploy && \
  docker compose build pwa-tracker && \
  docker compose up -d --no-deps pwa-tracker
'

echo "✅ pwa-tracker deployed and restarted."
