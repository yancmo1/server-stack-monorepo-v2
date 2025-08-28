#!/usr/bin/env bash
set -euo pipefail
# Retention policy pruning on MEGA using rclone delete, size, and filtering
# Adjust KEEP_DAYS and monthly retention to taste

REMOTE="mega:server-backups"
KEEP_DAYS_HOME=30
KEEP_DAILY_SYSTEM=14
KEEP_DAILY_DB=14

# Delete home archive folders older than KEEP_DAYS_HOME
rclone delete --min-age ${KEEP_DAYS_HOME}d "$REMOTE/home/archive" --rmdirs || true

# For system snapshots, delete daily folders older than KEEP_DAILY_SYSTEM days (naive)
rclone lsf "$REMOTE/system" --dirs-only --format pt | while read -r line; do
  # line example: 2025-08-27/; parse date
  date=${line%%/*}
  if [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    # If older than KEEP_DAILY_SYSTEM, delete
    if [[ $(date -d "$date +${KEEP_DAILY_SYSTEM} days" +%s) -lt $(date +%s) ]]; then
      rclone purge "$REMOTE/system/$date" || true
    fi
  fi
done

# DB daily
rclone lsf "$REMOTE/db" --dirs-only --format pt | while read -r line; do
  date=${line%%/*}
  if [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    if [[ $(date -d "$date +${KEEP_DAILY_DB} days" +%s) -lt $(date +%s) ]]; then
      rclone purge "$REMOTE/db/$date" || true
    fi
  fi
done
