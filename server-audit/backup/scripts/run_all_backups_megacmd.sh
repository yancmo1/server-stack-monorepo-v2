#!/usr/bin/env bash
set -euo pipefail
# One-time full backup using MEGAcmd (mega-*) instead of rclone.
# Prereqs: mega-cmd-server running and user logged in via `mega-login`.

BASE_DIR="/home/yancmo/apps/server-stack-monorepo-v2/server-audit/backup"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
DATE="$(date -u +%F)"
LOG="$LOG_DIR/backup_megacmd_$TS.log"

exec > >(tee -a "$LOG") 2>&1

echo "[$(date -u +%F\ %T)] Starting MEGAcmd backups"

# Ensure megacmd server is available
if ! mega-whoami >/dev/null 2>&1; then
  echo "Starting mega-cmd-server..."
  nohup mega-cmd-server >/dev/null 2>&1 &
  sleep 3
  if ! mega-whoami >/dev/null 2>&1; then
    echo "ERROR: mega-cmd-server not ready or not logged in. Run 'mega-login' in a shell and retry." >&2
    exit 1
  fi
fi

echo "== Ensure remote directories =="
mega-mkdir "mega:/server-backups/home/current" || true
mega-mkdir "mega:/server-backups/home/archive" || true
mega-mkdir "mega:/server-backups/system/$DATE" || true
mega-mkdir "mega:/server-backups/db/$DATE" || true

# Home incremental upload (MEGA keeps versions on overwrite)
echo "== Home incremental upload =="
mega-put -r --no-progress "$HOME/" "mega:/server-backups/home/current" || true

# System snapshot of key directories
echo "== System snapshot upload =="
for p in /etc /srv /opt /var/lib/postgresql /var/lib/docker/volumes; do
  [ -e "$p" ] || continue
  name=$(echo "$p" | sed 's#^/##; s#/#-#g; s#-$##')
  mega-mkdir "mega:/server-backups/system/$DATE/$name" || true
  mega-put -r --no-progress "$p" "mega:/server-backups/system/$DATE/$name" || true
done

# Database dumps (reuse existing script to create dumps locally)
echo "== Database dumps =="
sudo bash "$BASE_DIR/scripts/backup_db_daily.sh" || true
LOCAL_DB_DIR="/var/backups/postgres/$DATE"
if [ -d "$LOCAL_DB_DIR" ]; then
  mega-put -r --no-progress "$LOCAL_DB_DIR" "mega:/server-backups/db/$DATE" || true
else
  echo "WARN: Local DB dump directory not found: $LOCAL_DB_DIR"
fi

echo "[$(date -u +%F\ %T)] MEGAcmd backups finished"
