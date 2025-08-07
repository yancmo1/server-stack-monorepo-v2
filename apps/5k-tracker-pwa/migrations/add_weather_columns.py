"""
Migration script to add start_weather and finish_weather columns to race table.
"""
from sqlalchemy import text

def upgrade(connection):
    connection.execute(text('ALTER TABLE race ADD COLUMN start_weather VARCHAR(100);'))
    connection.execute(text('ALTER TABLE race ADD COLUMN finish_weather VARCHAR(100);'))

def downgrade(connection):
    connection.execute(text('ALTER TABLE race DROP COLUMN start_weather;'))
    connection.execute(text('ALTER TABLE race DROP COLUMN finish_weather;'))
