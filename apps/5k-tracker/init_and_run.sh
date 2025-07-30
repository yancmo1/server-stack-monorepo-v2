#!/bin/bash
set -e

# Wait for Postgres
echo "Waiting for Postgres to be available..."
/app/wait-for-it.sh -h db -p 5432 -t 30 -- echo "Postgres is up!"

# Initialize DB and create default users only if DB is empty
echo "Initializing database and creating default users (if needed)..."
python -c "
from app import app, init_db, create_default_users, add_test_races, User
with app.app_context():
    init_db()
    # Only create default users if no users exist
    if User.query.count() == 0:
        print('No users found, creating default users...')
        create_default_users()
        add_test_races()
    else:
        print('Users already exist, skipping default user creation.')
"

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:5554 --workers 2 --timeout 60 app:app
