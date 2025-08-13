#!/usr/bin/env python3
"""
Improved Carnival Cruise Price Tracker
======================================

A more robust price tracking system that:
1. Directly monitors your specific cruise booking URL
2. Tracks price changes from your baseline price
3. Sends alerts when prices drop
4. Stores price history for analysis
5. Handles errors gracefully with retry logic

Your cruise details:
- Ship: JB (Galveston departure)
- Route: 8-day Western Caribbean 
- Date: November 8, 2025
- Guests: 2
- Target: Interior stateroom
- Baseline price: $1,462 (Early Saver Sale)
"""

import requests
import json
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json as _json_for_discord
from carnival_scraper import CarnivalScraper, build_carnival_booking_url

# Setup logging
log_file = '/app/logs/cruise_price_tracker.log' if os.path.exists('/app/logs') else 'cruise_price_tracker.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CruisePriceTracker:
    def __init__(self, config_file: str = 'cruise_config.json'):
        """Initialize the cruise price tracker with your specific booking details"""
        self.config = self.load_config(config_file)
        self.init_database()
        # Lazy-created scraper instance (Playwright/Selenium/Requests)
        self._scraper_instance: Optional[CarnivalScraper] = None
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "cruise_details": {
                "ship_code": "JB",
                "departure_port": "GAL",  # Galveston
                "itinerary_code": "WE8",  # Western Caribbean 8-day
                "duration_days": 7,
                "sailing_id": "17415",
                "sail_date": "11082025",  # November 8, 2025
                "region_code": "CW",  # Caribbean West
                "num_guests": 2,
                "is_military": "N",
                "is_over_55": "N",
                "is_past_guest": "Y",
                "country": "US",
                "currency": "USD",
                "locality": "1"
            },
            "target_price": {
                "baseline_price": 1462,  # Your current price
                "alert_threshold": 50,   # Alert if price drops by $50+
                "rate_codes": ["PJS", "PUG"],  # Early Saver Sale, Standard
                "meta_codes": ["IS", "OB"]     # Interior, Oceanview Balcony
            },
            "monitoring": {
                "check_interval_hours": 6,
                "max_retries": 3,
                "timeout_seconds": 30
            },
            "storage": {
                "save_snapshots": False,
                "snapshot_dir": "snapshots",
                "retain_days": 7
            },
            "alerts": {
                "email_enabled": False,
                "email_smtp_server": "smtp.gmail.com",
                "email_smtp_port": 587,
                "email_from": "",
                "email_to": "",
                "email_password": ""
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except FileNotFoundError:
            logger.info(f"Config file {config_file} not found, using defaults")
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        return default_config
    
    def init_database(self):
        """Initialize SQLite database for price history"""
        # Use /app/data path when in container, current directory otherwise
        self.db_path = '/app/data/cruise_prices.db' if os.path.exists('/app/data') else 'cruise_prices.db'
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    price REAL,
                    rate_code TEXT,
                    meta_code TEXT,
                    availability TEXT,
                    url TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    currency TEXT,
                    engine TEXT,
                    raw_price_text TEXT,
                    price_hash TEXT,
                    debug_json TEXT
                )
            ''')
            conn.commit()
            # Migration: ensure columns exist (older versions may lack them)
            cursor.execute("PRAGMA table_info(price_history)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            new_cols = {
                'currency': 'TEXT',
                'engine': 'TEXT',
                'raw_price_text': 'TEXT',
                'price_hash': 'TEXT',
                'debug_json': 'TEXT'
            }
            for col, col_type in new_cols.items():
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE price_history ADD COLUMN {col} {col_type}")
            conn.commit()
    
    def build_booking_url(self, rate_code: str = "PJS", meta_code: str = "IS") -> str:
        """Build the direct booking URL for your specific cruise"""
        cruise = self.config["cruise_details"]
        target = self.config["target_price"]
        
        base_url = "https://www.carnival.com/booking/room-type"
        params = {
            "embkCode": cruise["departure_port"],
            "itinCode": cruise["itinerary_code"], 
            "durDays": cruise["duration_days"],
            "shipCode": cruise["ship_code"],
            "subRegionCode": cruise["region_code"],
            "sailingID": cruise["sailing_id"],
            "sailDate": cruise["sail_date"],
            "numGuests": cruise["num_guests"],
            "isMilitary": cruise["is_military"],
            "isOver55": cruise["is_over_55"],
            "isPastGuest": cruise["is_past_guest"],
            "stateCode": "",
            "evsel": "",
            "locality": cruise["locality"],
            "currency": cruise["currency"],
            "qbPrice": target["baseline_price"],
            "qbMetaCode": meta_code,
            "qbRateCode": rate_code,
            "country": cruise["country"]
        }
        
        # Build URL with parameters
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    def get_price_with_selenium(self, url: str) -> Tuple[Optional[float], Optional[str], bool]:
        """Backward-compatible method name; now delegates to modular scraper."""
        result = self._scrape_price(url, 'PJS', 'IS')
        price = result.get('price')  # type: ignore
        error = result.get('error')  # type: ignore
        success = bool(result.get('success'))
        return price, error, success
    
    def _extract_price_from_page(self, *args, **kwargs):  # legacy compatibility stub
        return None

    # ---------- New modular scraping integration ----------
    def _get_scraper(self) -> CarnivalScraper:
        if self._scraper_instance is None:
            self._scraper_instance = CarnivalScraper(self.config)
        return self._scraper_instance

    def _scrape_price(self, url: str, rate_code: str, meta_code: str) -> Dict:
        scraper = self._get_scraper()
        return scraper.get_price(url, rate_code, meta_code)

    def _maybe_save_snapshot(self, html: Optional[str], rate_code: str, meta_code: str, price: Optional[float]):
        if not html:
            return None
        storage_cfg = self.config.get('storage', {})
        if not storage_cfg.get('save_snapshots'):
            return None
        directory = storage_cfg.get('snapshot_dir', 'snapshots')
        base_dir = '/app/data' if os.path.exists('/app/data') else '.'
        snap_root = os.path.join(base_dir, directory)
        os.makedirs(snap_root, exist_ok=True)
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        price_part = f"{int(price)}" if price else 'na'
        filename = f"{ts}_{rate_code}_{meta_code}_{price_part}.html.gz"
        path = os.path.join(snap_root, filename)
        import gzip
        with gzip.open(path, 'wt', encoding='utf-8') as f:
            f.write(html)
        # Cleanup old snapshots
        retain_days = int(storage_cfg.get('retain_days', 7))
        cutoff = datetime.utcnow().timestamp() - retain_days * 86400
        try:
            for fname in os.listdir(snap_root):
                fpath = os.path.join(snap_root, fname)
                if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
        except Exception:
            pass
        return path

    def _compute_price_hash(self, rate_code: str, meta_code: str, price: Optional[float]) -> Optional[str]:
        if price is None:
            return None
        import hashlib
        date_bucket = datetime.utcnow().strftime('%Y-%m-%d')
        raw = f"{rate_code}|{meta_code}|{price}|{date_bucket}"
        return hashlib.sha256(raw.encode()).hexdigest()
    
    def check_price(self) -> Dict:
        """Check current price and return results"""
        results = []
        
        # Check both rate codes
        for rate_code in self.config["target_price"]["rate_codes"]:
            for meta_code in self.config["target_price"]["meta_codes"]:
                url = build_carnival_booking_url(self.config, rate_code, meta_code)
                final_result = None
                for attempt in range(self.config["monitoring"]["max_retries"]):
                    logger.info(f"Checking {rate_code}/{meta_code} - attempt {attempt + 1}")
                    scrape_result = self._scrape_price(url, rate_code, meta_code)
                    snapshot_path = self._maybe_save_snapshot(scrape_result.get('html'), rate_code, meta_code, scrape_result.get('price'))
                    price_hash = self._compute_price_hash(rate_code, meta_code, scrape_result.get('price'))
                    result = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'rate_code': rate_code,
                        'meta_code': meta_code,
                        'price': scrape_result.get('price'),
                        'success': scrape_result.get('success'),
                        'error': scrape_result.get('error'),
                        'url': url,
                        'attempt': attempt + 1,
                        'engine': scrape_result.get('engine'),
                        'debug': scrape_result.get('debug', []),
                        'raw_price_text': scrape_result.get('raw_price_text'),
                        'currency': scrape_result.get('currency'),
                        'price_hash': price_hash,
                        'snapshot_path': snapshot_path
                    }
                    self._store_price_check(result)
                    final_result = result
                    if result['success']:
                        results.append(result)
                        break
                    if attempt < self.config["monitoring"]["max_retries"] - 1:
                        time.sleep(5)
                if final_result and not final_result['success']:
                    results.append(final_result)
        
        # Check for price drops and send alerts
        self._check_price_alerts(results)
        
        return {
            'check_time': datetime.now().isoformat(),
            'results': results,
            'baseline_price': self.config["target_price"]["baseline_price"]
        }
    
    def _store_price_check(self, result: Dict):
        """Store price check result in database (with new extended columns)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Insert while gracefully handling older schema (omit missing columns)
            cursor.execute("PRAGMA table_info(price_history)")
            cols = {row[1] for row in cursor.fetchall()}
            base_cols = [
                ('price', result.get('price')),
                ('rate_code', result.get('rate_code')),
                ('meta_code', result.get('meta_code')),
                ('url', result.get('url')),
                ('success', result.get('success')),
                ('error_message', result.get('error'))
            ]
            extra_cols = [
                ('currency', result.get('currency')),
                ('engine', result.get('engine')),
                ('raw_price_text', result.get('raw_price_text')),
                ('price_hash', result.get('price_hash')),
                ('debug_json', json.dumps(result.get('debug', [])) if result.get('debug') else None)
            ]
            insert_cols = [name for name, _ in base_cols + extra_cols if name in cols]
            insert_vals = [val for name, val in base_cols + extra_cols if name in cols]
            placeholders = ','.join(['?'] * len(insert_cols))
            col_string = ','.join(insert_cols)
            cursor.execute(f"INSERT INTO price_history ({col_string}) VALUES ({placeholders})", insert_vals)
            conn.commit()
    
    def _check_price_alerts(self, results: List[Dict]):
        """Check for price drops and send alerts"""
        baseline = self.config["target_price"]["baseline_price"]
        threshold = self.config["target_price"]["alert_threshold"]
        
        for result in results:
            if result['success'] and result['price']:
                price_drop = baseline - result['price']
                
                if price_drop >= threshold:
                    message = (
                        f"🚨 CRUISE PRICE DROP ALERT! 🚨\n\n"
                        f"Your cruise price has dropped by ${price_drop:.0f}!\n\n"
                        f"Original price: ${baseline}\n"
                        f"New price: ${result['price']}\n"
                        f"Rate: {result['rate_code']}/{result['meta_code']}\n"
                        f"Savings: ${price_drop:.0f}\n\n"
                        f"Book now: {result['url']}"
                    )
                    
                    logger.warning(f"PRICE DROP ALERT: ${baseline} -> ${result['price']} (saved ${price_drop})")
                    
                    if self.config["alerts"]["email_enabled"]:
                        self._send_email_alert(message)
                    # Optional Discord webhook
                    webhook = os.environ.get('DISCORD_WEBHOOK_URL') or self.config['alerts'].get('discord_webhook')
                    if webhook:
                        self._send_discord_alert(webhook, result, baseline, price_drop)

    def _send_discord_alert(self, webhook: str, result: Dict, baseline: float, price_drop: float):
        try:
            import requests
            payload = {
                "username": "Cruise Price Tracker",
                "embeds": [
                    {
                        "title": "🚨 Cruise Price Drop",
                        "description": f"Price dropped by ${price_drop:.0f}",
                        "color": 15258703,
                        "fields": [
                            {"name": "Original", "value": f"${baseline}", "inline": True},
                            {"name": "New", "value": f"${result['price']}", "inline": True},
                            {"name": "Rate/Meta", "value": f"{result['rate_code']}/{result['meta_code']}", "inline": True},
                            {"name": "Engine", "value": str(result.get('engine')), "inline": True},
                            {"name": "Hash", "value": result.get('price_hash','-') or '-', "inline": False}
                        ],
                        "url": result['url'],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            }
            requests.post(webhook, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    def _send_email_alert(self, message: str):
        """Send email alert for price drops"""
        try:
            config = self.config["alerts"]
            
            msg = MIMEMultipart()
            msg['From'] = config["email_from"] 
            msg['To'] = config["email_to"]
            msg['Subject'] = "🚨 Carnival Cruise Price Drop Alert!"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(config["email_smtp_server"], config["email_smtp_port"])
            server.starttls()
            server.login(config["email_from"], config["email_password"])
            
            server.send_message(msg)
            server.quit()
            
            logger.info("Price drop alert email sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def get_price_history(self, days: int = 30) -> List[Dict]:
        """Get price history from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, price, rate_code, meta_code, success, error_message
                FROM price_history 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days))
            
            rows = cursor.fetchall()
            return [
                {
                    'timestamp': row[0],
                    'price': row[1], 
                    'rate_code': row[2],
                    'meta_code': row[3],
                    'success': bool(row[4]),
                    'error': row[5]
                }
                for row in rows
            ]
    
    def run_monitoring_loop(self):
        """Run continuous price monitoring"""
        logger.info("Starting cruise price monitoring...")
        logger.info(f"Baseline price: ${self.config['target_price']['baseline_price']}")
        logger.info(f"Alert threshold: ${self.config['target_price']['alert_threshold']}")
        logger.info(f"Check interval: {self.config['monitoring']['check_interval_hours']} hours")
        
        while True:
            try:
                results = self.check_price()
                logger.info(f"Price check completed: {len(results['results'])} checks")
                
                # Wait for next check
                sleep_seconds = self.config["monitoring"]["check_interval_hours"] * 3600
                logger.info(f"Sleeping for {self.config['monitoring']['check_interval_hours']} hours...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Carnival Cruise Price Tracker')
    parser.add_argument('--check', action='store_true', help='Run single price check')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--history', type=int, default=7, help='Show price history (days)')
    parser.add_argument('--summary', action='store_true', help='Show aggregated daily min/max/latest per rate/meta')
    parser.add_argument('--config', default='cruise_config.json', help='Config file path')
    
    args = parser.parse_args()
    
    tracker = CruisePriceTracker(args.config)
    
    if args.check:
        results = tracker.check_price()
        print(json.dumps(results, indent=2))
    elif args.monitor:
        tracker.run_monitoring_loop()
    elif args.history and not args.summary:
        history = tracker.get_price_history(args.history)
        print(json.dumps(history, indent=2))
    elif args.summary:
        summary = summarize_history(tracker, args.history)
        print(json.dumps(summary, indent=2))
    else:
        print("Use --check, --monitor, or --history. See --help for details.")

def summarize_history(tracker: 'CruisePriceTracker', days: int = 7):
    """Aggregate daily min/max/latest per (rate_code, meta_code)."""
    with sqlite3.connect(tracker.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(price_history)")
        cols = {r[1] for r in cursor.fetchall()}
        has_hash = 'price_hash' in cols
        cursor.execute(f"""
            SELECT date(timestamp) as day, rate_code, meta_code, price, success, price_hash
            FROM price_history
            WHERE timestamp >= datetime('now', '-{days} days') AND success = 1 AND price IS NOT NULL
            ORDER BY timestamp ASC
        """)
        data = {}
        for day, rate, meta, price, success, phash in cursor.fetchall():
            key = (day, rate, meta)
            if key not in data:
                data[key] = {
                    'day': day,
                    'rate_code': rate,
                    'meta_code': meta,
                    'min_price': price,
                    'max_price': price,
                    'first_price': price,
                    'last_price': price,
                    'observations': 1,
                    'distinct_hashes': set([phash]) if has_hash and phash else None
                }
            else:
                d = data[key]
                d['min_price'] = min(d['min_price'], price)
                d['max_price'] = max(d['max_price'], price)
                d['last_price'] = price
                d['observations'] += 1
                if d['distinct_hashes'] is not None and phash:
                    d['distinct_hashes'].add(phash)
        # Format output
        out = []
        for key, d in sorted(data.items()):
            out.append({
                'day': d['day'],
                'rate_code': d['rate_code'],
                'meta_code': d['meta_code'],
                'min': d['min_price'],
                'max': d['max_price'],
                'first': d['first_price'],
                'last': d['last_price'],
                'observations': d['observations'],
                'distinct_price_hashes': len(d['distinct_hashes']) if d['distinct_hashes'] is not None else None
            })
        return {
            'days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': out
        }

if __name__ == '__main__':
    main()