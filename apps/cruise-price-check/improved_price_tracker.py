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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

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
                # Merge with defaults
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except FileNotFoundError:
            logger.info(f"Config file {config_file} not found, using defaults")
            # Create default config file
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
                    error_message TEXT
                )
            ''')
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
        """
        Use Selenium to get the current price from Carnival's booking page
        Returns: (price, error_message, success)
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1280,720')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Additional options for container environment
        if os.getenv('CHROME_BIN'):
            chrome_options.binary_location = os.getenv('CHROME_BIN')
        
        # Container-specific options
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-popup-blocking')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.config["monitoring"]["timeout_seconds"])
            
            logger.info(f"Checking price at: {url}")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Check if we're on an error page
            if "error" in driver.current_url.lower() or "not found" in driver.page_source.lower():
                return None, "Booking page returned error or not found", False
            
            # Multiple strategies to find price
            price = self._extract_price_from_page(driver)
            
            if price:
                logger.info(f"Successfully extracted price: ${price}")
                return price, None, True
            else:
                return None, "Could not find price on page", False
                
        except TimeoutException:
            return None, "Page load timeout", False
        except WebDriverException as e:
            return None, f"WebDriver error: {str(e)}", False
        except Exception as e:
            return None, f"Unexpected error: {str(e)}", False
        finally:
            if driver:
                driver.quit()
    
    def _extract_price_from_page(self, driver) -> Optional[float]:
        """Extract price from the booking page using multiple strategies"""
        
        # Strategy 1: Look for prices in URL parameters (most reliable)
        current_url = driver.current_url
        price_match = re.search(r'qbPrice=(\d+)', current_url)
        if price_match:
            return float(price_match.group(1))
        
        # Strategy 2: Check JavaScript variables
        js_checks = [
            "return window.bookingData && window.bookingData.qbPrice;",
            "return window.utag_data && window.utag_data.cruise_price;",
            "return document.querySelector('[data-qb-price]')?.getAttribute('data-qb-price');",
        ]
        
        for js_check in js_checks:
            try:
                result = driver.execute_script(js_check)
                if result and isinstance(result, (int, float, str)):
                    price_val = float(str(result).replace('$', '').replace(',', ''))
                    if 200 <= price_val <= 15000:  # Reasonable cruise price range
                        return price_val
            except:
                continue
        
        # Strategy 3: DOM text extraction
        price_selectors = [
            "//*[contains(text(), '$') and contains(text(), ',')]",
            "//*[contains(@class, 'price')]",
            "//*[contains(@class, 'rate')]//text()[contains(., '$')]",
            "//*[contains(@class, 'total')]//text()[contains(., '$')]"
        ]
        
        for selector in price_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
                    if price_match:
                        price_val = float(price_match.group(1).replace(',', ''))
                        if 500 <= price_val <= 10000:  # Reasonable cabin price
                            return price_val
            except:
                continue
        
        return None
    
    def check_price(self) -> Dict:
        """Check current price and return results"""
        results = []
        
        # Check both rate codes
        for rate_code in self.config["target_price"]["rate_codes"]:
            for meta_code in self.config["target_price"]["meta_codes"]:
                url = self.build_booking_url(rate_code, meta_code)
                
                for attempt in range(self.config["monitoring"]["max_retries"]):
                    logger.info(f"Checking {rate_code}/{meta_code} - attempt {attempt + 1}")
                    
                    price, error, success = self.get_price_with_selenium(url)
                    
                    result = {
                        'timestamp': datetime.now().isoformat(),
                        'rate_code': rate_code,
                        'meta_code': meta_code,
                        'price': price,
                        'success': success,
                        'error': error,
                        'url': url,
                        'attempt': attempt + 1
                    }
                    
                    # Store in database
                    self._store_price_check(result)
                    
                    if success:
                        results.append(result)
                        break
                    
                    if attempt < self.config["monitoring"]["max_retries"] - 1:
                        logger.info(f"Retrying in 10 seconds...")
                        time.sleep(10)
                else:
                    # All attempts failed
                    results.append(result)
        
        # Check for price drops and send alerts
        self._check_price_alerts(results)
        
        return {
            'check_time': datetime.now().isoformat(),
            'results': results,
            'baseline_price': self.config["target_price"]["baseline_price"]
        }
    
    def _store_price_check(self, result: Dict):
        """Store price check result in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history 
                (price, rate_code, meta_code, url, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                result.get('price'),
                result.get('rate_code'),
                result.get('meta_code'), 
                result.get('url'),
                result.get('success'),
                result.get('error')
            ))
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
    parser.add_argument('--config', default='cruise_config.json', help='Config file path')
    
    args = parser.parse_args()
    
    tracker = CruisePriceTracker(args.config)
    
    if args.check:
        results = tracker.check_price()
        print(json.dumps(results, indent=2))
    elif args.monitor:
        tracker.run_monitoring_loop()
    elif args.history:
        history = tracker.get_price_history(args.history)
        print(json.dumps(history, indent=2))
    else:
        print("Use --check, --monitor, or --history. See --help for details.")

if __name__ == '__main__':
    main()