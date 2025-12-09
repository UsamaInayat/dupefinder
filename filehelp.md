# DupeFinder Codebase - File Documentation

**Last Updated**: December 9, 2025

This document provides a comprehensive overview of every active file in the DupeFinder codebase, explaining what each file does and how it contributes to the application.

---

## Table of Contents

1. [Backend (Python/FastAPI)](#backend-pythonfastapi)
   - [Main Application](#main-application)
   - [Core Modules](#core-modules)
   - [API Routes](#api-routes)
   - [Models](#models)
   - [Services](#services)
   - [Utilities](#utilities)
   - [Dependencies](#dependencies)
2. [Frontend (React/Vite)](#frontend-reactvite)
   - [Entry Points](#entry-points)
   - [Pages](#pages)
   - [Components](#components)
   - [Context](#context)
   - [Styles](#styles)
3. [Mobile App (Flutter/Dart)](#mobile-app-flutterdart)
   - [Main](#main)
   - [Screens](#screens)
   - [Services](#services-1)
4. [ML Engine (Python)](#ml-engine-python)
   - [Preprocessing](#preprocessing)
   - [Embeddings](#embeddings)
   - [Similarity](#similarity)
5. [Configuration Files](#configuration-files)

---

## Backend (Python/FastAPI)

The backend is built with FastAPI and handles all API requests, database operations, ML processing, and business logic.

### Main Application

#### `backend/app/main.py`

**Purpose**: Entry point for the FastAPI application. Sets up the server, middleware, and routes.

**Key Functions**:
- **App Initialization**: Creates FastAPI app instance with title, description, and version
- **CORS Middleware**: Allows cross-origin requests from frontend (localhost:3000, localhost:5173) and mobile apps
- **Route Registration**: Includes all API routers (auth, products, search, admin, database, health)
- **Root Endpoint**: `/` returns welcome message and available endpoints
- **Startup Event**: Initializes database connection when server starts

**Dependencies**: 
- FastAPI, CORS middleware
- All route modules from `app/api/routes/`

**How It Works**:
1. Server starts and connects to MongoDB
2. Registers all API route modules (auth, products, search, admin)
3. Applies CORS middleware to allow frontend/mobile access
4. Listens on port 8000 for HTTP requests
5. Routes requests to appropriate endpoint handlers

---

### Core Modules

#### `backend/app/core/config.py`

**Purpose**: Central configuration management using Pydantic settings. Stores all environment variables and app settings.

**Key Settings**:
- **MongoDB**: Connection string, database name
- **JWT**: Secret key, access token expiry (30 min), refresh token expiry (7 days)
- **Email**: SMTP settings for Gmail (sender email, app password)
- **OTP**: Expiration time (10 minutes), code length (6 digits)
- **CORS**: Allowed origins for cross-origin requests

**How It Works**:
- Reads from `.env` file or environment variables
- Provides type-safe access to configuration
- Uses Pydantic validation to ensure correct data types
- Single source of truth for all app settings

---

#### `backend/app/core/database.py`

**Purpose**: MongoDB database connection and collection management.

**Key Functions**:
- `get_db()`: Returns MongoDB database instance
- `get_users_collection()`: Returns users collection
- `get_products_collection()`: Returns products collection
- `get_search_history_collection()`: Returns search history
- `get_otps_collection()`: Returns OTP storage collection
- `get_refresh_tokens_collection()`: Returns refresh tokens collection
- `get_scraping_history_collection()`: Returns scraping job history

**Database Collections**:
1. **users**: User accounts with email, password hash, verification status
2. **otps**: One-time passwords with TTL (10 min auto-expiry)
3. **refresh_tokens**: JWT refresh tokens with TTL (7 days auto-expiry)
4. **products**: Product catalog with embeddings, images, metadata
5. **search_history**: User search queries and results
6. **scraping_history**: Web scraping job logs and status
7. **admins**: Admin accounts with elevated privileges

**How It Works**:
1. Connects to MongoDB Atlas using connection string
2. Creates indexes for faster queries (email unique, TTL indexes)
3. Provides helper functions to access each collection
4. Handles connection errors gracefully

---

#### `backend/app/core/security.py`

**Purpose**: Security utilities for password hashing and admin authentication (legacy).

**Key Functions**:
- `get_password_hash()`: Hash passwords using bcrypt
- `verify_password()`: Verify password against hash
- `create_access_token()`: Create JWT access token
- `get_current_user()`: Verify JWT token and get user

**Security Features**:
- Bcrypt hashing with automatic salt
- JWT token with expiration
- Token validation and decoding
- Admin role verification

**How It Works**:
1. Passwords are hashed before storing in database
2. Login verifies password hash matches
3. JWT tokens are generated with user info and expiry
4. Protected routes verify token before allowing access

---

### API Routes

#### `backend/app/api/routes/auth.py`

**Purpose**: User authentication endpoints (signup, login, OTP verification, token management).

**Endpoints** (6 total):
1. `POST /api/auth/signup`: Create account and send OTP email
2. `POST /api/auth/verify-otp`: Verify OTP code and activate account
3. `POST /api/auth/login`: Login with email/password, returns JWT tokens
4. `POST /api/auth/refresh`: Refresh expired access token
5. `POST /api/auth/logout`: Invalidate refresh token
6. `POST /api/auth/resend-otp`: Resend OTP if expired

**Authentication Flow**:
1. **Signup**: User submits email/password → System hashes password → Creates user (unverified) → Sends 6-digit OTP via email
2. **Verify**: User submits OTP → System checks database → Marks user as verified
3. **Login**: User submits credentials → System verifies password → Generates access + refresh tokens → Returns tokens
4. **Protected Requests**: Frontend sends access token → Backend verifies → Allows access
5. **Token Refresh**: Access token expires → Frontend sends refresh token → Backend generates new access token
6. **Logout**: User logs out → Refresh token deleted from database

**Security**:
- Passwords hashed with bcrypt
- OTP expires after 10 minutes
- Access token expires after 30 minutes
- Refresh token expires after 7 days
- Email verification required before login

---

#### `backend/app/api/routes/search.py`

**Purpose**: Image similarity search endpoints using ML model.

**Endpoints** (4 total):
1. `POST /api/search/similar`: Upload image, find similar products
2. `POST /api/search/upload`: Alternative endpoint for image upload
3. `GET /api/search/history`: Get recent search history
4. `GET /api/search/stats`: Get search statistics

**Image Search Flow**:
1. **Upload**: User uploads image (JPG, PNG, WebP) → Saved to `data/uploads/`
2. **Extract Embedding**: ResNet50 model extracts 2048-dim feature vector from image
3. **Compare**: Calculate cosine similarity between query embedding and all product embeddings
4. **Rank**: Sort products by similarity score (0-1, higher = more similar)
5. **Return**: Top-K most similar products with scores, names, prices, images
6. **Save History**: Store search query and results in database

**ML Model**:
- **Model**: ResNet50 pre-trained on ImageNet
- **Input**: 224x224 RGB image
- **Output**: 2048-dimensional embedding vector
- **Similarity**: Cosine similarity (dot product / magnitude)
- **Device**: CPU (can be configured for GPU)
- **Speed**: ~400-1400ms per search (depends on catalog size)

**Features**:
- Filter by category, price range
- Pagination (top-K results)
- Search history tracking
- Performance metrics (search time, accuracy)

---

#### `backend/app/api/routes/products.py`

**Purpose**: Public product browsing and retrieval endpoints.

**Endpoints** (6 total):
1. `GET /api/products`: Get paginated product list with filters
2. `GET /api/products/`: Alternative endpoint for product list
3. `GET /api/products/{product_id}`: Get single product by MongoDB ObjectId
4. `GET /api/products/by-product-id/{product_id}`: Get product by product_id (1-100)
5. `GET /api/products/categories/list`: Get all categories with counts
6. `GET /api/products/brands/list`: Get all brands with counts

**Filtering Options**:
- **Category**: bags, shoes, watches, clothing, accessories
- **Brand**: Filter by brand name (case-insensitive)
- **Price Range**: Min and max price
- **Search**: Text search in name, description, brand
- **Pagination**: Page number and page size (default: 20, max: 100)

**Product Data**:
- Product ID, name, category, brand
- Price (in USD, converted to PKR in frontend)
- Image URL/path
- Description
- Embedding (2048-dim vector, excluded from responses)
- Created/updated timestamps
- Gender (m/w for filtering)

**How It Works**:
1. Frontend requests products with filters
2. Backend builds MongoDB query based on filters
3. Executes query with pagination
4. Removes embeddings from response (too large)
5. Returns products with metadata (total count, pages)

---

#### `backend/app/api/routes/admin_new.py`

**Purpose**: Comprehensive admin dashboard with 4 modules (User Management, Product Catalogue, ML Training, Auto Sync).

**Total Endpoints**: 21 across 4 modules

**Module 1: User Management** (4 endpoints):
1. `GET /api/admin/users`: List all registered users with pagination/search/filtering
2. `PUT /api/admin/users/{user_id}/deactivate`: Deactivate user account
3. `PUT /api/admin/users/{user_id}/activate`: Reactivate user account
4. `DELETE /api/admin/users/{user_id}`: Permanently delete user

**User Management Features**:
- View all verified users
- Search by email
- Filter by active/inactive status
- Deactivate/activate accounts
- View login history and last login
- Pagination for large user lists

---

**Module 2: Product Catalogue Management** (8 endpoints):
1. `POST /api/admin/products/import-csv`: Bulk import products from CSV file
2. `POST /api/admin/products/cleanup-links`: Check all image URLs for broken links
3. `POST /api/admin/products/{product_id}/repair-link`: Re-check and repair broken link
4. `DELETE /api/admin/products/clear-all`: Clear entire product catalogue
5. `DELETE /api/admin/products/{product_id}`: Delete single product
6. `GET /api/admin/categories`: Get all unique categories with counts
7. `POST /api/admin/categories`: Add new category tag
8. `GET /api/admin/products`: Get products with advanced filtering

**CSV Import Process**:
1. Admin uploads CSV file (name, category, brand, price, image_url, description)
2. Backend validates CSV structure and required columns
3. Processes each row, handling missing/invalid data
4. Checks for duplicates (by product_id or name+brand)
5. Inserts new products or updates existing ones
6. Returns summary (total rows, success, failures, errors)

**Link Cleanup Process**:
1. Fetches all products with image URLs
2. Sends HTTP HEAD request to each URL (checks if reachable)
3. Marks products with broken links (status code >= 400 or connection error)
4. Returns list of broken links with product IDs
5. Admin can repair or delete products with broken links

---

**Module 3: ML Model Training Dashboard** (3 endpoints):
1. `POST /api/admin/ml/train`: Trigger model retraining with custom train/test split
2. `GET /api/admin/ml/training-status/{job_id}`: Get real-time training progress
3. `GET /api/admin/ml/metrics`: Get historical training metrics

**Training Process** (currently simulated, ready for real implementation):
1. Admin sets train/test split ratio (50%-95%, default: 80%)
2. Backend creates training job with unique job_id
3. Loads products from database
4. Splits dataset by ratio
5. Retrains/fine-tunes ResNet50 model
6. Calculates metrics (accuracy, precision, recall, F1 score)
7. Saves metrics to database
8. Updates job status throughout (pending → running → completed/failed)

**Metrics Tracked**:
- Accuracy: Overall correctness
- Precision: True positives / (true positives + false positives)
- Recall: True positives / (true positives + false negatives)
- F1 Score: Harmonic mean of precision and recall
- Train/test split ratio
- Training timestamp
- Job status and progress percentage

---

**Module 4: Auto Sync / Rescraping** (6 endpoints):
1. `GET /api/admin/scraping/brands`: Get list of brands available for scraping
2. `POST /api/admin/scraping/start`: Start rescraping job for selected brands
3. `GET /api/admin/scraping/status/{job_id}`: Get real-time scraping progress
4. `GET /api/admin/scraping/history`: Get paginated scraping job history
5. `DELETE /api/admin/scraping/history/{job_id}`: Delete scraping history entry

**Brand Sources**:
- **Women's Brands**: `women links dataset.xlsx` (141 brands)
- **Men's Brands**: `local_brands_links.csv` (CSV with Brand and Website columns)
- **Brand Types**: local (affordable), luxury (high-end), pakistani (designer)

**Scraping Process**:
1. Admin selects brands from list (sorted by product count - highest first)
2. Admin clicks "Start Scraping"
3. Backend creates scraping job with unique job_id
4. For each brand:
   - Visits brand website URL
   - Extracts product data (name, price, image, category)
   - Generates product_id from hash
   - Checks if product exists (by URL)
   - Inserts new products or updates existing
   - Logs progress (brands completed, products added)
5. Updates job status in database (pending → running → completed/failed)
6. Frontend polls status every 3 seconds to show progress

**Scraping Features**:
- Gender-aware (brands tagged as men's or women's)
- Concurrent brand scraping with timeout (60s per brand)
- Duplicate detection by URL
- Progress tracking with logs
- Error handling (continues on failure)
- History persistence in MongoDB

---

#### `backend/app/api/routes/admin.py`

**Purpose**: Legacy admin endpoints (older implementation, less feature-rich than admin_new.py).

**Endpoints** (9 total):
- Admin login, user management (list, ban/unban, delete)
- Product management (create, update, delete)
- System stats and analytics
- Health check

**Note**: This is the older admin implementation. Most functionality has been moved to `admin_new.py` with enhanced features. Kept for backward compatibility.

---

#### `backend/app/api/routes/database.py`

**Purpose**: Database health checks and monitoring endpoints.

**Endpoints** (3 total):
1. `GET /api/database/health`: Check MongoDB connection health
2. `GET /api/database/stats`: Get database statistics for all collections
3. `GET /api/database/collections`: List all collections in database

**How It Works**:
- Pings MongoDB to verify connection
- Returns collection counts and sizes
- Useful for monitoring and debugging

---

#### `backend/app/api/routes/health.py`

**Purpose**: System health check endpoints.

**Endpoints** (2 total):
1. `GET /health`: Main health check (database + ML engine status)
2. `GET /ping`: Simple ping for quick availability check

**Health Check Response**:
- Overall status: healthy/degraded/down
- Database status: connected/disconnected
- ML engine status: available/unavailable
- Timestamp

**Use Cases**:
- Monitor if server is running
- Check if database is connected
- Verify ML model is loaded
- Load balancer health checks

---

### Models

#### `backend/app/models/auth_schemas.py`

**Purpose**: Pydantic models for authentication request/response validation.

**Models**:
- `SignupRequest`: Email, password for new account
- `SignupResponse`: Success message, email, OTP sent status
- `VerifyOTPRequest`: Email, OTP code
- `VerifyOTPResponse`: Success message, verified status
- `LoginRequest`: Email, password
- `LoginResponse`: Access token, refresh token, user info
- `RefreshTokenRequest`: Refresh token
- `RefreshTokenResponse`: New access token
- `LogoutRequest`: Refresh token
- `LogoutResponse`: Success message

**Validation**:
- Email format validation
- Password strength requirements (min 8 chars)
- Required fields
- Type checking

---

#### `backend/app/models/schemas.py`

**Purpose**: Pydantic models for products and search responses.

**Models**:
- `Product`: Product data model (id, name, category, brand, price, image, description)
- `ProductList`: Paginated product list with total count
- `ProductWithSimilarity`: Product with similarity score (for search results)
- `SearchResponse`: Search results with query image, results, search time

**Product Categories** (enum):
- bags
- shoes
- watches
- clothing
- accessories

---

#### `backend/app/models/admin.py`

**Purpose**: Pydantic models for admin dashboard operations.

**Models**:
- `AdminLogin`: Email, password for admin login
- `AdminToken`: Admin JWT token and admin info
- `AdminResponse`: Admin user data (email, role, created date)
- `UserManagementResponse`: User list with pagination
- `ProductCreate`: Data for creating new product
- `ProductUpdate`: Data for updating existing product
- `SystemStats`: Comprehensive system statistics

---

#### `backend/app/models/mongodb_models.py`

**Purpose**: Pydantic models for MongoDB documents.

**Models**:
- `ProductEmbedding`: Product with ML embedding vector
- `UserSearchAnalytics`: User search behavior data
- `ImageMetadata`: Image file metadata
- `AnalyticsEvent`: User activity events
- `MLModelLog`: ML model training logs

---

#### `backend/app/models/user.py`

**Purpose**: User data models.

**Models**:
- `UserResponse`: User profile data (excludes password)
- `UserCreate`: Data for creating new user
- `UserUpdate`: Data for updating user profile

---

### Services

#### `backend/app/services/email_service.py`

**Purpose**: Email sending service for OTP verification using Gmail SMTP.

**Key Functions**:
- `generate_otp()`: Generate random 6-digit OTP code
- `send_otp_email()`: Send HTML email with OTP via Gmail SMTP
- `generate_and_send_otp()`: Generate OTP, save to database, send email
- `verify_otp()`: Verify OTP from database (check code, expiry, usage)

**Email Configuration**:
- **SMTP Server**: smtp.gmail.com
- **Port**: 587 (TLS)
- **Sender**: ussamainayat@gmail.com
- **App Password**: kqsh zlyu xiuf mfwe (Gmail app-specific password)

**OTP Storage**:
- Stored in MongoDB `otps` collection
- TTL index: Auto-deletes after 10 minutes
- Fields: email, otp_code, expires_at, is_used, created_at
- One-time use: Marked as used after verification

**How It Works**:
1. User requests OTP (signup or resend)
2. System generates random 6-digit code
3. Creates OTP document in database with 10-min expiry
4. Sends HTML email via Gmail SMTP
5. User enters OTP in frontend
6. Backend verifies: code matches, not expired, not used
7. Marks OTP as used to prevent reuse

---

#### `backend/app/services/scraper_service.py`

**Purpose**: Web scraping service for extracting product data from brand websites.

**Key Class**: `ProductScraper`

**Methods**:
- `scrape_brand_website()`: Scrape products from brand URL
- `extract_product_data()`: Extract product info from HTML
- `download_image()`: Download product images
- `close()`: Close browser session

**Scraping Features**:
- Uses Playwright for JavaScript rendering
- Headless browser mode
- User-agent rotation
- Timeout handling (60s per brand)
- Error recovery (continues on failure)
- Image validation
- Duplicate detection

**Data Extracted**:
- Product name
- Price (multiple formats)
- Image URL
- Product URL
- Category
- Brand name
- Gender (m/w)

**How It Works**:
1. Receives brand URL and category
2. Opens headless browser
3. Navigates to brand website
4. Waits for products to load
5. Extracts product cards/items
6. Parses name, price, image from HTML
7. Validates and cleans data
8. Returns list of products as dicts
9. Main scraping endpoint stores in MongoDB

---

#### `backend/app/services/category_normalizer.py`

**Purpose**: Normalize and standardize product category names.

**Key Functions**:
- `normalize_category()`: Convert various category names to standard format
- `get_category_display_name()`: Get human-readable category name

**Category Mapping**:
- "Men → Eastern" → "clothing"
- "Women → Stitched" → "clothing"
- "Bags & Accessories" → "bags" or "accessories"
- Handles plural forms, case variations

**Use Cases**:
- Ensure consistent category names in database
- Handle user input variations
- Simplify category filtering

---

#### `backend/app/services/mongodb_service.py`

**Purpose**: MongoDB service layer for database operations.

**Key Functions**:
- `get_database_stats()`: Get collection counts and sizes
- `insert_product()`: Insert product with embedding
- `find_similar_products()`: Find products by similarity
- `update_product()`: Update product data

**Database Operations**:
- CRUD operations for all collections
- Aggregation queries
- Index management
- Connection pooling

---

### Utilities

#### `backend/app/utils/auth.py`

**Purpose**: Authentication utility functions for JWT token management.

**Key Functions**:
- `hash_password()`: Hash password with bcrypt
- `verify_password()`: Verify password against hash
- `create_access_token()`: Create JWT access token (30 min expiry)
- `create_refresh_token()`: Create JWT refresh token (7 days expiry)
- `verify_token()`: Verify and decode JWT token

**JWT Token Structure**:
```json
{
  "user_id": "mongodb_object_id",
  "email": "user@example.com",
  "exp": 1234567890,  // Expiration timestamp
  "iat": 1234567890   // Issued at timestamp
}
```

**Security**:
- Tokens signed with secret key from config
- Expiration enforced
- Type checking (access vs refresh)

---

### Dependencies

#### `backend/app/dependencies/auth.py`

**Purpose**: FastAPI dependency injection for authentication.

**Key Functions**:
- `get_current_user()`: Dependency for protected routes
- Extracts token from Authorization header
- Verifies token validity
- Returns user object or raises 401 error

**Usage**:
```python
@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    # user is automatically injected
    return {"message": f"Hello {user['email']}"}
```

---

## Frontend (React/Vite)

The frontend is built with React and Vite, providing a fast and modern user interface.

### Entry Points

#### `frontend-app/src/main.jsx`

**Purpose**: Application entry point, renders the root React component.

**What It Does**:
- Imports React and ReactDOM
- Imports root CSS (index.css)
- Imports AppWithAuth (main app component)
- Renders app to DOM element with id "root"
- Enables React Strict Mode for development warnings

**Code Flow**:
```
main.jsx → AppWithAuth → AuthContext → Router → Pages
```

---

#### `frontend-app/src/AppWithAuth.jsx`

**Purpose**: Main application component with routing and authentication.

**Key Features**:
- React Router setup (landing page, dashboard, admin)
- Route protection (authenticated routes)
- Authentication context provider
- Navigation structure

**Routes**:
- `/` → Login page (landing)
- `/signup` → Signup page
- `/dashboard` → User dashboard (protected)
- `/admin-login` → Admin login
- `/admin-dashboard` → Admin dashboard (protected)

**How It Works**:
1. Wraps entire app in AuthContext provider
2. Sets up React Router with routes
3. Protected routes check authentication before rendering
4. Redirects unauthenticated users to login
5. Stores auth state in localStorage

---

#### `frontend-app/src/App.jsx`

**Purpose**: Legacy app component (mostly replaced by AppWithAuth).

**Note**: This file may contain older routing logic. Check if it's still being used or if AppWithAuth has fully replaced it.

---

### Pages

#### `frontend-app/src/pages/Login.jsx`

**Purpose**: User login page.

**Features**:
- Email and password input fields
- Form validation (email format, required fields)
- Submit handler calls `/api/auth/login`
- Stores JWT tokens in localStorage
- Redirects to dashboard on success
- Shows error messages
- Link to signup page

**State Management**:
- `email`: User email input
- `password`: User password input
- `error`: Error message display
- `loading`: Loading state during login

**API Call**:
```javascript
POST http://localhost:8000/api/auth/login
Body: { email, password }
Response: { access_token, refresh_token, user }
```

---

#### `frontend-app/src/pages/Signup.jsx`

**Purpose**: User registration page with OTP verification.

**Features**:
- Email and password input with validation
- Password strength requirements display
- Submit handler calls `/api/auth/signup`
- Shows OTP input field after signup
- Verify OTP button calls `/api/auth/verify-otp`
- Resend OTP with cooldown timer
- Success message and redirect to login
- Error handling

**Signup Flow**:
1. User enters email and password
2. Password meets requirements (8+ chars, uppercase, lowercase, digit, special char)
3. Click signup → API creates account and sends OTP
4. OTP input field appears
5. User enters 6-digit OTP from email
6. Click verify → API verifies OTP
7. Success message → Redirect to login

**State Management**:
- `email`, `password`: Input values
- `otp`: OTP code input
- `step`: 'signup' or 'verify-otp'
- `loading`: Loading states
- `error`: Error messages
- `cooldown`: Resend OTP cooldown timer

---

#### `frontend-app/src/pages/Dashboard.jsx`

**Purpose**: User dashboard with image search functionality (main app feature).

**Features**:
- Image upload (drag-and-drop or browse)
- Image preview before search
- Search button → calls `/api/search/similar`
- Results grid with similar products
- Product cards (image, name, brand, price, similarity score)
- Filter options (category, price range)
- Loading state during search
- Error handling

**Search Flow**:
1. User uploads image (JPG, PNG, WebP)
2. Image preview displays
3. Click "Find Similar Products"
4. Shows loading spinner
5. API processes image with ML model
6. Returns top-K similar products
7. Displays results in grid
8. User can click product for details

**State Management**:
- `selectedImage`: Uploaded image file
- `searchResults`: Array of similar products
- `loading`: Search in progress
- `filters`: Category, price range filters

---

#### `frontend-app/src/pages/AdminLogin.jsx`

**Purpose**: Admin-specific login page (separate from user login).

**Features**:
- Admin email and password input
- Calls `/api/admin/login`
- Stores admin token separately
- Redirects to admin dashboard
- Different styling (admin theme)

**Admin Credentials** (default):
- Email: admin@dupefinder.com
- Password: admin123

---

#### `frontend-app/src/pages/AdminDashboard.jsx`

**Purpose**: Admin dashboard layout with 4 modules.

**Features**:
- Sidebar navigation with 5 menu items
  - Overview
  - User Management
  - Product Catalogue
  - ML Training
  - Auto Sync / Scraping
- Top bar with admin info and logout
- Main content area for module display
- Black & white theme
- Module routing

**Layout Structure**:
```
┌─────────────┬────────────────────────┐
│  Sidebar    │  Top Bar (Logout)      │
│             ├────────────────────────┤
│  - Overview │                        │
│  - Users    │  Module Content        │
│  - Products │  (Selected Module)     │
│  - Training │                        │
│  - Scraping │                        │
└─────────────┴────────────────────────┘
```

**State Management**:
- `selectedModule`: Currently active module
- `admin`: Admin user info from token

---

#### `frontend-app/src/pages/AdminDashboardPro.jsx`

**Purpose**: Enhanced admin dashboard (Pro version with additional features).

**Differences from AdminDashboard**:
- More advanced UI components
- Additional analytics
- Enhanced styling
- Better performance

**Note**: Check which dashboard is currently being used (AdminDashboard vs AdminDashboardPro).

---

### Components

#### `frontend-app/src/components/admin/Overview.jsx`

**Purpose**: Admin dashboard overview module (Module 0).

**Features**:
- Quick statistics cards
  - Total users
  - Total products
  - ML model status
  - Last sync date
- Welcome message
- Quick action buttons
- Recent activity summary

**API Calls**:
- Fetches stats from `/api/admin/stats`
- Displays counts and metrics

---

#### `frontend-app/src/components/admin/UserManagement.jsx`

**Purpose**: User management module (Module 1).

**Features**:
- User list table with columns:
  - Email
  - Status (Active/Inactive)
  - Verified (Yes/No)
  - Created date
  - Last login
- Search bar (filter by email)
- Status filter (all/active/inactive)
- Action buttons:
  - Activate user
  - Deactivate user
  - Delete user (with confirmation)
- Pagination controls
- Shows user count

**API Calls**:
- `GET /api/admin/users`: Fetch user list
- `PUT /api/admin/users/{id}/activate`: Activate user
- `PUT /api/admin/users/{id}/deactivate`: Deactivate user
- `DELETE /api/admin/users/{id}`: Delete user

**State Management**:
- `users`: Array of user objects
- `page`: Current page number
- `searchQuery`: Search input value
- `statusFilter`: Active/inactive/all
- `loading`: Loading state

---

#### `frontend-app/src/components/admin/ProductManagement.jsx`

**Purpose**: Product catalogue management module (Module 2).

**Features**:
- **CSV Upload Section**:
  - Drag-and-drop or browse CSV file
  - Upload button → calls `/api/admin/products/import-csv`
  - Shows import progress and results
  - Error list for failed imports

- **Link Cleanup Section**:
  - "Check Broken Links" button
  - Scans all product images
  - Lists products with broken links
  - Repair button (re-check link)
  - Delete button (remove product)
  - Shows repair/delete notifications

- **Category Management**:
  - List of all categories with counts
  - Add new category
  - Edit category name
  - Delete category

- **Product Table**:
  - Columns: Image, Name, Category, Brand, Price, Status
  - Filter by category
  - Filter by broken links only
  - Search by name
  - Pagination
  - Delete button per product

**API Calls**:
- `POST /api/admin/products/import-csv`: Import CSV
- `POST /api/admin/products/cleanup-links`: Check links
- `POST /api/admin/products/{id}/repair-link`: Repair link
- `DELETE /api/admin/products/{id}`: Delete product
- `GET /api/admin/categories`: Get categories
- `POST /api/admin/categories`: Add category
- `GET /api/admin/products`: Get product list

**State Management**:
- `csvFile`: Selected CSV file
- `importing`: Import in progress
- `brokenLinks`: Array of products with broken links
- `categories`: Array of category objects
- `products`: Array of product objects
- `filters`: Category, broken links filter

**CSV Format Expected**:
```csv
name,category,brand,price,image_url,description
"Product Name","clothing","Brand Name",2999,"https://...","Description"
```

---

#### `frontend-app/src/components/admin/MLTraining.jsx`

**Purpose**: ML model training dashboard module (Module 3).

**Features**:
- **Training Configuration**:
  - Train/Test split slider (50% - 95%)
  - Visual slider with percentage display
  - "Start Training" button
  
- **Training Progress**:
  - Progress bar (0-100%)
  - Current status (Pending/Running/Completed/Failed)
  - Progress percentage
  - Estimated time remaining
  
- **Training Metrics Display**:
  - Accuracy
  - Precision
  - Recall
  - F1 Score
  - Training timestamp
  
- **Metrics History**:
  - Table of last 10 training runs
  - Line chart showing metric trends over time
  - Best model highlight
  - Compare multiple runs

**API Calls**:
- `POST /api/admin/ml/train`: Start training job
- `GET /api/admin/ml/training-status/{job_id}`: Poll status
- `GET /api/admin/ml/metrics`: Get metrics history

**Training Flow**:
1. Admin sets train/test split (e.g., 80/20)
2. Click "Start Training"
3. Backend creates job, returns job_id
4. Frontend polls status every 3 seconds
5. Shows progress bar updating
6. Displays metrics when complete
7. Updates history chart

**State Management**:
- `trainSplit`: Train/test split ratio (0.5-0.95)
- `training`: Training in progress boolean
- `currentJob`: Job ID for status polling
- `progress`: Training progress (0-100)
- `metrics`: Latest metrics object
- `history`: Array of past training runs

---

#### `frontend-app/src/components/admin/ScrapingManagement.jsx`

**Purpose**: Auto sync/rescraping module (Module 4).

**Features**:
- **Gender Toggle**:
  - Women button (red when selected)
  - Men button (red when selected)
  - Switches between women's and men's brands
  - Separate oval buttons with gap

- **Brand Selection**:
  - Grid of brand cards (5 columns)
  - Each card shows:
    - Brand name
    - Product count
    - Category
    - Last scraped date
  - Checkbox for selection
  - Click card to toggle selection
  - "Select All" button for current gender
  - Brands sorted by product count (highest first)
  - Pagination (20 brands per page)
  
- **Scraping Actions**:
  - Shows selected brand count
  - "Start Scraping" button (red, oval)
  - Disabled during scraping
  
- **Scraping Progress**:
  - Brands completed / total
  - Products added count
  - Progress bar
  - Activity logs (real-time)
  - Updates every 3 seconds
  
- **Scraping History**:
  - List of past scraping jobs
  - Status badges (completed/failed/running)
  - Shows brands scraped and products added
  - Delete button (with confirmation)
  - Pagination

**API Calls**:
- `GET /api/admin/scraping/brands?brand_type=local`: Get brand list
- `POST /api/admin/scraping/start`: Start scraping
- `GET /api/admin/scraping/status/{job_id}`: Poll status
- `GET /api/admin/scraping/history`: Get history
- `DELETE /api/admin/scraping/history/{job_id}`: Delete history

**Scraping Flow**:
1. Admin toggles Women/Men
2. Backend fetches brands from Excel files (sorted by product count)
3. Admin selects brands from grid
4. Click "Start Scraping"
5. Backend creates job, starts scraping
6. Frontend polls status every 3 seconds
7. Shows progress (brands done, products added)
8. Displays activity logs
9. Shows completion notification
10. Refreshes brand list with new counts
11. Adds entry to history

**State Management**:
- `selectedGender`: 'women' or 'men'
- `brands`: Array of brand objects
- `selectedBrands`: Array of selected brands
- `scraping`: Boolean, scraping in progress
- `currentJob`: Job ID for status polling
- `jobStatus`: Job status object (progress, logs)
- `history`: Array of past jobs
- `brandsPage`: Current page for brand pagination

**Recent Changes**:
- Brands now sorted by product count (most products first)
- Gender toggle uses separate oval buttons
- Selected button is bright red (#EF4444)
- Unselected button is dark red (#C74242)
- Button colors stay consistent (no hover color change on selected)

---

### Context

#### `frontend-app/src/context/AuthContext.jsx`

**Purpose**: Global authentication state management using React Context.

**Provided State**:
- `user`: Current user object
- `token`: JWT access token
- `isAuthenticated`: Boolean, user logged in
- `loading`: Authentication check in progress

**Provided Functions**:
- `login(email, password)`: Login user
- `signup(email, password)`: Register user
- `verifyOTP(email, otp)`: Verify OTP
- `logout()`: Logout user
- `refreshToken()`: Refresh access token

**How It Works**:
1. On app load, checks localStorage for token
2. If token exists, validates it
3. Sets user and isAuthenticated state
4. Provides auth functions to entire app
5. Handles token refresh automatically
6. Clears state on logout

**Usage in Components**:
```javascript
import { useAuth } from '../context/AuthContext'

function MyComponent() {
  const { user, login, logout } = useAuth()
  
  return (
    <div>
      {user ? (
        <button onClick={logout}>Logout</button>
      ) : (
        <button onClick={() => login(email, password)}>Login</button>
      )}
    </div>
  )
}
```

---

### Styles

#### `frontend-app/src/styles/AdminDashboard.css`

**Purpose**: Styles for admin dashboard components.

**Key Styles**:
- Sidebar navigation (black background, white text)
- Content area (white background)
- Tables (alternating rows, hover effects)
- Buttons (primary, danger, success colors)
- Cards (white with shadows)
- Forms (inputs, selects, file uploads)
- Modals (overlays, dialogs)
- Progress bars
- Status badges

**Theme Colors**:
- Primary: Purple (#6B63CB)
- Danger: Red (#EF4444)
- Success: Green (#82CE59)
- Background: Black (#000)
- Text: White (#FFF)

---

#### `frontend-app/src/styles/Auth.css`

**Purpose**: Styles for authentication pages (login, signup).

**Key Styles**:
- Centered auth forms
- Input fields with icons
- Password strength indicator
- OTP input styling
- Submit buttons
- Error messages
- Link buttons

---

#### `frontend-app/src/styles/Dashboard.css`

**Purpose**: Styles for user dashboard (image search).

**Key Styles**:
- Image upload area (drag-and-drop)
- Image preview
- Search button
- Results grid
- Product cards
- Filter sidebar
- Loading spinner

---

#### `frontend-app/src/styles/AdminPro.css`

**Purpose**: Enhanced styles for AdminDashboardPro.

**Additional Features**:
- Advanced animations
- Better transitions
- Improved responsive design
- Enhanced visual effects

---

#### `frontend-app/src/styles/theme.css`

**Purpose**: Global theme variables and base styles.

**CSS Variables**:
- `--primary-color`: Main brand color
- `--secondary-color`: Accent color
- `--background-color`: Page background
- `--text-color`: Default text color
- `--border-color`: Border color
- `--shadow`: Box shadow values

**Usage**:
```css
.my-component {
  background: var(--primary-color);
  color: var(--text-color);
}
```

---

#### `frontend-app/src/index.css`

**Purpose**: Global base styles and resets.

**Includes**:
- CSS reset (normalize)
- Base font family
- Default colors
- Box-sizing
- Smooth scrolling

---

## Mobile App (Flutter/Dart)

The mobile app is built with Flutter for cross-platform iOS and Android support.

### Main

#### `mobile/lib/main.dart`

**Purpose**: Entry point for Flutter mobile app.

**What It Does**:
- Initializes Flutter app
- Sets up app theme
- Defines initial route (login screen)
- Configures navigation

**App Structure**:
```dart
void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DupeFinder',
      theme: ThemeData(...),
      home: LoginScreen(),
    );
  }
}
```

**Routes**:
- `/` → Login screen
- `/register` → Register screen
- `/home` → Home screen (image search)

---

### Screens

#### `mobile/lib/screens/login_screen.dart`

**Purpose**: Mobile login screen.

**Features**:
- Email and password input fields
- Login button
- Register link
- Error handling
- API call to `/api/auth/login`
- Stores token in secure storage
- Navigates to home on success

**UI Elements**:
- Logo at top
- Input fields with icons
- Submit button
- "Don't have account?" link

---

#### `mobile/lib/screens/register_screen.dart`

**Purpose**: Mobile registration screen with OTP verification.

**Features**:
- Email and password inputs
- Password requirements display
- Register button
- OTP input field (appears after signup)
- Verify OTP button
- Resend OTP link
- API calls to `/api/auth/signup` and `/api/auth/verify-otp`

**Registration Flow**:
1. User enters email and password
2. Click register → API creates account
3. OTP sent to email
4. OTP input appears
5. User enters OTP
6. Click verify → Account activated
7. Navigate to login screen

---

#### `mobile/lib/screens/home_screen.dart`

**Purpose**: Main app screen with image search functionality.

**Features**:
- Camera button (take photo)
- Gallery button (select photo)
- Image preview
- Search button
- Results list/grid
- Product cards with similarity scores
- Loading indicator

**Search Flow**:
1. User selects image from camera or gallery
2. Image preview displays
3. Click "Find Similar"
4. Shows loading
5. API processes with ML model
6. Displays results
7. User can tap product for details

**State Management**:
- `selectedImage`: File object
- `searchResults`: List of products
- `isLoading`: Boolean

---

### Services

#### `mobile/lib/services/api_service.dart`

**Purpose**: API client for making HTTP requests to backend.

**Key Functions**:
- `login(email, password)`: Login API call
- `register(email, password)`: Register API call
- `verifyOTP(email, otp)`: Verify OTP API call
- `searchSimilar(imageFile)`: Upload image and search
- `getProducts()`: Fetch product list

**Configuration**:
- Base URL: `http://192.168.1.108:8000` (local IP - needs to be changed for different networks)
- Headers: `Authorization: Bearer {token}`
- Timeout: 30 seconds
- Error handling

**HTTP Client**:
- Uses `http` package or `dio` package
- Handles multipart file uploads (for images)
- Parses JSON responses
- Manages authentication tokens

**Connection Issue**:
- Current base URL uses local IP (192.168.1.108)
- Only works on same WiFi network
- **Solution Needed**: Use ngrok, cloud deployment, or dynamic IP configuration

---

## ML Engine (Python)

The ML engine handles image processing and similarity calculations.

### Preprocessing

#### `ml-engine/preprocessing/image_preprocessor.py`

**Purpose**: Image preprocessing for ML model input.

**Key Class**: `ImagePreprocessor`

**Methods**:
- `preprocess(image)`: Convert image to model-ready tensor
- `resize(image, size)`: Resize to 256x256 then center crop to 224x224
- `normalize(tensor)`: Apply ImageNet normalization
- `to_rgb(image)`: Convert grayscale/RGBA to RGB

**Image Processing Steps**:
1. **Load Image**: PIL or OpenCV
2. **Convert to RGB**: Handle grayscale, RGBA
3. **Resize**: 256x256 (maintains aspect ratio)
4. **Center Crop**: 224x224 (ResNet50 input size)
5. **Convert to Tensor**: NumPy array → PyTorch tensor
6. **Normalize**: ImageNet mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
7. **Add Batch Dimension**: (3, 224, 224) → (1, 3, 224, 224)

**Supported Formats**:
- JPG/JPEG
- PNG
- WebP
- BMP
- GIF
- TIFF

**Input Types**:
- File path (string)
- Bytes (from upload)
- PIL Image
- NumPy array

---

### Embeddings

#### `ml-engine/embeddings/feature_extractor.py`

**Purpose**: Extract feature embeddings from images using ResNet50.

**Key Class**: `FeatureExtractor`

**Methods**:
- `extract_from_path(image_path)`: Extract embedding from file
- `extract_from_bytes(image_bytes)`: Extract from bytes
- `extract_batch(images)`: Process multiple images
- `save(embeddings, path)`: Save to file
- `load(path)`: Load from file

**Model Details**:
- **Architecture**: ResNet50 (pre-trained on ImageNet)
- **Parameters**: 23.5 million
- **Input**: (1, 3, 224, 224) RGB image
- **Output**: (1, 2048) embedding vector
- **Layer**: Last layer before classification (avgpool)
- **Device**: CPU (can use GPU if available)

**Extraction Process**:
1. Load pre-trained ResNet50
2. Remove classification layer
3. Set model to evaluation mode
4. Preprocess image
5. Forward pass through network
6. Extract features from avgpool layer
7. Return 2048-dimensional vector

**Performance**:
- CPU: 400-1400ms per image
- GPU: 50-100ms per image (if available)
- Batch processing: Faster for multiple images

---

### Similarity

#### `ml-engine/similarity/similarity_searcher.py`

**Purpose**: Calculate similarity between embeddings and find top-K matches.

**Key Class**: `SimilaritySearcher`

**Methods**:
- `add_embedding(embedding, metadata)`: Add to search index
- `search(query_embedding, top_k)`: Find top-K similar items
- `cosine_similarity(vec1, vec2)`: Calculate similarity score
- `save_index(path)`: Save search index
- `load_index(path)`: Load search index

**Similarity Calculation**:
```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
```
- Range: -1 to 1 (higher = more similar)
- 1 = identical
- 0 = orthogonal (no similarity)
- -1 = opposite

**Search Process**:
1. Load query embedding (2048-dim)
2. Load all product embeddings from database
3. Calculate cosine similarity with each product
4. Sort by similarity score (descending)
5. Return top-K results with scores
6. Filter by category/price if specified

**Optimization**:
- Pre-compute embeddings (stored in database)
- Use numpy for fast vector operations
- Can upgrade to FAISS for faster search with large catalogs (>10,000 products)

**Performance**:
- 100 products: ~3ms search time
- 1,000 products: ~30ms search time
- 10,000 products: ~300ms search time
- FAISS (optional): Sub-millisecond for 1M+ products

---

## Configuration Files

### `backend/requirements.txt`

**Purpose**: Python dependencies for backend.

**Key Packages**:
- `fastapi==0.104.1`: Web framework
- `uvicorn==0.24.0`: ASGI server
- `pymongo==4.5.0`: MongoDB driver
- `motor==3.3.2`: Async MongoDB driver
- `pydantic==2.4.2`: Data validation
- `python-jose[cryptography]==3.3.0`: JWT tokens
- `passlib[bcrypt]==1.7.4`: Password hashing
- `python-multipart==0.0.6`: File uploads
- `aiosmtplib==3.0.1`: Async email sending
- `pandas==2.1.1`: CSV processing
- `httpx==0.25.0`: HTTP client
- `beautifulsoup4==4.12.2`: Web scraping
- `playwright==1.40.0`: Browser automation

---

### `ml-engine/requirements.txt`

**Purpose**: Python dependencies for ML engine.

**Key Packages**:
- `torch>=2.0.0`: PyTorch deep learning
- `torchvision>=0.15.0`: Computer vision models
- `numpy>=1.24.0`: Numerical computing
- `scipy>=1.10.0`: Scientific computing
- `Pillow>=10.0.0`: Image processing
- `opencv-python>=4.8.0`: Computer vision
- `PyYAML>=6.0`: Configuration

---

### `frontend-app/package.json`

**Purpose**: Node.js dependencies for frontend.

**Key Packages**:
- `react==18.2.0`: UI library
- `react-dom==18.2.0`: DOM rendering
- `react-router-dom==6.18.0`: Routing
- `axios==1.5.1`: HTTP client
- `vite==4.5.0`: Build tool

**Scripts**:
- `npm run dev`: Start development server (port 5173)
- `npm run build`: Build for production
- `npm run preview`: Preview production build

---

### `mobile/pubspec.yaml`

**Purpose**: Flutter dependencies for mobile app.

**Key Packages**:
- `flutter`: Flutter SDK
- `http`: HTTP client
- `image_picker`: Camera/gallery access
- `shared_preferences`: Local storage
- `flutter_secure_storage`: Secure token storage

---

### `.env.example`

**Purpose**: Template for environment variables.

**Required Variables**:
```
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dupefinder
MONGODB_DB_NAME=dupefinder

# JWT
JWT_SECRET=your_secret_key_here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
EMAIL_SENDER=ussamainayat@gmail.com
EMAIL_APP_PASSWORD=kqsh zlyu xiuf mfwe
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# OTP
OTP_EXPIRATION_MINUTES=10
OTP_LENGTH=6
```

---

## Summary Statistics

### Codebase Size

**Backend**:
- **Total Files**: 25 Python files
- **API Endpoints**: 52 endpoints across 7 route files
- **Models**: 15 Pydantic models
- **Services**: 4 service modules
- **Database Collections**: 7 collections

**Frontend**:
- **Total Files**: 20 JavaScript/JSX files
- **Pages**: 6 main pages
- **Components**: 5 admin components
- **Context Providers**: 1 auth context
- **Style Files**: 5 CSS files

**Mobile**:
- **Total Files**: 4 Dart files
- **Screens**: 3 screens
- **Services**: 1 API service

**ML Engine**:
- **Total Files**: 3 Python modules
- **Model**: ResNet50 (23.5M parameters)
- **Embedding Dimension**: 2048

---

## Key Technologies

**Backend Stack**:
- FastAPI (Python web framework)
- MongoDB Atlas (cloud database)
- PyTorch (deep learning)
- JWT (authentication)
- Gmail SMTP (email)
- Playwright (web scraping)

**Frontend Stack**:
- React 18 (UI library)
- Vite (build tool)
- React Router (routing)
- Axios (HTTP client)
- CSS (styling)

**Mobile Stack**:
- Flutter (cross-platform framework)
- Dart (programming language)
- HTTP package (API client)

**ML Stack**:
- PyTorch (deep learning framework)
- ResNet50 (CNN architecture)
- ImageNet (pre-training dataset)
- Cosine Similarity (similarity metric)

---

## Data Flow

### Image Search Flow (End-to-End)

1. **Mobile/Web**: User uploads image
2. **Frontend**: Sends image via POST to `/api/search/similar`
3. **Backend**: Receives image, saves to `data/uploads/`
4. **ML Engine**: Preprocesses image (resize, normalize)
5. **ML Engine**: Extracts 2048-dim embedding via ResNet50
6. **Database**: Fetches all product embeddings
7. **ML Engine**: Calculates cosine similarity for each product
8. **ML Engine**: Sorts by similarity, returns top-K
9. **Backend**: Formats response with product details
10. **Frontend**: Displays results in grid
11. **Database**: Saves search history

**Time Breakdown**:
- Image upload: ~100-500ms (depends on size/network)
- Preprocessing: ~50-100ms
- Embedding extraction: ~400-1400ms (CPU)
- Similarity calculation: ~3-300ms (depends on catalog size)
- **Total**: ~500-2000ms average

---

### Authentication Flow (End-to-End)

1. **Frontend**: User enters email/password on signup page
2. **Backend**: Receives POST to `/api/auth/signup`
3. **Backend**: Validates email format, password strength
4. **Backend**: Hashes password with bcrypt
5. **Database**: Creates user document (unverified)
6. **Backend**: Generates 6-digit OTP
7. **Database**: Stores OTP with 10-min expiry
8. **Email Service**: Sends OTP via Gmail SMTP
9. **Frontend**: Shows OTP input field
10. **Frontend**: User enters OTP from email
11. **Backend**: Receives POST to `/api/auth/verify-otp`
12. **Database**: Verifies OTP (correct, not expired, not used)
13. **Database**: Marks user as verified
14. **Frontend**: Shows success, redirects to login
15. **Frontend**: User enters email/password on login page
16. **Backend**: Receives POST to `/api/auth/login`
17. **Backend**: Verifies password hash
18. **Backend**: Generates JWT access token (30 min) + refresh token (7 days)
19. **Database**: Stores refresh token
20. **Frontend**: Receives tokens, stores in localStorage
21. **Frontend**: Redirects to dashboard
22. **Frontend**: All API requests include `Authorization: Bearer {token}`
23. **Backend**: Verifies token on protected routes

---

### Scraping Flow (End-to-End)

1. **Admin Dashboard**: Admin selects brands from grid
2. **Frontend**: Sends POST to `/api/admin/scraping/start` with brand list
3. **Backend**: Creates scraping job with unique job_id
4. **Database**: Stores job in scraping_history collection
5. **Backend**: Starts async task for each brand:
   - Opens headless browser (Playwright)
   - Navigates to brand website
   - Waits for products to load
   - Extracts product cards from HTML
   - Parses name, price, image URL
   - Downloads/validates images
   - Generates product_id hash
6. **Database**: For each product:
   - Checks if exists by URL
   - Inserts new or updates existing
   - Increments products_added counter
7. **Backend**: Updates job status (brands_completed, products_added, logs)
8. **Database**: Saves progress to scraping_history
9. **Frontend**: Polls `/api/admin/scraping/status/{job_id}` every 3 seconds
10. **Frontend**: Updates progress bar and logs in real-time
11. **Backend**: Job completes, marks status as completed/failed
12. **Frontend**: Shows completion notification
13. **Frontend**: Refreshes brand list (updated product counts)
14. **Frontend**: Adds entry to history table

---

## Common Issues & Solutions

### Issue 1: Mobile App Cannot Connect to Backend

**Problem**: Connection timeout error when mobile app tries to reach backend at `192.168.1.108:8000`.

**Cause**: Backend running on local IP, mobile device on different network (different WiFi or mobile data).

**Solutions**:
1. **Same Network**: Connect both to same WiFi
2. **ngrok**: Create public URL tunnel to localhost
3. **Cloud Deployment**: Deploy backend to Heroku, AWS, DigitalOcean
4. **Dynamic IP**: Configure mobile app to accept IP input

---

### Issue 2: OTP Email Not Sending

**Problem**: OTP verification email not received.

**Cause**: Gmail SMTP authentication failure or firewall blocking.

**Solutions**:
1. Check Gmail app password is correct in `.env`
2. Enable "Less secure app access" in Gmail settings
3. Check spam folder
4. Verify SMTP port 587 is open
5. Test with different email provider

---

### Issue 3: Scraping Fails

**Problem**: Scraping job fails or returns no products.

**Cause**: Website structure changed, anti-scraping measures, timeout.

**Solutions**:
1. Update CSS selectors in scraper_service.py
2. Increase timeout (currently 60s per brand)
3. Add delays between requests
4. Rotate user agents
5. Use proxies if IP blocked

---

### Issue 4: Search Returns Irrelevant Results

**Problem**: Image search returns products that don't look similar.

**Cause**: Model not trained on fashion data, poor image quality, or category mismatch.

**Solutions**:
1. Fine-tune ResNet50 on fashion dataset
2. Use fashion-specific model (e.g., FashionNet)
3. Filter by category before similarity search
4. Increase product catalog size
5. Pre-filter by color/pattern

---

## Development Workflow

### Starting Development

1. **Backend**:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. **Frontend**:
```bash
cd frontend-app
npm install
npm run dev
```

3. **Mobile**:
```bash
cd mobile
flutter pub get
flutter run -d chrome  # or specific device
```

### Testing

- **Backend**: Create test files in `tests/`
- **Frontend**: Use React Testing Library
- **Mobile**: Use Flutter test framework

### Deployment

- **Backend**: Docker container → Cloud platform
- **Frontend**: `npm run build` → Static hosting
- **Mobile**: Build APK/IPA → App stores

---

## Future Enhancements

1. **Real ML Training**: Implement actual model training in Module 3
2. **FAISS Integration**: Faster similarity search for large catalogs
3. **Mobile Network Fix**: Deploy backend to cloud or use ngrok
4. **Advanced Scraping**: Handle more websites, better anti-scraping
5. **User Dashboard**: Search history, saved products, recommendations
6. **Social Features**: Share finds, community reviews
7. **Price Tracking**: Alert when prices drop
8. **Multi-language**: Support for multiple languages
9. **AR Try-On**: Virtual try-on for fashion items
10. **Analytics Dashboard**: User behavior, search trends, conversion rates

---

**End of Documentation**

For more information, refer to:
- `API.md` - Complete API endpoint documentation
- `README.md` - Project setup and overview
- `ARCHITECTURE.md` - System architecture details
- `.cursor/scratchpad.md` - Development progress and decisions



