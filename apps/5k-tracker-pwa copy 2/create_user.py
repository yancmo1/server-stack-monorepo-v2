#!/usr/bin/env python3
"""
Script to create a new user in the race tracker database
"""
import sys
from app import app, db, User

def create_user(username, email, first_name, last_name, password):
    """Create a new user"""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists!")
            return False
            
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"Email '{email}' is already registered!")
            return False
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            print(f"User '{username}' created successfully!")
            print(f"  Email: {email}")
            print(f"  Name: {first_name} {last_name}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python create_user.py <username> <email> <first_name> <last_name> <password>")
        print("Example: python create_user.py yancmo yancy@example.com Yancy Shepherd mypassword")
        sys.exit(1)
    
    username, email, first_name, last_name, password = sys.argv[1:6]
    success = create_user(username, email, first_name, last_name, password)
    sys.exit(0 if success else 1)
