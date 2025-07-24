#!/usr/bin/env python3
"""
Test the PZQ rate code that Yancy discovered with the $714 price
"""

from improved_price_tracker import CruisePriceTracker
import json

def test_pzq_discovery():
    """Test the new PZQ rate code with updated config"""
    print("🚢 Testing PZQ Rate Code Discovery")
    print("New baseline: $714 (down from $1,462!)")
    print("=" * 50)
    
    # Initialize tracker with updated config
    tracker = CruisePriceTracker('cruise_config.json')
    
    print(f"📋 Updated Configuration:")
    config = tracker.config
    print(f"   New Baseline: ${config['target_price']['baseline_price']}")
    print(f"   Alert Threshold: ${config['target_price']['alert_threshold']}")
    print(f"   Rate Codes: {config['target_price']['rate_codes']}")
    print(f"   VIFP Number: {config.get('vifp_tracking', {}).get('vifp_number', 'Not set')}")
    
    # Build the specific PZQ URL that Yancy found
    def build_pzq_review_url():
        cruise = config["cruise_details"]
        return (
            f"https://www.carnival.com/booking/review?"
            f"embkCode={cruise['departure_port']}&"
            f"itinCode={cruise['itinerary_code']}&"
            f"durDays={cruise['duration_days']}&"
            f"shipCode={cruise['ship_code']}&"
            f"subRegionCode={cruise['region_code']}&"
            f"sailingID={cruise['sailing_id']}&"
            f"sailDate={cruise['sail_date']}&"
            f"numGuests={cruise['num_guests']}&"
            f"isMilitary={cruise['is_military']}&"
            f"isOver55={cruise['is_over_55']}&"
            f"isPastGuest={cruise['is_past_guest']}&"
            f"stateCode=&evsel=&"
            f"locality={cruise['locality']}&"
            f"currency={cruise['currency']}&"
            f"vifp=9003242299&"
            f"qbPrice=714&"
            f"qbMetaCode=IS&"
            f"qbRateCode=PZQ&"
            f"country={cruise['country']}"
        )
    
    pzq_url = build_pzq_review_url()
    
    print(f"\n🔗 Testing Yancy's PZQ URL:")
    print(f"   {pzq_url[:80]}...")
    
    # Test the PZQ URL
    print(f"\n🔍 Checking PZQ rate price...")
    try:
        price, error, success = tracker.get_price_with_selenium(pzq_url)
        
        if success:
            print(f"✅ SUCCESS! PZQ Rate: ${price}")
            
            # Compare to old baseline
            old_baseline = 1462
            savings_from_old = old_baseline - price
            print(f"💸 Savings from original $1,462: ${savings_from_old} ({savings_from_old/old_baseline*100:.1f}% off)")
            
            # Check if this would trigger alerts with new threshold
            new_baseline = config['target_price']['baseline_price']
            threshold = config['target_price']['alert_threshold']
            
            if price < new_baseline - threshold:
                price_drop = new_baseline - price
                print(f"🚨 Would trigger alert! Price ${price} is ${price_drop} below ${new_baseline} baseline")
            elif price <= new_baseline:
                print(f"✅ Price at or below new baseline of ${new_baseline}")
            else:
                price_increase = price - new_baseline
                print(f"⚠️  Price ${price_increase} above new baseline")
                
        else:
            print(f"❌ Failed: {error}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Now test all rate codes with new config
    print(f"\n🔍 Testing all rate codes with new baseline...")
    results = tracker.check_price()
    
    print(f"\n📊 All Rate Code Results:")
    for i, result in enumerate(results['results']):
        if result['success']:
            price = result['price']
            status = "✅"
            comparison = ""
            
            if price < config['target_price']['baseline_price']:
                savings = config['target_price']['baseline_price'] - price
                comparison = f" (${savings} below baseline!)"
            elif price == config['target_price']['baseline_price']:
                comparison = " (at baseline)"
            else:
                increase = price - config['target_price']['baseline_price']
                comparison = f" (${increase} above baseline)"
                
            print(f"   {status} {result['rate_code']}/{result['meta_code']}: ${price}{comparison}")
        else:
            print(f"   ❌ {result['rate_code']}/{result['meta_code']}: Failed - {result['error']}")
    
    print(f"\n🎯 Summary:")
    print(f"   - Found working PZQ rate code")
    print(f"   - Updated baseline from $1,462 to $714")
    print(f"   - Lowered alert threshold to $25")
    print(f"   - System now tracks 3 rate codes: PJS, PUG, PZQ")
    print(f"   - Ready to alert on prices below $689")

if __name__ == '__main__':
    test_pzq_discovery()