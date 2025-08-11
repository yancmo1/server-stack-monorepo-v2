#!/bin/bash
# Deploy only the clan-map service to the production server, forcing rebuild with no cache.
# Usage: scripts/deploy_clan_map_nocache.sh [optional commit message]
set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)
INPUT_MSG="$1"
CHANGED=$(git status --porcelain)

if [ -z "$CHANGED" ]; then
  echo "No local changes to commit. Proceeding to remote deploy."
else
  if [ -z "$INPUT_MSG" ]; then
    FILE_COUNT=$(git status -s | wc -l | tr -d ' ')
    SUMMARY=$(git status -s | awk '{print $2}' | sed -e 's/^apps\///' -e 's/^scripts\///' | head -n 5 | paste -sd ', ' -)
    INPUT_MSG="clan-map: ${FILE_COUNT} file(s) updated - ${SUMMARY}"
  fi
  git add -A
  git commit -m "$INPUT_MSG"
  git push origin "$BRANCH"
fi

ssh yancmo@ubuntumac '
  set -e
  cd /home/yancmo/apps/server-stack-monorepo-v2 && \
  # Protect any accidental local changes on server
  if ! git diff --quiet || ! git diff --cached --quiet; then \
    echo "Stashing local changes before pull..."; \
    git stash push -u -m "auto-stash before clan-map deploy $(date '+%Y-%m-%d %H:%M:%S')" || true; \
  fi && \
  git pull --rebase && \
  cd deploy && \
  # Build without cache and recreate only clan-map
  docker compose build --no-cache clan-map && \
  docker compose up -d --no-deps --force-recreate clan-map && \
  docker compose ps clan-map
'

echo "✅ clan-map rebuilt without cache and restarted."
