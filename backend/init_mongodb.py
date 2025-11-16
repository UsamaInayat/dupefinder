#!/usr/bin/env python3
"""
MongoDB Database Initialization Script for DupeFinder
Created: November 9, 2025
Purpose: Import product catalog with pre-computed embeddings into MongoDB
"""

import os
import sys
import csv
import pickle
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pymongo import MongoClient, ASCENDING, TEXT
    from pymongo.errors import ConnectionFailure, DuplicateKeyError
except ImportError:
    print("[ERROR] pymongo not installed. Install with: pip install pymongo")
    sys.exit(1)

# ============================================
# Configuration
# ============================================

MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "dupefinder"
COLLECTION_NAME = "products"

# File paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
CATALOG_CSV = PROJECT_ROOT / "data" / "product_catalog.csv"
EMBEDDINGS_PKL = PROJECT_ROOT / "data" / "embeddings" / "product_embeddings.pkl"


# ============================================
# Helper Functions
# ============================================

def test_connection(client):
    """Test MongoDB connection"""
    try:
        # The ping command is cheap and does not require auth
        client.admin.command('ping')
        print("[OK] Successfully connected to MongoDB server")
        return True
    except ConnectionFailure as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        print("[INFO] Make sure MongoDB service is running:")
        print("       - Windows: Check 'Services' app for 'MongoDB Server'")
        print("       - Or run: net start MongoDB")
        return False


def load_embeddings(embeddings_path):
    """Load pre-computed embeddings from pickle file"""
    print(f"\n[INFO] Loading embeddings from: {embeddings_path}")
    
    if not embeddings_path.exists():
        print(f"[ERROR] Embeddings file not found: {embeddings_path}")
        print("[INFO] Run ml-engine/precompute_embeddings.py first!")
        sys.exit(1)
    
    with open(embeddings_path, 'rb') as f:
        data = pickle.load(f)
    
    embeddings = data['embeddings']
    image_paths = data['image_paths']
    
    print(f"[OK] Loaded {len(embeddings)} embeddings")
    print(f"[INFO] Embedding dimension: {embeddings[0].shape[0]}")
    
    return embeddings, image_paths


def load_product_catalog(csv_path):
    """Load product catalog from CSV"""
    print(f"\n[INFO] Loading product catalog from: {csv_path}")
    
    if not csv_path.exists():
        print(f"[ERROR] Catalog CSV not found: {csv_path}")
        sys.exit(1)
    
    products = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                'product_id': int(row['id']),
                'name': row['name'],
                'category': row['category'],
                'brand': row['brand'],
                'price': float(row['price']),
                'image_path': row['image_path'],
                'description': row.get('description', '')
            })
    
    print(f"[OK] Loaded {len(products)} products from catalog")
    return products


def create_indexes(collection):
    """Create indexes for efficient queries"""
    print("\n[INFO] Creating indexes...")
    
    try:
        # Category index
        collection.create_index([("category", ASCENDING)], name="idx_category")
        print("[OK] Created category index")
        
        # Price index
        collection.create_index([("price", ASCENDING)], name="idx_price")
        print("[OK] Created price index")
        
        # Compound category + price index
        collection.create_index(
            [("category", ASCENDING), ("price", ASCENDING)],
            name="idx_category_price"
        )
        print("[OK] Created category+price compound index")
        
        # Unique product_id index
        collection.create_index(
            [("product_id", ASCENDING)],
            unique=True,
            name="idx_product_id"
        )
        print("[OK] Created unique product_id index")
        
        # Text search index
        collection.create_index(
            [("name", TEXT), ("description", TEXT), ("brand", TEXT)],
            weights={"name": 10, "brand": 5, "description": 1},
            name="text_search_index"
        )
        print("[OK] Created text search index")
        
    except Exception as e:
        print(f"[WARNING] Some indexes may already exist: {e}")


def import_products(collection, products, embeddings, image_paths):
    """Import products with embeddings into MongoDB"""
    print("\n[INFO] Importing products into MongoDB...")
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, product in enumerate(products):
        try:
            # Find matching embedding
            # Normalize paths for comparison (remove 'data/' prefix if present)
            product_image = product['image_path'].replace('/', '\\')
            
            # Find index in image_paths
            embedding_idx = None
            for idx, img_path in enumerate(image_paths):
                # Normalize embedding path (remove 'data\' prefix for comparison)
                normalized_emb_path = img_path.replace('data\\', '').replace('/', '\\')
                if normalized_emb_path == product_image:
                    embedding_idx = idx
                    break
            
            if embedding_idx is None:
                print(f"[WARNING] No embedding found for product {product['product_id']}: {product['name']}")
                error_count += 1
                continue
            
            # Get embedding vector
            embedding_vector = embeddings[embedding_idx].tolist()
            
            # Create document
            document = {
                'product_id': product['product_id'],
                'name': product['name'],
                'category': product['category'],
                'brand': product['brand'],
                'price': product['price'],
                'image_path': product['image_path'],
                'embedding': embedding_vector,
                'description': product['description'],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert document
            result = collection.insert_one(document)
            imported_count += 1
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"[INFO] Imported {i + 1}/{len(products)} products...")
                
        except DuplicateKeyError:
            print(f"[WARNING] Product {product['product_id']} already exists, skipping")
            skipped_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to import product {product['product_id']}: {e}")
            error_count += 1
    
    print(f"\n[SUMMARY] Import completed:")
    print(f"  - Imported: {imported_count}")
    print(f"  - Skipped (duplicates): {skipped_count}")
    print(f"  - Errors: {error_count}")
    
    return imported_count


def verify_import(collection):
    """Verify the imported data"""
    print("\n[INFO] Verifying import...")
    
    # Count total products
    total_count = collection.count_documents({})
    print(f"[OK] Total products in database: {total_count}")
    
    # Count by category
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_counts = list(collection.aggregate(pipeline))
    
    print("\n[INFO] Products by category:")
    for item in category_counts:
        print(f"  - {item['_id']}: {item['count']}")
    
    # Check embedding dimensions
    sample = collection.find_one({})
    if sample and 'embedding' in sample:
        embedding_dim = len(sample['embedding'])
        print(f"\n[OK] Embedding dimension: {embedding_dim}")
        
        if embedding_dim != 2048:
            print(f"[WARNING] Expected 2048-dim embeddings, got {embedding_dim}")
    else:
        print("[WARNING] No embeddings found in sample document")
    
    # Price statistics
    pipeline = [
        {
            "$group": {
                "_id": None,
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"},
                "avg_price": {"$avg": "$price"}
            }
        }
    ]
    price_stats = list(collection.aggregate(pipeline))
    if price_stats:
        stats = price_stats[0]
        print(f"\n[INFO] Price statistics:")
        print(f"  - Min: ${stats['min_price']:.2f}")
        print(f"  - Max: ${stats['max_price']:.2f}")
        print(f"  - Avg: ${stats['avg_price']:.2f}")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("DupeFinder MongoDB Initialization")
    print("=" * 60)
    
    # Step 1: Connect to MongoDB
    print("\n[Step 1] Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    
    if not test_connection(client):
        print("\n[FAILED] Cannot proceed without MongoDB connection")
        sys.exit(1)
    
    # Step 2: Create/access database
    print(f"\n[Step 2] Creating database: {DATABASE_NAME}")
    db = client[DATABASE_NAME]
    print(f"[OK] Database '{DATABASE_NAME}' ready")
    
    # Step 3: Create/access collection
    print(f"\n[Step 3] Creating collection: {COLLECTION_NAME}")
    collection = db[COLLECTION_NAME]
    
    # Check if collection already has data
    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"[WARNING] Collection already contains {existing_count} documents")
        response = input("Do you want to drop existing data and reimport? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            collection.drop()
            print("[OK] Existing collection dropped")
            collection = db[COLLECTION_NAME]
        else:
            print("[INFO] Keeping existing data. Will skip duplicates.")
    
    # Step 4: Load embeddings
    embeddings, image_paths = load_embeddings(EMBEDDINGS_PKL)
    
    # Step 5: Load product catalog
    products = load_product_catalog(CATALOG_CSV)
    
    # Step 6: Import products
    imported = import_products(collection, products, embeddings, image_paths)
    
    # Step 7: Create indexes
    create_indexes(collection)
    
    # Step 8: Verify import
    verify_import(collection)
    
    # Success
    print("\n" + "=" * 60)
    print("[SUCCESS] MongoDB initialization complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Start the FastAPI backend")
    print("  2. Query products: db.products.find()")
    print("  3. Test similarity search with uploaded images")
    print("\nConnection string:", MONGODB_URI)
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Import cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

