"""
Insert dummy data into MongoDB Atlas to test the connection
Run this script to populate the database with sample data
"""

import asyncio
import sys
from datetime import datetime
from app.core.database import connect_to_mongo, get_database, check_connection
from app.core.config import settings


async def insert_dummy_data():
    """Insert dummy data into MongoDB collections"""
    print("=" * 60)
    print("Inserting Dummy Data into MongoDB Atlas")
    print("=" * 60)
    print(f"Database: {settings.MONGO_DB_NAME}")
    print("-" * 60)
    
    try:
        # Connect to database
        print("[*] Connecting to MongoDB Atlas...")
        await connect_to_mongo()
        print("[OK] Connected successfully!")
        
        # Verify connection
        if not await check_connection():
            print("[ERROR] Connection verification failed!")
            return False
        
        db = get_database()
        print(f"[OK] Using database: {db.name}\n")
        
        # 1. Insert Product Embeddings
        print("[*] Inserting product embeddings...")
        embeddings_collection = db["product_embeddings"]
        
        # Create dummy embeddings (2048 dimensions filled with sample values)
        dummy_embedding = [0.1 * (i % 10) for i in range(2048)]
        
        product_embeddings = [
            {
                "product_id": "prod_001",
                "embedding": dummy_embedding,
                "model_version": "resnet50",
                "image_features": {
                    "dominant_colors": ["#FF5733", "#33FF57", "#3357FF"],
                    "patterns": ["solid", "minimal"],
                    "textures": ["smooth"],
                    "style_tags": ["modern", "classic"]
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "product_id": "prod_002",
                "embedding": [0.2 * (i % 10) for i in range(2048)],
                "model_version": "resnet50",
                "image_features": {
                    "dominant_colors": ["#FF33A1", "#A133FF"],
                    "patterns": ["striped"],
                    "textures": ["textured"],
                    "style_tags": ["vintage", "elegant"]
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "product_id": "prod_003",
                "embedding": [0.3 * (i % 10) for i in range(2048)],
                "model_version": "efficientnet-b0",
                "image_features": {
                    "dominant_colors": ["#000000", "#FFFFFF"],
                    "patterns": ["geometric"],
                    "textures": ["glossy"],
                    "style_tags": ["minimalist", "contemporary"]
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        result = await embeddings_collection.insert_many(product_embeddings)
        print(f"[OK] Inserted {len(result.inserted_ids)} product embeddings")
        
        # 2. Insert User Search Analytics
        print("[*] Inserting user search analytics...")
        analytics_collection = db["user_search_analytics"]
        
        search_analytics = [
            {
                "user_id": "user_001",
                "search_id": "search_001",
                "uploaded_image": {
                    "url": "https://example.com/images/watch1.jpg",
                    "size": 245678,
                    "dimensions": {"width": 800, "height": 600}
                },
                "query_embedding": dummy_embedding[:100],  # Shorter for demo
                "results": [
                    {"product_id": "prod_001", "similarity_score": 0.95, "rank": 1},
                    {"product_id": "prod_002", "similarity_score": 0.87, "rank": 2},
                    {"product_id": "prod_003", "similarity_score": 0.82, "rank": 3}
                ],
                "filters_applied": {
                    "category": "Watches",
                    "price_range": {"min": 50, "max": 200},
                    "gender": "unisex"
                },
                "user_interactions": [
                    {"product_id": "prod_001", "action": "view", "timestamp": datetime.utcnow()},
                    {"product_id": "prod_001", "action": "click", "timestamp": datetime.utcnow()}
                ],
                "timestamp": datetime.utcnow()
            },
            {
                "user_id": "user_002",
                "search_id": "search_002",
                "uploaded_image": {
                    "url": "https://example.com/images/bag1.jpg",
                    "size": 312456,
                    "dimensions": {"width": 1024, "height": 768}
                },
                "results": [
                    {"product_id": "prod_002", "similarity_score": 0.92, "rank": 1}
                ],
                "filters_applied": {
                    "category": "Bags",
                    "max_price": 150
                },
                "timestamp": datetime.utcnow()
            }
        ]
        
        result = await analytics_collection.insert_many(search_analytics)
        print(f"[OK] Inserted {len(result.inserted_ids)} search analytics records")
        
        # 3. Insert Image Metadata
        print("[*] Inserting image metadata...")
        images_collection = db["image_metadata"]
        
        image_metadata = [
            {
                "image_url": "https://example.com/products/watch1.jpg",
                "type": "product",
                "reference_id": "prod_001",
                "storage_location": "s3://dupefinder-images/products/watch1.jpg",
                "metadata": {
                    "file_size": 245678,
                    "format": "JPEG",
                    "width": 800,
                    "height": 600
                },
                "processed_versions": [
                    {
                        "version": "thumbnail",
                        "url": "https://example.com/products/watch1_thumb.jpg",
                        "dimensions": {"width": 200, "height": 150}
                    },
                    {
                        "version": "medium",
                        "url": "https://example.com/products/watch1_med.jpg",
                        "dimensions": {"width": 400, "height": 300}
                    }
                ],
                "created_at": datetime.utcnow()
            },
            {
                "image_url": "https://example.com/products/bag1.jpg",
                "type": "product",
                "reference_id": "prod_002",
                "storage_location": "s3://dupefinder-images/products/bag1.jpg",
                "metadata": {
                    "file_size": 312456,
                    "format": "JPEG",
                    "width": 1024,
                    "height": 768
                },
                "created_at": datetime.utcnow()
            },
            {
                "image_url": "https://example.com/uploads/user_upload_001.jpg",
                "type": "user_upload",
                "reference_id": "user_001",
                "metadata": {
                    "file_size": 189234,
                    "format": "PNG",
                    "width": 600,
                    "height": 600
                },
                "created_at": datetime.utcnow()
            }
        ]
        
        result = await images_collection.insert_many(image_metadata)
        print(f"[OK] Inserted {len(result.inserted_ids)} image metadata records")
        
        # 4. Insert Analytics Events
        print("[*] Inserting analytics events...")
        events_collection = db["analytics_events"]
        
        events = [
            {
                "event_type": "search",
                "user_id": "user_001",
                "product_id": None,
                "session_id": "session_001",
                "metadata": {"search_type": "image", "results_count": 5},
                "device_info": {
                    "type": "mobile",
                    "os": "iOS",
                    "browser": "Safari"
                },
                "location": {
                    "city": "Karachi",
                    "country": "Pakistan",
                    "ip": "192.168.1.1"
                },
                "timestamp": datetime.utcnow()
            },
            {
                "event_type": "view",
                "user_id": "user_001",
                "product_id": "prod_001",
                "session_id": "session_001",
                "metadata": {"view_duration": 15},
                "device_info": {
                    "type": "mobile",
                    "os": "iOS",
                    "browser": "Safari"
                },
                "timestamp": datetime.utcnow()
            },
            {
                "event_type": "favorite",
                "user_id": "user_002",
                "product_id": "prod_002",
                "session_id": "session_002",
                "metadata": {},
                "device_info": {
                    "type": "web",
                    "os": "Windows",
                    "browser": "Chrome"
                },
                "timestamp": datetime.utcnow()
            },
            {
                "event_type": "click",
                "user_id": "user_001",
                "product_id": "prod_001",
                "session_id": "session_001",
                "metadata": {"source": "search_results"},
                "timestamp": datetime.utcnow()
            }
        ]
        
        result = await events_collection.insert_many(events)
        print(f"[OK] Inserted {len(result.inserted_ids)} analytics events")
        
        # 5. Insert ML Model Logs
        print("[*] Inserting ML model logs...")
        logs_collection = db["ml_model_logs"]
        
        model_logs = [
            {
                "model_version": "resnet50",
                "search_id": "search_001",
                "performance_metrics": {
                    "embedding_time_ms": 45.2,
                    "search_time_ms": 12.5,
                    "total_time_ms": 57.7
                },
                "accuracy_feedback": {
                    "user_rating": 5,
                    "top_k_relevant": 3,
                    "clicked_rank": 1
                },
                "timestamp": datetime.utcnow()
            },
            {
                "model_version": "efficientnet-b0",
                "search_id": "search_002",
                "performance_metrics": {
                    "embedding_time_ms": 38.1,
                    "search_time_ms": 10.3,
                    "total_time_ms": 48.4
                },
                "accuracy_feedback": {
                    "user_rating": 4,
                    "top_k_relevant": 2,
                    "clicked_rank": 1
                },
                "timestamp": datetime.utcnow()
            }
        ]
        
        result = await logs_collection.insert_many(model_logs)
        print(f"[OK] Inserted {len(result.inserted_ids)} ML model logs")
        
        # Display summary
        print("\n" + "=" * 60)
        print("Data Insertion Summary")
        print("=" * 60)
        
        collections = [
            "product_embeddings",
            "user_search_analytics",
            "image_metadata",
            "analytics_events",
            "ml_model_logs"
        ]
        
        for collection_name in collections:
            count = await db[collection_name].count_documents({})
            print(f"  {collection_name}: {count} documents")
        
        print("\n" + "=" * 60)
        print("[OK] All dummy data inserted successfully!")
        print("=" * 60)
        print("\nYou can now verify the data in MongoDB Atlas dashboard")
        print("or use the API endpoints to query the data.")
        print("\nAPI Endpoints:")
        print("  - GET /api/database/stats - View collection statistics")
        print("  - GET /api/database/collections - List all collections")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to insert data: {e}")
        print("\nTroubleshooting:")
        print("1. Check MongoDB Atlas connection")
        print("2. Verify database permissions")
        print("3. Check internet connection")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(insert_dummy_data())
    sys.exit(0 if success else 1)

