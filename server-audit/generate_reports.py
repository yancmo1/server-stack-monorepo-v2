#!/usr/bin/env python3
import argparse
import csv
import os
import re
from pathlib import Path

RAW_FILES_HINT = {
    'ports_ss': 'ss -lntup output (listeners with PIDs)',
    'ports_lsof': 'lsof LISTEN sockets',
    'systemd_running': 'running systemd services',
    'docker_ps': 'docker ps listing',
    'docker_networks': 'docker networks',
    'nginx_T': 'nginx -T full config dump',
    'caddyfile': 'Caddyfile',
    'apache_S': 'apachectl -S output',
    'ufw_status': 'ufw status verbose',
    'iptables_rules': 'iptables -S or nft ruleset',
}

def anonymize(text: str) -> str:
    # Replace likely hostnames and emails with placeholders
    text = re.sub(r"[\w.-]+@[\w.-]+", "<redacted@email>", text)
    text = re.sub(r"\b([a-zA-Z0-9-]+\.)+(com|net|org|io|app|dev|co|me|ai|gg|xyz)\b", "<redacted.domain>", text)
    return text

def parse_ss_listeners(lines):
    entries = []
    # Example line: tcp LISTEN 0 511 0.0.0.0:80 0.0.0.0:* users:("nginx",pid=123,fd=6)
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith('Netid') or ln.startswith('State'):
            continue
        try:
            # Split preserving spaces within users
            parts = re.split(r"\s+", ln)
            if len(parts) < 5:
                continue
            proto = parts[0]
            local = parts[4]
            users = ln.split('users:')[-1] if 'users:' in ln else ''
            bind_ip, port = None, None
            if ':' in local:
                bind_ip, port = local.rsplit(':', 1)
            proc = None
            pid = None
            m = re.search(r'\("([^"\\]+)",pid=(\d+)', users)
            if m:
                proc = m.group(1)
                pid = m.group(2)
            entries.append({
                'proto': proto,
                'bind': bind_ip or local,
                'port': port or '',
                'process': proc or '',
                'pid': pid or '',
            })
        except Exception:
            continue
    return entries

def load_file(path: Path):
    if not path.exists():
        return []
    return path.read_text(errors='ignore').splitlines()

def main():
    ap = argparse.ArgumentParser(description='Generate server audit reports from raw data')
    ap.add_argument('--raw-dir', required=False, help='Path to raw data directory (default: server-audit/raw/latest)')
    args = ap.parse_args()

    base = Path('server-audit')
    raw_base = base / 'raw'
    if args.raw_dir:
        raw_dir = Path(args.raw_dir)
    else:
        latest_file = raw_base / 'latest'
        if latest_file.exists():
            raw_dir = Path(latest_file.read_text().strip())
        else:
            # fallback to the most recent timestamp dir
            dirs = sorted([p for p in raw_base.glob('*') if p.is_dir()], reverse=True)
            raw_dir = dirs[0] if dirs else None

    base.mkdir(parents=True, exist_ok=True)
    if not raw_dir or not raw_dir.exists():
        raise SystemExit(f"Raw directory not found. Provide --raw-dir (looked at {raw_base}).")

    # Load raw files
    ports_ss = load_file(raw_dir / 'ports_ss.txt')
    ports = parse_ss_listeners(ports_ss)

    # CSV output
    csv_path = base / 'ports.csv'
    with csv_path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['port','proto','bind','process','pid','unit','container','image','compose_file','notes'])
        w.writeheader()
        for e in ports:
            w.writerow({**e, 'unit':'', 'container':'', 'image':'', 'compose_file':'', 'notes':''})

    # PORTS.md
    md = []
    md.append('# Server Ports and Services')
    md.append('')
    md.append(f'Raw source: {raw_dir}')
    md.append('')
    md.append('## Listening Ports (from ss)')
    md.append('')
    if ports:
        md.append('| Port | Proto | Bind | Process | PID |')
        md.append('|-----:|:-----:|:-----|:--------|----:|')
        for e in sorted(ports, key=lambda x: (x['proto'], int(x['port'] or 0))):
            md.append(f"| {e['port']} | {e['proto']} | {e['bind']} | {e['process']} | {e['pid']} |")
    else:
        md.append('_No listening ports parsed; ensure ports_ss.txt was captured._')

    # Firewall summary
    ufw_lines = load_file(raw_dir / 'ufw_status.txt')
    ipt_lines = load_file(raw_dir / 'iptables_rules.txt')
    md.append('')
    md.append('## Firewall Summary')
    md.append('')
    if ufw_lines:
        md.append('### UFW (status excerpt)')
        md.append('')
        md.append('```')
        md.extend(ufw_lines[:80])
        md.append('```')
    if ipt_lines:
        md.append('### Packet Filter (iptables/nft excerpt)')
        md.append('')
        md.append('```')
        md.extend(ipt_lines[:120])
        md.append('```')

    # Reverse proxy configs excerpt
    nginx_lines = load_file(raw_dir / 'nginx_T.txt')
    caddy_lines = load_file(raw_dir / 'caddyfile.txt')
    apache_lines = load_file(raw_dir / 'apache_S.txt')
    def add_proxy_section(title, lines):
        if not lines:
            return
        md.append('')
        md.append(f'## {title} (excerpt)')
        md.append('')
        content = anonymize('\n'.join(lines))
        md.append('```')
        md.extend(content.splitlines()[:200])
        md.append('```')
    add_proxy_section('Nginx Config Dump', nginx_lines)
    add_proxy_section('Caddyfile', caddy_lines)
    add_proxy_section('Apache vhost map', apache_lines)

    (base / 'PORTS.md').write_text('\n'.join(md))

    # HARDENING.md (skeleton recommendations)
    hard = []
    hard.append('# Server Hardening Recommendations')
    hard.append('')
    hard.append('Prioritized actions:')
    hard.append('')
    hard.append('## High Priority')
    hard.append('- Default deny inbound; allow 22/tcp, 80/tcp, 443/tcp; restrict admin ports by IP')
    hard.append('- Terminate TLS at a single reverse proxy; backend apps bind to 127.0.0.1 or Docker networks only')
    hard.append('- SSH: keys only, disable root login, enable fail2ban; consider moving SSH to a non-default port')
    hard.append('')
    hard.append('## Medium Priority')
    hard.append('- Set up automatic security updates (unattended-upgrades) and regular apt maintenance')
    hard.append('- Standardize subdomains per app and document routing rules')
    hard.append('- Add monitoring (node_exporter + cAdvisor) and log retention policies')
    hard.append('')
    hard.append('## Low Priority')
    hard.append('- Backup strategy: config + compose files + DB dumps; document restore steps and test quarterly')
    hard.append('- Inventory: maintain APPS.md (app → URL → owner → repo → compose file → contact)')
    (base / 'HARDENING.md').write_text('\n'.join(hard))

    # Optional diagram placeholder
    diag = []
    diag.append('flowchart LR')
    diag.append('  Internet((Users)) --> RP[Reverse Proxy :443]')
    diag.append('  RP --> App1[App 1]')
    diag.append('  RP --> App2[App 2]')
    diag.append('  App1 --> DB[(Database)]')
    (base / 'diagram.mmd').write_text('\n'.join(diag))

    print(f"Generated: {base / 'PORTS.md'}")
    print(f"Generated: {base / 'ports.csv'}")
    print(f"Generated: {base / 'HARDENING.md'}")
    print(f"Generated: {base / 'diagram.mmd'}")

if __name__ == '__main__':
    main()
