#!/usr/bin/env bash
set -euo pipefail
# Daily PostgreSQL dumps (system cluster and dockerized DBs), then upload to MEGA

REMOTE="mega:server-backups/db"
DATE="$(date -u +%F)"
LOCAL_DIR="/var/backups/postgres/$DATE"
mkdir -p "$LOCAL_DIR"

# System Postgres cluster (if psql present)
if command -v psql >/dev/null 2>&1; then
  pg_dumpall -U postgres > "$LOCAL_DIR/system_postgres_all.sql" 2>"$LOCAL_DIR/system_pg_dumpall.log" || true
fi

# Docker Postgres containers (filter by image)
if command -v docker >/dev/null 2>&1; then
  while IFS=';' read -r cid name ports image; do
    [[ -z "$cid" ]] && continue
    if echo "$image" | grep -qi 'postgres'; then
      dump_file="$LOCAL_DIR/${name}_all.sql"
      docker exec "$cid" pg_dumpall -U postgres > "$dump_file" 2>"$dump_file.log" || true
    fi
  done < <(docker ps --format '{{.ID}};{{.Names}};{{.Ports}};{{.Image}}')
fi

# Upload to MEGA and (optionally) prune local
rclone copy "$LOCAL_DIR" "$REMOTE/$DATE" --fast-list || true
