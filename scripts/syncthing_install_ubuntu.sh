#!/usr/bin/env bash
# Install and start Syncthing on Ubuntu from the official repository.
# Usage: bash scripts/syncthing_install_ubuntu.sh
set -euo pipefail

if [[ $(id -u) -eq 0 ]]; then
  echo "Please run this as a regular user (not root). The script will use sudo where needed." >&2
fi

# Add Syncthing apt repo and key
curl -fsSL https://syncthing.net/release-key.txt | sudo gpg --dearmor -o /usr/share/keyrings/syncthing-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list >/dev/null

# Install
sudo apt-get update -y
sudo apt-get install -y syncthing

# Enable lingering so user services survive logout (optional but recommended on servers)
systemctl --user daemon-reload || true
loginctl enable-linger "$USER" || true

# Enable and start Syncthing as user service
systemctl --user enable syncthing
systemctl --user start syncthing

# Show status hint
sleep 1
echo "Syncthing started. Open http://127.0.0.1:8384/ on the server (or tunnel the port) to finish setup."
echo "Logs: journalctl --user -u syncthing -f"
