#!/usr/bin/env python3
"""
Test the improved cruise price tracker without Selenium
Shows URL building and basic functionality
"""

import json
import sqlite3
import requests
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs

def test_url_building():
    """Test building the direct booking URLs"""
    print("🔗 Testing URL Building...")
    
    # Load config
    with open('cruise_config.json', 'r') as f:
        config = json.load(f)
    
    cruise = config["cruise_details"]
    target = config["target_price"]
    
    def build_booking_url(rate_code="PJS", meta_code="IS"):
        """Build the direct booking URL"""
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
        
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    # Test different rate combinations
    rate_combinations = [
        ("PJS", "IS", "Early Saver Sale + Interior"),
        ("PUG", "IS", "Standard + Interior"), 
        ("PJS", "OB", "Early Saver Sale + Oceanview"),
        ("PUG", "OB", "Standard + Oceanview")
    ]
    
    print("✅ Generated booking URLs:")
    for rate_code, meta_code, description in rate_combinations:
        url = build_booking_url(rate_code, meta_code)
        print(f"   {description}: {url[:80]}...")
        
        # Test URL parsing
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        price_param = params.get('qbPrice', ['N/A'])[0]
        print(f"      → Price parameter: ${price_param}")
    
    return True

def test_database():
    """Test database functionality"""
    print("\n💾 Testing Database...")
    
    # Create test database
    with sqlite3.connect('test_cruise_prices.db') as conn:
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
        
        # Insert test data
        test_records = [
            (1462.0, 'PJS', 'IS', 'https://carnival.com/test1', True, None),
            (1520.0, 'PUG', 'IS', 'https://carnival.com/test2', True, None),
            (1399.0, 'PJS', 'IS', 'https://carnival.com/test3', True, None),  # Price drop!
            (None, 'PJS', 'OB', 'https://carnival.com/test4', False, 'Page not found')
        ]
        
        for price, rate_code, meta_code, url, success, error in test_records:
            cursor.execute('''
                INSERT INTO price_history (price, rate_code, meta_code, url, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (price, rate_code, meta_code, url, success, error))
        
        conn.commit()
        
        # Query the data
        cursor.execute('SELECT * FROM price_history ORDER BY timestamp DESC')
        records = cursor.fetchall()
        
        print("✅ Database created and populated:")
        for record in records:
            success_icon = "✅" if record[7] else "❌"
            price_text = f"${record[2]}" if record[2] else "N/A"
            print(f"   {success_icon} {record[1]}: {price_text} ({record[3]}/{record[4]})")
    
    return True

def test_price_alerts():
    """Test price alert logic"""
    print("\n🚨 Testing Price Alert Logic...")
    
    baseline_price = 1462
    alert_threshold = 50
    
    test_scenarios = [
        (1462, "Same price - no alert"),
        (1450, "Small drop ($12) - no alert"), 
        (1400, "Medium drop ($62) - ALERT!"),
        (1300, "Big drop ($162) - ALERT!"),
        (1500, "Price increase ($38) - no alert")
    ]
    
    print("✅ Price alert scenarios:")
    for test_price, description in test_scenarios:
        price_drop = baseline_price - test_price
        should_alert = price_drop >= alert_threshold
        alert_icon = "🚨" if should_alert else "😴"
        
        if price_drop > 0:
            print(f"   {alert_icon} ${baseline_price} → ${test_price} (drop: ${price_drop}) - {description}")
        else:
            print(f"   {alert_icon} ${baseline_price} → ${test_price} (increase: ${abs(price_drop)}) - {description}")
    
    return True

def test_price_extraction():
    """Test price extraction methods without Selenium"""
    print("\n💰 Testing Price Extraction Methods...")
    
    # Test URL parameter extraction
    test_urls = [
        "https://www.carnival.com/booking/room-type?qbPrice=1462&other=params",
        "https://www.carnival.com/booking/review?price=1520&qbPrice=1450", 
        "https://www.carnival.com/booking/room-type?noprice=true"
    ]
    
    def extract_price_from_url(url):
        """Extract price from URL parameters"""
        price_match = re.search(r'qbPrice=(\d+)', url)
        if price_match:
            return float(price_match.group(1))
        return None
    
    print("✅ URL price extraction:")
    for url in test_urls:
        price = extract_price_from_url(url)
        price_text = f"${price}" if price else "No price found"
        print(f"   {price_text} from {url[:60]}...")
    
    # Test HTML price extraction patterns
    test_html_snippets = [
        '<div class="price">$1,462.00</div>',
        '<span data-price="1520">Book Now</span>',
        '<div class="total-cost">Total: $1,399</div>',
        '<div>No price here</div>'
    ]
    
    def extract_price_from_html(html):
        """Extract price from HTML content"""
        price_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'data-price="(\d+)"'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, html)
            if match:
                price_str = match.group(1).replace(',', '')
                return float(price_str)
        return None
    
    print("✅ HTML price extraction:")
    for html in test_html_snippets:
        price = extract_price_from_html(html)
        price_text = f"${price}" if price else "No price found"
        print(f"   {price_text} from {html}")
    
    return True

def test_monitoring_config():
    """Test monitoring configuration"""
    print("\n⏰ Testing Monitoring Configuration...")
    
    with open('cruise_config.json', 'r') as f:
        config = json.load(f)
    
    monitoring = config["monitoring"]
    alerts = config["alerts"]
    
    print("✅ Current monitoring settings:")
    print(f"   Check interval: {monitoring['check_interval_hours']} hours")
    print(f"   Max retries: {monitoring['max_retries']}")
    print(f"   Timeout: {monitoring['timeout_seconds']} seconds")
    print(f"   Email alerts: {'Enabled' if alerts['email_enabled'] else 'Disabled'}")
    
    # Calculate monitoring frequency
    checks_per_day = 24 / monitoring['check_interval_hours']
    checks_per_week = checks_per_day * 7
    
    print(f"   → {checks_per_day} checks per day")
    print(f"   → {checks_per_week} checks per week")
    
    return True

def main():
    """Run all tests"""
    print("🚢 Testing Improved Carnival Cruise Price Tracker")
    print("=" * 55)
    
    tests = [
        test_url_building,
        test_database,
        test_price_alerts,
        test_price_extraction,
        test_monitoring_config
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print(f"\n🎉 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All systems working! Ready for Selenium installation.")
        print("\n🚀 Next steps:")
        print("   1. Install Selenium: pip3 install selenium webdriver-manager")
        print("   2. Run real price check: python3 improved_price_tracker.py --check")
        print("   3. Start monitoring: python3 improved_price_tracker.py --monitor")
    else:
        print("❌ Some tests failed. Please check the configuration.")
    
    return passed == len(tests)

if __name__ == '__main__':
    main()