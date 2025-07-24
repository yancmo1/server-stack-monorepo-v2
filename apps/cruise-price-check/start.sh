#!/bin/bash

# Simple startup script for Improved Cruise Price Tracker
echo "🚢 Starting Improved Cruise Price Tracker..."
echo ""

# Check if we're in the right directory
if [ ! -f "improved_price_tracker.py" ]; then
    echo "❌ Error: Please run this script from the cruise-price-check directory"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "📦 Installing dependencies first..."
    ./setup_improved.sh
fi

echo "🌐 Starting web interface..."
echo "   Access at: http://localhost:5001"
echo "   Or from other devices: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'YOUR-IP'):5001"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the web interface
python3 start_web_app.py