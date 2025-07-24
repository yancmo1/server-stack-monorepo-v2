#!/bin/bash
# Automated schema migration for coc-discord-bot Postgres DB

set -e

# Find the running Postgres container
container=$(docker ps --format '{{.Names}}' | grep postgres)
if [ -z "$container" ]; then
  echo "No running Postgres container found!"
  exit 1
fi

# Read DB credentials from .env
export $(grep -E '^POSTGRES_' .env | xargs)

if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
  echo "Missing DB credentials in .env!"
  exit 1
fi

# Apply the schema
cat init_schema_postgres.sql | docker exec -i "$container" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "Schema migration complete!"
