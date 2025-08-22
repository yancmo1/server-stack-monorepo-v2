Audit Report - Existing QSL Project (apps/W5XY-QSL-CARD-CREATOR)

Inventory
- web_app.py (~2650 lines): Flask app with PDF generation (ReportLab+PyPDF2), Gmail draft creation, HAMQTH lookup, DB access helpers
- Dockerfile, Dockerfile.arm: Python 3.11 slim with poppler, PIL, PDF deps
- requirements files: Flask, PyPDF2, reportlab, pdf2image, Google API libs, requests, Pillow, lxml, python-dotenv
- Templates and static assets for web UI
- qsl_settings.json: stores paths, HAMQTH creds, feature flags
- gmail_credentials.json and gmail_token.pickle present in repo (risk)

Data flow
- Reads QSOs directly from Log4OM SQLite (local path or Syncthing mount)
- Generates PDFs by overlay on template; offers preview via Poppler
- Email: creates Gmail drafts via API or compose URL; sometimes marks DB QSL status
- Upload/download DB to/from PC or network path via file copy

Security posture (risks)
- Secrets in repo: gmail_credentials.json and token file committed
- .env path hardcoded: load_dotenv from shared path
- Flask secret defaulted to static value
- Extensive debug logging including names and possibly emails (PII)
- Direct SQLite writes without strict field allowlist; no auditing

Reliability/maintainability
- Monolithic file; mixed UI, DB, email, PDF logic
- Weak idempotency — may re-send/draft without stable keys
- No tests; no structured logging/metrics
- Poppler dependency for preview; ReportLab template positioning brittle

Docker
- Reasonable base, installs build-essential and poppler-utils; images may be heavier than needed

Conclusion
- Functionality present but security and architecture need modernization. Proceed with V2 modular rewrite.
