# DupeFinder API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://api.dupefinder.com (TBD)
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "access_token": "jwt_token"
}
```

#### Login
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

### Products

#### List Products
```http
GET /api/products
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `category` (string): Filter by category
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price
- `gender` (string): male, female, unisex
- `city` (string): Filter by city

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Product Name",
      "description": "Product description",
      "price": 49.99,
      "original_price": 500.00,
      "savings": 450.01,
      "image_url": "https://...",
      "category": "Watches",
      "brand": "Brand Name",
      "source_url": "https://...",
      "availability": "in_stock"
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 8
}
```

#### Get Product Details
```http
GET /api/products/{product_id}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Product Name",
  "description": "Detailed description",
  "price": 49.99,
  "original_price": 500.00,
  "images": ["url1", "url2"],
  "category": "Watches",
  "specifications": {
    "color": "Silver",
    "material": "Stainless Steel",
    "size": "42mm"
  },
  "reviews_summary": {
    "average_rating": 4.5,
    "total_reviews": 120
  }
}
```

### Search

#### Image Search
```http
POST /api/search/image
```

**Request Body (multipart/form-data):**
- `image`: Image file
- `filters`: JSON object (optional)

```json
{
  "category": "Watches",
  "max_price": 100,
  "gender": "male"
}
```

**Response:**
```json
{
  "search_id": "uuid",
  "results": [
    {
      "product_id": "uuid",
      "name": "Similar Product",
      "similarity_score": 0.95,
      "price": 49.99,
      "image_url": "https://...",
      "savings": 450.01
    }
  ],
  "total_results": 25,
  "processing_time_ms": 150
}
```

#### Text Search
```http
GET /api/search/text
```

**Query Parameters:**
- `q` (string): Search query
- `category` (string): Filter by category
- `page` (int): Page number
- `limit` (int): Results per page

**Response:**
```json
{
  "query": "silver watch",
  "results": [...],
  "total": 45
}
```

### Reviews

#### Get Product Reviews
```http
GET /api/reviews/{product_id}
```

**Query Parameters:**
- `page` (int): Page number
- `limit` (int): Reviews per page
- `sort`: recent, helpful, rating

**Response:**
```json
{
  "product_id": "uuid",
  "reviews": [
    {
      "id": "uuid",
      "user": {
        "username": "johndoe",
        "is_verified": true
      },
      "rating": 5,
      "title": "Excellent quality!",
      "comment": "Great alternative to luxury brand...",
      "helpful_count": 24,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "average_rating": 4.5,
  "total_reviews": 120
}
```

#### Create Review
```http
POST /api/reviews
```

**Request Body:**
```json
{
  "product_id": "uuid",
  "rating": 5,
  "title": "Great product",
  "comment": "Highly recommend..."
}
```

### Favorites

#### Get User Favorites
```http
GET /api/favorites
```

**Response:**
```json
{
  "favorites": [
    {
      "id": "uuid",
      "product": {...},
      "added_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 15
}
```

#### Add to Favorites
```http
POST /api/favorites
```

**Request Body:**
```json
{
  "product_id": "uuid"
}
```

#### Remove from Favorites
```http
DELETE /api/favorites/{product_id}
```

### Analytics

#### User Savings
```http
GET /api/analytics/savings
```

**Response:**
```json
{
  "total_savings": 1250.50,
  "items_found": 25,
  "average_savings": 50.02,
  "top_categories": [
    {
      "category": "Watches",
      "savings": 600.00
    }
  ]
}
```

#### Trending Products
```http
GET /api/analytics/trending
```

**Response:**
```json
{
  "trending": [
    {
      "product": {...},
      "view_count": 1520,
      "search_count": 340
    }
  ]
}
```

### Community

#### List Community Posts
```http
GET /api/community/posts
```

**Response:**
```json
{
  "posts": [
    {
      "id": "uuid",
      "title": "Looking for alternative to Rolex Submariner",
      "description": "Budget around $100",
      "image_url": "https://...",
      "status": "open",
      "replies_count": 5,
      "upvotes": 12,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Post
```http
POST /api/community/posts
```

**Request Body:**
```json
{
  "title": "Looking for dupe",
  "description": "Details...",
  "image_url": "https://...",
  "luxury_item_name": "Brand Item"
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Rate Limiting

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Admin users**: No limit

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1640995200
```

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page`: Page number (1-indexed)
- `limit`: Items per page (max: 100)

**Response Headers:**
```
X-Total-Count: 1500
X-Page-Count: 75
Link: <url>; rel="next", <url>; rel="prev"
```

## Versioning

API version is included in the URL path:
```
/api/v1/products
/api/v2/products (future)
```

Current version: v1 (implicit, no version in path)

