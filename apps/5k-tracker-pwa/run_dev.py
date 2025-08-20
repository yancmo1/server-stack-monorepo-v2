#!/usr/bin/env python3
"""
Simple development server runner for testing changes
"""
from app import app

if __name__ == '__main__':
    # Run Flask development server
    app.run(host='127.0.0.1', port=5555, debug=True)