"""
Core modules for DupeFinder backend
"""

from .database import db_manager, get_db, get_products_collection, get_search_history_collection

__all__ = [
    'db_manager',
    'get_db',
    'get_products_collection',
    'get_search_history_collection'
]
