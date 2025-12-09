# DupeFinder API Documentation

**Base URL:** `http://localhost:8000`

This document provides a complete reference of all API endpoints in the DupeFinder application, organized by functional modules.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Image Search](#image-search)
3. [Products](#products)
4. [Admin Dashboard (New)](#admin-dashboard-new)
5. [Admin (Legacy)](#admin-legacy)
6. [Health & Database](#health--database)

---

## Authentication

**Base Path:** `/api/auth`

All authentication-related endpoints for user signup, login, OTP verification, and token management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Create new user account and send OTP verification email |
| `POST` | `/api/auth/verify-otp` | Verify OTP code and activate user account |
| `POST` | `/api/auth/login` | User login with email and password, returns JWT access and refresh tokens |
| `POST` | `/api/auth/refresh` | Refresh expired access token using refresh token |
| `POST` | `/api/auth/logout` | Invalidate refresh token and logout user |
| `POST` | `/api/auth/resend-otp` | Resend OTP verification email to user |

---

## Image Search

**Base Path:** `/api/search`

Endpoints for image similarity search, search history, and statistics.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search/similar` | Upload image and find similar products using ML-based image similarity |
| `POST` | `/api/search/upload` | Alternative endpoint for uploading image and finding similar products |
| `GET` | `/api/search/history` | Retrieve recent search history with pagination |
| `GET` | `/api/search/stats` | Get search statistics including total searches and average search time |

---

## Products

**Base Path:** `/api/products`

Public endpoints for browsing and retrieving product information.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | Get paginated list of products with optional filters (category, brand, price range) |
| `GET` | `/api/products/` | Alternative endpoint for getting paginated product list |
| `GET` | `/api/products/{product_id}` | Get single product details by MongoDB ObjectId |
| `GET` | `/api/products/by-product-id/{product_id}` | Get single product details by product_id (1-100) |
| `GET` | `/api/products/categories/list` | Get list of all available categories with product counts and price ranges |
| `GET` | `/api/products/brands/list` | Get list of all available brands with product counts |

---

## Admin Dashboard (New)

**Base Path:** `/api/admin`

Comprehensive admin dashboard with 4 modules: User Management, Product Catalogue, ML Training, and Auto Sync.

### Admin Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/login` | Admin login with email and password, returns admin JWT token |

### Module 1: User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/users` | Get all registered users with pagination, search, and status filtering |
| `PUT` | `/api/admin/users/{user_id}/deactivate` | Deactivate user account permanently |
| `PUT` | `/api/admin/users/{user_id}/activate` | Reactivate previously deactivated user account |
| `DELETE` | `/api/admin/users/{user_id}` | Permanently delete user account from database |

### Module 2: Product Catalogue Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/products/import-csv` | Import products in bulk from CSV file upload |
| `POST` | `/api/admin/products/cleanup-links` | Check all product image URLs and mark broken links |
| `POST` | `/api/admin/products/{product_id}/repair-link` | Re-check and attempt to repair a broken image link |
| `DELETE` | `/api/admin/products/clear-all` | Clear all products from catalogue (use with caution) |
| `DELETE` | `/api/admin/products/{product_id}` | Delete single product permanently from catalogue |
| `GET` | `/api/admin/categories` | Get all unique product categories with counts |
| `POST` | `/api/admin/categories` | Add new category tag to the system |
| `GET` | `/api/admin/products` | Get products with advanced filtering (category, brand, gender, broken links, search) |

### Module 3: ML Model Training Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/ml/train` | Trigger ML model retraining with custom train/test split ratio |
| `GET` | `/api/admin/ml/training-status/{job_id}` | Get real-time training job status and progress percentage |
| `GET` | `/api/admin/ml/metrics` | Get historical training metrics (accuracy, precision, recall, F1 score) |

### Module 4: Auto Sync / Rescraping

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/scraping/brands` | Get list of brands available for rescraping from Excel files |
| `POST` | `/api/admin/scraping/start` | Start rescraping job for selected brands |
| `GET` | `/api/admin/scraping/status/{job_id}` | Get real-time scraping job status and progress |
| `GET` | `/api/admin/scraping/history` | Get paginated scraping job history from MongoDB |
| `DELETE` | `/api/admin/scraping/history/{job_id}` | Delete scraping job from history |

---

## Admin (Legacy)

**Base Path:** `/api/admin` (older implementation)

Legacy admin endpoints for user management, product management, and analytics.

### Authentication & Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/login` | Admin login endpoint (legacy version) |
| `GET` | `/api/admin/users` | Get all users with pagination (returns UserManagementResponse model) |
| `PUT` | `/api/admin/users/{user_id}/status` | Toggle user active/inactive status (ban/unban user) |
| `DELETE` | `/api/admin/users/{user_id}` | Delete user permanently (legacy version) |

### Product Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/products` | Create new product manually in catalogue |
| `PUT` | `/api/admin/products/{product_id}` | Update existing product details |
| `DELETE` | `/api/admin/products/{product_id}` | Delete product from catalogue (legacy version) |

### Analytics & System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/stats` | Get comprehensive system statistics (users, products, searches, top categories) |
| `GET` | `/api/admin/analytics/searches` | Get search analytics for specified number of days (1-30) |
| `GET` | `/api/admin/health` | Check system health including database and ML engine status |

---

## Health & Database

System health checks and database monitoring endpoints.

### Health Checks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Main health check endpoint returning system, database, and ML engine status |
| `GET` | `/ping` | Simple ping endpoint for quick availability check |

### Database

**Base Path:** `/api/database`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/database/health` | Check MongoDB Atlas connection health |
| `GET` | `/api/database/stats` | Get database statistics for all collections |
| `GET` | `/api/database/collections` | List all collections in the MongoDB database |

---

## Authentication & Authorization

### JWT Token Format

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Types

- **Access Token**: Short-lived (30 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens
- **Admin Token**: Special JWT token with `role: "admin"` claim

### Protected Endpoints

- All `/api/admin/*` endpoints require admin authentication
- User-specific endpoints require valid user access token
- Public endpoints: `/api/products`, `/api/search`, `/health`, `/ping`

---

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Paginated Response

```json
{
  "items": [ ... ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider adding:
- Rate limiting on OTP generation endpoints (prevent spam)
- Rate limiting on image search endpoints (prevent abuse)
- Rate limiting on scraping endpoints (protect resources)

---

## CORS Configuration

The backend is configured to allow CORS requests from:
- `http://localhost:3000` (React frontend)
- `http://localhost:5173` (Vite dev server)
- Mobile app origins (configured in backend)

---

## Database Collections

### MongoDB Collections Used

1. **users** - User accounts with authentication data
2. **otps** - One-time passwords for email verification (TTL: 10 minutes)
3. **refresh_tokens** - Active refresh tokens (TTL: 7 days)
4. **products** - Product catalogue with embeddings
5. **search_history** - User search history and results
6. **scraping_history** - Scraping job history and logs
7. **admins** - Admin accounts with elevated privileges

---

## External Dependencies

### ML Engine

- **Model**: ResNet50 (pre-trained on ImageNet)
- **Embedding Dimension**: 2048
- **Similarity Metric**: Cosine similarity
- **Device**: CPU (can be configured for GPU)

### Email Service

- **Provider**: Gmail SMTP
- **Sender**: ussamainayat@gmail.com
- **OTP Format**: 6-digit numeric code
- **Expiration**: 10 minutes

---

## Notes

1. **Duplicate Endpoints**: Some endpoints exist in both `admin.py` (legacy) and `admin_new.py` (current). The `admin_new.py` endpoints are the actively maintained version.

2. **Image Upload**: Image search endpoints accept multipart/form-data with file upload. Supported formats: JPG, PNG, WebP, BMP.

3. **CSV Import**: Product CSV import expects columns: `name`, `category`, `brand`, `price`, `image_url`, `description`.

4. **Scraping**: The scraping module reads from Excel files (`women links dataset.xlsx`, `men dataset.xlsx`, `local_brands_links.csv`) in the project root.

5. **Gender Field**: Products have a `gender` field (`m` for men, `w` for women) used for filtering and categorization.

---

## Getting Started

### 1. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

### 3. Create Admin Account

```bash
python backend/create_admin.py
```

### 4. Login as Admin

```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dupefinder.com","password":"admin123"}'
```

---

## Support

For issues or questions, refer to:
- `README.md` - Project overview and setup
- `ARCHITECTURE.md` - System architecture details
- `.cursor/scratchpad.md` - Development progress and decisions

---

**Last Updated**: December 9, 2025

