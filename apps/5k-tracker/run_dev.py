#!/usr/bin/env python3
"""
Development server with HTTPS support for testing PWA features
"""
from app import app, db, create_default_users, init_db
import os

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        init_db()
        create_default_users()
    
    # Check if SSL certificates exist
    cert_file = 'localhost.pem'
    key_file = 'localhost-key.pem'
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("Starting with HTTPS (mkcert certificates found)")
        ssl_context = (cert_file, key_file)
        port = 5001
        protocol = "https"
    else:
        print("No SSL certificates found. Starting with HTTP.")
        print("PWA features require HTTPS. Please run: mkcert localhost")
        ssl_context = None
        port = 5000
        protocol = "http"
    
    print(f"Server starting at {protocol}://localhost:{port}/tracker/")
    print("Default users: admin/admin123, runner/runner123")
    
    app.run(
        host='127.0.0.1',
        port=port,
        ssl_context=ssl_context,
        debug=True
    )