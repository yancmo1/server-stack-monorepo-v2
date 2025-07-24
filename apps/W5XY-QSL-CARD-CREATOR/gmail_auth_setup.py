#!/usr/bin/env python3
"""
Gmail Authentication Helper
This script helps set up Gmail API authentication for the QSL Card Creator.
Run this script on the host machine to generate the gmail_token.pickle file.
"""

import os
import pickle
import sys

# Add current directory to path to import Gmail classes
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def authenticate_gmail():
    """Run Gmail authentication and save token"""
    try:
        # Import Gmail API modules
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        # Gmail API scope for composing emails
        SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
        
        credentials_path = 'gmail_credentials.json'
        token_path = 'gmail_token.pickle'
        
        print(f"🔐 Starting Gmail API authentication...")
        print(f"📁 Credentials file: {credentials_path}")
        print(f"💾 Token will be saved to: {token_path}")
        
        if not os.path.exists(credentials_path):
            print(f"❌ Error: {credentials_path} not found!")
            print("Please download the credentials file from Google Cloud Console:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Select your project")
            print("3. Go to APIs & Services > Credentials")
            print("4. Create OAuth 2.0 Client ID (Desktop application)")
            print("5. Download the JSON file and save as 'gmail_credentials.json'")
            return False
        
        creds = None
        
        # Load existing token if available
        if os.path.exists(token_path):
            print(f"📂 Loading existing token...")
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
                
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"🔄 Refreshing expired token...")
                creds.refresh(Request())
            else:
                print(f"🌐 Starting OAuth flow...")
                print("Your browser will open. Please:")
                print("1. Sign in to your Gmail account")
                print("2. Grant permission to the QSL Card Creator")
                print("3. Return to this terminal")
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            print(f"💾 Saving token...")
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Test the Gmail API
        print(f"🧪 Testing Gmail API connection...")
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile to verify connection
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        
        print(f"✅ Gmail API authentication successful!")
        print(f"📧 Connected to: {email_address}")
        print(f"💾 Token saved to: {token_path}")
        print()
        print("🐳 You can now use the Docker container with Gmail API support!")
        print("The gmail_token.pickle file will be copied into the container.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error: Required Gmail API libraries not installed")
        print(f"Please install them with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False

if __name__ == "__main__":
    print("🚀 QSL Card Creator - Gmail API Authentication Helper")
    print("=" * 60)
    
    success = authenticate_gmail()
    
    if success:
        print("\n🎉 Authentication complete! You can now:")
        print("   • Create QSL email drafts with attachments")
        print("   • Drafts will appear in your Gmail drafts folder")
        print("   • Review and send drafts manually from Gmail")
    else:
        print("\n❌ Authentication failed. Please check the error messages above.")
        sys.exit(1)
