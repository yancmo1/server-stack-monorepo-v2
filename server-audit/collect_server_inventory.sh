#!/usr/bin/env bash
set -euo pipefail

# Read-only server inventory collection
# Collects: ports, processes, services, containers, firewalls, web configs, TLS cert presence, cron
# Outputs to: ${OUTPUT_DIR:-$PWD/server-audit/raw}/<timestamp>

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BASE_DIR="${OUTPUT_DIR:-$PWD/server-audit/raw}"
OUT_DIR="$BASE_DIR/$TS"
mkdir -p "$OUT_DIR"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }
run() { local name="$1"; shift; log "Run: $*"; { "$@"; } >"$OUT_DIR/$name.txt" 2>&1 || true; }
run_sudo() { local name="$1"; shift; if command -v sudo >/dev/null 2>&1; then run "$name" sudo "$@"; else run "$name" "$@"; fi }

log "Writing outputs to $OUT_DIR"

# Basic system info
run sys_os_release cat /etc/os-release
run sys_uname uname -a
run sys_uptime uptime
run sys_df df -hT
run sys_mem free -m

# Processes and ports
run ports_ss ss -lntup
run ports_lsof bash -lc "command -v lsof >/dev/null 2>&1 && lsof -i -P -n | grep LISTEN || true"
run ps_top ps aux --sort=-%cpu

# Systemd services
run systemd_running systemctl list-units --type=service --state=running
run systemd_all systemctl list-unit-files --type=service
run systemd_timers systemctl list-timers --all

# Packages of interest
run packages_grep dpkg -l
run packages_services dpkg -l | grep -E 'nginx|apache|caddy|traefik|postgres|mysql|mariadb|redis|fail2ban|ufw|docker|podman|certbot|letsencrypt' || true

# Docker/Podman
run docker_ps bash -lc "command -v docker >/dev/null 2>&1 && docker ps --format '{{.ID}};{{.Names}};{{.Ports}};{{.Image}}' || true"
run docker_networks bash -lc "command -v docker >/dev/null 2>&1 && docker network ls || true"
if command -v docker >/dev/null 2>&1; then
  while read -r net; do
    [ -z "$net" ] && continue
    run "docker_network_inspect_${net}" docker network inspect "$net"
  done < <(docker network ls --format '{{.Name}}' | grep -vE 'bridge|host|none' || true)
  run docker_compose_find bash -lc "sudo find / -maxdepth 5 -type f -name 'docker-compose*.y*ml' 2>/dev/null || true"
fi

# Web servers / reverse proxies
run nginx_T bash -lc "command -v nginx >/dev/null 2>&1 && nginx -T 2>&1 || true"
run nginx_sites ls -la /etc/nginx/sites-enabled 2>/dev/null
run caddyfile cat /etc/caddy/Caddyfile 2>/dev/null
run apache_S bash -lc "command -v apachectl >/dev/null 2>&1 && apachectl -S 2>&1 || true"
run traefik_static cat /etc/traefik/traefik.yml 2>/dev/null
run traefik_dynamic ls -la /etc/traefik 2>/dev/null

# Firewalls & networking
run_sudo ufw_status ufw status verbose
run_sudo iptables_rules bash -lc "iptables -S 2>/dev/null || nft list ruleset 2>/dev/null || true"
run ip_a ip -o addr show
run ip_r ip route

# TLS certificates (names only)
run letsencrypt_dirs bash -lc "ls -1 /etc/letsencrypt/live 2>/dev/null || true"

# Databases / caches
run postgres_ver bash -lc "command -v psql >/dev/null 2>&1 && psql --version || true"
run mysql_ver bash -lc "command -v mysql >/dev/null 2>&1 && mysql --version || true"
run redis_ver bash -lc "command -v redis-server >/dev/null 2>&1 && redis-server --version 2>/dev/null || true"

# Mega.nz / rclone presence
run mega_proc bash -lc "ps aux | grep -iE 'mega(cmd|sync|put|backup)' | grep -v grep || true"
run mega_conf ls -la ~/.megaCMD ~/.config/MEGAcmd /root/.megaCMD /root/.config/MEGAcmd 2>/dev/null
run rclone_conf bash -lc "command -v rclone >/dev/null 2>&1 && rclone config file || true"

# Cron jobs
run crontab_user bash -lc "crontab -l 2>/dev/null || true"
run_sudo cron_system ls -la /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly /etc/crontab
run_sudo cron_grep bash -lc "grep -RIE --line-number '(mega|rclone|backup|pg_dump|restic|borg|rsync)' /etc/cron.* /etc/crontab /var/spool/cron 2>/dev/null || true"

log "Collection complete: $OUT_DIR"
echo "$OUT_DIR" >"$BASE_DIR/latest"
