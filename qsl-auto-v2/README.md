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
