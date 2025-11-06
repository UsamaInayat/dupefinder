/**
 * DupeFinder MongoDB Schema Definitions
 * MongoDB will be used for storing image data, embeddings, and unstructured data
 */

// Product Embeddings Collection
const productEmbeddingsSchema = {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["product_id", "embedding", "model_version"],
      properties: {
        product_id: {
          bsonType: "string",
          description: "UUID of the product from PostgreSQL"
        },
        embedding: {
          bsonType: "array",
          description: "Vector embedding of product image (2048 dimensions)",
          items: {
            bsonType: "double"
          }
        },
        model_version: {
          bsonType: "string",
          description: "ML model version used for embedding"
        },
        image_features: {
          bsonType: "object",
          properties: {
            dominant_colors: { bsonType: "array" },
            patterns: { bsonType: "array" },
            textures: { bsonType: "array" },
            style_tags: { bsonType: "array" }
          }
        },
        created_at: {
          bsonType: "date",
          description: "Timestamp of embedding creation"
        },
        updated_at: {
          bsonType: "date"
        }
      }
    }
  }
};

// User Search Analytics Collection
const userSearchAnalyticsSchema = {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "timestamp"],
      properties: {
        user_id: {
          bsonType: "string",
          description: "UUID of the user"
        },
        search_id: {
          bsonType: "string",
          description: "Unique search session ID"
        },
        uploaded_image: {
          bsonType: "object",
          properties: {
            url: { bsonType: "string" },
            size: { bsonType: "int" },
            dimensions: { 
              bsonType: "object",
              properties: {
                width: { bsonType: "int" },
                height: { bsonType: "int" }
              }
            }
          }
        },
        query_embedding: {
          bsonType: "array",
          description: "Embedding of uploaded image"
        },
        results: {
          bsonType: "array",
          description: "Search results with similarity scores",
          items: {
            bsonType: "object",
            properties: {
              product_id: { bsonType: "string" },
              similarity_score: { bsonType: "double" },
              rank: { bsonType: "int" }
            }
          }
        },
        filters_applied: {
          bsonType: "object",
          properties: {
            category: { bsonType: "string" },
            price_range: { 
              bsonType: "object",
              properties: {
                min: { bsonType: "double" },
                max: { bsonType: "double" }
              }
            },
            gender: { bsonType: "string" },
            city: { bsonType: "string" }
          }
        },
        user_interactions: {
          bsonType: "array",
          description: "Products clicked/viewed",
          items: {
            bsonType: "object",
            properties: {
              product_id: { bsonType: "string" },
              action: { bsonType: "string" }, // view, click, favorite, compare
              timestamp: { bsonType: "date" }
            }
          }
        },
        timestamp: {
          bsonType: "date"
        }
      }
    }
  }
};

// Image Metadata Collection
const imageMetadataSchema = {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["image_url", "type"],
      properties: {
        image_url: {
          bsonType: "string",
          description: "URL or path to image"
        },
        type: {
          bsonType: "string",
          enum: ["product", "user_upload", "community"],
          description: "Type of image"
        },
        reference_id: {
          bsonType: "string",
          description: "ID of related entity (product_id, user_id, etc.)"
        },
        storage_location: {
          bsonType: "string",
          description: "S3/Cloud storage location"
        },
        metadata: {
          bsonType: "object",
          properties: {
            file_size: { bsonType: "int" },
            format: { bsonType: "string" },
            width: { bsonType: "int" },
            height: { bsonType: "int" },
            exif_data: { bsonType: "object" }
          }
        },
        processed_versions: {
          bsonType: "array",
          description: "Different sizes/versions of the image",
          items: {
            bsonType: "object",
            properties: {
              version: { bsonType: "string" }, // thumbnail, medium, large
              url: { bsonType: "string" },
              dimensions: {
                bsonType: "object",
                properties: {
                  width: { bsonType: "int" },
                  height: { bsonType: "int" }
                }
              }
            }
          }
        },
        created_at: {
          bsonType: "date"
        }
      }
    }
  }
};

// Analytics Events Collection
const analyticsEventsSchema = {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["event_type", "timestamp"],
      properties: {
        event_type: {
          bsonType: "string",
          enum: ["search", "view", "click", "favorite", "purchase_intent", "share"],
          description: "Type of user event"
        },
        user_id: {
          bsonType: "string"
        },
        product_id: {
          bsonType: "string"
        },
        session_id: {
          bsonType: "string"
        },
        metadata: {
          bsonType: "object",
          description: "Additional event-specific data"
        },
        device_info: {
          bsonType: "object",
          properties: {
            type: { bsonType: "string" }, // mobile, web, tablet
            os: { bsonType: "string" },
            browser: { bsonType: "string" }
          }
        },
        location: {
          bsonType: "object",
          properties: {
            city: { bsonType: "string" },
            country: { bsonType: "string" },
            ip: { bsonType: "string" }
          }
        },
        timestamp: {
          bsonType: "date"
        }
      }
    }
  }
};

// ML Model Performance Logs Collection
const mlModelLogsSchema = {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["model_version", "timestamp"],
      properties: {
        model_version: {
          bsonType: "string"
        },
        search_id: {
          bsonType: "string"
        },
        performance_metrics: {
          bsonType: "object",
          properties: {
            embedding_time_ms: { bsonType: "double" },
            search_time_ms: { bsonType: "double" },
            total_time_ms: { bsonType: "double" }
          }
        },
        accuracy_feedback: {
          bsonType: "object",
          description: "User feedback on results quality",
          properties: {
            user_rating: { bsonType: "int" },
            top_k_relevant: { bsonType: "int" },
            clicked_rank: { bsonType: "int" }
          }
        },
        timestamp: {
          bsonType: "date"
        }
      }
    }
  }
};

// Export schemas for reference
module.exports = {
  productEmbeddingsSchema,
  userSearchAnalyticsSchema,
  imageMetadataSchema,
  analyticsEventsSchema,
  mlModelLogsSchema
};

/**
 * Index Creation Commands:
 * 
 * db.product_embeddings.createIndex({ "product_id": 1 }, { unique: true })
 * db.product_embeddings.createIndex({ "model_version": 1 })
 * 
 * db.user_search_analytics.createIndex({ "user_id": 1 })
 * db.user_search_analytics.createIndex({ "timestamp": -1 })
 * 
 * db.image_metadata.createIndex({ "image_url": 1 })
 * db.image_metadata.createIndex({ "reference_id": 1 })
 * 
 * db.analytics_events.createIndex({ "user_id": 1 })
 * db.analytics_events.createIndex({ "event_type": 1, "timestamp": -1 })
 * 
 * db.ml_model_logs.createIndex({ "model_version": 1 })
 * db.ml_model_logs.createIndex({ "timestamp": -1 })
 */

