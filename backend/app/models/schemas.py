"""
Pydantic models for API request/response validation
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from bson import ObjectId


# ============================================
# Custom Types
# ============================================

class PyObjectId(str):
    """Custom type for MongoDB ObjectId"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# ============================================
# Product Models
# ============================================

class ProductBase(BaseModel):
    """Base product model"""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., pattern="^(bags|shoes|watches|clothing|accessories)$")
    brand: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Classic Leather Tote Bag",
                "category": "bags",
                "brand": "LuxeBrand",
                "price": 89.99,
                "description": "Premium leather tote bag with gold hardware"
            }
        }


class Product(ProductBase):
    """Complete product model with all fields"""
    id: str = Field(alias="_id")
    product_id: int
    image_path: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProductWithSimilarity(Product):
    """Product model with similarity score (for search results)"""
    similarity_score: float = Field(..., ge=0, le=1)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "product_id": 1,
                "name": "Classic Leather Tote Bag",
                "category": "bags",
                "brand": "LuxeBrand",
                "price": 89.99,
                "image_path": "data/products/bags/product_1.jpg",
                "description": "Premium leather tote bag",
                "similarity_score": 0.95,
                "created_at": "2025-11-09T10:30:00",
                "updated_at": "2025-11-09T10:30:00"
            }
        }


class ProductList(BaseModel):
    """Response model for product listing"""
    products: List[Product]
    total: int
    page: int
    page_size: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "products": [],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        }


# ============================================
# Search Models
# ============================================

class SearchResponse(BaseModel):
    """Response model for similarity search"""
    query_image: str
    results: List[ProductWithSimilarity]
    search_time_ms: float
    total_results: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_image": "uploads/search_20251109_103045.jpg",
                "results": [],
                "search_time_ms": 2.77,
                "total_results": 5
            }
        }


class SearchHistoryEntry(BaseModel):
    """Model for search history entry"""
    id: str = Field(alias="_id")
    uploaded_image_path: str
    results: List[dict]
    timestamp: datetime
    search_time_ms: float
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# ============================================
# Filter Models
# ============================================

class ProductFilter(BaseModel):
    """Model for product filtering"""
    category: Optional[str] = Field(None, pattern="^(bags|shoes|watches|clothing|accessories)$")
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    brand: Optional[str] = None
    search_text: Optional[str] = None
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        """Ensure max_price >= min_price"""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "bags",
                "min_price": 50.0,
                "max_price": 200.0,
                "brand": "LuxeBrand",
                "search_text": "leather tote"
            }
        }


# ============================================
# Health Check Models
# ============================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: Optional[dict] = None
    ml_engine: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-09T10:30:00",
                "database": {
                    "status": "connected",
                    "products_count": 100
                },
                "ml_engine": {
                    "status": "loaded",
                    "model": "ResNet50"
                }
            }
        }


# ============================================
# Error Models
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {"field": "category", "issue": "Invalid category"}
            }
        }








