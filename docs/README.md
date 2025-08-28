
# YANCY Monorepo

Welcome to your unified workspace for all personal apps, bots, and web projects.

## Folder Structure

- `apps/` — All major apps and services (Discord bot, webapps, trackers, etc.)
- `shared/` — Shared configs, SSL certs, templates, scripts
- `deploy/` — Deployment files (Docker, systemd, nginx)
- `docs/` — Documentation and guides
- `archive/` — Legacy and backup files
- `.env.example` — Example environment variables for all apps
- `.gitignore` — Git ignore rules for all projects
- `.vscode/` — VS Code workspace settings

## Workflow

1. Each app is independent, but can share resources (e.g., Postgres DB) via configs in `shared/`.
2. Use Docker Compose in `deploy/` to run services locally or in production.
3. Store all documentation in `docs/` for easy reference.
4. Archive old or backup files in `archive/` to keep the workspace clean.

## Getting Started

1. See `docs/SETUP-GUIDE.md` for setup instructions.
2. Configure your `.env` files for each app as needed.
3. Use the provided scripts and Docker Compose files for local development and deployment.

## Database Sharing

To share data between apps (e.g., Discord bot and webapp), ensure both use the same Postgres connection settings from `.env` or `shared/config/`.

## Questions?

Refer to `docs/TROUBLESHOOTING_GUIDE.md` for common issues and solutions.

# QSL Card Creator (v2 connector + legacy GUI)

- Dev start: VS Code task "📟 QSL v2: Start (GUI + Connector)"
- Connector API: https://connector.yancmo.xyz/ (Swagger at /docs)
- GUI: https://qsl.yancmo.xyz/
- Syncthing integration and setup guide: see `docs/SYNCTHING_SETUP.md`

# Local Development Secrets Setup

For local development, secrets are managed in a single `.env` file at the repo root. Symlinks are created in each subproject so both can access the same secrets. Start scripts in each project will automatically load these secrets.

**How to use:**
1. Fill out `.env` in the repo root with your secret values (see `.env.example`).
2. Use the provided start scripts:
   - `coc-discord-bot/start_bot_local.sh`
   - `clan-map/start_map_local.sh`
3. Secrets are loaded automatically for both projects.

**Never commit `.env` to git.**

