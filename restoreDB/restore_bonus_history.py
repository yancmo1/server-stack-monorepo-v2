import os
import sys
import argparse
import psycopg2
import psycopg2.extras
import re
from datetime import datetime

# Read connection details from environment with sensible defaults
PG_HOST_ENV = os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "localhost"))
PG_PORT_ENV = int(os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432")))
PG_DB_ENV = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "cocstack"))
PG_USER_ENV = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "cocuser"))
PG_PASS_ENV = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", ""))

DEFAULT_SQL_FILE = "/home/yancmo/apps/server-stack-monorepo-v2/restoreDB/restore_bonus_history.sql"


def parse_sql_inserts(sql_path):
    with open(sql_path, "r") as f:
        sql = f.read()
    
    # Find VALUES section and extract only data tuples (not column names)
    values_match = re.search(r'VALUES\s+(.*)', sql, re.DOTALL | re.IGNORECASE)
    if not values_match:
        return []
    
    values_text = values_match.group(1)
    # Extract tuples that start with quoted strings (data, not column names)
    tuples = re.findall(r"\(([^()]*?'[^']*'[^()]*)\)", values_text, flags=re.S)
    
    records = []
    for t in tuples:
        # Split on commas not inside single quotes
        parts = re.findall(r"(?:'[^']*'|[^,]+)", t)
        row = [p.strip().strip("'") for p in parts]
        # Expect exactly 6 columns and first column shouldn't be a SQL keyword
        if len(row) == 6 and not row[0].lower() in ['player_name', 'awarded_date']:
            records.append(row)
    return records


def try_connect(host, port, db, user, password):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            row = cur.fetchone()
            ver = row[0] if row else "unknown"
        return conn, ver
    except Exception as e:
        return None, str(e)


def ensure_bonus_history_table(conn):
    create_sql = """
    CREATE TABLE IF NOT EXISTS bonus_history (
        id SERIAL PRIMARY KEY,
        player_name TEXT NOT NULL,
        player_tag TEXT,
        awarded_date DATE NOT NULL,
        awarded_by TEXT,
        bonus_type TEXT,
        notes TEXT
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_sql)
        conn.commit()


def insert_records(conn, records, dry_run=False, batch_size=200):
    if dry_run:
        print(f"[DRY-RUN] Would insert {len(records)} records into bonus_history")
        return 0

    inserted = 0
    sql = (
        "INSERT INTO bonus_history (player_name, player_tag, awarded_date, awarded_by, bonus_type, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
    )
    with conn.cursor() as cur:
        for i in range(0, len(records), batch_size):
            chunk = records[i:i+batch_size]
            psycopg2.extras.execute_batch(cur, sql, chunk, page_size=len(chunk))
            inserted += len(chunk)
        conn.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Restore bonus_history data into PostgreSQL")
    parser.add_argument("--file", default=DEFAULT_SQL_FILE, help="Path to restore_bonus_history.sql")
    parser.add_argument("--host", default=PG_HOST_ENV, help="Postgres host (default from env)")
    parser.add_argument("--port", type=int, default=PG_PORT_ENV, help="Postgres port (default from env)")
    parser.add_argument("--db", default=PG_DB_ENV, help="Database name (default from env)")
    parser.add_argument("--user", default=PG_USER_ENV, help="Database user (default from env)")
    parser.add_argument("--password", default=PG_PASS_ENV, help="Database password (default from env)")
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate only; do not insert")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: SQL file not found: {args.file}")
        sys.exit(1)

    records = parse_sql_inserts(args.file)
    print(f"Found {len(records)} records to process from: {args.file}")

    # Build fallback host list
    hosts_to_try = [args.host]
    if args.host == "db":
        hosts_to_try.append("localhost")
    elif args.host == "localhost":
        hosts_to_try.append("127.0.0.1")

    conn = None
    for host in hosts_to_try:
        print(f"Attempting connection to postgres at {host}:{args.port} db={args.db} user={args.user}")
        conn_obj, info = try_connect(host, args.port, args.db, args.user, args.password)
        if conn_obj:
            print(f"Connected OK. Server: {info}")
            conn = conn_obj
            break
        else:
            print(f"Connection failed: {info}")

    if not conn:
        print("Failed to connect to PostgreSQL. Check host/port/credentials and try again.")
        sys.exit(2)

    try:
        ensure_bonus_history_table(conn)
        inserted = insert_records(conn, records, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry-run complete. No changes made.")
        else:
            print(f"Insert complete. Attempted inserts: {len(records)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()