Deploying the Connector on the Remote Host

Prereqs
- Python 3.11
- Access to the Log4OM SQLite database path

Steps
1) Copy the folder `qsl-auto-v2/connector` to the remote host
2) Create a virtualenv and install deps:
   python -m venv .venv && source .venv/bin/activate
   pip install fastapi uvicorn pydantic
3) Run the service:
   SOURCE_DB_PATH="/absolute/path/Log4OM db.SQLite" CONNECTOR_TOKEN="<token>" uvicorn main:app --host 0.0.0.0 --port 8081
4) Firewall: allow inbound from your IP only; consider reverse proxy with HTTPS

API
- GET /qsos?limit=50&since=ISO8601
- POST /qsos/{id}/status { qsl_sent_flag, qsl_sent_at, email_message_id, postcard_ref }

Security
- Bearer token via CONNECTOR_TOKEN env
- Optional IP allowlist at network layer
- HTTPS recommended

Fallback
- If connector not possible, export pending updates to a CSV/JSON and run an import script on the remote PC.
