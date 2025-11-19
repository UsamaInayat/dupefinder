"""
DupeFinder Backend - MongoDB Models/Schemas

This module defines the MongoDB document schemas using Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# Product Embedding Model
class ProductEmbedding(BaseModel):
    """Product embedding document schema"""
    product_id: str = Field(..., description="UUID of the product")
    embedding: List[float] = Field(..., description="Vector embedding (2048 dimensions)")
    model_version: str = Field(default="resnet50", description="ML model version")
    image_features: Optional[dict] = Field(None, description="Image features (colors, patterns, etc.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


# User Search Analytics Model
class UserSearchAnalytics(BaseModel):
    """User search analytics document schema"""
    user_id: Optional[str] = Field(None, description="UUID of the user")
    search_id: str = Field(..., description="Unique search session ID")
    uploaded_image: Optional[dict] = Field(None, description="Uploaded image metadata")
    query_embedding: Optional[List[float]] = Field(None, description="Embedding of uploaded image")
    results: Optional[List[dict]] = Field(None, description="Search results with similarity scores")
    filters_applied: Optional[dict] = Field(None, description="Filters applied to search")
    user_interactions: Optional[List[dict]] = Field(None, description="User interactions with results")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}


# Image Metadata Model
class ImageMetadata(BaseModel):
    """Image metadata document schema"""
    image_url: str = Field(..., description="URL or path to image")
    type: str = Field(..., description="Type: product, user_upload, community")
    reference_id: Optional[str] = Field(None, description="ID of related entity")
    storage_location: Optional[str] = Field(None, description="S3/Cloud storage location")
    metadata: Optional[dict] = Field(None, description="File metadata (size, format, dimensions)")
    processed_versions: Optional[List[dict]] = Field(None, description="Different sizes/versions")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}


# Analytics Events Model
class AnalyticsEvent(BaseModel):
    """Analytics event document schema"""
    event_type: str = Field(..., description="Type: search, view, click, favorite, etc.")
    user_id: Optional[str] = Field(None, description="UUID of the user")
    product_id: Optional[str] = Field(None, description="UUID of the product")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Optional[dict] = Field(None, description="Additional event data")
    device_info: Optional[dict] = Field(None, description="Device information")
    location: Optional[dict] = Field(None, description="Location information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}


# ML Model Logs Model
class MLModelLog(BaseModel):
    """ML model performance log document schema"""
    model_version: str = Field(..., description="Model version")
    search_id: Optional[str] = Field(None, description="Search session ID")
    performance_metrics: Optional[dict] = Field(None, description="Performance metrics")
    accuracy_feedback: Optional[dict] = Field(None, description="User feedback on results")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}

