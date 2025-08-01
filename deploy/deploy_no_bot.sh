#!/bin/bash
# Commit, push, pull on server, and restart all apps except coc-discord-bot

set -e

echo "[Local] Committing and pushing changes..."
git add .
git commit -m "Update"
git push

echo "[Remote] Pulling and restarting apps (except coc-discord-bot)..."
ssh yancmo@ubuntumac '
  cd /home/yancmo/apps/server-stack-monorepo-v2/deploy && \
  git pull && \
  docker compose up -d --no-deps dashboard clan-map qsl-card-creator tracker pwa-tracker
'

echo "Done."
