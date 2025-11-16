# Admin Dashboard API - Backend Complete! 🎉

## 📊 Implementation Status

✅ **Backend Complete** - All 4 modules implemented with 14 endpoints  
⏳ **Frontend** - Next step (Phase D)

---

## 🔐 Authentication

All admin endpoints require authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

---

## 📡 API Endpoints

### **MODULE 1: User Management**

#### 1. Get All Users (with pagination & filtering)
```http
GET /api/admin/users
```

**Query Parameters:**
- `page` (default: 1) - Page number
- `page_size` (default: 20) - Users per page
- `search` - Search by email
- `status_filter` - Filter by status: `active`, `inactive`, `all`

**Response:**
```json
{
  "users": [
    {
      "_id": "user_id",
      "email": "user@example.com",
      "is_active": true,
      "is_verified": true,
      "created_at": "2025-11-11T...",
      "last_login": "2025-11-11T..."
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 2. Deactivate User
```http
PUT /api/admin/users/{user_id}/deactivate
```

**Response:**
```json
{
  "success": true,
  "message": "User deactivated successfully",
  "user_id": "..."
}
```

#### 3. Activate User
```http
PUT /api/admin/users/{user_id}/activate
```

---

### **MODULE 2: Product Catalogue Management**

#### 4. Import Products from CSV
```http
POST /api/admin/products/import-csv
Content-Type: multipart/form-data
```

**Body:** File upload (CSV)

**CSV Format:**
```csv
name,category,brand,price,image_url,description
Product 1,bags,Brand A,99.99,https://...,Description...
Product 2,shoes,Brand B,149.99,https://...,Description...
```

**Response:**
```json
{
  "success": true,
  "message": "Import completed",
  "total_rows": 100,
  "imported": 95,
  "failed": 5,
  "errors": ["Row 3: Invalid price", "..."]
}
```

#### 5. Cleanup Broken Links
```http
POST /api/admin/products/cleanup-links
```

Checks all product image URLs and marks broken ones.

**Response:**
```json
{
  "success": true,
  "checked": 100,
  "broken": 12,
  "working": 88,
  "broken_ids": ["id1", "id2", "..."]
}
```

#### 6. Get All Categories
```http
GET /api/admin/categories
```

**Response:**
```json
{
  "categories": [
    {"name": "bags", "count": 45},
    {"name": "shoes", "count": 32}
  ],
  "total": 2
}
```

#### 7. Add Category
```http
POST /api/admin/categories?category_name=accessories
```

#### 8. Get Products (Admin View)
```http
GET /api/admin/products
```

**Query Parameters:**
- `page`, `page_size` - Pagination
- `category` - Filter by category
- `brand` - Filter by brand
- `broken_links_only` (boolean) - Show only broken links
- `search` - Search by name or description

**Response:**
```json
{
  "products": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### **MODULE 3: ML Model Training Dashboard**

#### 9. Trigger Model Training
```http
POST /api/admin/ml/train?train_split=0.8
```

**Query Parameters:**
- `train_split` (0.5-0.95) - Training/Test split ratio (default: 0.8)

**Response:**
```json
{
  "success": true,
  "job_id": "uuid-here",
  "message": "Training started",
  "train_split": 0.8
}
```

#### 10. Get Training Status
```http
GET /api/admin/ml/training-status/{job_id}
```

**Response:**
```json
{
  "job_id": "...",
  "status": "running",
  "progress": 60,
  "train_split": 0.8,
  "started_at": "...",
  "message": "Training in progress..."
}
```

Status values: `pending`, `running`, `completed`, `failed`

#### 11. Get Training Metrics (History)
```http
GET /api/admin/ml/metrics?limit=10
```

**Response:**
```json
{
  "metrics": [
    {
      "job_id": "...",
      "status": "completed",
      "train_split": 0.8,
      "completed_at": "...",
      "metrics": {
        "accuracy": 0.92,
        "precision": 0.89,
        "recall": 0.91,
        "f1_score": 0.90
      }
    }
  ],
  "total": 5
}
```

---

### **MODULE 4: Auto Sync / Rescraping**

#### 12. Get Available Brands
```http
GET /api/admin/scraping/brands
```

**Response:**
```json
{
  "brands": [
    {
      "brand_name": "Nike",
      "product_count": 45,
      "last_scraped_at": "2025-11-10T..."
    }
  ],
  "total": 10
}
```

#### 13. Start Rescraping
```http
POST /api/admin/scraping/start
Content-Type: application/json

{
  "brand_ids": ["Nike", "Adidas", "Puma"]
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "uuid-here",
  "message": "Scraping started for 3 brand(s)"
}
```

#### 14. Get Scraping Status
```http
GET /api/admin/scraping/status/{job_id}
```

**Response:**
```json
{
  "job_id": "...",
  "status": "running",
  "brands": ["Nike", "Adidas"],
  "brands_completed": 1,
  "brands_total": 2,
  "products_added": 15,
  "started_at": "...",
  "logs": [
    "Scraping Nike...",
    "Completed Nike: 15 products added",
    "Scraping Adidas..."
  ]
}
```

#### 15. Get Scraping History
```http
GET /api/admin/scraping/history?limit=10
```

---

## 🧪 Testing the API

### Using Swagger UI (Recommended)
1. Backend must be running: http://localhost:8000
2. Go to: http://localhost:8000/api/docs
3. Click **Authorize** button
4. Enter: `Bearer <your_access_token>`
5. Try out any endpoint!

### Using cURL

**Example: Get All Users**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/admin/users?page=1&page_size=10"
```

**Example: Import CSV**
```bash
curl -X POST "http://localhost:8000/api/admin/products/import-csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products.csv"
```

**Example: Start Training**
```bash
curl -X POST "http://localhost:8000/api/admin/ml/train?train_split=0.85" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📦 Dependencies Added

The following packages are required (already in requirements.txt):
- `pandas` - For CSV processing
- `httpx` - For checking image URLs (async HTTP client)

---

## 🎯 What's Working Now

✅ **Module 1**: User Management
  - View all users with pagination
  - Search by email
  - Filter by active/inactive status
  - Deactivate/activate accounts

✅ **Module 2**: Product Catalogue Management
  - CSV bulk import with validation
  - Broken link detection and marking
  - Category management and stats
  - Product filtering and search

✅ **Module 3**: ML Training Dashboard
  - Trigger training with custom train/test split
  - Real-time progress tracking
  - Historical metrics storage
  - Performance metrics (accuracy, precision, recall, F1)

✅ **Module 4**: Auto Sync/Rescraping
  - Brand listing with stats
  - Multi-brand scraping jobs
  - Progress monitoring with logs
  - Scraping history

---

## 🚀 Next Steps

**Frontend Implementation (Phase D):**
1. Create Admin Dashboard layout
2. User Management UI
3. Product Management UI (with CSV upload)
4. ML Training Dashboard UI (with sliders and charts)
5. Scraping Management UI (brand selection, progress bars)

**Then:**
- Phase E: Apply black & white theme
- Phase F: Integration testing

---

## 📊 API Summary

| Module | Endpoints | Status |
|--------|-----------|--------|
| User Management | 3 | ✅ Complete |
| Product Catalogue | 5 | ✅ Complete |
| ML Training | 3 | ✅ Complete |
| Auto Sync/Scraping | 3 | ✅ Complete |
| **TOTAL** | **14** | **✅ Backend Complete** |

---

## 🔥 Ready to Use!

The backend is fully functional and ready for frontend integration!

**Next:** Build the Admin Dashboard Frontend to interact with these endpoints.






