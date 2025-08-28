#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../apps/cruise-price-check"

# Create venv if missing
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install -r requirements.txt >/dev/null

export PYTHONUNBUFFERED=1
export CRUISE_DB_PATH=${CRUISE_DB_PATH:-$(pwd)/cruise_prices.db}

python web_interface.py
