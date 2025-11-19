// MongoDB Schema for DupeFinder - 40% Milestone
// Database: dupefinder
// Updated: November 9, 2025 - Switched from PostgreSQL to MongoDB

// ============================================
// Collection: products
// ============================================
// Stores product information with embeddings
// embedded directly in the document

db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "category", "brand", "price", "image_path", "embedding"],
      properties: {
        _id: {
          bsonType: "objectId",
          description: "Unique identifier (auto-generated)"
        },
        product_id: {
          bsonType: "int",
          description: "Original product ID from CSV (1-100)"
        },
        name: {
          bsonType: "string",
          description: "Product name"
        },
        category: {
          bsonType: "string",
          enum: ["bags", "shoes", "watches", "clothing", "accessories"],
          description: "Product category"
        },
        brand: {
          bsonType: "string",
          description: "Brand name"
        },
        price: {
          bsonType: "double",
          minimum: 0,
          description: "Product price in dollars"
        },
        image_path: {
          bsonType: "string",
          description: "Relative path to product image"
        },
        embedding: {
          bsonType: "array",
          items: {
            bsonType: "double"
          },
          minItems: 2048,
          maxItems: 2048,
          description: "2048-dimensional ResNet50 embedding vector"
        },
        description: {
          bsonType: "string",
          description: "Product description (optional)"
        },
        created_at: {
          bsonType: "date",
          description: "Timestamp when product was added"
        },
        updated_at: {
          bsonType: "date",
          description: "Timestamp when product was last updated"
        }
      }
    }
  }
});

// ============================================
// Indexes for products collection
// ============================================

// Index on category for filtering
db.products.createIndex({ "category": 1 });

// Index on price for range queries
db.products.createIndex({ "price": 1 });

// Compound index for category + price queries
db.products.createIndex({ "category": 1, "price": 1 });

// Text index for searching by name/description
db.products.createIndex({ 
  "name": "text", 
  "description": "text",
  "brand": "text"
}, {
  weights: {
    "name": 10,
    "brand": 5,
    "description": 1
  },
  name: "text_search_index"
});

// Index on product_id for quick lookups
db.products.createIndex({ "product_id": 1 }, { unique: true });

// ============================================
// Collection: search_history (Optional - for analytics)
// ============================================

db.createCollection("search_history", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["uploaded_image_path", "results", "timestamp"],
      properties: {
        _id: {
          bsonType: "objectId",
          description: "Unique identifier"
        },
        uploaded_image_path: {
          bsonType: "string",
          description: "Path to uploaded search image"
        },
        embedding: {
          bsonType: "array",
          items: {
            bsonType: "double"
          },
          description: "Embedding of uploaded image"
        },
        results: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              product_id: {
                bsonType: "objectId",
                description: "Reference to product"
              },
              similarity_score: {
                bsonType: "double",
                minimum: 0,
                maximum: 1,
                description: "Cosine similarity score"
              }
            }
          },
          description: "Top-K similar products"
        },
        timestamp: {
          bsonType: "date",
          description: "When search was performed"
        },
        search_time_ms: {
          bsonType: "double",
          description: "Search execution time in milliseconds"
        }
      }
    }
  }
});

// Index on timestamp for analytics
db.search_history.createIndex({ "timestamp": -1 });

// ============================================
// Sample Document Structure
// ============================================

/*
Example product document:
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "product_id": 1,
  "name": "Classic Leather Tote Bag",
  "category": "bags",
  "brand": "LuxeBrand",
  "price": 89.99,
  "image_path": "data/products/bags/product_1.jpg",
  "embedding": [0.123, -0.456, 0.789, ... (2048 dimensions)],
  "description": "Premium leather tote bag with gold hardware",
  "created_at": ISODate("2025-11-09T10:30:00Z"),
  "updated_at": ISODate("2025-11-09T10:30:00Z")
}

Example search history document:
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "uploaded_image_path": "uploads/search_20251109_103045.jpg",
  "embedding": [0.234, -0.567, 0.890, ... (2048 dimensions)],
  "results": [
    {
      "product_id": ObjectId("507f1f77bcf86cd799439011"),
      "similarity_score": 0.95
    },
    {
      "product_id": ObjectId("507f1f77bcf86cd799439013"),
      "similarity_score": 0.92
    }
  ],
  "timestamp": ISODate("2025-11-09T10:30:45Z"),
  "search_time_ms": 2.77
}
*/

// ============================================
// Useful Queries
// ============================================

// Find all products in a category
// db.products.find({ "category": "bags" })

// Find products in price range
// db.products.find({ "price": { $gte: 50, $lte: 150 } })

// Text search for products
// db.products.find({ $text: { $search: "leather bag" } })

// Get product count by category
// db.products.aggregate([
//   { $group: { _id: "$category", count: { $sum: 1 } } }
// ])

// Get average price by category
// db.products.aggregate([
//   { $group: { _id: "$category", avg_price: { $avg: "$price" } } }
// ])
