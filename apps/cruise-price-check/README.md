# Cruise Price Checker (Refactored)

Modern, modular Carnival cruise price tracker focused on robustness, observability, and future extensibility.

## Key Improvements

- Multi‑engine scraping (Playwright → Selenium → Requests fallback) via `CarnivalScraper`
- Direct booking URL generation (no brittle multi‑click navigation dependence)
- Structured extraction: regex + semantic class scan + JSON sniffing
- SQLite price history with automatic schema migration
- Extended fields stored: `currency`, `engine`, `raw_price_text`, `price_hash`, `debug_json`
- Optional HTML snapshot archiving (gzip) with retention policy
- Deterministic daily price hash for de‑dup / change detection
- Improved web API (`web_interface.py`) exposing monitoring + history
- Config auto-merging with safe defaults (`cruise_config.json`)
- Unit tests for scraper fallback logic (`test_carnival_scraper.py`)

## Folder Highlights

| File | Purpose |
|------|---------|
| `improved_price_tracker.py` | Orchestrates checks, persistence, alerts |
| `carnival_scraper.py` | Engine abstraction + extraction heuristics |
| `web_interface.py` | Flask UI / API endpoints |
| `cruise_config.json` | User config (merged with defaults) |
| `test_carnival_scraper.py` | Core scraper logic tests |

## Configuration

`cruise_config.json` (user editable) – new `storage` section:

```json
"storage": {
  "save_snapshots": false,
  "snapshot_dir": "snapshots",
  "retain_days": 7
}
```

Other notable keys:
- `target_price.rate_codes` / `meta_codes` – permutations to monitor
- `target_price.baseline_price` – used for drop threshold comparisons and qbPrice param
- `monitoring.max_retries` – per combination retry attempts

If the file is missing, a default one is generated automatically.

## Running a One‑Off Check (CLI)

```bash
python improved_price_tracker.py --check
```

Or via repository helper script (from repo root):
```bash
bash scripts/run_cruise_tracker_dev.sh
```

Output example:

```json
{
  "check_time": "2025-08-12T15:55:21.987Z",
  "baseline_price": 1462,
  "results": [
    {
      "timestamp": "2025-08-12T15:55:21.055000",
      "rate_code": "PJS",
      "meta_code": "IS",
      "price": 1462.0,
      "success": true,
      "engine": "requests",
      "raw_price_text": "1462",
      "price_hash": "<sha256>",
      "debug": [ {"source": "regex_url_qbPrice", "value": 1462.0} ]
    }
  ]
}
```

## Web Interface

Expose endpoints (example port may differ):

| Endpoint | Description |
|----------|-------------|
| `/` | Basic dashboard HTML |
| `/api/status` | Current monitoring state + last check timestamp |
| `/api/check-price` (POST) | Trigger immediate check (returns extended fields) |
| `/api/history/<days>` | Historical results (includes `engine`, `raw_price_text`, `price_hash` if available) |
| `/health` | Generic health probe |

Start (typical):
```bash
python web_interface.py
```

## Database Schema (price_history)

Columns: `id, timestamp, price, rate_code, meta_code, availability (legacy placeholder), url, success, error_message, currency, engine, raw_price_text, price_hash, debug_json`.
Missing columns are added automatically on startup (idempotent migrations).

## Snapshots

When `storage.save_snapshots` = true, sanitized HTML is stored as gzip under `snapshot_dir` (default `snapshots/`; path relocates to `/app/data` in container). Retention cleanup runs opportunistically during saves.

Guidelines:
- Leave off for normal monitoring (reduces I/O and disk usage)
- Enable temporarily while debugging price extraction failures
- Adjust `retain_days` for longer investigations; lower it in constrained environments

## Scraper Engine Selection

1. Playwright (if installed & `prefer_playwright` true internally)
2. Selenium (if available)
3. Raw HTTP GET (Requests) – resilient baseline

Each engine returns a uniform dict: `{success, price, engine, raw_price_text, debug, html?, error}`.

## Testing

`pytest` tests added for core fallback & variant extraction scenarios:
```bash
pytest -k carnival_scraper -q
```

Optional (install Playwright browser runtime for dynamic engine):
```bash
python -m playwright install chromium
```

Run full suite (example path):
```bash
pytest apps/cruise-price-check -q
```

## Alerts

Email alerts fire when `(baseline_price - current_price) >= alert_threshold`. Provide SMTP creds in config & set `email_enabled` true.

## Extending

- Add other cruise lines: create new scraper module & integrate via strategy map in tracker
- Alternate notification channels (Discord/Slack) – hook into `_check_price_alerts`
- Rich analytics: compute deltas & moving averages with a separate reporting module

## Troubleshooting

| Issue | Hint |
|-------|------|
| No price detected | Inspect `debug` array; enable snapshots for HTML review |
| Always fallback to requests | Ensure Playwright/Selenium installed & importable |
| Duplicate rows same day | Hash includes date; multiple identical checks are expected (use price_hash aggregation) |
| Email not sent | Verify `email_enabled` and SMTP credentials / app password |

## Roadmap Ideas

- Tenacity-based retry backoff
- Concurrent rate/meta fetches
- Multi-cruise portfolio support
- Structured HTML diffing between snapshots

## Optional CI (GitHub Actions)

```yaml
name: cruise-price-check
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r apps/cruise-price-check/requirements.txt
      - run: pytest apps/cruise-price-check -k carnival_scraper -q
```

---
Refactor focus: reliability, clarity, and future extensibility while preserving straightforward usage.
\n+## Docker Development & Operations
\n+Container workflow (mirrors production browser dependencies):\n+\n+```bash
# from repo root
./scripts/cruise_dev.sh up       # start service
./scripts/cruise_dev.sh rebuild  # rebuild image & recreate
./scripts/cruise_dev.sh logs     # follow logs
./scripts/cruise_dev.sh check    # one-off price check inside container
./scripts/cruise_dev.sh summary  # 7 day summary
./scripts/cruise_dev.sh down     # stop container
```
\n+VS Code tasks titled "Cruise Docker" wrap these commands for click-to-run convenience.\n+\n+Prefer Docker when you need: reproducible headless Chromium, CI/server parity, isolated deps.\n+Prefer local Python when rapidly iterating scraper logic, running unit tests, or debugging with interactive tools.\n+