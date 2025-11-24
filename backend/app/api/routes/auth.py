"""
Authentication Routes
Endpoints for user signup, login, OTP verification, token refresh, logout
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict
from bson import ObjectId

from app.models.auth_schemas import (
    SignupRequest,
    SignupResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse
)
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.services.email_service import (
    generate_and_send_otp,
    verify_otp
)
from app.core.database import (
    get_users_collection,
    get_refresh_tokens_collection
)
from app.core.config import settings

router = APIRouter(tags=["Authentication"])


# ============================================
# Signup Endpoint
# ============================================

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Create new user account and send OTP for verification
    
    Process:
    1. Check if email already exists
    2. Hash password
    3. Create user account (is_verified=False)
    4. Generate and send OTP
    5. Return success response
    """
    users = get_users_collection()
    
    # Check if user already exists
    existing_user = users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user document
    user_doc = {
        "email": request.email,
        "password_hash": password_hash,
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    # Insert user
    result = users.insert_one(user_doc)
    
    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )
    
    # Generate and send OTP
    try:
        otp_sent = await generate_and_send_otp(request.email)
        
        if not otp_sent:
            # Rollback user creation
            users.delete_one({"_id": result.inserted_id})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please check your email settings or try again later."
            )
    except Exception as e:
        # Rollback user creation on any error
        users.delete_one({"_id": result.inserted_id})
        print(f"[ERROR] Signup failed for {request.email}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {str(e)}"
        )
    
    return SignupResponse(
        message="Account created successfully. Please check your email for verification code.",
        email=request.email,
        otp_sent=True
    )


# ============================================
# OTP Verification Endpoint
# ============================================

@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp_endpoint(request: VerifyOTPRequest):
    """
    Verify OTP and activate user account
    
    Process:
    1. Verify OTP from database
    2. Update user is_verified=True
    3. Return success response
    """
    # Verify OTP
    is_valid = verify_otp(request.email, request.otp_code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Update user verification status
    users = get_users_collection()
    result = users.update_one(
        {"email": request.email},
        {"$set": {"is_verified": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return VerifyOTPResponse(
        message="Email verified successfully! You can now log in.",
        verified=True
    )


# ============================================
# Login Endpoint
# ============================================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    User login
    
    Process:
    1. Find user by email
    2. Verify password
    3. Check if verified
    4. Generate access + refresh tokens
    5. Store refresh token in database
    6. Update last_login
    7. Return tokens
    """
    users = get_users_collection()
    
    # Find user
    user = users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if verified
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    
    # Check if active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact support."
        )
    
    # Generate tokens
    user_id = str(user["_id"])
    
    token_data = {
        "user_id": user_id,
        "email": user["email"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": user_id})
    
    # Store refresh token
    tokens = get_refresh_tokens_collection()
    token_doc = {
        "user_id": user_id,
        "token": refresh_token,
        "expires_at": datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "created_at": datetime.utcnow()
    }
    tokens.insert_one(token_doc)
    
    # Update last login
    users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Return response
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "email": user["email"],
            "is_active": user.get("is_active", True),
            "is_verified": user.get("is_verified", False)
        }
    )


# ============================================
# Token Refresh Endpoint
# ============================================

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Process:
    1. Validate refresh token
    2. Check if token exists in database
    3. Generate new access token
    4. Return new access token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("user_id")
    
    # Check if refresh token exists in database
    tokens = get_refresh_tokens_collection()
    token_doc = tokens.find_one({
        "user_id": user_id,
        "token": request.refresh_token
    })
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Get user info
    users = get_users_collection()
    user = users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate new access token
    token_data = {
        "user_id": user_id,
        "email": user["email"]
    }
    
    access_token = create_access_token(token_data)
    
    return RefreshTokenResponse(
        access_token=access_token
    )


# ============================================
# Logout Endpoint
# ============================================

@router.post("/logout", response_model=LogoutResponse)
async def logout(request: LogoutRequest):
    """
    User logout
    
    Process:
    1. Delete refresh token from database
    2. Return success response
    """
    # Delete refresh token
    tokens = get_refresh_tokens_collection()
    result = tokens.delete_one({"token": request.refresh_token})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    
    return LogoutResponse(
        message="Logged out successfully"
    )


# ============================================
# Resend OTP Endpoint (Bonus)
# ============================================

@router.post("/resend-otp", response_model=SignupResponse)
async def resend_otp(email: str):
    """
    Resend OTP for email verification
    """
    users = get_users_collection()
    
    # Check if user exists
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate and send OTP
    otp_sent = await generate_and_send_otp(email)
    
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return SignupResponse(
        message="Verification code sent to your email",
        email=email,
        otp_sent=True
    )
