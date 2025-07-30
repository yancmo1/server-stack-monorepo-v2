#!/bin/bash
set -e

# Wait for Postgres
echo "Waiting for Postgres to be available..."
/app/wait-for-it.sh -h db -p 5432 -t 30 -- echo "Postgres is up!"

# Initialize DB and create default users
echo "Initializing database and creating default users..."
python -c "from app import app, init_db, create_default_users, add_test_races; init_db(); create_default_users(); add_test_races()"

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:5554 --workers 2 --timeout 60 app:app
