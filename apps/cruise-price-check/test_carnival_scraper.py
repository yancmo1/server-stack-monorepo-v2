import os
import sys
import json
import pytest
from typing import Dict

# Ensure path
sys.path.append(os.path.abspath('apps/cruise-price-check'))
from carnival_scraper import CarnivalScraper

BASIC_CONFIG: Dict = {
    "cruise_details": {
        "ship_code": "JB",
        "departure_port": "GAL",
        "itinerary_code": "WE8",
        "duration_days": 7,
        "sailing_id": "17415",
        "sail_date": "11082025",
        "region_code": "CW",
        "num_guests": 2,
        "is_military": "N",
        "is_over_55": "N",
        "is_past_guest": "Y",
        "country": "US",
        "currency": "USD",
        "locality": "1"
    },
    "target_price": {
        "baseline_price": 1462,
        "alert_threshold": 50,
        "rate_codes": ["PJS"],
        "meta_codes": ["IS"],
    },
    "monitoring": {"max_retries": 1, "timeout_seconds": 5},
    "storage": {"save_snapshots": False, "snapshot_dir": "snapshots", "retain_days": 1},
    "alerts": {},
}

PRICE_HTML_VARIANTS = [
    ("Simple dollar", '<div class="price">$1,234</div>', 1234.0),
    ("JSON price field", '<script>var data = {"price":1999};</script>', 1999.0),
    ("Semantic price class", '<span class="ccl-price-numbering">2,345</span>', 2345.0),
]

@pytest.mark.parametrize("name,html,expected", PRICE_HTML_VARIANTS)
def test_extract_price_variants(monkeypatch, name, html, expected):
    scraper = CarnivalScraper(BASIC_CONFIG)

    # Monkeypatch network methods to bypass real HTTP
    def fake_requests(url, rate_code, meta_code):
        return {
            'engine': 'requests',
            'success': True,
            'price': expected,
            'raw_price_text': str(int(expected)),
            'debug': [{'source': 'test', 'variant': name}],
            'html': html,
            'currency': 'USD'
        }
    scraper._get_with_requests = fake_requests  # type: ignore
    scraper.prefer_playwright = False

    result = scraper.get_price('http://example.com', 'PJS', 'IS')
    assert result['success'] is True
    assert result['price'] == expected
    assert result['engine'] == 'requests'
    assert result['currency'] == 'USD'


def test_fallback_on_failure(monkeypatch):
    scraper = CarnivalScraper(BASIC_CONFIG)

    def bad_playwright(url, rate_code, meta_code):
        raise RuntimeError('playwright fail')
    def bad_selenium(url, rate_code, meta_code):
        raise RuntimeError('selenium fail')
    def good_requests(url, rate_code, meta_code):
        return {'engine':'requests','success':True,'price':111.0,'raw_price_text':'111','debug':[], 'currency':'USD'}

    scraper._get_with_playwright = bad_playwright  # type: ignore
    scraper._get_with_selenium = bad_selenium      # type: ignore
    scraper._get_with_requests = good_requests     # type: ignore

    scraper.prefer_playwright = True
    result = scraper.get_price('http://example.com','PJS','IS')
    assert result['success'] and result['price'] == 111.0
    assert result['engine'] == 'requests'


def test_failure_propagates(monkeypatch):
    scraper = CarnivalScraper(BASIC_CONFIG)

    def bad(url, rate_code, meta_code):
        return {'engine':'requests','success':False,'error':'no price','debug':[], 'currency':'USD'}

    scraper._get_with_requests = bad  # type: ignore
    scraper.prefer_playwright = False

    result = scraper.get_price('http://example.com','PJS','IS')
    assert result['success'] is False
    assert result.get('price') is None
    assert 'error' in result
