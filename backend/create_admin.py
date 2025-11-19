#!/usr/bin/env python3
"""
Create default admin account for DupeFinder
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from backend.app.core.security import get_password_hash

# Configuration
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "dupefinder"

# Default admin credentials
DEFAULT_ADMIN = {
    "email": "admin@dupefinder.com",
    "password": "admin123",  # Change this in production!
    "full_name": "Admin User",
    "role": "admin"
}


def create_admin():
    """Create default admin account"""
    print("=" * 60)
    print("DupeFinder - Create Admin Account")
    print("=" * 60)
    
    # Connect to MongoDB
    print("\n[INFO] Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    admins_collection = db.admins
    
    # Check if admin already exists
    existing_admin = admins_collection.find_one({"email": DEFAULT_ADMIN["email"]})
    
    if existing_admin:
        print(f"\n[WARNING] Admin account already exists: {DEFAULT_ADMIN['email']}")
        response = input("Do you want to reset the password? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            # Update password
            hashed_password = get_password_hash(DEFAULT_ADMIN["password"])
            admins_collection.update_one(
                {"email": DEFAULT_ADMIN["email"]},
                {"$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.utcnow()
                }}
            )
            print("\n[OK] Admin password reset successfully!")
        else:
            print("\n[INFO] No changes made.")
        
    else:
        # Create new admin
        print(f"\n[INFO] Creating admin account: {DEFAULT_ADMIN['email']}")
        
        hashed_password = get_password_hash(DEFAULT_ADMIN["password"])
        
        admin_doc = {
            "email": DEFAULT_ADMIN["email"],
            "hashed_password": hashed_password,
            "full_name": DEFAULT_ADMIN["full_name"],
            "role": DEFAULT_ADMIN["role"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = admins_collection.insert_one(admin_doc)
        print(f"\n[OK] Admin account created successfully!")
        print(f"     Admin ID: {result.inserted_id}")
    
    # Display credentials
    print("\n" + "=" * 60)
    print("Admin Credentials")
    print("=" * 60)
    print(f"Email:    {DEFAULT_ADMIN['email']}")
    print(f"Password: {DEFAULT_ADMIN['password']}")
    print("\n⚠️  IMPORTANT: Change the default password after first login!")
    print("=" * 60)
    
    print("\n[SUCCESS] Admin setup complete!")
    print("\nYou can now login at:")
    print("  - API: http://localhost:8000/api/docs")
    print("  - Frontend: http://localhost:3000/admin")


if __name__ == "__main__":
    try:
        create_admin()
    except Exception as e:
        print(f"\n[ERROR] Failed to create admin: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)








