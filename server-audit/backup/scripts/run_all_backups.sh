#!/usr/bin/env bash
set -euo pipefail
# Orchestrate all backups with simple logging
BASE_DIR="/home/yancmo/apps/server-stack-monorepo-v2/server-audit/backup"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/backup_$TS.log"
{
  echo "[$(date -u +%F\ %T)] Starting backups"
  echo "== Home incremental =="
  bash "$BASE_DIR/scripts/backup_home_incremental.sh"
  echo "== System daily =="
  sudo bash "$BASE_DIR/scripts/backup_system_daily.sh"
  echo "== DB daily =="
  sudo bash "$BASE_DIR/scripts/backup_db_daily.sh"
  echo "[$(date -u +%F\ %T)] Backups finished"
} |& tee -a "$LOG"
