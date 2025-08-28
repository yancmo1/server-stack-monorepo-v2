#!/bin/sh
set -e

# Optional: rerun pipeline every N seconds. If 0 or unset, run once and exit.
: "${APP_LOOP_SECONDS:=0}"
: "${LIMIT:=5}"

if [ "$APP_LOOP_SECONDS" -gt 0 ] 2>/dev/null; then
  echo "[start.sh] Looping: running pipeline every ${APP_LOOP_SECONDS}s (DRY_RUN=${DRY_RUN:-true}, LIMIT=${LIMIT})"
  while true; do
    python -m app.cli run --limit "${LIMIT}" || true
    sleep "${APP_LOOP_SECONDS}"
  done
else
  echo "[start.sh] Single run: executing pipeline once (DRY_RUN=${DRY_RUN:-true}, LIMIT=${LIMIT})"
  exec python -m app.cli run --limit "${LIMIT}"
fi
