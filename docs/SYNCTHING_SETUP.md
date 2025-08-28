# Syncthing Setup and Upgrade Guide (Windows, macOS, Ubuntu)

This guide standardizes Syncthing across your Windows desktop (Log4OM), this macOS dev machine, and the ubuntumac server.

## Goals
- Keep the Log4OM SQLite DB in sync across devices
- Make the qsl-auto-v2 connector read the same DB on each machine
- Use a simple, robust "just works" workflow (symlink in dev; env or symlink in prod)

---

## 1) Install or Upgrade Syncthing

### macOS
- Prefer Homebrew:
  - `brew install syncthing`
  - For upgrades later: `brew upgrade syncthing`
- Optional: Run as LaunchAgent so it starts at login:
  - `brew services start syncthing`
  - Manage with: `brew services list`
- Web UI: http://127.0.0.1:8384/

### Ubuntu (ubuntumac)
- Official repo (recommended):
  - `curl -s https://syncthing.net/release-key.txt | sudo gpg --dearmor -o /usr/share/keyrings/syncthing-archive-keyring.gpg`
  - `echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list`
  - `sudo apt-get update && sudo apt-get install -y syncthing`
- Service management (systemd):
  - Per-user: `loginctl enable-linger $USER` (optional if not always logged in)
  - `systemctl --user enable syncthing`
  - `systemctl --user start syncthing`
  - Logs: `journalctl --user -u syncthing -f`
- Web UI: http://127.0.0.1:8384/

### Windows (Log4OM machine)
- Download the installer from https://syncthing.net
- Install and launch Syncthing; it will open the Web UI at http://127.0.0.1:8384/
- For upgrades: download and reinstall, or use built-in auto-updater when prompted.

---

## 2) Link Devices (pairing)

You need to add devices to each other using their Device ID:
- Find your Device ID in the top-right menu of the Syncthing Web UI (Actions → Show ID)
- On each device, Add Remote Device and paste the other device's ID
- Give them friendly names (e.g., "Windows-Log4OM", "Mac-Dev", "UbuntuMac")
- Accept on the other side when prompted

Once devices are linked, they can share folders.

---

## 3) Share the Log4OM Folder

On the Windows machine (Log4OM source):
- Identify the Log4OM DB location and share the parent folder via Syncthing (Actions → Add Folder)
- Give it a Folder Label like `Log4OM` and Folder ID like `log4om`
- Path example (Windows): `C:\Users\<you>\Documents\Log4OM` (ensure the SQLite file exists inside)
- Share this folder to Mac-Dev and UbuntuMac

On macOS and Ubuntu, accept the folder share:
- Choose a local path, e.g.:
  - macOS: `~/Syncthing/Log4OM`
  - Ubuntu: `/srv/syncthing/Log4OM` (create parent with `sudo mkdir -p /srv/syncthing && sudo chown $USER:$USER /srv/syncthing`)
- Advanced tips:
  - Set Versioning to Staggered or Simple if you want recovery of deleted/changed files
  - Add `.stignore` rules to avoid temp or massive files. Example `.stignore`:
    ```
    # Exclude temp files
    *.tmp
    *.temp
    ~*
    # Exclude thumbnails/caches
    cache/
    thumbnails/
    ```

---

## 4) Wire into qsl-auto-v2

### macOS Dev (symlink workflow — "just works")
1. Ensure the folder sync landed, e.g., DB at `~/Syncthing/Log4OM/Log4OM.db`
2. From repo root:
   ```bash
   bash scripts/qsl_link_syncthing_db.sh "$HOME/Syncthing/Log4OM/Log4OM.db"
   ```
   This creates: `qsl-auto-v2/data/Log4OM.db -> ~/Syncthing/Log4OM/Log4OM.db`
3. Start from VS Code task: "📟 QSL v2: Start (GUI + Connector)"
   - Connector: https://connector.yancmo.xyz/
   - QSL: https://qsl.yancmo.xyz/

### macOS Alternative (env-based)
- If you prefer not to symlink:
  ```bash
  export SOURCE_DB_PATH="$HOME/Syncthing/Log4OM"
  # Or pin exact file
  # export SOURCE_DB_PATH="$HOME/Syncthing/Log4OM/Log4OM.db"
  ```
- Then start as usual. The connector resolves folders/files smartly.

### UbuntuMac (production-style)
- Choose one:
  - Symlink into `qsl-auto-v2/data` (mirrors dev):
    ```bash
    bash scripts/qsl_link_syncthing_db.sh "/srv/syncthing/Log4OM/Log4OM.db"
    ```
  - Or env-based:
    ```bash
    export SOURCE_DB_PATH="/srv/syncthing/Log4OM"
    ```
- Set a strong connector token:
  ```bash
  export CONNECTOR_TOKEN="<long-random-string>"
  ```
- Start connector+app under qsl-auto-v2:
  ```bash
  docker compose up -d --build
  # or use the start script if running from the monorepo
  ```
- Confirm:
  ```bash
  curl https://connector.yancmo.xyz/ | jq .
  ```

---

## 5) Maintenance & Upgrades
- macOS (Homebrew): `brew upgrade syncthing`
- Ubuntu: `sudo apt-get update && sudo apt-get install -y syncthing`
- Windows: use the in-app updater or reinstall from the website
- Monitor sync status in the Web UI (errors, out-of-sync files)

---

## 6) Safety Practices
- Treat the SQLite file as your source of truth; avoid concurrent writes from different programs
- The connector writes QSL updates to a sidecar table `qsl_status` — it doesn’t alter the original schema
- Consider enabling versioning in Syncthing for extra safety
- Ensure good backups on at least one device

---

## 7) Troubleshooting
- Folder out of sync: check ignore patterns, permissions, and that all devices are connected
- DB not found by connector: verify the symlink or `SOURCE_DB_PATH`, then check `curl https://connector.yancmo.xyz/`
- Permission issues on Ubuntu: ensure the syncthing folder is owned by the user running the connector
- Token errors: pass the correct `Authorization: Bearer <CONNECTOR_TOKEN>` header when calling protected endpoints

---

## 8) Production Deploy Checklist (ubuntumac)

1. Install/start Syncthing on ubuntumac (see section 1, or run `bash scripts/syncthing_install_ubuntu.sh`).
2. Link devices and accept the `Log4OM` folder to `/srv/syncthing/Log4OM`.
3. Choose wiring method:
  - Symlink: `bash scripts/qsl_link_syncthing_db.sh "/srv/syncthing/Log4OM/Log4OM.db"`
  - Env: `export SOURCE_DB_PATH="/srv/syncthing/Log4OM"`
4. Set a strong token: `export CONNECTOR_TOKEN="<long-random-string>"`
5. Start connector/app: `cd qsl-auto-v2 && docker compose up -d --build`
6. Verify: `curl https://connector.yancmo.xyz/ | jq .` (should report `db_exists: true`)
7. Optionally reverse proxy or firewall as needed; keep token secret.
