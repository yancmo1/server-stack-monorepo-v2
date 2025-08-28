# Backup Plan (MEGA.nz via rclone)

Goal
- Daily full coverage of system-critical paths; incremental, versioned backups for $HOME and app data.
- Keep MEGA.nz as the offsite remote.
- Fast, granular restores without giant zip archives.

Approach
- Use rclone with a MEGA remote (name it `mega`) and versioning via `--backup-dir` for home/app increments.
- Separate jobs:
  1) Home incremental: `rclone sync $HOME -> mega:server-backups/home/current` with `--backup-dir mega:server-backups/home/archive/<timestamp>`.
  2) System daily snapshot (selected roots): mirror `/etc`, `/srv`, `/opt`, `/var/lib/postgresql`, `/var/lib/docker/volumes` (and any data dirs) into dated dirs under `mega:server-backups/system/YYYY-MM-DD/`.
  3) Databases daily: dump system Postgres cluster(s) and Postgres containers to `/var/backups/postgres/YYYY-MM-DD/` then `rclone move` to `mega:server-backups/db/YYYY-MM-DD/`.
- Retention: prune old archives and snapshots on a schedule.

MEGA layout
- mega:server-backups/
  - home/
    - current/
    - archive/YYYY/MM/DDTHHMMSSZ/
  - system/
    - YYYY-MM-DD/etc/
    - YYYY-MM-DD/srv/
    - YYYY-MM-DD/opt/
    - YYYY-MM-DD/var-lib-postgresql/
    - YYYY-MM-DD/var-lib-docker-volumes/
  - db/
    - YYYY-MM-DD/system-postgres/
    - YYYY-MM-DD/docker-cocstack-db/
    - YYYY-MM-DD/docker-tracker-db/

Retention (suggested)
- Home archive: keep last 30 days of increments; keep 6 monthly snapshots.
- System snapshots: keep last 14 daily and 6 monthly.
- DB dumps: keep last 14 daily and 6 monthly.

Prereqs
- rclone installed and configured: `rclone config` with MEGA remote named `mega`.
- Sudo for reading some system dirs and running `pg_dumpall` on the local cluster.
- Docker CLI access for dumping Postgres containers.

How to deploy (after review/approval)
1) Fill in variables in scripts under `server-audit/backup/scripts/` (REMOTE, EXCLUDES, DB creds if needed).
2) Test scripts manually.
3) Install systemd units from `server-audit/backup/systemd/` and enable timers.

Restore quick reference
- Browse `mega:server-backups/home/archive/<timestamp>` for previous versions; latest files in `home/current/`.
- Pull specific dated system subfolders from `system/YYYY-MM-DD/`.
- Fetch the desired DB dump `.sql` from `db/YYYY-MM-DD/` and restore with `psql` or `pg_restore`.

Security
- Use MFA on MEGA.
- Ensure `~/.config/rclone/rclone.conf` is 600. Consider `rclone obscure` for secrets.

---
This is a plan and templates only. No changes are applied until you approve.
