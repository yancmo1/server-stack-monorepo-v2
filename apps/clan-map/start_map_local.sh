#!/bin/bash
# Start the clan-map Flask app locally and monitor its output
# Usage: ./start_map_local.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load .env from ~/config/.env
if [ -f "$HOME/config/.env" ]; then
    export $(grep -v '^#' "$HOME/config/.env" | xargs)
    echo "[INFO] Loaded environment variables from $HOME/config/.env (global config)"
else
    echo "[WARNING] $HOME/config/.env file not found."
fi

LOGFILE="map_local.log"
nohup python3 app.py > "$LOGFILE" 2>&1 &
MAP_PID=$!
echo "Clan map started with PID $MAP_PID. Logging to $LOGFILE."

echo "--- Monitoring map output (Ctrl+C to stop monitoring, app keeps running) ---"
tail -f "$LOGFILE"
