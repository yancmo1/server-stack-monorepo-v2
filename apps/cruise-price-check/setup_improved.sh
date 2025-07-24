#!/bin/bash

# Setup script for Improved Carnival Cruise Price Tracker
echo "🚢 Setting up Improved Carnival Cruise Price Tracker..."
echo "================================================="

# Check if we're in the right directory
if [ ! -f "improved_price_tracker.py" ]; then
    echo "❌ Error: Please run this script from the cruise-price-check directory"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install selenium webdriver-manager requests beautifulsoup4

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies. Please install manually:"
    echo "   pip3 install selenium webdriver-manager requests beautifulsoup4"
    exit 1
fi

# Make scripts executable
chmod +x improved_price_tracker.py
chmod +x quick_test.py
chmod +x simple_demo.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🔍 Quick Test Commands:"
echo "   ./simple_demo.py                                    # Show configuration demo"
echo "   python3 improved_price_tracker.py --check          # Run single price check"
echo "   python3 improved_price_tracker.py --monitor        # Start continuous monitoring"
echo "   python3 improved_price_tracker.py --history 30     # View 30-day price history"
echo ""
echo "📧 To enable email alerts:"
echo "   Edit cruise_config.json and set email_enabled: true"
echo "   Add your Gmail credentials (use App Password for security)"
echo ""
echo "🚀 Your new system is ready! It will monitor:"
echo "   Cruise: Ship JB, Western Caribbean, November 8, 2025"
echo "   Price: \$1,462 baseline (Interior Early Saver Sale)"
echo "   Alerts: When price drops by \$50 or more"
echo ""