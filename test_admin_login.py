"""
Quick test to verify admin login endpoint works
Run this to test if the backend is working before trying in the browser
"""

import requests
import json

def test_admin_login():
    """Test admin login endpoint"""
    print("=" * 60)
    print("Testing Admin Login Endpoint")
    print("=" * 60)
    
    url = "http://localhost:8000/api/admin/login"
    data = {
        "email": "admin@dupefinder.com",
        "password": "admin123"
    }
    
    print(f"\n1. Testing if backend is running...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is running!")
        else:
            print(f"   ❌ Backend returned status: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend is NOT running!")
        print("\n   Please start the backend server:")
        print("   cd backend")
        print("   python start_server.py")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print(f"\n2. Testing admin login endpoint...")
    print(f"   URL: {url}")
    print(f"   Email: {data['email']}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"\n   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Admin login successful!")
            print(f"   Access Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"   Admin Email: {result.get('admin', {}).get('email', 'N/A')}")
        else:
            print(f"   ❌ Login failed!")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection reset - Backend might have crashed!")
        print("   Check backend terminal for error messages")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_admin_login()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")



