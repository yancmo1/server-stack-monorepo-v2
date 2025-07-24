#!/usr/bin/env python3
"""
Test the new $714 price URL that Yancy found
This is a much better deal than the baseline $1,462!
"""

from improved_price_tracker import CruisePriceTracker
import json

def test_new_price_url():
    """Test the specific URL with the $714 price"""
    
    print("🚢 Testing New Price Discovery: $714 vs $1,462 Baseline")
    print("=" * 60)
    
    # The URL Yancy found
    new_url = "https://www.carnival.com/booking/review?embkCode=GAL&itinCode=WE8&durDays=7&shipCode=JB&subRegionCode=CW&sailingID=17415&sailDate=11082025&numGuests=2&isMilitary=N&isOver55=N&isPastGuest=Y&stateCode=&evsel=&locality=1&currency=USD&vifp=9003242299&qbPrice=714&qbMetaCode=IS&qbRateCode=PZQ&country=US"
    
    print(f"🔗 Testing URL: {new_url[:80]}...")
    print(f"💰 Expected Price: $714 (PZQ rate code)")
    print(f"💸 Potential Savings: $748 from baseline!")
    print()
    
    # Initialize tracker
    tracker = CruisePriceTracker()
    
    # Test the URL directly
    print("🔍 Testing price extraction from the new URL...")
    try:
        price, error, success = tracker.get_price_with_selenium(new_url)
        
        if success:
            print(f"✅ SUCCESS! Found price: ${price}")
            savings = 1462 - price
            if savings > 0:
                print(f"💸 Confirmed savings: ${savings}")
                if savings >= 50:
                    print(f"🚨 This would trigger an alert! (>${tracker.config['target_price']['alert_threshold']} threshold)")
                else:
                    print(f"ℹ️  Below alert threshold of ${tracker.config['target_price']['alert_threshold']}")
            else:
                print(f"⚠️  Price higher than baseline")
        else:
            print(f"❌ Failed to extract price: {error}")
            
    except Exception as e:
        print(f"❌ Error testing URL: {e}")
        
    print()
    print("🎯 Key Findings:")
    print(f"   - Rate Code: PZQ (new code we weren't tracking)")
    print(f"   - VIFP Number: 9003242299 (VIP guest number)")  
    print(f"   - Page Type: /booking/review (review page vs room-type)")
    print(f"   - Same cruise: Ship JB, Nov 8, 2025, Galveston")
    
    print()
    print("📋 Recommendations:")
    print("   1. Update config to track PZQ rate code")
    print("   2. Monitor both /booking/room-type AND /booking/review URLs")
    print("   3. Consider tracking VIFP-specific pricing")
    print("   4. Lower alert threshold since we found 51% savings!")

if __name__ == '__main__':
    test_new_price_url()