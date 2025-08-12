#!/bin/bash
# Robust deploy script for pwa-tracker.
# Features:
#  - Optional skipping of commit/push
#  - Custom commit message
#  - Optional skipping of remote build
#  - Remote logs and status retrieval
#  - Clear structured logging with timestamps
# Usage: deploy_pwa_tracker.sh [--no-commit] [--message "msg"] [--skip-remote-build]

set -euo pipefail

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
LOG() { echo "[LOCAL $(timestamp)] $*"; }
RUN() { LOG "➤ $*"; "$@"; }

DO_COMMIT=1
CUSTOM_MSG=""
SKIP_REMOTE_BUILD=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-commit) DO_COMMIT=0; shift ;;
    --message|-m) CUSTOM_MSG="$2"; shift 2 ;;
    --skip-remote-build) SKIP_REMOTE_BUILD=1; shift ;;
    *) LOG "Unknown arg: $1"; exit 1 ;;
  esac
done

BRANCH=$(git rev-parse --abbrev-ref HEAD)
CHANGED=$(git status --porcelain || true)

if [[ $DO_COMMIT -eq 1 ]]; then
  if [[ -z "$CHANGED" ]]; then
    LOG "No local changes to commit."
  else
    if [[ -z "$CUSTOM_MSG" ]]; then
      FILE_COUNT=$(git status -s | wc -l | tr -d ' ')
      SCOPE=$(git status -s | awk '{print $2}' | awk -F'/' 'NR==1{if ($1=="apps") {print $2} else if ($1=="scripts") {print $1} else {print $1}}')
      [[ -z "$SCOPE" ]] && SCOPE="repo"
      SUMMARY=$(git status -s | awk '{print $2}' | sed -e 's/^apps\///' -e 's/^scripts\///' | head -n 5 | paste -sd ', ' -)
      MSG="${SCOPE}: ${FILE_COUNT} file(s) updated - ${SUMMARY}"
    else
      MSG="$CUSTOM_MSG"
    fi
    RUN git add .
    RUN git commit -m "$MSG"
    RUN git push origin "$BRANCH"
    LOG "Committed & pushed: $MSG"
  fi
else
  LOG "--no-commit specified: skipping commit/push phase."
fi

LOG "Starting remote deploy (branch: $BRANCH)..."
SSH_OPTS=(-tt -o BatchMode=yes -o ConnectTimeout=15)

# Build remote script with explicit newlines between all commands
REMOTE_SCRIPT=$(cat <<'RSCRIPT'
set -euo pipefail

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
LOG() { echo "[REMOTE $(timestamp)] $*"; }

cd /home/yancmo/apps/server-stack-monorepo-v2
BR=$(git rev-parse --abbrev-ref HEAD)
LOG "On branch $BR"
if ! git diff --quiet || ! git diff --cached --quiet; then
  LOG "Stashing local changes before pull..."
  git stash push -u -m "auto-stash before deploy $(date '+%Y-%m-%d %H:%M:%S')" || true
fi
LOG "Pulling latest changes..."
git pull --rebase
cd deploy
RSCRIPT
)

if [[ $SKIP_REMOTE_BUILD -eq 0 ]]; then
  REMOTE_SCRIPT+=$'\nLOG "Building pwa-tracker image..."\n'
  REMOTE_SCRIPT+=$'docker compose build pwa-tracker || { LOG "Build failed"; exit 1; }\n'
else
  REMOTE_SCRIPT+=$'\nLOG "Skipping remote build (using existing image)."\n'
fi
REMOTE_SCRIPT+=$'\nLOG "Restarting service..."\n'
REMOTE_SCRIPT+=$'docker compose up -d --no-deps pwa-tracker || { LOG "docker compose up failed"; exit 1; }\n'
REMOTE_SCRIPT+=$'\nLOG "Service status:"\n'
REMOTE_SCRIPT+=$'docker compose ps pwa-tracker || true\n'
REMOTE_SCRIPT+=$'\nLOG "Recent logs (last 60 lines):"\n'
REMOTE_SCRIPT+=$'docker compose logs --tail=60 pwa-tracker || true\n'
REMOTE_SCRIPT+=$'\nLOG "Healthcheck curl attempt:"\n'
REMOTE_SCRIPT+=$'curl -fsS http://localhost:5555/health || echo "Health endpoint not reachable (yet)."\n'
REMOTE_SCRIPT+=$'\nLOG "✅ Remote deploy complete."\n'

if ! ssh "${SSH_OPTS[@]}" yancmo@ubuntumac "bash -l" <<<"$REMOTE_SCRIPT"; then
  LOG "ERROR: Remote deploy failed." >&2
  exit 1
fi

LOG "✅ pwa-tracker deploy finished successfully."