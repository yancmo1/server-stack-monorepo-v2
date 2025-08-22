#!/usr/bin/env python3
"""
Gmail Authentication Helper

This script helps authenticate Gmail API outside of the Docker container
where a browser is available for the OAuth flow.

Run this script on the host machine to generate the gmail_token.pickle file
that can then be used by the containerized application.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def authenticate_gmail():
    """Authenticate Gmail API and save token for container use"""
    credentials_path = 'gmail_credentials.json'
    token_path = 'gmail_token.pickle'
    
    print(f"🔐 Gmail Authentication Helper")
    print(f"================================")
    
    if not os.path.exists(credentials_path):
        print(f"❌ Error: {credentials_path} not found")
        print(f"Please download the Gmail API credentials file from Google Cloud Console")
        print(f"and save it as '{credentials_path}' in this directory.")
        return False
    
    creds = None
    
    # Load existing token if available
    if os.path.exists(token_path):
        print(f"📂 Loading existing token from {token_path}")
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing token: {e}")
            creds = None
    
    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                creds = None
        
        if not creds:
            print("🌐 Starting OAuth flow...")
            print("This will open a browser window for Gmail authentication.")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ Authentication completed successfully")
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False
    
    # Save credentials
    try:
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        print(f"💾 Token saved to {token_path}")
        print("✅ Gmail authentication complete!")
        print(f"You can now run the QSL Card Creator container and email drafts will work.")
        return True
    except Exception as e:
        print(f"❌ Failed to save token: {e}")
        return False

if __name__ == "__main__":
    try:
        authenticate_gmail()
    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
