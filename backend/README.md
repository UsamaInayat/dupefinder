# DupeFinder Backend API

FastAPI backend for image-based fashion search and similarity matching.

**Version**: 0.1.0 (40% Milestone)  
**Created**: November 9, 2025  
**Database**: MongoDB

---

## 📋 Features

- ✅ **Image Upload & Search**: Upload fashion images to find similar products
- ✅ **Product Management**: Browse, filter, and search products
- ✅ **MongoDB Integration**: Stores products with embeddings
- ✅ **ResNet50 ML Engine**: Extract 2048-dim embeddings for similarity
- ✅ **RESTful API**: Clean, documented endpoints
- ✅ **CORS Support**: Ready for React frontend integration
- ✅ **Search History**: Track and analyze searches
- ✅ **Health Check**: Monitor system status

---

## 🏗️ Architecture

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── health.py      # Health check endpoints
│   │       ├── products.py    # Product CRUD endpoints
│   │       └── search.py      # Image search endpoints
│   ├── core/
│   │   └── database.py        # MongoDB connection
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   └── main.py                # FastAPI application
├── init_mongodb.py            # Database initialization script
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **MongoDB** installed and running
3. **ML Engine embeddings** pre-computed (from ml-engine/)

### Installation

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install ML engine dependencies (if not already done)
cd ../ml-engine
pip install -r requirements.txt
cd ../backend

# 5. Install Playwright browsers (required for Admin scraping / Auto Sync)
playwright install chromium
```

### Database Setup

```bash
# 1. Ensure MongoDB is running
# Windows: Check Services for "MongoDB Server"
# Or start manually: net start MongoDB

# 2. Initialize database and import products
python init_mongodb.py
```

Expected output:
```
============================================================
DupeFinder MongoDB Initialization
============================================================

[Step 1] Connecting to MongoDB...
[OK] Successfully connected to MongoDB server

[Step 2] Creating database: dupefinder
[OK] Database 'dupefinder' ready

[INFO] Loading embeddings from: ml-engine/product_embeddings.pkl
[OK] Loaded 100 embeddings

[INFO] Loading product catalog from: data/product_catalog.csv
[OK] Loaded 100 products from catalog

[INFO] Importing products into MongoDB...
[INFO] Imported 100/100 products...

[SUMMARY] Import completed:
  - Imported: 100
  - Skipped (duplicates): 0
  - Errors: 0

[SUCCESS] MongoDB initialization complete!
```

### Run the Server

```bash
# Start FastAPI server
python app/main.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

---

## 📚 API Endpoints

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

## 🔍 Endpoint Reference

### Health Check

#### `GET /health`
Check system health including database and ML engine status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T10:30:00",
  "database": {
    "status": "connected",
    "database": "dupefinder",
    "products_count": 100
  },
  "ml_engine": {
    "status": "available",
    "model": "ResNet50",
    "embedding_dim": 2048
  }
}
```

#### `GET /ping`
Simple ping for quick health check.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-09T10:30:00"
}
```

---

### Products

#### `GET /api/products`
Get paginated list of products with optional filters.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page
- `category` (string): Filter by category (bags/shoes/watches/clothing/accessories)
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price
- `brand` (string): Filter by brand name
- `search` (string): Text search in name/description/brand

**Example:**
```bash
curl "http://localhost:8000/api/products?category=bags&min_price=50&max_price=150&page=1&page_size=10"
```

**Response:**
```json
{
  "products": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "product_id": 1,
      "name": "Classic Leather Tote Bag",
      "category": "bags",
      "brand": "LuxeBrand",
      "price": 89.99,
      "image_path": "data/products/bags/product_1.jpg",
      "description": "Premium leather tote bag",
      "created_at": "2025-11-09T10:30:00",
      "updated_at": "2025-11-09T10:30:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### `GET /api/products/{product_id}`
Get single product by MongoDB ObjectId.

**Example:**
```bash
curl "http://localhost:8000/api/products/507f1f77bcf86cd799439011"
```

#### `GET /api/products/by-product-id/{product_id}`
Get single product by product_id (1-100).

**Example:**
```bash
curl "http://localhost:8000/api/products/by-product-id/1"
```

#### `GET /api/products/categories/list`
Get all categories with statistics.

**Response:**
```json
{
  "categories": [
    {
      "name": "bags",
      "count": 20,
      "avg_price": 125.50,
      "price_range": {
        "min": 50.00,
        "max": 250.00
      }
    }
  ],
  "total_categories": 5
}
```

#### `GET /api/products/brands/list`
Get all brands with product counts.

---

### Image Search

#### `POST /api/search/upload`
Search for similar products by uploading an image.

**Form Data:**
- `file` (file, required): Image file (JPG, PNG, WebP, BMP)

**Query Parameters:**
- `top_k` (int, default: 5, max: 20): Number of results
- `category` (string): Filter by category
- `min_price` (float): Minimum price filter
- `max_price` (float): Maximum price filter

**Example:**
```bash
curl -X POST "http://localhost:8000/api/search/upload?top_k=5" \
  -F "file=@my_bag_image.jpg"
```

**Response:**
```json
{
  "query_image": "data/uploads/search_20251109_103045_my_bag_image.jpg",
  "results": [
    {
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
  ],
  "search_time_ms": 2.77,
  "total_results": 5
}
```

#### `GET /api/search/history`
Get recent search history.

**Query Parameters:**
- `limit` (int, default: 10, max: 100): Number of entries

#### `GET /api/search/stats`
Get search statistics (total searches, avg search time, etc.)

---

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Get all products
curl http://localhost:8000/api/products

# Get bags only
curl "http://localhost:8000/api/products?category=bags"

# Search by image
curl -X POST "http://localhost:8000/api/search/upload?top_k=5" \
  -F "file=@path/to/your/image.jpg"
```

### Using Python Requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Get products
response = requests.get("http://localhost:8000/api/products", params={
    "category": "bags",
    "min_price": 50,
    "max_price": 150
})
print(response.json())

# Search by image
with open("my_bag_image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/search/upload",
        files={"file": f},
        params={"top_k": 5}
    )
    print(response.json())
```

### Using FastAPI Docs

Navigate to http://localhost:8000/api/docs and use the interactive "Try it out" feature!

---

## ⚙️ Configuration

### MongoDB Connection

Edit `backend/app/core/database.py`:
```python
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "dupefinder"
```

Or set environment variables:
```bash
export MONGODB_URI="mongodb://localhost:27017/"
export DATABASE_NAME="dupefinder"
```

### CORS Origins

Edit `backend/app/main.py` to add allowed origins:
```python
allow_origins=[
    "http://localhost:3000",  # React frontend
    "http://your-frontend-url.com"
]
```

---

## 📊 Database Schema

### Collection: `products`

```javascript
{
  _id: ObjectId("..."),
  product_id: 1,
  name: "Classic Leather Tote Bag",
  category: "bags",  // bags|shoes|watches|clothing|accessories
  brand: "LuxeBrand",
  price: 89.99,
  image_path: "data/products/bags/product_1.jpg",
  embedding: [0.123, -0.456, ...],  // 2048-dim array
  description: "Premium leather tote bag",
  created_at: ISODate("2025-11-09T10:30:00Z"),
  updated_at: ISODate("2025-11-09T10:30:00Z")
}
```

### Collection: `search_history`

```javascript
{
  _id: ObjectId("..."),
  uploaded_image_path: "data/uploads/search_20251109_103045.jpg",
  embedding: [0.234, -0.567, ...],  // 2048-dim array
  results: [
    {
      product_id: ObjectId("..."),
      similarity_score: 0.95
    }
  ],
  timestamp: ISODate("2025-11-09T10:30:45Z"),
  search_time_ms: 2.77
}
```

---

## 🐛 Troubleshooting

### MongoDB Connection Error

```
[ERROR] Failed to connect to MongoDB
```

**Solutions:**
1. Check if MongoDB service is running:
   - Windows: Open Services, look for "MongoDB Server"
   - Or run: `net start MongoDB`
2. Verify connection string: `mongodb://localhost:27017/`
3. Check firewall settings

### Module Not Found Error

```
ModuleNotFoundError: No module named 'pymongo'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Image Upload Error

```
[ERROR] Failed to extract embedding
```

**Solution:**
1. Ensure ML engine dependencies are installed
2. Check image file is valid (JPG, PNG, WebP, BMP)
3. Verify ResNet50 model is downloaded (first run takes ~1 minute)

### No Products Found

```
[ERROR] No products found matching the filters
```

**Solution:**
Run database initialization:
```bash
python init_mongodb.py
```

---

## 📈 Performance

- **Search Time**: ~3-10ms per query (100 products, CPU)
- **Upload Time**: ~500-1500ms (includes embedding extraction)
- **Database Query**: ~1-5ms per query
- **Embedding Extraction**: ~400-1400ms per image (CPU)

---

## 🔄 Development

### Auto-reload on Code Changes

```bash
uvicorn app.main:app --reload
```

### Add New Endpoints

1. Create route file in `app/api/routes/`
2. Import in `app/main.py`
3. Include router:
   ```python
   app.include_router(your_router, prefix="/api/your-route", tags=["Your Tag"])
   ```

### Add Database Indexes

Edit `database/schemas/mongodb_schema.js` and run:
```bash
mongo dupefinder < database/schemas/mongodb_schema.js
```

---

## 📝 Next Steps (60% Milestone)

- [ ] Add user authentication (JWT)
- [ ] Implement rate limiting
- [ ] Add caching (Redis)
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Add more advanced filters
- [ ] Implement FAISS for faster similarity search
- [ ] Add image preprocessing optimizations
- [ ] GPU support for faster embeddings

---

## 📄 License

Part of DupeFinder FYP Project (2025)

---

## 🤝 Contributing

This is a Final Year Project. For questions or issues, contact the project team.

---

**Status**: ✅ Ready for 40% Milestone Demo  
**Last Updated**: November 9, 2025
