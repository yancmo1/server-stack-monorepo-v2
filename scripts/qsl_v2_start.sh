#!/usr/bin/env bash
# Start qsl-auto-v2 connector and the legacy W5XY web GUI wired to it
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
QSL_V2_DIR="$ROOT_DIR/qsl-auto-v2"
GUI_DIR="$ROOT_DIR/apps/W5XY-QSL-CARD-CREATOR"

# Config
CONNECTOR_URL_DEFAULT="https://connector.yancmo.xyz"
GUI_PORT_DEFAULT="5553"

CONNECTOR_BASE_URL="${CONNECTOR_BASE_URL:-$CONNECTOR_URL_DEFAULT}"
CONNECTOR_TOKEN="${CONNECTOR_TOKEN:-}"
QSL_WEB_PORT="${QSL_WEB_PORT:-$GUI_PORT_DEFAULT}"

echo "==> Starting qsl-auto-v2 connector (Docker Compose)"
cd "$QSL_V2_DIR"

# Load token from .env if not provided
if [[ -z "$CONNECTOR_TOKEN" && -f .env ]]; then
  CONNECTOR_TOKEN=$(grep -E '^\s*CONNECTOR_TOKEN=' .env | sed -E 's/^.*=//') || true
fi
export CONNECTOR_TOKEN

# If a Syncthing folder is provided, include the override to mount it
if [[ -n "${SYNCTHING_LOG4OM_DIR:-}" && -f docker-compose.syncthing.yml ]]; then
  echo "==> Using Syncthing override (SYNCTHING_LOG4OM_DIR=${SYNCTHING_LOG4OM_DIR})"
  docker compose -f docker-compose.yml -f docker-compose.syncthing.yml up -d --build
else
  docker compose up -d --build
fi

echo "==> Waiting for connector health at $CONNECTOR_BASE_URL/"
ATTEMPTS=20
SLEEP_SECS=2
for ((i=1; i<=ATTEMPTS; i++)); do
  if curl -fsS "$CONNECTOR_BASE_URL/" >/dev/null; then
    echo "✅ Connector is healthy"
    break
  fi
  echo ".. not ready yet ($i/$ATTEMPTS), retrying in ${SLEEP_SECS}s"
  sleep "$SLEEP_SECS"
  if [[ $i -eq $ATTEMPTS ]]; then
    echo "⚠️  Connector did not report healthy in time. Continuing anyway."
  fi
done

echo "==> Starting legacy web GUI with connector integration"
cd "$GUI_DIR"

# Create venv if missing and install deps
if [[ ! -d .venv ]]; then
  echo "Creating Python venv..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install -r web_requirements.txt

echo "==> Running web_app.py on port ${QSL_WEB_PORT}"
export CONNECTOR_BASE_URL
export CONNECTOR_TOKEN
export QSL_WEB_PORT

# Detect if desired port is already in use
if lsof -nP -iTCP:"${QSL_WEB_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  EXISTING_PID=$(lsof -nP -iTCP:"${QSL_WEB_PORT}" -sTCP:LISTEN -t 2>/dev/null | head -n1 || true)
  if [[ -n "${QSL_FORCE_RESTART:-}" ]]; then
    echo "⚠️  Port ${QSL_WEB_PORT} is in use by PID ${EXISTING_PID}. Forcing restart (QSL_FORCE_RESTART=1)" >&2
    if [[ -n "$EXISTING_PID" ]]; then
      kill "$EXISTING_PID" || true
      sleep 1
      if lsof -nP -iTCP:"${QSL_WEB_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "... process still listening; sending SIGKILL" >&2
        kill -9 "$EXISTING_PID" || true
        sleep 1
      fi
    fi
  else
    if [[ -n "${QSL_AUTO_PORT:-}" ]]; then
      # Auto-pick next available port starting from requested
      PORT_CANDY=${QSL_WEB_PORT}
      for _ in $(seq 1 20); do
        if ! lsof -nP -iTCP:"${PORT_CANDY}" -sTCP:LISTEN >/dev/null 2>&1; then
          export QSL_WEB_PORT=${PORT_CANDY}
          echo "ℹ️  Port ${QSL_WEB_PORT} will be used (auto-picked)."
          break
        fi
        PORT_CANDY=$((PORT_CANDY+1))
      done
      # If still in use after loop, fall through to skip
    fi
    if lsof -nP -iTCP:"${QSL_WEB_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "✅ GUI already running on port ${QSL_WEB_PORT} (PID ${EXISTING_PID}). Skipping new launch."
      echo "    Tip: set QSL_FORCE_RESTART=1 to stop and relaunch, or QSL_AUTO_PORT=1 to auto-pick a new port."
      exit 0
    fi
  fi
fi

exec python web_app.py
