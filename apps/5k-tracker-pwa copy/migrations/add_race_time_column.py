from app import db
from sqlalchemy import text

def upgrade():
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE race ADD COLUMN race_time VARCHAR(20);'))

def downgrade():
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE race DROP COLUMN race_time;'))

if __name__ == '__main__':
    upgrade()
    print('Migration complete: race_time column added.')
