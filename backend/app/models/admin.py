"""
Admin models and schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class AdminLogin(BaseModel):
    """Schema for admin login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@dupefinder.com",
                "password": "admin123"
            }
        }


class AdminResponse(BaseModel):
    """Schema for admin data in responses"""
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    role: str = "admin"
    created_at: datetime
    
    class Config:
        populate_by_name = True


class AdminToken(BaseModel):
    """Schema for admin authentication token response"""
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


class UserManagementResponse(BaseModel):
    """Schema for user management listing"""
    users: List[dict]
    total: int
    active_users: int
    inactive_users: int


class ProductCreate(BaseModel):
    """Schema for creating new product via admin"""
    name: str = Field(..., min_length=2, max_length=200)
    category: str = Field(..., pattern="^(bags|shoes|watches|clothing|accessories)$")
    brand: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Luxury Leather Bag",
                "category": "bags",
                "brand": "Designer Brand",
                "price": 299.99,
                "description": "Premium quality leather bag",
                "image_url": "https://example.com/bag.jpg"
            }
        }


class ProductUpdate(BaseModel):
    """Schema for updating product"""
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class SystemStats(BaseModel):
    """Schema for system statistics"""
    total_users: int
    total_products: int
    total_searches: int
    active_users_today: int
    searches_today: int
    avg_search_time_ms: float
    top_categories: List[dict]
    recent_users: List[dict]
    recent_searches: List[dict]








