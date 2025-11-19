"""
Similarity Package
Vector similarity search for DupeFinder ML Engine

Provides SimilaritySearcher for finding similar items based on cosine similarity.
"""

from .similarity_searcher import (
    SimilaritySearcher,
    create_searcher,
    find_similar_items
)

__all__ = [
    'SimilaritySearcher',
    'create_searcher',
    'find_similar_items'
]
