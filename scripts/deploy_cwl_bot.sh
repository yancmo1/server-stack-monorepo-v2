#!/bin/bash
# Deploy the new CWL-only Discord bot to the server.
# - Commits local changes (unless no changes)
# - Pushes current branch
# - SSH to server, pulls, rebuilds bot image, restarts service, shows status/logs
# Usage: scripts/deploy_cwl_bot.sh [--no-cache]

set -euo pipefail

NO_CACHE=0
if [[ ${1-} == "--no-cache" ]]; then
  NO_CACHE=1
fi

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
LOG() { echo "[LOCAL $(timestamp)] $*"; }
RUN() { LOG "➤ $*"; "$@"; }

BRANCH=$(git rev-parse --abbrev-ref HEAD)
CHANGED=$(git status --porcelain || true)

if [[ -n "$CHANGED" ]]; then
  FILE_COUNT=$(git status -s | wc -l | tr -d ' ')
  SUMMARY=$(git status -s | awk '{print $2}' | sed -e 's/^apps\///' -e 's/^scripts\///' | head -n 5 | paste -sd ', ' -)
  MSG="cwl-bot: ${FILE_COUNT} update(s) - ${SUMMARY}"
  RUN git add .
  RUN git commit -m "$MSG"
  RUN git push origin "$BRANCH"
else
  LOG "No local changes to commit. Pushing to ensure remote is current."
  RUN git push origin "$BRANCH"
fi

SSH_OPTS=(-tt -o BatchMode=yes -o ConnectTimeout=15)
REMOTE_SCRIPT=$(cat <<'RS'
set -euo pipefail

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
LOG() { echo "[REMOTE $(timestamp)] $*"; }

cd /home/yancmo/apps/server-stack-monorepo-v2
LOG "Pulling latest changes..."
git pull --rebase
cd deploy
LOG "Building coc-discord-bot image (CWL)..."
RS
)

if [[ $NO_CACHE -eq 1 ]]; then
  REMOTE_SCRIPT+=$'docker compose build --no-cache coc-discord-bot\n'
else
  REMOTE_SCRIPT+=$'docker compose build coc-discord-bot\n'
fi
REMOTE_SCRIPT+=$'LOG "Restarting service..."\n'
REMOTE_SCRIPT+=$'docker compose up -d --no-deps --force-recreate coc-discord-bot\n'
REMOTE_SCRIPT+=$'LOG "Service status:"\n'
REMOTE_SCRIPT+=$'docker compose ps coc-discord-bot || true\n'
REMOTE_SCRIPT+=$'LOG "Recent logs (last 80 lines):"\n'
REMOTE_SCRIPT+=$'docker compose logs --tail=80 coc-discord-bot || true\n'

if ! ssh "${SSH_OPTS[@]}" yancmo@ubuntumac "bash -l" <<<"$REMOTE_SCRIPT"; then
  LOG "ERROR: Remote deploy failed." >&2
  exit 1
fi

LOG "✅ CWL bot deploy complete."
