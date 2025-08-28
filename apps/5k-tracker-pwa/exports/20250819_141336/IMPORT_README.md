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
