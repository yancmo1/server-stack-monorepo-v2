Migration Notes (V1 → V2)

Major changes
- Introduced Typer CLI and modular pipeline with Pydantic validation
- Rendering uses WeasyPrint (HTML/CSS) with embedded fonts; ReportLab deprecated for layout
- Gmail via Gmail API with OAuth (dry-run default avoids sending)
- Remote DB writes use optional connector microservice; fallback via manual export/import documented

Env mapping
- DRY_RUN (default true) replaces ad-hoc toggles
- CONNECTOR_BASE_URL, CONNECTOR_TOKEN for remote access
- GOOGLE_CLIENT_SECRET_PATH, GOOGLE_TOKEN_PATH for Gmail OAuth
- OUTPUT_DIR and STATE_DB control artifacts and idempotency store

Rollback
- Original app remains under apps/W5XY-QSL-CARD-CREATOR (unchanged)
- V2 is isolated in qsl-auto-v2. Stop containers and revert to V1 if needed
