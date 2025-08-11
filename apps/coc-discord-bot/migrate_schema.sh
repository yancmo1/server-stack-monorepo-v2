#!/bin/bash
# Automated schema migration for coc-discord-bot Postgres DB

set -e

# Find the cocstack-db Postgres container (fallback to any postgres container)
container=$(docker ps --format '{{.Names}}' | grep -E '^cocstack-db$' || true)
if [ -z "$container" ]; then
  container=$(docker ps --format '{{.Names}}' | grep postgres | head -n1)
fi
if [ -z "$container" ]; then
  echo "No running Postgres container found!"
  exit 1
fi


# Read DB credentials from repo shared env if available, else fallback to $HOME/config/.env
ENV_FILE="$(cd "$(dirname "$0")"/../../.. && pwd)/shared/config/.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -E '^POSTGRES_' "$ENV_FILE" | xargs)
else
  export $(grep -E '^POSTGRES_' "$HOME/config/.env" | xargs)
fi


if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
  echo "Missing DB credentials in $HOME/config/.env!"
  exit 1
fi

# Apply the schema as superuser to avoid role issues
APPLY_USER="postgres"
cat init_schema_postgres.sql | docker exec -i "$container" psql -U "$APPLY_USER" -d "$POSTGRES_DB"

echo "Schema migration complete!"
