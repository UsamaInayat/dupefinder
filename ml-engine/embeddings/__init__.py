"""
Embeddings Package
Feature extraction and embedding generation for DupeFinder ML Engine

Provides FeatureExtractor for extracting deep embeddings from images using ResNet50.
"""

from .feature_extractor import (
    FeatureExtractor,
    create_feature_extractor,
    extract_embedding
)

__all__ = [
    'FeatureExtractor',
    'create_feature_extractor',
    'extract_embedding'
]
