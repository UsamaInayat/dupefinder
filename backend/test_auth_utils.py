"""
Test Authentication Utilities
Test password hashing and JWT token generation
"""

from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    get_user_id_from_token,
    get_email_from_token
)


def test_password_hashing():
    """Test password hashing and verification"""
    print("\n[TEST 1] Password Hashing & Verification")
    print("-" * 60)
    
    password = "TestPassword123!"
    print(f"Original password: {password}")
    
    # Hash password
    hashed = hash_password(password)
    print(f"Hashed password: {hashed[:50]}...")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"Verify correct password: {is_valid}")
    assert is_valid, "Password verification failed"
    
    # Verify wrong password
    is_valid = verify_password("WrongPassword", hashed)
    print(f"Verify wrong password: {is_valid}")
    assert not is_valid, "Wrong password verified as valid"
    
    print("[OK] Password hashing works correctly!")


def test_jwt_tokens():
    """Test JWT token creation and validation"""
    print("\n[TEST 2] JWT Token Generation & Validation")
    print("-" * 60)
    
    # Create tokens
    user_data = {
        "user_id": "12345",
        "email": "test@example.com"
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token({"user_id": user_data["user_id"]})
    
    print(f"Access token: {access_token[:50]}...")
    print(f"Refresh token: {refresh_token[:50]}...")
    
    # Decode access token
    payload = decode_token(access_token)
    print(f"\nAccess token payload:")
    print(f"  - user_id: {payload.get('user_id')}")
    print(f"  - email: {payload.get('email')}")
    print(f"  - type: {payload.get('type')}")
    print(f"  - exp: {payload.get('exp')}")
    
    assert payload.get("user_id") == "12345", "User ID mismatch"
    assert payload.get("email") == "test@example.com", "Email mismatch"
    assert payload.get("type") == "access", "Token type mismatch"
    
    # Verify token type
    verified_access = verify_token(access_token, "access")
    verified_refresh = verify_token(refresh_token, "refresh")
    
    print(f"\nVerify access token as access: {verified_access is not None}")
    print(f"Verify refresh token as refresh: {verified_refresh is not None}")
    
    assert verified_access is not None, "Access token verification failed"
    assert verified_refresh is not None, "Refresh token verification failed"
    
    # Try wrong token type
    wrong_type = verify_token(access_token, "refresh")
    print(f"Verify access token as refresh: {wrong_type is not None}")
    assert wrong_type is None, "Wrong token type accepted"
    
    # Extract user info
    user_id = get_user_id_from_token(access_token)
    email = get_email_from_token(access_token)
    
    print(f"\nExtracted from token:")
    print(f"  - user_id: {user_id}")
    print(f"  - email: {email}")
    
    assert user_id == "12345", "User ID extraction failed"
    assert email == "test@example.com", "Email extraction failed"
    
    print("\n[OK] JWT tokens work correctly!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Authentication Utilities")
    print("=" * 60)
    
    try:
        test_password_hashing()
        test_jwt_tokens()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        print("\nAuthentication utilities are ready to use:")
        print("  ✓ Password hashing (bcrypt)")
        print("  ✓ Password verification")
        print("  ✓ JWT access token generation (30 min)")
        print("  ✓ JWT refresh token generation (7 days)")
        print("  ✓ Token validation and decoding")
        print("  ✓ User info extraction from tokens")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)






