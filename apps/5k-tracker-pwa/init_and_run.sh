#!/bin/bash
set -e

# Wait for Postgres
echo "Waiting for Postgres to be available..."
bash /app/wait-for-it.sh -h db -p 5432 -t 30 -- echo "Postgres is up!"

# Initialize DB and create default users only if DB is empty
echo "Initializing database and ensuring admin login works (dev)..."
python -c "
from os import environ
from app import app, init_db, create_default_users, User, db
with app.app_context():
    init_db()
    # Ensure required schema migrations are applied (dev-friendly check)
    try:
        import sqlalchemy as sa
        insp = sa.inspect(db.engine)
        cols = {c['name'] for c in insp.get_columns('race')}
        missing = []
        if 'start_weather' not in cols:
            missing.append('start_weather')
        if 'finish_weather' not in cols:
            missing.append('finish_weather')
        if missing:
            from sqlalchemy import text
            print('Applying dev schema migration for race columns:', ', '.join(missing))
            with db.engine.connect() as conn:
                if 'start_weather' in missing:
                    conn.execute(text('ALTER TABLE race ADD COLUMN start_weather VARCHAR(100);'))
                if 'finish_weather' in missing:
                    conn.execute(text('ALTER TABLE race ADD COLUMN finish_weather VARCHAR(100);'))
                conn.commit()
            print('Schema migration complete.')
    except Exception as e:
        print('Non-fatal: schema check/migration failed:', e)
    # Ensure an admin user exists. If none, create or fix it explicitly (independent of other users)
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        try:
            print('Admin user not found; ensuring default users and creating admin@example.com...')
            # Try default seeding if DB is empty; safe no-op if not
            create_default_users()
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                # Explicitly create admin if still missing
                admin = User(
                    username='admin@example.com',
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print('Admin user created explicitly.')
        except Exception as e:
            db.session.rollback()
            print('Error while creating admin user:', e)
    # In development, reset admin password to a known value and enforce admin flag
    if environ.get('FLASK_ENV') == 'development' or environ.get('FLASK_DEBUG') == '1':
        pwd = environ.get('ADMIN_DEFAULT_PASSWORD', 'test123')
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            try:
                admin.set_password(pwd)
                admin.is_admin = True
                db.session.add(admin)
                db.session.commit()
                print('Admin password set for development environment.')
            except Exception as e:
                db.session.rollback()
                print('Failed to set admin password in development:', e)
        else:
            print('Warning: admin@example.com still not present after initialization.')
    else:
        print('Production environment detected; not resetting admin password.')
"

# Start Gunicorn (enable auto-reload in development)
CMD=(gunicorn --bind 0.0.0.0:5555 --workers 2 --timeout 60 app:app)
if [ "${FLASK_ENV}" = "development" ] || [ "${GUNICORN_RELOAD}" = "1" ]; then
    echo "Starting Gunicorn in --reload mode (development)"
    CMD=(gunicorn --reload --bind 0.0.0.0:5555 --workers 2 --timeout 60 app:app)
fi
exec "${CMD[@]}"
