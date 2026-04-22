"""
DupeFinder Backend - Configuration Settings

This module handles all configuration settings using Pydantic Settings.
Load settings from environment variables
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application
    APP_NAME: str = "DupeFinder"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # MongoDB Atlas
    MONGO_URI: str = "mongodb+srv://ussamainayat:ussamainayat@dupefinder.u30xrsm.mongodb.net/"
    MONGO_DB_NAME: str = "dupefinder"
    MONGODB_URL: str = "mongodb+srv://ussamainayat:ussamainayat@dupefinder.u30xrsm.mongodb.net/"
    MONGODB_DATABASE: str = "dupefinder"
    
    # PostgreSQL (for future use)
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "dupefinder-super-secret-key-change-in-production-12345"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days for admin dashboard
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: str = "ussamainayat@gmail.com"
    SMTP_PASSWORD: str = "kqsh zlyu xiuf mfwe"
    EMAIL_FROM: str = "ussamainayat@gmail.com"
    EMAIL_FROM_NAME: str = "DupeFinder"
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 10
    OTP_LENGTH: int = 6
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "webp"]

    # Remote scraper worker (Railway split deploy)
    # When SCRAPER_SERVICE_URL is set, admin scraping can delegate Playwright work to a separate service
    # to keep the API image under platform size limits.
    SCRAPER_SERVICE_URL: str = ""  # e.g. https://dupefinder-scraper.up.railway.app
    SCRAPER_SERVICE_TOKEN: str = ""  # shared secret; sent as X-Scraper-Token
    SCRAPER_REQUEST_TIMEOUT_S: float = 300.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Helper function to get settings
def get_settings() -> Settings:
    """
    Get application settings
    Use with FastAPI Depends()
    """
    return settings
