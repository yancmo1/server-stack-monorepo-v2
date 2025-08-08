#!/bin/bash
# scripts/deploy_pwa_tracker.sh
# Deploys only the pwa-tracker service: commit, push, ssh, pull, rebuild, restart

set -e

# Commit and push changes
BRANCH=$(git rev-parse --abbrev-ref HEAD)
CHANGED=$(git status --porcelain)

# Allow an optional commit message as the first arg
INPUT_MSG="$1"

if [ -z "$CHANGED" ]; then
  echo "No changes to commit. Proceeding to remote deploy."
else
  # Build a better message if none supplied
  if [ -z "$INPUT_MSG" ]; then
    FILE_COUNT=$(git status -s | wc -l | tr -d ' ')
    # Extract a short scope from changed paths
    SCOPE=$(git status -s | awk '{print $2}' | awk -F'/' 'NR==1{if ($1=="apps") {print $2} else if ($1=="scripts") {print $1} else {print $1}}')
    [ -z "$SCOPE" ] && SCOPE="repo"
    SUMMARY=$(git status -s | awk '{print $2}' | sed -e 's/^apps\///' -e 's/^scripts\///' | head -n 5 | paste -sd ', ' -)
    MSG="${SCOPE}: ${FILE_COUNT} file(s) updated - ${SUMMARY}"
  else
    MSG="$INPUT_MSG"
  fi

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
