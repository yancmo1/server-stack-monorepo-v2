QSL Auto V2

Purpose: Generate and email QSL postcards from QSOs, with safe idempotent processing and sync-back to the source DB via a connector.

Key features
- Idempotent pipeline with local SQLite state store (no duplicate sends)
- Dry-run by default: generate PDFs and logs, no email sent unless DRY_RUN=false
- Structured logging and end-of-run report
- Batch processing with retries and rate limiting
- Optional FastAPI connector for remote SQLite access with token auth
- Dockerized for one-command local dev

Quick start (dry-run)
- Create .env from .env.example and adjust paths if needed
- Install dependencies: pip install -r requirements.txt
- Run: python -m app.cli run --limit 3
- PDFs will appear in output/{YYYY}/{MM}/{CALLSIGN}/ and a run report will print at the end

Docker (optional)
- docker compose up --build
- Tokens and output are mounted under ./data

See docs/README.md for details.

Using Syncthing for the Log4OM database
---------------------------------------

If your Log4OM database lives on another machine and you sync it via Syncthing to this Mac, the connector can read it without any DB server.

Two easy options:

1) Point SOURCE_DB_PATH to the synced file (recommended)

- Have Syncthing sync the folder containing your Log4OM SQLite file to a path like `~/Syncthing/Log4OM/Log4OM.db`.
- Set `SOURCE_DB_PATH` to either the folder or the exact file path:
	- If set to a folder, the connector searches common filenames: `Log4OM.db`, `Log4OM db.SQLite`, `Log4OM.db3`.
	- If set to a file, that exact path is used.

Examples:

```bash
# Use an exact file
export SOURCE_DB_PATH="$HOME/Syncthing/Log4OM/Log4OM.db"

# Or point at the folder to auto-detect common names
export SOURCE_DB_PATH="$HOME/Syncthing/Log4OM"

# Start from the repo root
bash scripts/qsl_v2_start.sh
```

2) Symlink the synced file into qsl-auto-v2/data (convenient defaults)

The connector compose mounts `./data` at `/data` and, by default, looks for `/data/Log4OM.db`. You can create a symlink so the defaults “just work”:

```bash
bash scripts/qsl_link_syncthing_db.sh "$HOME/Syncthing/Log4OM/Log4OM.db"
```

This will create or refresh `qsl-auto-v2/data/Log4OM.db -> ~/Syncthing/Log4OM/Log4OM.db`.

Notes:
- Consider a `.stignore` in your Syncthing folder to exclude temporary files.
- The connector doesn’t alter the source schema; it writes QSL updates to a sidecar table `qsl_status` in the same SQLite file.
