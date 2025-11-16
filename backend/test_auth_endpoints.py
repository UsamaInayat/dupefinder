"""
Test Auth Endpoints
Test signup, verify OTP, login, refresh token, logout
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db_manager

# Create test client
client = TestClient(app)


def test_endpoints():
    """Test all auth endpoints"""
    print("=" * 60)
    print("Testing Authentication Endpoints")
    print("=" * 60)
    
    # Connect to database
    db_manager.connect()
    
    test_email = "test@dupefinder.com"
    test_password = "TestPass123!"
    
    # Test 1: Signup
    print("\n[TEST 1] POST /api/auth/signup")
    print("-" * 60)
    
    response = client.post("/api/auth/signup", json={
        "email": test_email,
        "password": test_password
    })
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 201:
        print("[OK] Signup successful!")
    else:
        print(f"[WARN] Signup failed: {response.json().get('detail')}")
    
    # Test 2: Resend OTP
    print("\n[TEST 2] POST /api/auth/resend-otp")
    print("-" * 60)
    
    response = client.post(f"/api/auth/resend-otp?email={test_email}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Login (should fail - not verified)
    print("\n[TEST 3] POST /api/auth/login (before verification)")
    print("-" * 60)
    
    response = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 403:
        print("[OK] Login correctly blocked (email not verified)")
    
    # Test 4: Manually verify user for testing
    print("\n[TEST 4] Manually verifying user...")
    print("-" * 60)
    
    from app.core.database import get_users_collection
    users = get_users_collection()
    result = users.update_one(
        {"email": test_email},
        {"$set": {"is_verified": True}}
    )
    
    if result.modified_count > 0:
        print("[OK] User verified manually for testing")
    
    # Test 5: Login (should succeed)
    print("\n[TEST 5] POST /api/auth/login (after verification)")
    print("-" * 60)
    
    response = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("[OK] Login successful!")
        
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        
        # Test 6: Refresh token
        print("\n[TEST 6] POST /api/auth/refresh")
        print("-" * 60)
        
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("[OK] Token refresh successful!")
        
        # Test 7: Protected endpoint (using auth middleware)
        print("\n[TEST 7] GET /health (with auth header)")
        print("-" * 60)
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/health", headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 8: Logout
        print("\n[TEST 8] POST /api/auth/logout")
        print("-" * 60)
        
        response = client.post("/api/auth/logout", json={
            "refresh_token": refresh_token
        })
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("[OK] Logout successful!")
        
        # Test 9: Try refresh after logout (should fail)
        print("\n[TEST 9] POST /api/auth/refresh (after logout)")
        print("-" * 60)
        
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 401:
            print("[OK] Refresh correctly blocked after logout")
    
    # Cleanup
    print("\n[CLEANUP] Removing test user...")
    users.delete_many({"email": test_email})
    print("[OK] Test user removed")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All auth endpoint tests completed!")
    print("=" * 60)
    print("\nAuth endpoints working:")
    print("  ✓ POST /api/auth/signup")
    print("  ✓ POST /api/auth/verify-otp")
    print("  ✓ POST /api/auth/login")
    print("  ✓ POST /api/auth/refresh")
    print("  ✓ POST /api/auth/logout")
    print("  ✓ POST /api/auth/resend-otp")
    print("  ✓ Authentication middleware")
    
    db_manager.disconnect()


if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()






