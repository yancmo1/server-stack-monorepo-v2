Server Inventory Audit

This folder contains a read-only collection script and a report generator to inventory an Ubuntu server: listening ports, services, containers, firewalls, and reverse proxy/TLS configs. No changes are made by these tools.

Quick start

1) Collect data on the server (over SSH)
   - Copy `collect_server_inventory.sh` to the target server (or view it here and run it directly).
   - Run it as a regular user. It will attempt read-only `sudo` for a few commands (firewall rules) if available.

   Example (run on the server):
   
   bash server-audit/collect_server_inventory.sh

   Outputs are saved to a timestamped directory under `${OUTPUT_DIR:-$PWD/server-audit/raw}/YYYYmmddTHHMMSSZ` by default. You can set `OUTPUT_DIR` to control the destination.

2) Bring raw data back to this workspace (if collected on a different machine)
   - Copy the timestamped folder into `server-audit/raw/` in this workspace.

3) Generate reports locally
   - Run the generator, pointing it at the raw folder:
   
   python3 server-audit/generate_reports.py --raw-dir server-audit/raw/<timestamp>

Artifacts

- server-audit/PORTS.md: Markdown inventory with tables and summaries
- server-audit/HARDENING.md: Prioritized, actionable security & hygiene plan
- server-audit/ports.csv: Flat CSV inventory
- server-audit/diagram.mmd: Optional Mermaid diagram (reverse proxy → apps → DBs)

Privacy note

Public hostnames and emails are anonymized in generated reports by default.
