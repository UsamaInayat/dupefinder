"""
Authentication Schemas
Pydantic models for auth requests and responses
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================
# Request Schemas
# ============================================

class SignupRequest(BaseModel):
    """Signup request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class VerifyOTPRequest(BaseModel):
    """OTP verification request"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: str


# ============================================
# Response Schemas
# ============================================

class SignupResponse(BaseModel):
    """Signup response"""
    message: str
    email: str
    otp_sent: bool


class VerifyOTPResponse(BaseModel):
    """OTP verification response"""
    message: str
    verified: bool


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenResponse(BaseModel):
    """Token refresh response"""
    access_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    """Logout response"""
    message: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str


# ============================================
# User Models
# ============================================

class User(BaseModel):
    """User model"""
    email: EmailStr
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class UserInDB(User):
    """User model with password hash"""
    password_hash: str
    
    class Config:
        from_attributes = True






