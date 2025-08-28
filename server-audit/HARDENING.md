# Server Hardening Recommendations

Prioritized actions:

## High Priority
- Default deny inbound; allow 22/tcp, 80/tcp, 443/tcp; restrict admin ports by IP
- Terminate TLS at a single reverse proxy; backend apps bind to 127.0.0.1 or Docker networks only
- SSH: keys only, disable root login, enable fail2ban; consider moving SSH to a non-default port

## Medium Priority
- Set up automatic security updates (unattended-upgrades) and regular apt maintenance
- Standardize subdomains per app and document routing rules
- Add monitoring (node_exporter + cAdvisor) and log retention policies

## Low Priority
- Backup strategy: config + compose files + DB dumps; document restore steps and test quarterly
- Inventory: maintain APPS.md (app → URL → owner → repo → compose file → contact)