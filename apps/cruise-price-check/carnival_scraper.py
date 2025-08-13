"""carnival_scraper.py
Modular scraping layer for Carnival (and future cruise lines).

Goals:
 - Provide a clear interface (fetch -> parse -> normalize)
 - Support multiple execution backends: requests (static), playwright (dynamic), selenium (legacy fallback)
 - Allow offline testing via stored HTML snapshots
 - Centralize all selector / pattern logic so tracker logic stays simple

NOTE: Dynamic prices on Carnival frequently load via client-side React hydration
and/or XHR/Fetch JSON endpoints. A robust approach is to:
 1. Use Playwright headless Chromium to load the booking page with realistic headers
 2. Wait for network idle OR a specific selector containing price tokens
 3. Capture network responses; look for JSON with keys like 'sailingPrice', 'voyagePrice', etc.
 4. Fallback to DOM text / embedded data attributes / URL params (qbPrice=)

Given the environment may not have Playwright browsers installed yet, we implement
an adaptive strategy that attempts imports lazily and degrades gracefully.

Usage:
    scraper = CarnivalScraper(config)
    result = scraper.get_price(url, rate_code="PJS", meta_code="IS")

Result dict shape (None fields if unavailable):
    {
        'price': float|None,
        'currency': 'USD',
        'raw_price_text': str|None,
        'rate_code': 'PJS',
        'meta_code': 'IS',
        'url': url,
        'engine': 'playwright'|'selenium'|'requests',
        'success': bool,
        'error': str|None,
        'debug': [list of strings],
        'extracted_at': iso timestamp
    }

Future extension: add Royal Caribbean or others by creating new scraper classes
implementing BaseCruiseScraper interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple, Protocol
import re
import time
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

_playwright_import_error: Optional[str] = None
try:  # pragma: no cover - runtime dependent
    from playwright.sync_api import sync_playwright  # type: ignore
    _playwright_available = True
except Exception as e:  # pragma: no cover
    _playwright_available = False
    _playwright_import_error = str(e)

try:  # pragma: no cover
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except Exception:  # pragma: no cover
    webdriver = None  # type: ignore
    Options = None  # type: ignore

class BaseCruiseScraper(Protocol):
    def get_price(self, url: str, rate_code: str, meta_code: str) -> Dict[str, Any]:
        ...

PRICE_REGEXES = [
    re.compile(r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"),
    re.compile(r'"price"\s*:\s*"?(\d{2,5})'),
    re.compile(r'qbPrice=(\d{2,5})'),
]

def _clean_price(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value.replace(',', '').replace('$', ''))
    except Exception:
        return None

@dataclass
class CarnivalScraper:
    config: Dict[str, Any]
    prefer_playwright: bool = True
    max_wait_seconds: int = 20
    headless: bool = True

    def get_price(self, url: str, rate_code: str, meta_code: str) -> Dict[str, Any]:
        debug: List[str] = []
        engine_sequence: List[str] = []

        if self.prefer_playwright and _playwright_available:
            engine_sequence.append('playwright')
        if webdriver is not None:
            engine_sequence.append('selenium')
        engine_sequence.append('requests')

        last_error = None
        for engine in engine_sequence:
            try:
                if engine == 'playwright':
                    result = self._get_with_playwright(url, debug)
                elif engine == 'selenium':
                    result = self._get_with_selenium(url, debug)
                else:
                    result = self._get_with_requests(url, debug)

                html = result.get('html', '')
                price, raw_text = self._extract_price(html, debug, url)
                if price is not None:
                    return self._result_dict(price, raw_text, rate_code, meta_code, url, engine, True, None, debug, html)
                else:
                    debug.append(f"Engine {engine} returned HTML but price not found")
            except Exception as e:  # pragma: no cover
                last_error = str(e)
                debug.append(f"Engine {engine} failed: {e}")
                continue

        return self._result_dict(None, None, rate_code, meta_code, url, engine_sequence[-1], False, last_error or 'Price not found', debug, '')

    def _get_with_playwright(self, url: str, debug: List[str]) -> Dict[str, Any]:  # pragma: no cover
        if not _playwright_available:
            raise RuntimeError(f"Playwright unavailable: {_playwright_import_error}")
        debug.append("Playwright: launching browser")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless,
                                        args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"])  # type: ignore
            context = browser.new_context(user_agent=self._user_agent())
            page = context.new_page()
            page.set_default_timeout(self.max_wait_seconds * 1000)
            page.goto(url, wait_until='domcontentloaded')
            self._playwright_wait_for_price(page, debug)
            html = page.content()
            context.close()
            browser.close()
            debug.append("Playwright: page content captured")
            return {'html': html}

    def _playwright_wait_for_price(self, page, debug: List[str]):  # pragma: no cover
        start = time.time()
        while time.time() - start < self.max_wait_seconds:
            html = page.content()
            for rx in PRICE_REGEXES:
                if rx.search(html):
                    debug.append("Playwright: price regex found during wait")
                    return
            time.sleep(0.5)
        debug.append("Playwright: timeout waiting for price pattern")

    def _get_with_selenium(self, url: str, debug: List[str]) -> Dict[str, Any]:  # pragma: no cover
        if webdriver is None:
            raise RuntimeError("Selenium not installed")
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--user-agent={self._user_agent()}')
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.set_page_load_timeout(self.max_wait_seconds)
            driver.get(url)
            time.sleep(5)
            html = driver.page_source
            debug.append("Selenium: page source captured")
            return {'html': html}
        finally:
            driver.quit()

    def _get_with_requests(self, url: str, debug: List[str]) -> Dict[str, Any]:
        import requests
        attempts = int(self.config.get('monitoring', {}).get('max_retries', 3))
        timeout = int(self.config.get('monitoring', {}).get('timeout_seconds', 30))

        @retry(
            stop=stop_after_attempt(max(1, attempts)),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(Exception),
            reraise=True
        )
        def _do_request() -> Dict[str, Any]:
            headers = {
                'User-Agent': self._user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            resp = requests.get(url, headers=headers, timeout=timeout)
            debug.append(f"Requests: status {resp.status_code}")
            if resp.status_code >= 500:
                # trigger retry for server errors
                raise RuntimeError(f"Transient HTTP {resp.status_code}")
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            return {'html': resp.text}

        try:
            return _do_request()
        except Exception as e:
            debug.append(f"Requests final failure: {e}")
            raise

    def _extract_price(self, html: str, debug: List[str], url: str) -> Tuple[Optional[float], Optional[str]]:
        if not html:
            return None, None
        m = re.search(r'qbPrice=(\d{2,6})', url)
        if m:
            price = _clean_price(m.group(1))
            if price:
                debug.append("Extracted price from URL qbPrice param")
                return price, m.group(1)
        for rx in PRICE_REGEXES:
            m = rx.search(html)
            if m:
                price = _clean_price(m.group(1))
                if price:
                    debug.append(f"Extracted price via regex {rx.pattern}")
                    return price, m.group(1)
        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, 'html.parser')
            candidate_nodes = []
            for cls_hint in ['price', 'total', 'fare', 'amount']:
                candidate_nodes.extend(soup.select(f"*[class*='{cls_hint}']"))
            seen = set()
            for node in candidate_nodes:
                text = node.get_text(strip=True)
                if text in seen:
                    continue
                seen.add(text)
                m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
                if m:
                    price = _clean_price(m.group(1))
                    if price:
                        debug.append("Extracted price from semantic class node")
                        return price, text
        return None, None

    def _user_agent(self) -> str:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )

    def _result_dict(self, price: Optional[float], raw_text: Optional[str], rate_code: str, meta_code: str,
                      url: str, engine: str, success: bool, error: Optional[str], debug: List[str], html: str) -> Dict[str, Any]:
        # Only include html if snapshots enabled in config to limit memory usage
        include_html = self.config.get('storage', {}).get('save_snapshots', False)
        return {
            'price': price,
            'currency': self.config.get('cruise_details', {}).get('currency', 'USD'),
            'raw_price_text': raw_text,
            'rate_code': rate_code,
            'meta_code': meta_code,
            'url': url,
            'engine': engine,
            'success': success and price is not None,
            'error': None if (price is not None and success) else error or 'Price not found',
            'debug': debug,
            'extracted_at': datetime.utcnow().isoformat(),
            'html': html if include_html else None
        }

def build_carnival_booking_url(config: Dict[str, Any], rate_code: str, meta_code: str, qb_price: Optional[float] = None) -> str:
    cruise = config['cruise_details']
    baseline = qb_price if qb_price is not None else config['target_price'].get('baseline_price')
    params = {
        "embkCode": cruise['departure_port'],
        "itinCode": cruise['itinerary_code'],
        "durDays": cruise['duration_days'],
        "shipCode": cruise['ship_code'],
        "subRegionCode": cruise['region_code'],
        "sailingID": cruise['sailing_id'],
        "sailDate": cruise['sail_date'],
        "numGuests": cruise['num_guests'],
        "isMilitary": cruise['is_military'],
        "isOver55": cruise['is_over_55'],
        "isPastGuest": cruise['is_past_guest'],
        "stateCode": '',
        "evsel": '',
        "locality": cruise['locality'],
        "currency": cruise['currency'],
        "qbPrice": baseline,
        "qbMetaCode": meta_code,
        "qbRateCode": rate_code,
        "country": cruise['country']
    }
    if config.get('vifp_tracking', {}).get('enabled'):
        params['vifp'] = config['vifp_tracking'].get('vifp_number', '')
    param_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.carnival.com/booking/room-type?{param_string}"

__all__ = [
    'CarnivalScraper',
    'build_carnival_booking_url'
]
