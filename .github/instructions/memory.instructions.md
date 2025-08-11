---
applyTo: '**'
---

# User Preferences (compact)

- deploy: clan-map and coc-discord-bot must be deployed/restarted on server (ubuntumac) only; do not run locally.

## Session Summary (2025-08-11)
- clan-map fixed and redesigned; bulk writes replaced with targeted DB updates (`update_player_in_db`) to prevent pin wipes; submit/admin now regenerate map/snapshot.
- Added admin repair route to re-geocode missing pins; UI moved to dark theme with `base.html` and simplified templates.
- New server-only no-cache deploy for clan-map (`scripts/deploy_clan_map_nocache.sh`) and VS Code task; `deploy/deploy.sh` supports `bot-nocache`.
- Env separation clarified: tracker DB vs cocstack DB; local `.env` corrected; server env needs alignment; set `CLANMAP_ADMIN_PASSWORD` in production.
- Next: set strong admin password on server, run clan-map no-cache deploy, verify pins/admin login, align `SERVER.env`, then continue bot CWL cadence and /who_is improvements.
