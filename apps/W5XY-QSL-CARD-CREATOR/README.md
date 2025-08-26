# QSL Card Creator Web App

This directory contains a Dockerized Flask web application for QSL card management. All dependencies and environment setup are handled via Docker for easy deployment and testing.

## Quick Start with Docker

### 1. Build the Docker Image
```sh
docker build -t qsl-card-creator-web .
```

### 2. Run the Container (with persistent database and template)
Replace paths with your actual system paths.

```sh
# For Mac with Syncthing database setup:
docker run -d --name qsl-card-creator -p 5001:5001 \
  -v "/Users/yancyshepherd/SyncthingFolders/Log4OM-Database/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
  qsl-card-creator

# For generic setup (replace with your actual paths):
docker run -d --name qsl-card-creator -p 5001:5001 \
  -v "/absolute/path/to/Log4OM db.SQLite":/app/"Log4OM db.SQLite" \
  -v "/absolute/path/to/W5XY QSL Card Python TEMPLATE.pdf":/app/"W5XY QSL Card Python TEMPLATE.pdf" \
  -e CONNECTOR_BASE_URL="http://host.docker.internal:5557" \
  -e CONNECTOR_TOKEN="please-change-me" \
  qsl-card-creator
```

- The app will be available at [http://localhost:5001](http://localhost:5001)
- Data will persist because the database and template are mounted from your host.

### 3. Development Tips
- Edit your code and rebuild the image to test changes.
- Use Docker volumes to keep your data safe and persistent.

## Files
- `Dockerfile` — Defines the container build process.
- `.dockerignore` — Excludes unnecessary files from the image.
- `web_app.py`, `web_requirements.txt`, `static/`, `templates/` — Main app code.

## More
- For advanced Docker usage, see [Docker documentation](https://docs.docker.com/).
- For troubleshooting, check container logs with:
  ```sh
  docker logs <container_id>
  ```

## Structure

- `web_app.py` — Main Flask web application.
- `web_requirements.txt` — Python dependencies for the web app.
- `static/` — Static assets (CSS, JS, images) for the web app.
- `templates/` — Jinja2 HTML templates for the web app.
- `backup_files/` — Archived legacy code, extra scripts, and documentation.

## Usage

1. Install dependencies:
   ```bash
   pip install -r web_requirements.txt
   ```
2. Run the web app:
   ```bash
   python web_app.py
   ```

## HamQTH integration (email + biography)

This app uses the official HamQTH XML API for callsign details and biography text.

- Configure credentials via environment variables (preferred):
  - `HAMQTH_USERNAME` — your HamQTH username (usually your callsign)
  - `HAMQTH_PASSWORD` — your HamQTH password

These are loaded from the shared .env used across the stack:

- Edit: `shared/config/.env`
- Example entries:
  ```ini
  HAMQTH_USERNAME=W5XY
  HAMQTH_PASSWORD=super-secret-password
  ```

If environment variables are missing, the app will look in `qsl_settings.json` for `hamqth_username` and `hamqth_password` (these can also be set via the Email modal’s “Save & Test Credentials” button).

### What the UI does
- On Create QSL, enter a callsign and click “Lookup” (or wait ~1.5s after typing).
- The app will:
  - Fill the Email field if available from HamQTH
  - Show a collapsible “HamQTH Bio” panel when a biography is present
  - If credentials are missing/invalid, you’ll see guidance and a browser fallback link

### Quick test
1) Set your credentials in `shared/config/.env` and restart the app
2) Open: http://localhost:5001/create
3) Enter a real callsign and press “Lookup”
4) Expect: email auto-filled (if present) and a Bio panel displayed when available

API endpoints for debugging:
- `GET /api/hamqth/<callsign>` — structured data; includes `bio` when available
- `GET /api/hamqth-bio/<callsign>` — only biography text

### Using the qsl-auto-v2 Connector (optional but recommended)

This GUI can use the new qsl-auto-v2 connector for robust, read-only access to your Log4OM database and to record QSL sent status in a safe sidecar table.

- Environment variables:
  - `CONNECTOR_BASE_URL` (default `http://localhost:5557`)
  - `CONNECTOR_TOKEN` (default `please-change-me`)

When configured, the QSOs list page will prefer fetching via the connector; updates to QSL sent are attempted via the connector first, then fall back to direct DB updates if the connector is unavailable.

Connector API docs live at: `http://localhost:5557/docs`

## Notes
- All desktop app and test scripts are now in `backup_files/`.
- This structure is optimized for web deployment and maintainability.
- Runs as part of the server stack on port 5553.
