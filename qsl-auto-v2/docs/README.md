QSL Auto V2 - Developer Guide

Setup
- python -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt
- cp .env.example .env and adjust values

Run (dry-run)
- python -m app.cli run --limit 3

Connector (optional)
- uvicorn connector.main:app --reload --port 8081
- Provide SOURCE_DB_PATH env var pointing to the SQLite file on the remote host

Docker
- docker compose up --build

Troubleshooting
- Missing system libs for WeasyPrint: install cairo, pango, gdk-pixbuf
- Gmail auth: ensure credentials.json is mounted at GOOGLE_CLIENT_SECRET_PATH, token saved to GOOGLE_TOKEN_PATH
