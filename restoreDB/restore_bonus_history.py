import psycopg2
import re

# --- CONFIGURE THESE VARIABLES ---
PG_HOST = "db"
PG_PORT = 5432
PG_DB = "cocstack"
PG_USER = "cocuser"
PG_PASS = "yourpassword"
SQL_FILE = "/home/yancmo/apps/server-stack-monorepo-v2/restoreDB/restore_bonus_history.sql"
# ---------------------------------

def parse_sql_inserts(sql_path):
    with open(sql_path, "r") as f:
        sql = f.read()
    # Find all tuples inside VALUES (...)
    matches = re.findall(r"\(([^)]+)\)", sql)
    records = []
    for match in matches:
        # Split on commas not inside quotes
        parts = re.findall(r"(?:'[^']*'|[^,]+)", match)
        # Remove quotes and whitespace
        row = [p.strip().strip("'") for p in parts]
        records.append(row)
    return records

def main():
    records = parse_sql_inserts(SQL_FILE)
    print(f"Found {len(records)} records to insert.")

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )
    cur = conn.cursor()
    for row in records:
        try:
            cur.execute("""
                INSERT INTO bonus_history (player_name, player_tag, awarded_date, awarded_by, bonus_type, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, row)
        except Exception as e:
            print(f"Error inserting row {row}: {e}")
    conn.commit()
    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()