#!/usr/bin/env bash
set -euo pipefail

# 5k-tracker-pwa database export script
# - Creates a timestamped folder under ./exports/
# - Produces:
#   * Full pg_dump in plain SQL and custom format
#   * Per-table CSV exports (public schema)
#   * Per-table JSONL exports (row_to_json)
#   * Optional uploads tarball if ./uploads exists
#
# It prefers running pg_dump/psql inside the docker container 'race-tracker-db'.
# If the container is not running, it will try local pg_dump/psql using PG* env vars
# or reasonable defaults (see below).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

timestamp() { date +%Y%m%d_%H%M%S; }

EXPORT_DIR="$SCRIPT_DIR/exports/$(timestamp)"
CSV_DIR="$EXPORT_DIR/csv"
JSONL_DIR="$EXPORT_DIR/jsonl"
mkdir -p "$CSV_DIR" "$JSONL_DIR"

# Default DB settings (overridable by environment)
: "${DB_HOST:=localhost}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=racetracker}"
: "${DB_USER:=racetracker}"
: "${DB_PASSWORD:=racetracker}"

# Allow TRACKER_DATABASE_URI to override connection settings
if [[ -n "${TRACKER_DATABASE_URI:-}" ]]; then
  # Try to load TRACKER_DATABASE_URI from shared config if not already provided
  if [[ -z "${TRACKER_DATABASE_URI:-}" ]]; then
    ENV_FILE_REL="../../shared/config/.env"
    if [[ -f "$ENV_FILE_REL" ]]; then
      TRACKER_DATABASE_URI=$(grep -E '^TRACKER_DATABASE_URI=' "$ENV_FILE_REL" | sed -E 's/^TRACKER_DATABASE_URI=//') || true
      export TRACKER_DATABASE_URI
    fi
  fi

  # Parse a URI like: postgresql://user:pass@host:port/dbname
  # shellcheck disable=SC2001
  proto="$(echo "$TRACKER_DATABASE_URI" | sed -E 's|://.*||')"
  if [[ "$proto" == postgresql* || "$proto" == postgres* ]]; then
    # Extract user, password, host, port, db
    # Use python for robust parsing if available
    if command -v python3 >/dev/null 2>&1; then
      eval "$(python3 - <<'PY'
import os, sys
from urllib.parse import urlparse
uri = os.environ.get('TRACKER_DATABASE_URI')
u = urlparse(uri)
if u.username: print(f"DB_USER='{u.username}'")
if u.password: print(f"DB_PASSWORD='{u.password}'")
if u.hostname: print(f"DB_HOST='{u.hostname}'")
if u.port: print(f"DB_PORT='{u.port}'")
if u.path and len(u.path) > 1: print(f"DB_NAME='{u.path.lstrip('/')}'")
PY
      )"
    fi
  fi
fi

echo "[export] Using connection: host=$DB_HOST port=$DB_PORT db=$DB_NAME user=$DB_USER"

# Decide execution mode: docker-exec vs local
USE_DOCKER=false
# Default container name (can be overridden by DOCKER_DB_CONTAINER env var)
DB_CONTAINER_DEFAULT="race-tracker-db"
DB_CONTAINER="${DOCKER_DB_CONTAINER:-$DB_CONTAINER_DEFAULT}"
TEMP_CONTAINER="race-tracker-db-export"
if command -v docker >/dev/null 2>&1; then
  # If DOCKER_DB_CONTAINER is explicitly provided and running, use it
  if [[ -n "${DOCKER_DB_CONTAINER:-}" ]] && docker ps --format '{{.Names}}' | grep -q "^${DOCKER_DB_CONTAINER}$"; then
    USE_DOCKER=true
    DB_CONTAINER="$DOCKER_DB_CONTAINER"
  elif docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    USE_DOCKER=true
  else
    # If the named volume from compose exists, spin up a temporary container to use it
    if docker volume ls --format '{{.Name}}' | grep -q '^5k-tracker-pwa_pgdata$'; then
      echo "[export] Starting temporary Postgres container using volume 5k-tracker-pwa_pgdata ..."
      # Start ephemeral container without publishing ports to avoid conflicts
      docker run -d --rm --name "$TEMP_CONTAINER" \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -v 5k-tracker-pwa_pgdata:/var/lib/postgresql/data \
        postgres:15 >/dev/null
      # Wait for Postgres to be ready
      echo -n "[export] Waiting for Postgres to be ready"
      for i in {1..30}; do
        if docker exec "$TEMP_CONTAINER" pg_isready -h localhost -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
          echo " - ready"
          USE_DOCKER=true
          DB_CONTAINER="$TEMP_CONTAINER"
          break
        fi
        echo -n "."
        sleep 1
      done
      if ! $USE_DOCKER; then
        echo "\n[export] Postgres did not become ready in time. Aborting." >&2
        docker rm -f "$TEMP_CONTAINER" >/dev/null 2>&1 || true
        exit 1
      fi
    fi
  fi
fi

run_psql() {
  local sql="$1"
  if $USE_DOCKER; then
    docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
  psql -h "localhost" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -At -c "$sql"
  else
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -At -c "$sql"
  fi
}

copy_table_csv() {
  local table="$1"        # bare table name without schema
  local schema_fq="public.\"$table\""  # schema-qualified and quoted
  if $USE_DOCKER; then
    docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
  psql -h "localhost" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -c "\\copy (SELECT * FROM $schema_fq) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)" \
      > "$CSV_DIR/${table}.csv"
  else
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
      "\\copy (SELECT * FROM $schema_fq) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)" \
      > "$CSV_DIR/${table}.csv"
  fi
}

copy_table_jsonl() {
  local table="$1"
  local sql="COPY (SELECT row_to_json(t) FROM public.\"$table\" t) TO STDOUT;"
  if $USE_DOCKER; then
    docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
  psql -h "localhost" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -c "$sql" \
      > "$JSONL_DIR/${table}.jsonl"
  else
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql" \
      > "$JSONL_DIR/${table}.jsonl"
  fi
}

echo "[export] Creating full dumps ..."
if $USE_DOCKER; then
  docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
  pg_dump -h "localhost" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    > "$EXPORT_DIR/db_dump.sql"
  docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
  pg_dump -h "localhost" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc \
    > "$EXPORT_DIR/db_dump.custom"
else
  PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    > "$EXPORT_DIR/db_dump.sql"
  PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc \
    > "$EXPORT_DIR/db_dump.custom"
fi

echo "[export] Listing tables ..."
# Get plain table names from public schema (we'll quote as needed later)
TABLES=$(run_psql "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1;")

echo "[export] Exporting tables to CSV and JSONL ..."
IFS=$'\n'
for tbl in $TABLES; do
  # tbl is bare table name (may be reserved like user)
  echo "  - $tbl"
  copy_table_csv "$tbl"
  copy_table_jsonl "$tbl"
done
unset IFS

# If no Postgres tables were exported, fall back to SQLite if present
if [[ -z "$TABLES" ]]; then
  SQLITE_DB="$SCRIPT_DIR/race_tracker.db"
  if [[ -f "$SQLITE_DB" && -s "$SQLITE_DB" ]]; then
    echo "[export] No Postgres tables found. Detected SQLite database at $SQLITE_DB — exporting from SQLite instead."

    # List SQLite tables (exclude sqlite internal tables)
    if command -v sqlite3 >/dev/null 2>&1; then
      mapfile -t SQLITE_TABLES < <(sqlite3 "$SQLITE_DB" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    else
      echo "[export] ERROR: sqlite3 is not installed on the host. Please install sqlite3 and re-run." >&2
      SQLITE_TABLES=()
    fi

    # Export SQLite tables to CSV
    for tbl in "${SQLITE_TABLES[@]}"; do
      echo "  - (sqlite) $tbl"
      if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 -readonly -header -csv "$SQLITE_DB" "SELECT * FROM '"$tbl"';" > "$CSV_DIR/${tbl}.csv" || true
      fi
      # Export JSONL via python for robust JSON encoding
      if command -v python3 >/dev/null 2>&1; then
        python3 - <<PY
import json, sqlite3, sys
db = sqlite3.connect(r"$SQLITE_DB")
db.row_factory = sqlite3.Row
cur = db.execute(f"SELECT * FROM '{tbl}'")
with open(r"$JSONL_DIR/${tbl}.jsonl", 'w', encoding='utf-8') as f:
    for row in cur:
        f.write(json.dumps({k: row[k] for k in row.keys()}, ensure_ascii=False))
        f.write("\n")
db.close()
PY
      fi
    done

    # Also include a raw SQLite .dump for completeness
    if command -v sqlite3 >/dev/null 2>&1; then
      sqlite3 "$SQLITE_DB" ".dump" > "$EXPORT_DIR/sqlite_dump.sql" || true
    fi
  else
    echo "[export] WARNING: No Postgres tables and no SQLite database found. Data exports (csv/jsonl) will be empty."
  fi
fi

if [[ -d "$SCRIPT_DIR/uploads" ]]; then
  echo "[export] Archiving uploads directory ..."
  tar -czf "$EXPORT_DIR/uploads.tar.gz" -C "$SCRIPT_DIR" uploads
fi

# Write import helper files
cat > "$EXPORT_DIR/IMPORT_README.md" <<'MD'
# 5k-tracker-pwa Export Import Guide

You have two primary ways to import this export into a new Postgres database:

## Option A: Use the full custom dump (recommended)

This preserves schema, constraints, sequences, and data exactly.

```bash
# Set these for your target DB
export PGPASSWORD="<target_password>"
export PGUSER="<target_user>"
export PGHOST="<target_host>"   # e.g., localhost or container hostname
export PGPORT="5432"
export PGDATABASE="<target_db>"

# Create database if not exists
createdb -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" || true

# Restore (drops and recreates objects)
pg_restore -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c db_dump.custom
```

## Option B: Import CSVs with psql

This is useful if you need to massage schema manually or selectively import.

```bash
export PGPASSWORD="<target_password>"
export PGUSER="<target_user>"
export PGHOST="<target_host>"
export PGPORT="5432"
export PGDATABASE="<target_db>"

# Temporarily relax constraints for bulk load
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -c "SET session_replication_role = replica;"

# Import each table CSV (order is not important when replication_role=replica)
for f in csv/*.csv; do
  tbl=$(basename "$f" .csv)
  echo "Importing $tbl ..."
  psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -c "\\copy \"$tbl\" FROM '$f' WITH (FORMAT CSV, HEADER TRUE)"
done

# Re-enable constraints
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -c "SET session_replication_role = DEFAULT;"
```

Notes:
- JSONL files are provided for inspection or custom import tooling; primary import path is CSV or pg_dump.
- If your app expects uploaded photos, extract `uploads.tar.gz` into your app's `uploads/` folder.

## If your source was SQLite (fallback path)

This export can include `sqlite_dump.sql` plus CSV/JSONL generated from `race_tracker.db` if Postgres contained no tables.

- Preferred: create your target schema in Postgres manually, then import the CSVs (Option B above).
- Alternatively, use tools like `pgloader` to migrate directly from SQLite to Postgres using `sqlite_dump.sql` as reference.
MD

echo "[export] Done. Output written to: $EXPORT_DIR"

# Cleanup temporary container if we created one
if command -v docker >/dev/null 2>&1; then
  if docker ps --format '{{.Names}}' | grep -q "^${TEMP_CONTAINER}$"; then
    echo "[export] Stopping temporary Postgres container ..."
    docker rm -f "$TEMP_CONTAINER" >/dev/null 2>&1 || true
  fi
fi
