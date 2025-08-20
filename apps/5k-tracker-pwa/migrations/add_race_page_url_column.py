#!/usr/bin/env python3
"""
Migration script to add race_page_url column to the races table
"""
import os
import sys

# Add parent directory to Python path so we can import from app.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import app, db, Race

def add_race_page_url_column():
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('race')]
            
            if 'race_page_url' not in columns:
                print("Adding race_page_url column to race table...")
                db.engine.execute(db.text('ALTER TABLE race ADD COLUMN race_page_url TEXT'))
                print("Successfully added race_page_url column!")
            else:
                print("Column race_page_url already exists in race table.")
                
    except Exception as e:
        print(f"Error adding column: {e}")
        raise

if __name__ == "__main__":
    add_race_page_url_column()