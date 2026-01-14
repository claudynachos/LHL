#!/usr/bin/env python3
"""
Create an admin user for the application
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from extensions import db
from models.user import User

def create_admin():
    """Create an admin user"""
    with app.app_context():
        username = input("Admin username: ")
        email = input("Admin email: ")
        password = input("Admin password: ")
        
        # Check if user exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"User '{username}' already exists!")
            make_admin = input("Make this user an admin? (y/n): ")
            if make_admin.lower() == 'y':
                existing.is_admin = True
                db.session.commit()
                print(f"✓ {username} is now an admin")
            return
        
        # Create new admin user
        user = User(
            username=username,
            email=email,
            is_admin=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  Admin: Yes")

if __name__ == '__main__':
    create_admin()
