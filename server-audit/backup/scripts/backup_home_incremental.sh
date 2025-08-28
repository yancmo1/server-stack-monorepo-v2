#!/usr/bin/env bash
set -euo pipefail
# Incremental home backup to MEGA via rclone with backup-dir versioning
# READ-ONLY to system; only copies to remote
# Configure: REMOTE, EXCLUDES

REMOTE="mega:server-backups"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
SRC="$HOME/"
DEST_CURRENT="$REMOTE/home/current"
DEST_ARCHIVE="$REMOTE/home/archive/$TS"

# Exclusions (edit as needed)
EXCLUDES=(
  "--exclude=.cache/**"
  "--exclude=.local/share/Trash/**"
  "--exclude=.gvfs/**"
  "--exclude=**/node_modules/**"
  "--exclude=**/.venv/**"
  "--exclude=**/__pycache__/**"
)

rclone sync "$SRC" "$DEST_CURRENT" \
  --backup-dir "$DEST_ARCHIVE" \
  --links \
  --fast-list \
  --transfers=8 \
  --checkers=8 \
  --delete-excluded \
  "${EXCLUDES[@]}"
