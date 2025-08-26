#!/usr/bin/env bash
# Symlink a Syncthing-synced Log4OM SQLite DB into qsl-auto-v2/data/Log4OM.db
# Usage: qsl_link_syncthing_db.sh /path/to/Log4OM.db
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/Log4OM.db" >&2
  exit 1
fi

SRC_PATH="$1"
if [[ ! -f "$SRC_PATH" ]]; then
  echo "Error: Source file not found: $SRC_PATH" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$ROOT_DIR/qsl-auto-v2/data"
DEST_PATH="$DEST_DIR/Log4OM.db"

mkdir -p "$DEST_DIR"

# Remove existing file/symlink if present
if [[ -e "$DEST_PATH" || -L "$DEST_PATH" ]]; then
  rm -f "$DEST_PATH"
fi

ln -s "$SRC_PATH" "$DEST_PATH"

echo "Symlink created: $DEST_PATH -> $SRC_PATH"
