#!/usr/bin/env bash
set -euo pipefail
# Daily system snapshot of key directories to dated paths on MEGA
# Adjust PATHS to your needs; uses rclone sync

REMOTE="mega:server-backups/system"
DATE="$(date -u +%F)"

# Paths to mirror (read-only copy)
PATHS=(
  "/etc/"
  "/srv/"
  "/opt/"
  "/var/lib/postgresql/"
  "/var/lib/docker/volumes/"
)

EXCLUDES=(
  "--exclude=**/cache/**"
  "--exclude=**/tmp/**"
  "--exclude=**/.cache/**"
)

for p in "${PATHS[@]}"; do
  name=$(echo "$p" | sed 's#^/##; s#/#-#g; s#-$##')
  dest="$REMOTE/$DATE/$name"
  rclone sync "$p" "$dest" --copy-links --links --fast-list "${EXCLUDES[@]}" || true
done
