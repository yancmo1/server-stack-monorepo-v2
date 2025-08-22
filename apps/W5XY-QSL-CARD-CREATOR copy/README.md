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

## Notes
- All desktop app and test scripts are now in `backup_files/`.
- This structure is optimized for web deployment and maintainability.
- Runs as part of the server stack on port 5553.
