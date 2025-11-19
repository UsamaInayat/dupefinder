"""
Quick test script to verify MongoDB Atlas connection
Run this before starting the main server to test the connection.
"""

import asyncio
import sys
from app.core.database import connect_to_mongo, check_connection, get_database
from app.core.config import settings


async def test_connection():
    """Test MongoDB Atlas connection"""
    print("=" * 50)
    print("Testing MongoDB Atlas Connection")
    print("=" * 50)
    print(f"Connection URI: {settings.MONGO_URI}")
    print(f"Database Name: {settings.MONGO_DB_NAME}")
    print("-" * 50)
    
    try:
        # Connect to database
        print("[*] Attempting to connect...")
        await connect_to_mongo()
        print("[OK] Connection successful!")
        
        # Check connection status
        is_connected = await check_connection()
        if is_connected:
            print("[OK] Connection verified!")
        else:
            print("[ERROR] Connection check failed!")
            return False
        
        # Get database instance
        db = get_database()
        print(f"[OK] Database instance retrieved: {db.name}")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"\n[*] Collections in database: {len(collections)}")
        if collections:
            for collection in collections:
                count = await db[collection].count_documents({})
                print(f"   - {collection}: {count} documents")
        else:
            print("   (No collections yet - database is empty)")
        
        print("\n" + "=" * 50)
        print("[OK] All tests passed! MongoDB Atlas is ready to use.")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify MongoDB Atlas connection string")
        print("3. Check MongoDB Atlas IP whitelist (should allow all IPs: 0.0.0.0/0)")
        print("4. Verify database user credentials")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)

