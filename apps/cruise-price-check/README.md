# Cruise Price Checker

This app checks cruise prices from Carnival.com by navigating through the multi-page booking flow. It automatically clicks through 2 CONTINUE buttons and extracts the price of the second interior room ($1,462), excluding the "ROOM WILL BE ASSIGNED" option.

## Features

- **Multi-page Navigation**: Automatically clicks through 2 CONTINUE buttons in the Carnival booking flow
- **Specific Price Extraction**: Targets the second interior room price ($1,462)
- **Raspberry Pi Deployment**: Designed to run on Raspberry Pi at 192.168.50.100
- **Web API**: Simple REST API for remote access
- **Debug Information**: Provides detailed debug info for troubleshooting

## Quick Start

### Local Testing

1. Test locally first:
```bash
./test_local.sh
```

2. Test price extraction with a Carnival URL:
```bash
python test_price_extraction.py <carnival_url>
```

### Deploy to Raspberry Pi

1. Deploy to Pi (auto-commits, pushes, and deploys):
```bash
./deploy_to_pi.sh
```

## Manual Usage

### Start the server locally:

```bash
source .venv/bin/activate
python app.py
```

### Access the API:

- **Home page**: `http://localhost:5000/`
- **Price check**: `http://localhost:5000/check_price?url=<carnival-url>`

### From Raspberry Pi:

```
http://192.168.50.100:5000/check_price?url=<carnival-url>
```

Replace `<carnival-url>` with the full Carnival.com booking URL.

## API Response

The API returns JSON with the following structure:

```json
{
  "price": "$1,462",
  "page_title": "Carnival Cruise Page Title",
  "current_url": "https://final-page-url.com",
  "debug_info": [
    "Initial page loaded: ...",
    "First CONTINUE button clicked using selector: ...",
    "Second CONTINUE button clicked using selector: ...",
    "Found target price: $1,462"
  ]
}
```

## Requirements

- Python 3.13+
- Flask
- Selenium
- BeautifulSoup4
- Requests
- Chrome/Chromium browser
- ChromeDriver

All dependencies are installed automatically during setup.

## Files

- `app.py` - Main Flask application with multi-page navigation logic
- `test_price_extraction.py` - Test script for price extraction
- `test_local.sh` - Local testing script
- `deploy_to_pi.sh` - Automated deployment to Raspberry Pi
- `setup_pi.sh` - Raspberry Pi setup script

## Navigation Logic

1. **Load Initial Page**: Loads the provided Carnival URL
2. **First CONTINUE**: Finds and clicks the first CONTINUE button
3. **Second CONTINUE**: Finds and clicks the second CONTINUE button  
4. **Price Extraction**: Searches for the specific $1,462 price from the second interior room (not "ROOM WILL BE ASSIGNED")

## Troubleshooting

- Check debug_info in the API response for navigation details
- Ensure ChromeDriver is properly installed on Raspberry Pi
- Verify the Carnival URL leads to the booking flow
- Check that the price selectors match the current page structure