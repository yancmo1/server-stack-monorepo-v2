#!/usr/bin/env python3
"""
Script to sync clan members from clan_data.json to the bot's Postgres database
This will populate the database with real clan members and their roles
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

CLAN_DATA_PATH = 'clan_data.json'
# Use environment variables for DB connection
POSTGRES_DB = os.getenv("POSTGRES_DB", "cocstack")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cocuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourpassword")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

def get_bot_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Postgres database: {e}")
        return None

def load_clan_data():
    """Load clan data from JSON file"""
    try:
        with open(CLAN_DATA_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {CLAN_DATA_PATH} not found")
        return []

def sync_to_bot_db():
    """Sync clan members to bot database"""
    clan_data = load_clan_data()
    
    if not clan_data:
        print("No clan data found to sync")
        return
    
    conn = get_bot_db_connection()
    
    if not conn:
        print("Failed to connect to Postgres database")
        return
    
    cursor = conn.cursor()
    
    # Clear test data first
    cursor.execute("DELETE FROM players WHERE name LIKE 'Test%'")
    print("Cleared test data from database")
    
    # Insert/update real clan members
    for member in clan_data:
        name = member['name']
        role = member.get('role', 'Member')
        location = member.get('location', 'Unknown')
        latitude = member.get('latitude')
        longitude = member.get('longitude')
        favorite_troop = member.get('favorite_troop')
        updated_at = member.get('updated_at', member.get('updated'))
        
        # Check if player exists
        cursor.execute("SELECT id FROM players WHERE name ILIKE %s", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing player
            cursor.execute("""
                UPDATE players SET 
                    role = %s, location = %s, latitude = %s, longitude = %s, 
                    favorite_troop = %s, location_updated = %s
                WHERE name ILIKE %s
            """, (role, location, latitude, longitude, favorite_troop, updated_at, name))
            print(f"Updated {name} ({role})")
        else:
            # Insert new player
            join_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO players 
                (name, role, location, latitude, longitude, favorite_troop, 
                 location_updated, join_date, bonus_eligibility, bonus_count, missed_attacks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, 0)
            """, (name, role, location, latitude, longitude, favorite_troop, updated_at, join_date))
            print(f"Added {name} ({role})")
    
    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully synced {len(clan_data)} clan members to bot database!")

if __name__ == "__main__":
    sync_to_bot_db()
