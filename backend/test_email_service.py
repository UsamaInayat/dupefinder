"""
Test Email Service
Test OTP generation and email sending
"""

import asyncio
import sys
from app.services.email_service import (
    generate_otp,
    generate_and_send_otp,
    verify_otp
)
from app.core.database import db_manager


async def test_otp_generation():
    """Test OTP generation"""
    print("\n[TEST 1] OTP Generation")
    print("-" * 60)
    
    # Generate OTP
    otp1 = generate_otp()
    otp2 = generate_otp(8)
    
    print(f"Generated 6-digit OTP: {otp1}")
    print(f"Generated 8-digit OTP: {otp2}")
    
    assert len(otp1) == 6, "OTP length should be 6"
    assert len(otp2) == 8, "OTP length should be 8"
    assert otp1.isdigit(), "OTP should be numeric"
    assert otp2.isdigit(), "OTP should be numeric"
    
    print("[OK] OTP generation works!")


async def test_email_sending():
    """Test email sending with OTP"""
    print("\n[TEST 2] Email Sending with OTP")
    print("-" * 60)
    
    # Get email address from user
    test_email = input("Enter your email address to receive test OTP: ").strip()
    
    if not test_email or '@' not in test_email:
        print("[SKIP] Invalid email, skipping email test")
        return
    
    print(f"Sending OTP to: {test_email}")
    
    # Connect to database
    db_manager.connect()
    
    try:
        # Generate and send OTP
        success = await generate_and_send_otp(test_email)
        
        if success:
            print("[OK] OTP email sent successfully!")
            print("\nPlease check your email inbox (and spam folder)")
            
            # Ask user to enter OTP
            user_otp = input("Enter the OTP you received (or press Enter to skip verification): ").strip()
            
            if user_otp:
                # Verify OTP
                is_valid = verify_otp(test_email, user_otp)
                
                if is_valid:
                    print("[OK] OTP verified successfully!")
                else:
                    print("[WARN] OTP verification failed (wrong code or expired)")
        else:
            print("[ERROR] Failed to send OTP email")
            print("Please check:")
            print("  - Gmail SMTP settings in .env")
            print("  - App password is correct")
            print("  - Internet connection")
    
    finally:
        db_manager.disconnect()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Email Service & OTP")
    print("=" * 60)
    
    try:
        await test_otp_generation()
        await test_email_sending()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Email service tests completed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)






