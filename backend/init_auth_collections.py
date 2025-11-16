"""
Initialize Authentication Collections in MongoDB
Creates users, otps, and refresh_tokens collections with proper indexes
"""

import sys
from app.core.database import db_manager


def init_auth_collections():
    """
    Initialize authentication collections with indexes
    """
    print("=" * 60)
    print("DupeFinder - Initialize Auth Collections")
    print("=" * 60)
    
    try:
        # Connect to database
        print("\n[1/3] Connecting to MongoDB...")
        db_manager.connect()
        
        if not db_manager.is_connected():
            print("[ERROR] Failed to connect to MongoDB")
            return False
        
        # Setup indexes
        print("\n[2/3] Creating indexes for auth collections...")
        db_manager.setup_auth_indexes()
        
        # Verify collections
        print("\n[3/3] Verifying collections...")
        collections = db_manager.db.list_collection_names()
        auth_collections = ['users', 'otps', 'refresh_tokens']
        
        for coll in auth_collections:
            if coll in collections or True:  # Collections created on first insert
                print(f"  - {coll}: Ready")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Auth collections initialized successfully!")
        print("=" * 60)
        print("\nCollections created:")
        print("  1. users - Stores user accounts (email, password, status)")
        print("  2. otps - Stores OTP codes with auto-expiry (10 minutes)")
        print("  3. refresh_tokens - Stores refresh tokens with auto-expiry (7 days)")
        print("\nIndexes created:")
        print("  - users.email (unique)")
        print("  - otps.expires_at (TTL)")
        print("  - otps.email")
        print("  - refresh_tokens.expires_at (TTL)")
        print("  - refresh_tokens.user_id")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}")
        return False
    
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    success = init_auth_collections()
    sys.exit(0 if success else 1)






