#!/bin/bash

# 5K Race Tracker - Development Setup Script
# Run this script to set up the development environment

echo "🏃‍♀️ Setting up 5K Race Tracker development environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads/photos

# Initialize database
echo "🗄️  Initializing database..."
python -c "
from app import app, init_db, create_default_users
init_db()
create_default_users()
print('Database initialized with default users!')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the development server:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 Then open http://localhost:5011 in your browser"
echo ""
echo "👤 Default login credentials:"
echo "   Admin: admin / admin123"
echo "   Test User: runner / runner123"
echo ""
echo "📝 Remember to:"
echo "   1. Change the SECRET_KEY in app.py for production"
echo "   2. Set up your GitHub repository"
echo "   3. Configure your domain on the Raspberry Pi"
echo ""
