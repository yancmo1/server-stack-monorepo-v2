#!/bin/bash
# test_local.sh - Test the app locally before deploying to Pi

echo "=== Testing Cruise Price Checker Locally ==="

# Navigate to project directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install flask requests beautifulsoup4 selenium webdriver-manager

# Start the Flask app in background
echo "Starting Flask app..."
python app.py &
APP_PID=$!

# Wait for app to start
sleep 3

# Test the home endpoint
echo "Testing home endpoint..."
curl -s http://localhost:5000/ | head -3

echo -e "\n=== Local Test Complete ==="
echo "Flask app is running at http://localhost:5000"
echo "To test price extraction, use:"
echo "  python test_price_extraction.py <carnival_url>"
echo ""
echo "To stop the app, run: kill $APP_PID"
echo "App PID: $APP_PID"
