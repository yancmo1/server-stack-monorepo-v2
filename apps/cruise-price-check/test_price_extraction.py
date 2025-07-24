#!/usr/bin/env python3
"""
Test script for price extraction functionality
"""

import requests
import json
import sys

def test_price_extraction(url, local_port=5000):
    """Test the price extraction with a given URL"""
    try:
        response = requests.get(f'http://localhost:{local_port}/check_price', 
                              params={'url': url}, 
                              timeout=120)  # Extended timeout for navigation
        
        if response.status_code == 200:
            result = response.json()
            print("=== PRICE EXTRACTION RESULTS ===")
            print(f"Price found: {result.get('price', 'None')}")
            print(f"Page title: {result.get('page_title', 'None')}")
            print(f"Final URL: {result.get('current_url', 'None')}")
            
            if 'debug_info' in result:
                print("\n=== DEBUG INFO ===")
                for info in result['debug_info']:
                    print(f"- {info}")
            
            if 'error' in result:
                print(f"\nError: {result['error']}")
                
            return result
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # Default test URL - replace with actual Carnival URL
        test_url = "https://www.carnival.com/"
        print("No URL provided, using default. Usage: python test_price_extraction.py <carnival_url>")
    
    print(f"Testing price extraction with URL: {test_url}")
    print("Make sure the Flask app is running on localhost:5000")
    print("Starting test...\n")
    
    result = test_price_extraction(test_url)
    
    if result and result.get('price'):
        print(f"\n✅ SUCCESS: Found price {result['price']}")
    else:
        print("\n❌ FAILED: No price found")
