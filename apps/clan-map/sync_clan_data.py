#!/usr/bin/env python3
"""
Sync script to update clan_data.json with latest player information from the Discord bot database (now Postgres)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime

# Database configuration - Postgres connection using environment variables
POSTGRES_DB = os.getenv("POSTGRES_DB", "cocstack")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cocuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourpassword")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

CLAN_DATA_PATH = 'clan_data.json'

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
    """Load existing clan data"""
    try:
        with open(CLAN_DATA_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_clan_data(data):
    """Save clan data"""
    with open(CLAN_DATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def sync_from_bot_db():
    """Sync player data from bot database to clan_data.json"""
    conn = get_bot_db_connection()
    if not conn:
        print("Failed to connect to Postgres database")
        return False
    # Load existing clan data
    clan_data = load_clan_data()
    existing_players = {player['name'].lower(): player for player in clan_data}
    cursor = conn.cursor()
    cursor.execute('SELECT name, tag, role FROM players WHERE inactive = 0')
    bot_players = cursor.fetchall()
    updated_count = 0
    added_count = 0
    for row in bot_players:
        name = row[0]
        tag = row[1]
        role = row[2]
        player_key = name.lower()
        if player_key in existing_players:
            player = existing_players[player_key]
            old_role = player.get('role', '')
            if old_role != role:
                player['role'] = role or 'Member'
                player['tag'] = tag
                player['updated_at'] = datetime.now().isoformat()
                updated_count += 1
                print(f"Updated {name}: role changed from '{old_role}' to '{role}'")
        else:
            new_player = {
                'name': name,
                'location': 'Unknown',
                'latitude': None,
                'longitude': None,
                'role': role or 'Member',
                'tag': tag,
                'favorite_troop': '',
                'updated_at': datetime.now().isoformat()
            }
            clan_data.append(new_player)
            added_count += 1
            print(f"Added new player: {name} ({role})")
    conn.close()
    save_clan_data(clan_data)
    print(f"\nSync complete!")
    print(f"- Players updated: {updated_count}")
    print(f"- Players added: {added_count}")
    print(f"- Total players: {len(clan_data)}")
    return True

def list_players():
    """List all players and their status"""
    clan_data = load_clan_data()
    
    print(f"\nClan Members ({len(clan_data)} total):")
    print("-" * 60)
    
    located = 0
    by_role = {}
    
    for player in sorted(clan_data, key=lambda x: x['name']):
        name = player['name']
        role = player.get('role', 'Member')
        location = player.get('location', 'Unknown')
        has_coords = player.get('latitude') is not None
        
        if has_coords:
            located += 1
            status = "\u2705 Located"
        else:
            status = "\u274c Unknown"
        
        by_role[role] = by_role.get(role, 0) + 1
        
        print(f"{name:20} | {role:10} | {location:20} | {status}")
    
    print("-" * 60)
    print(f"Located: {located}/{len(clan_data)} ({located/len(clan_data)*100:.1f}%)")
    print("\nBy Role:")
    for role, count in sorted(by_role.items()):
        print(f"  {role}: {count}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "sync":
            sync_from_bot_db()
        elif command == "list":
            list_players()
        else:
            print("Usage: python3 sync_clan_data.py [sync|list]")
    else:
        print("Clan Data Sync Tool")
        print("==================")
        print("Commands:")
        print("  sync  - Sync player data from bot database")
        print("  list  - List all players and their status")
        print("\nUsage: python3 sync_clan_data.py [command]")
