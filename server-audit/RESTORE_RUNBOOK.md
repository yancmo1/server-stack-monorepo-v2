# Restore Runbook (MEGA.nz)

Scope: file-level restores (home/system), database restores (PostgreSQL), and application redeploy steps.

Home restore
1) Identify timestamp in mega:server-backups/home/archive/ or use latest in home/current.
2) Pull files locally with rclone:
   - rclone copy mega:server-backups/home/archive/2025.../path/to/dir/ ~/restore/path/
3) Place restored files back to desired location; verify ownership and permissions.

System config restore
1) Browse mega:server-backups/system/YYYY-MM-DD/etc/ and fetch needed files.
2) Apply cautiously; prefer diff and targeted merges.

Database restore
- System Postgres cluster:
  1) Download dump file (system_postgres_all.sql) for the date.
  2) psql -U postgres -f system_postgres_all.sql
- Dockerized Postgres containers:
  1) Download container-specific dump (e.g., cocstack-db_all.sql).
  2) docker exec -i <container> psql -U postgres -d <db> < dump.sql (or create DBs first).

Validation
- Start dependent services/app containers and validate application behavior.
- Keep a log of what was restored and why.

Security
- Sanitize secrets when sharing restore logs.
