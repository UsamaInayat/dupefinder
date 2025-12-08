# DupeFinder - Complete Codebase Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Mobile App Architecture](#mobile-app-architecture)
6. [ML Engine Architecture](#ml-engine-architecture)
7. [API Endpoints & Working](#api-endpoints--working)
8. [Auto-Scraping System (Detailed)](#auto-scraping-system-detailed)
9. [Data Flow & Integration](#data-flow--integration)
10. [Key Features Implementation](#key-features-implementation)

---

## Project Overview

**DupeFinder** is an AI-powered fashion search application that helps users find affordable alternatives to luxury fashion items through image-based similarity search. The system consists of:

- **Backend**: FastAPI-based REST API (Python)
- **Frontend**: React admin dashboard (Vite)
- **Mobile**: Flutter mobile application
- **ML Engine**: PyTorch-based image feature extraction and similarity search
- **Database**: MongoDB Atlas for product storage and user management

---

## Project Structure

```
dupefinder/
├── backend/                    # FastAPI Backend Server
│   ├── app/
│   │   ├── api/routes/         # API endpoint definitions
│   │   ├── core/               # Core configuration & database
│   │   ├── models/             # Data models & schemas
│   │   ├── services/           # Business logic services
│   │   ├── utils/              # Utility functions
│   │   ├── dependencies/       # FastAPI dependencies
│   │   └── main.py             # FastAPI app initialization
│   ├── create_admin.py         # Admin user creation script
│   ├── init_auth_collections.py # MongoDB collection initialization
│   ├── start_server.py         # Server startup script
│   └── requirements.txt        # Python dependencies
│
├── frontend-app/               # React Admin Dashboard
│   ├── src/
│   │   ├── components/admin/   # Admin module components
│   │   ├── pages/              # Page components
│   │   ├── context/            # React context (Auth)
│   │   └── styles/             # CSS stylesheets
│   ├── package.json
│   └── vite.config.js
│
├── mobile/                     # Flutter Mobile App
│   ├── lib/
│   │   ├── screens/            # Screen widgets
│   │   ├── services/           # API service
│   │   └── main.dart           # App entry point
│   └── pubspec.yaml
│
├── ml-engine/                  # Machine Learning Engine
│   ├── embeddings/             # Feature extraction
│   ├── preprocessing/          # Image preprocessing
│   └── similarity/             # Similarity search
│
├── data/                       # Product images & data
│   ├── products/               # Product images by category
│   └── uploads/                # User uploaded images
│
├── database/schemas/           # Database schema definitions
├── docker-compose.yml          # Docker services configuration
└── README.md                   # Project documentation
```

---

## Backend Architecture

### 1. Main Application Entry Point

#### `backend/app/main.py`
**Purpose**: FastAPI application initialization and configuration

**Key Components**:
- **Lifespan Events**: Manages MongoDB connection on startup/shutdown
- **CORS Configuration**: Allows requests from localhost (including dynamic Flutter web ports)
- **Router Registration**: Includes all API route modules
- **Static Files**: Serves product images from `/data` directory
- **Global Exception Handler**: Catches unhandled errors and adds CORS headers

**How it works**:
1. On startup: Connects to MongoDB Atlas
2. Registers API routers: `/api/auth`, `/api/admin`, `/api/products`, `/api/search`
3. Configures CORS for cross-origin requests
4. Mounts static file directory for serving images

---

### 2. Core Configuration

#### `backend/app/core/config.py`
**Purpose**: Centralized configuration management using Pydantic Settings

**Key Settings**:
- MongoDB connection URI
- JWT secret keys and expiration times
- SMTP email configuration (Gmail)
- OTP settings (length, expiry)
- File upload limits

**How it works**:
- Loads environment variables from `.env` file
- Provides `settings` object accessible throughout the app
- Validates configuration on startup

#### `backend/app/core/database.py`
**Purpose**: MongoDB connection management

**Key Components**:
- **DatabaseManager**: Singleton class for sync MongoDB connections
- **Collection Helpers**: Functions to get specific collections
- **Health Check**: Database connection status monitoring
- **Index Setup**: Creates TTL indexes for OTPs and refresh tokens

**Collections Used**:
- `products`: Product catalog
- `users`: User accounts
- `otps`: Email verification codes
- `refresh_tokens`: JWT refresh tokens
- `search_history`: User search logs
- `scraping_history`: Auto-scraping job logs
- `admins`: Admin user accounts

**How it works**:
1. Creates MongoDB client connection
2. Provides collection access functions
3. Manages connection lifecycle
4. Sets up database indexes automatically

#### `backend/app/core/security.py`
**Purpose**: Security utilities for authentication

**Key Functions**:
- `verify_password()`: Validates passwords using bcrypt
- `get_password_hash()`: Hashes passwords
- `create_access_token()`: Generates JWT access tokens
- `decode_access_token()`: Validates and decodes JWT tokens
- `get_current_user()`: Extracts user from JWT token

**How it works**:
- Uses `passlib` with bcrypt for password hashing
- Uses `jose` library for JWT token creation/validation
- Tokens contain user email and expiration time

---

### 3. API Routes

#### `backend/app/api/routes/auth.py`
**Purpose**: User authentication endpoints

**Endpoints**:
1. **POST `/api/auth/signup`**: User registration
   - Validates email uniqueness
   - Hashes password
   - Creates user document (is_verified=False)
   - Sends OTP email
   - Returns success message

2. **POST `/api/auth/verify-otp`**: Email verification
   - Validates OTP from database
   - Updates user is_verified=True
   - Returns verification success

3. **POST `/api/auth/login`**: User login
   - Validates email/password
   - Checks if email is verified
   - Generates access + refresh tokens
   - Stores refresh token in database
   - Returns tokens and user info

4. **POST `/api/auth/refresh`**: Token refresh
   - Validates refresh token
   - Generates new access token
   - Returns new access token

5. **POST `/api/auth/logout`**: User logout
   - Deletes refresh token from database

6. **POST `/api/auth/resend-otp`**: Resend verification code
   - Generates new OTP
   - Sends email again

**Data Flow**:
```
User → Signup → OTP Email → Verify OTP → Login → JWT Tokens → Protected Routes
```

#### `backend/app/api/routes/admin_new.py`
**Purpose**: Admin dashboard API with 4 modules

**Module 1: User Management**
- **GET `/api/admin/users`**: List all users (pagination, search, filters)
- **PUT `/api/admin/users/{id}/deactivate`**: Deactivate user account
- **PUT `/api/admin/users/{id}/activate`**: Reactivate user account
- **DELETE `/api/admin/users/{id}`**: Delete user permanently

**Module 2: Product Catalogue**
- **POST `/api/admin/products/import-csv`**: Import products from CSV
  - Reads CSV file
  - Normalizes column names
  - Validates required fields (name, category, brand, price)
  - Inserts/updates products in MongoDB
  - Returns import statistics
  
- **POST `/api/admin/products/cleanup-links`**: Check broken image links
  - Tests all product image URLs
  - Marks broken links in database
  
- **POST `/api/admin/products/{id}/repair-link`**: Re-check single link
  
- **DELETE `/api/admin/products/clear-all`**: Delete all products
  
- **DELETE `/api/admin/products/{id}`**: Delete single product
  
- **GET `/api/admin/products`**: List products (filters: category, brand, gender, broken links)
  
- **GET `/api/admin/categories`**: Get all unique categories
  
- **POST `/api/admin/categories`**: Add new category tag

**Module 3: ML Training**
- **POST `/api/admin/ml/train`**: Trigger model training
  - Creates training job
  - Runs training in background
  - Returns job_id for status tracking
  
- **GET `/api/admin/ml/training-status/{job_id}`**: Get training progress
  
- **GET `/api/admin/ml/metrics`**: Get historical training metrics

**Module 4: Auto Sync / Rescraping**
- **GET `/api/admin/scraping/brands`**: Get available brands from Excel files
  - Reads `women links dataset.xlsx`
  - Reads `men dataset.xlsx`
  - Reads `local_brands_links.csv`
  - Returns brands with product counts
  
- **POST `/api/admin/scraping/start`**: Start rescraping
  - Accepts list of brand objects
  - Creates scraping job
  - Runs scraping in background
  - Returns job_id
  
- **GET `/api/admin/scraping/status/{job_id}`**: Get scraping progress
  
- **GET `/api/admin/scraping/history`**: Get scraping history (pagination)
  
- **DELETE `/api/admin/scraping/history/{job_id}`**: Delete history entry

**Admin Authentication**:
- **POST `/api/admin/login`**: Admin login
  - Validates admin credentials from `admins` collection
  - Returns admin JWT token
  - Default: admin@dupefinder.com / admin123

#### `backend/app/api/routes/search.py`
**Purpose**: Image-based product search

**Endpoints**:
1. **POST `/api/search/similar`** or **POST `/api/search/upload`**
   - Accepts image file upload
   - Extracts embedding using ResNet50
   - Compares with all product embeddings
   - Calculates cosine similarity
   - Returns top-K most similar products
   - Saves search to history

2. **GET `/api/search/history`**: Get recent search history

3. **GET `/api/search/stats`**: Get search statistics

**How it works**:
1. User uploads image
2. Image saved to `data/uploads/`
3. Feature extractor generates 2048-dim embedding
4. Cosine similarity calculated with all products
5. Results sorted by similarity score
6. Top-K products returned with scores

#### `backend/app/api/routes/products.py`
**Purpose**: Product CRUD operations (if exists)

#### `backend/app/api/routes/health.py`
**Purpose**: Health check endpoints

---

### 4. Services Layer

#### `backend/app/services/scraper_service.py`
**Purpose**: Web scraping service for product extraction

**Key Class: `ProductScraper`**

**Main Method: `scrape_brand_website()`**
- Scrapes products from brand websites
- Handles men's and women's brands differently
- Extracts: name, price, image_url, category, description

**Scraping Process for Women's Brands**:
1. Finds product listing pages (`/products`, `/shop`, etc.)
2. Extracts product URLs from listing pages
3. Visits each product page
4. Extracts product details using BeautifulSoup
5. Validates product data (name, price, image)
6. Normalizes category
7. Returns list of products

**Scraping Process for Men's Brands**:
1. Goes directly to homepage
2. Extracts products from homepage containers
3. Also tries `/men` page if available
4. More lenient validation (allows missing images/prices)
5. Sets default values for missing data
6. Filters out women's products

**Product Extraction Methods**:
- `_extract_product_name()`: Finds product title (h1, .product-title, etc.)
- `_extract_price()`: Extracts price (handles PKR, Rs., $)
- `_extract_image_url()`: Gets product image (prioritizes high-res)
- `_extract_description()`: Gets product description
- `_extract_product_category()`: Gets category from page

**Product Validation**:
- Filters out logos, placeholders, navigation items
- Validates product names (min length, not generic)
- Validates prices (reasonable range)
- Validates images (not logos/icons)
- Removes duplicates

**Function: `scrape_from_excel_files()`**
- Reads Excel files (`women links dataset.xlsx`, `men dataset.xlsx`)
- Reads CSV file (`local_brands_links.csv`)
- For each brand:
  - Calls `scrape_brand_website()`
  - Stores products in MongoDB
  - Handles duplicates (updates existing)
- Returns scraping statistics

**How it works**:
1. Admin selects brands in dashboard
2. Frontend calls `/api/admin/scraping/start`
3. Backend creates scraping job
4. Background task runs `scrape_from_excel_files()`
5. Products stored in MongoDB `products` collection
6. Job status updated in real-time
7. Frontend polls status endpoint

#### `backend/app/services/category_normalizer.py`
**Purpose**: Normalize product categories to consistent tags

**Key Functions**:
- `normalize_category()`: Maps category names to standard tags
  - Handles "Women → Stitched" format
  - Maps variants (kurta, kurtis, kurti → "kurta")
  - Adds gender suffix for men's categories (_m)
  
- `extract_gender_from_category()`: Extracts gender from category string
  - "Women → Stitched" → "w"
  - "Men → Eastern" → "m"

- `get_category_display_name()`: Converts normalized tag to display name

**Category Mappings**:
- Women: kurta, shalwar_kameez, saree, lehenga, dress, tops, trousers, dupatta
- Men: kurta_m, shalwar_kameez_m, shirt_m, trouser_m, waistcoat

#### `backend/app/services/email_service.py`
**Purpose**: Email sending and OTP management

**Key Functions**:
- `generate_otp()`: Creates random 6-digit OTP
- `send_email()`: Sends email via SMTP (Gmail)
- `store_otp()`: Saves OTP in MongoDB with expiration
- `verify_otp()`: Validates OTP from database
- `generate_and_send_otp()`: Complete OTP flow

**Email Template**:
- HTML email with DupeFinder branding
- Large OTP code display
- Expiration warning
- Plain text fallback

**How it works**:
1. User signs up
2. OTP generated and stored in MongoDB
3. Email sent via SMTP (Gmail)
4. OTP expires after 10 minutes (TTL index)
5. User enters OTP
6. Backend verifies and marks as used

#### `backend/app/services/mongodb_service.py`
**Purpose**: MongoDB service layer (async operations)

**Functions**:
- Product embedding operations
- Search analytics
- Image metadata
- Analytics events
- ML model logs

---

### 5. Models & Schemas

#### `backend/app/models/auth_schemas.py`
**Purpose**: Pydantic models for authentication

**Models**:
- `SignupRequest`: email, password
- `SignupResponse`: message, email, otp_sent
- `LoginRequest`: email, password
- `LoginResponse`: access_token, refresh_token, user
- `VerifyOTPRequest`: email, otp_code
- `RefreshTokenRequest`: refresh_token

#### `backend/app/models/admin.py`
**Purpose**: Admin-related models

**Models**:
- `AdminLogin`: email, password
- `AdminToken`: access_token, admin
- `AdminResponse`: admin user data

#### `backend/app/models/schemas.py`
**Purpose**: General API schemas

**Models**:
- `SearchResponse`: query_image, results, search_time_ms
- `ProductWithSimilarity`: product with similarity_score

#### `backend/app/models/mongodb_models.py`
**Purpose**: MongoDB document models

#### `backend/app/models/user.py`
**Purpose**: User data models

---

### 6. Utilities

#### `backend/app/utils/auth.py`
**Purpose**: Authentication utility functions

**Functions**:
- `hash_password()`: Bcrypt password hashing
- `verify_password()`: Password verification
- `create_access_token()`: JWT access token (30 min expiry)
- `create_refresh_token()`: JWT refresh token (7 days expiry)
- `verify_token()`: Token validation with type check
- `decode_token()`: Token decoding

**How it works**:
- Uses `jose` library for JWT
- Tokens contain: user_id, email, exp, type
- Secret key from config
- HS256 algorithm

#### `backend/app/dependencies/auth.py`
**Purpose**: FastAPI dependencies for route protection

**Functions**:
- `get_current_user()`: Extracts user from JWT token
- `require_admin()`: Ensures admin authentication

---

### 7. Initialization Scripts

#### `backend/create_admin.py`
**Purpose**: Creates default admin user

**How it works**:
- Hashes password
- Inserts admin document in `admins` collection
- Default: admin@dupefinder.com / admin123

#### `backend/init_auth_collections.py`
**Purpose**: Initializes MongoDB collections and indexes

**Actions**:
- Creates TTL indexes for OTPs and refresh tokens
- Creates unique index on users.email

#### `backend/start_server.py`
**Purpose**: Server startup script

**Actions**:
- Runs uvicorn server
- Auto-reload on code changes
- Host: 0.0.0.0, Port: 8000

---

## Frontend Architecture

### 1. Main Application

#### `frontend-app/src/main.jsx`
**Purpose**: React application entry point

**How it works**:
- Renders `AppWithAuth` component
- Sets up React root

#### `frontend-app/src/AppWithAuth.jsx`
**Purpose**: Authentication wrapper

**How it works**:
- Checks for admin token in localStorage
- Redirects to login if not authenticated
- Shows admin dashboard if authenticated

#### `frontend-app/src/App.jsx`
**Purpose**: Main app component (if used)

### 2. Admin Dashboard

#### `frontend-app/src/pages/AdminDashboard.jsx`
**Purpose**: Main admin dashboard with module navigation

**Structure**:
- Sidebar with 5 modules: Overview, User Management, Product Catalogue, ML Training, Auto Sync
- Main content area renders active module
- Logout button

**Modules**:
1. Overview: Statistics and quick actions
2. User Management: User list and management
3. Product Catalogue: Product import, view, delete
4. ML Training: Model training interface
5. Auto Sync: Brand scraping management

#### `frontend-app/src/pages/AdminLogin.jsx`
**Purpose**: Admin login page

**Features**:
- Email and password input
- Calls `/api/admin/login`
- Stores admin token in localStorage
- Redirects to dashboard on success

### 3. Admin Components

#### `frontend-app/src/components/admin/UserManagement.jsx`
**Purpose**: User management module

**Features**:
- Fetches users from `/api/admin/users`
- Pagination, search, filters
- Deactivate/activate users
- Delete users
- Shows user statistics

#### `frontend-app/src/components/admin/ProductManagement.jsx`
**Purpose**: Product catalogue management

**Features**:
- CSV import (drag & drop)
- Product list with filters
- Delete products
- Cleanup broken links
- Category management

#### `frontend-app/src/components/admin/ScrapingManagement.jsx`
**Purpose**: Auto-scraping management

**Features**:
- Brand selection (separated by gender)
- Start scraping button
- Real-time progress display
- Scraping history with pagination
- Delete history entries

**How it works**:
1. Fetches brands from `/api/admin/scraping/brands`
2. User selects brands
3. Calls `/api/admin/scraping/start` with selected brands
4. Polls `/api/admin/scraping/status/{job_id}` every 3 seconds
5. Displays progress: brands completed, products added, logs
6. Shows history from MongoDB

#### `frontend-app/src/components/admin/MLTraining.jsx`
**Purpose**: ML model training interface

**Features**:
- Start training button
- Training progress display
- Historical metrics view

#### `frontend-app/src/components/admin/Overview.jsx`
**Purpose**: Dashboard overview

**Features**:
- Statistics cards
- Quick navigation to modules

### 4. Context & State

#### `frontend-app/src/context/AuthContext.jsx`
**Purpose**: React context for authentication state

**Features**:
- Stores admin token
- Provides auth state to components
- Handles login/logout

### 5. Styling

#### `frontend-app/src/styles/AdminDashboard.css`
**Purpose**: Admin dashboard styles

**Theme**: Black and white minimalist design

---

## Mobile App Architecture

### 1. Main Application

#### `mobile/lib/main.dart`
**Purpose**: Flutter app entry point

**Structure**:
- `DupeFinderApp`: MaterialApp with black/white theme
- Routes: `/` (auth check), `/login`, `/register`, `/home`
- `AuthCheckScreen`: Checks if user is logged in, redirects accordingly

**How it works**:
1. App starts
2. `AuthCheckScreen` checks for stored token
3. If logged in → `/home`
4. If not → `/login`

### 2. Screens

#### `mobile/lib/screens/login_screen.dart`
**Purpose**: User login screen

**Features**:
- Email input (with @gmail.com validation)
- Password input (with strength requirements)
- Real-time validation feedback
- Calls `/api/auth/login`
- Stores tokens in SharedPreferences
- Navigates to home on success

**Validation**:
- Email must end with @gmail.com
- Password: uppercase, lowercase, digit, special char, min 8 chars
- Real-time error messages below fields

#### `mobile/lib/screens/register_screen.dart`
**Purpose**: User registration screen

**Features**:
- Name input (real-time validation)
- Email input (@gmail.com validation)
- Password input (strength requirements)
- Confirm password (must match)
- Calls `/api/auth/signup`
- OTP verification screen
- Navigates to login after verification

**Validation**:
- Name: min 2 characters
- Email: @gmail.com required
- Password: all requirements
- Confirm password: must match

#### `mobile/lib/screens/home_screen.dart`
**Purpose**: Main home screen (after login)

**Features**:
- Image upload for search
- Product search results
- Logout functionality

### 3. Services

#### `mobile/lib/services/api_service.dart`
**Purpose**: API communication service

**Key Features**:
- Platform-aware base URL:
  - Web: `http://localhost:8000/api`
  - Android Emulator: `http://10.0.2.2:8000/api`
  - Physical Device: `http://192.168.1.108:8000/api` (configurable)
- Token management (SharedPreferences)
- API methods:
  - `register()`: POST `/api/auth/signup`
  - `verifyOTP()`: POST `/api/auth/verify-otp`
  - `login()`: POST `/api/auth/login`
  - `logout()`: Removes tokens

**How it works**:
- Detects platform (web, Android, iOS)
- Sets appropriate base URL
- Stores JWT tokens in SharedPreferences
- Adds Authorization header to requests
- Handles errors and exceptions

---

## ML Engine Architecture

### 1. Feature Extraction

#### `ml-engine/embeddings/feature_extractor.py`
**Purpose**: Extract image embeddings using ResNet50

**Key Class: `FeatureExtractor`**

**Initialization**:
- Loads pre-trained ResNet50 (ImageNet weights)
- Removes final classification layer
- Keeps feature extraction layers (2048-dim output)
- Moves to device (CPU/GPU/MPS)

**Methods**:
- `extract_from_path()`: Extract from image file
- `extract_from_bytes()`: Extract from image bytes
- `extract_from_tensor()`: Extract from preprocessed tensor
- `extract_batch()`: Batch processing for multiple images

**How it works**:
1. Image preprocessed to 224x224
2. Passed through ResNet50
3. Output: 2048-dimensional feature vector
4. Vector represents semantic content of image

**Usage in Search**:
- User uploads image
- Feature extractor generates embedding
- Compared with product embeddings
- Cosine similarity calculated
- Top-K most similar products returned

### 2. Image Preprocessing

#### `ml-engine/preprocessing/image_preprocessor.py`
**Purpose**: Preprocess images for ResNet50

**Key Class: `ImagePreprocessor`**

**Preprocessing Pipeline**:
1. Resize to 256px (shortest side)
2. Center crop to 224x224
3. Convert to RGB (if needed)
4. Convert to tensor [0, 1]
5. Normalize with ImageNet mean/std:
   - Mean: [0.485, 0.456, 0.406]
   - Std: [0.229, 0.224, 0.225]

**Methods**:
- `preprocess_from_path()`: From file path
- `preprocess_from_bytes()`: From image bytes
- `preprocess_from_pil()`: From PIL Image
- `preprocess_batch()`: Batch preprocessing

**How it works**:
- Uses torchvision transforms
- Ensures images are in correct format for ResNet50
- Handles various image formats (JPG, PNG, WebP, etc.)

### 3. Similarity Search

#### `ml-engine/similarity/similarity_searcher.py`
**Purpose**: Similarity calculation and search

**Key Class: `SimilaritySearcher`**

**Methods**:
- `compute_similarity()`: Calculate similarity between two embeddings
- `search()`: Find top-K most similar items
- `search_with_metadata()`: Search with category filters

**Similarity Metric**:
- Cosine similarity (default)
- Formula: `1 - cosine_distance(query, target)`
- Range: [0, 1] where 1 is identical

**How it works**:
1. Stores product embeddings in memory
2. User query embedding compared with all products
3. Cosine similarity calculated for each
4. Results sorted by similarity (descending)
5. Top-K returned

**Current Implementation**:
- Uses numpy/scipy for computation
- In-memory search (suitable for <10K products)
- Can be upgraded to FAISS for large-scale

---

## API Endpoints & Working

### Authentication Flow

```
1. User Registration:
   POST /api/auth/signup
   → Creates user (is_verified=False)
   → Generates OTP
   → Sends email
   → Returns success

2. Email Verification:
   POST /api/auth/verify-otp
   → Validates OTP
   → Updates is_verified=True
   → Returns success

3. User Login:
   POST /api/auth/login
   → Validates credentials
   → Checks is_verified
   → Generates JWT tokens
   → Stores refresh token
   → Returns tokens

4. Protected Routes:
   → Include Authorization: Bearer <token> header
   → Backend validates token
   → Extracts user info
   → Processes request
```

### Admin Authentication Flow

```
1. Admin Login:
   POST /api/admin/login
   → Validates admin credentials
   → Generates admin JWT token
   → Returns token

2. Admin Routes:
   → Include Authorization: Bearer <admin_token> header
   → require_admin() dependency validates
   → Checks role="admin" in token
   → Processes admin request
```

### Image Search Flow

```
1. User Uploads Image:
   POST /api/search/upload
   → File saved to data/uploads/
   → Feature extractor generates embedding
   → Compares with all product embeddings
   → Calculates cosine similarity
   → Returns top-K products with scores
   → Saves search to history
```

### Product Import Flow

```
1. Admin Uploads CSV:
   POST /api/admin/products/import-csv
   → Reads CSV file
   → Normalizes columns
   → Validates data
   → Inserts/updates products
   → Returns statistics
```

---

## Auto-Scraping System (Detailed)

### Overview

The auto-scraping system extracts product data from brand websites and stores them in MongoDB. It's accessible through the Admin Dashboard's "Auto Sync" module.

### Components

#### 1. Brand Data Sources

**Excel Files**:
- `women links dataset.xlsx`: Contains women's brand links
  - Columns: Luxury Brand Link, Pakistani Designer Brand Link, Local Dupe Brand Link
  - Columns: Luxury / International Brand, Pakistani Luxury / Designer Brand, Local Affordable Brand (Dupe)
  - Column: Main Category (e.g., "Women → Stitched")
  - Column: Price ranges

- `men dataset.xlsx`: Contains men's brand links (if available)
  - Similar structure to women's dataset

**CSV File**:
- `local_brands_links.csv`: Contains men's local brand links
  - Columns: Brand, Website
  - Default category: "Men → Eastern"

#### 2. Scraping Process Flow

```
Admin Dashboard → Select Brands → Start Scraping
    ↓
Backend: POST /api/admin/scraping/start
    ↓
Creates Scraping Job (job_id)
    ↓
Background Task: run_scraping_job()
    ↓
For each selected brand:
    ↓
    ProductScraper.scrape_brand_website()
        ↓
        Finds product pages
        ↓
        Extracts product URLs
        ↓
        For each product URL:
            ↓
            Scrapes product page
            ↓
            Extracts: name, price, image, category, description
            ↓
            Validates product data
            ↓
            Normalizes category
            ↓
            Stores in MongoDB
    ↓
Updates job status
    ↓
Frontend polls status endpoint
    ↓
Displays progress and results
```

#### 3. Scraping Implementation Details

**File: `backend/app/services/scraper_service.py`**

**Class: `ProductScraper`**

**Initialization**:
- Creates httpx.AsyncClient with timeout (15s)
- Sets connection limits
- Initializes counters (scraped_count, failed_count, errors)

**Method: `scrape_brand_website()`**

**For Women's Brands**:
1. Calls `_find_product_pages()` to discover product listing pages
2. Tries common paths: `/products`, `/shop`, `/catalog`, etc.
3. Extracts product URLs from listing pages
4. For each product URL (up to 50):
   - Calls `_scrape_product_page()`
   - Extracts product details
   - Validates data
   - Adds to products list
5. Removes duplicates
6. Returns products

**For Men's Brands**:
1. Goes directly to homepage
2. Calls `_extract_products_from_page()` to extract products from homepage
3. Also tries `/men` page if available
4. More lenient validation (allows missing images/prices)
5. Sets default values
6. Filters out women's products
7. Returns products

**Method: `_find_product_pages()`**
- Tries common product listing paths
- Uses `_find_products_on_page()` to extract product URLs
- Returns list of product URLs

**Method: `_find_products_on_page()`**
- Looks for product containers (`.product`, `.product-item`, etc.)
- Extracts links from containers
- Uses CSS selectors and patterns
- For men's brands: more lenient (checks all links)

**Method: `_scrape_product_page()`**
- Fetches product page HTML
- Parses with BeautifulSoup
- Extracts:
  - Name: `_extract_product_name()` (h1, .product-title, etc.)
  - Price: `_extract_price()` (handles PKR, Rs., $)
  - Image: `_extract_image_url()` (prioritizes high-res)
  - Description: `_extract_description()`
  - Category: `_extract_product_category()`
- Validates product:
  - Name not too short/generic
  - Price in reasonable range
  - Image not a logo/placeholder
  - Not a navigation item
- Normalizes category
- Generates product_id (MD5 hash of URL)
- Returns product dict

**Method: `_extract_products_from_page()`**
- For listing pages (homepage, category pages)
- Finds product containers
- Extracts name, price, image from each container
- Validates each product
- Returns list of products

**Product Validation Rules**:

**For Women's Products**:
- Name: min 5 chars, not in invalid list (logo, placeholder, etc.)
- Price: required, 500-100000 PKR
- Image: required, not logo/icon/placeholder
- Category: must be meaningful

**For Men's Products**:
- Name: min 3 chars, not generic
- Price: optional (defaults to 1000 if missing)
- Image: optional (uses placeholder if missing)
- Category: defaults to "Men → Stitched" or "Men → Unstitched"
- Filters out women's indicators

**Function: `scrape_from_excel_files()`**

**Process**:
1. Creates `ProductScraper` instance
2. Reads Excel/CSV files based on `brand_type`:
   - `luxury`: Luxury Brand Link column
   - `pakistani`: Pakistani Designer Brand Link column
   - `local`: Local Dupe Brand Link column
3. For each brand row:
   - Extracts brand_name, brand_url, category, price_range
   - Calls `scraper.scrape_brand_website()`
   - Gets products list
   - Stores in MongoDB:
     - Checks if product exists (by URL)
     - If new: inserts
     - If exists: updates
   - Small delay (2s) between brands
4. Closes scraper
5. Returns statistics

**Product Storage**:
- Collection: `products`
- Document structure:
  ```json
  {
    "product_id": 12345678,
    "name": "Product Name",
    "brand": "Brand Name",
    "category": "Women → Stitched",
    "normalized_category": "kurta",
    "price": 2500.0,
    "image_url": "https://...",
    "product_url": "https://...",
    "description": "...",
    "gender": "w",
    "scraped_at": ISODate("..."),
    "broken_link": false,
    "embedding": [0.1, 0.2, ...]  // Added later
  }
  ```

#### 4. Admin Dashboard Integration

**File: `frontend-app/src/components/admin/ScrapingManagement.jsx`**

**Features**:
1. **Brand Selection**:
   - Fetches brands from `/api/admin/scraping/brands`
   - Displays brands separated by gender (Men's / Women's)
   - Shows product count for each brand
   - Checkbox selection

2. **Start Scraping**:
   - User selects brands
   - Clicks "Start Scraping"
   - Calls `/api/admin/scraping/start` with selected brands
   - Receives job_id

3. **Progress Monitoring**:
   - Polls `/api/admin/scraping/status/{job_id}` every 3 seconds
   - Displays:
     - Brands completed / total
     - Products added
     - Progress bar
     - Activity logs

4. **History**:
   - Fetches scraping history from `/api/admin/scraping/history`
   - Shows past jobs with status, brands, products added
   - Pagination support
   - Delete history entries

**Backend Job Management**:

**File: `backend/app/api/routes/admin_new.py`**

**In-Memory Storage**:
- `scraping_jobs` dict: Stores active job status
- Key: job_id, Value: job data

**MongoDB Storage**:
- Collection: `scraping_history`
- Stores persistent job records

**Background Task: `run_scraping_job()`**
1. Updates job status to "running"
2. Creates `ProductScraper` instance
3. For each brand:
   - Calls `scraper.scrape_brand_website()`
   - Stores products in MongoDB
   - Updates job progress (brands_completed, products_added)
   - Adds log entry
   - 2s delay between brands
4. Updates job status to "completed"
5. Closes scraper
6. Handles errors (marks as "failed")

**Status Endpoint**:
- `GET /api/admin/scraping/status/{job_id}`
- Returns job data from in-memory dict
- Includes: status, brands_completed, products_added, logs

#### 5. Error Handling

**Scraping Errors**:
- Network timeouts: 15s per request, 60s per brand
- Invalid HTML: BeautifulSoup handles gracefully
- Missing data: Validation filters out invalid products
- Duplicate products: URL-based deduplication
- Database errors: Retry with new product_id

**Job Errors**:
- Failed brands: Logged, job continues
- Complete failure: Job marked as "failed", error message stored

---

## Data Flow & Integration

### Complete User Journey

```
1. User Registration (Mobile App):
   User → Register Screen → API: POST /api/auth/signup
   → Backend creates user → Sends OTP email
   → User enters OTP → API: POST /api/auth/verify-otp
   → User verified → Login Screen

2. User Login (Mobile App):
   User → Login Screen → API: POST /api/auth/login
   → Backend validates → Returns JWT tokens
   → Tokens stored in SharedPreferences
   → Home Screen

3. Image Search (Mobile App):
   User → Upload Image → API: POST /api/search/upload
   → Backend: Feature extractor generates embedding
   → Compares with product embeddings
   → Returns top-K similar products
   → Display results
```

### Complete Admin Journey

```
1. Admin Login (Web Dashboard):
   Admin → Login Page → API: POST /api/admin/login
   → Backend validates → Returns admin JWT token
   → Token stored in localStorage
   → Admin Dashboard

2. Product Import (Admin Dashboard):
   Admin → Product Management → Upload CSV
   → API: POST /api/admin/products/import-csv
   → Backend processes CSV → Stores products in MongoDB
   → Returns import statistics

3. Auto-Scraping (Admin Dashboard):
   Admin → Auto Sync → Select Brands → Start Scraping
   → API: POST /api/admin/scraping/start
   → Backend creates job → Background scraping starts
   → Frontend polls status → Displays progress
   → Products stored in MongoDB
   → Job completes → History updated
```

### Data Storage Flow

```
1. Product Creation:
   Scraping/CSV Import → Product Document
   → MongoDB: products collection
   → Fields: name, brand, category, price, image_url, etc.

2. Embedding Generation:
   Product stored → ML Engine processes image
   → ResNet50 extracts features
   → 2048-dim embedding generated
   → Stored in product.embedding field

3. Search:
   User uploads image → Embedding extracted
   → Compared with product embeddings
   → Cosine similarity calculated
   → Top-K products returned
```

---

## Key Features Implementation

### 1. Real-Time Validation (Mobile)

**Location**: `mobile/lib/screens/login_screen.dart`, `register_screen.dart`

**Implementation**:
- `TextEditingController` for each field
- `onChanged` callback triggers validation
- State variables store error messages
- Error messages displayed below fields in red
- Validation prevents form submission

**Email Validation**:
- Must end with @gmail.com
- Real-time check on every keystroke

**Password Validation**:
- Uppercase letter
- Lowercase letter
- Digit
- Special character
- Minimum 8 characters
- Real-time feedback with checkmarks

### 2. CORS Configuration

**Location**: `backend/app/main.py`

**Implementation**:
- Allows specific localhost origins
- Regex pattern for dynamic Flutter web ports
- CORS headers in error responses
- Preflight handler for OPTIONS requests

**Why Needed**:
- Flutter web uses dynamic ports (e.g., localhost:51108)
- React frontend uses port 5173
- Backend needs to allow all localhost origins

### 3. Platform-Aware API URLs (Mobile)

**Location**: `mobile/lib/services/api_service.dart`

**Implementation**:
- Detects platform (web, Android, iOS)
- Sets base URL accordingly:
  - Web: localhost
  - Android Emulator: 10.0.2.2
  - Physical Device: Configurable IP (192.168.1.108)

**Why Needed**:
- Emulator uses special IP to access host machine
- Physical device needs local network IP
- Web uses localhost

### 4. Category Normalization

**Location**: `backend/app/services/category_normalizer.py`

**Implementation**:
- Maps variant names to standard tags
- Handles gender-specific categories
- Extracts gender from category strings
- Provides display names

**Example**:
- "Kurtis" → "kurta"
- "Women → Stitched" → gender="w", category="kurta"
- "Men → Eastern" → gender="m", category="kurta_m"

### 5. Product Deduplication

**Location**: `backend/app/services/scraper_service.py`

**Implementation**:
- Checks product existence by URL
- If exists: updates
- If new: inserts
- Handles product_id collisions (regenerates)

**Why Needed**:
- Same product may be scraped multiple times
- Prevents duplicate entries
- Updates product data if changed

### 6. Broken Link Detection

**Location**: `backend/app/api/routes/admin_new.py`

**Implementation**:
- Tests image URLs with HTTP HEAD request
- Marks broken links in database
- Admin can repair individual links
- Bulk cleanup option

**Why Needed**:
- External image URLs may become unavailable
- Helps maintain data quality
- Admin can fix or remove broken products

---

## Database Schema

### Collections

#### `users`
```json
{
  "_id": ObjectId,
  "email": "user@gmail.com",
  "password_hash": "$2b$...",
  "is_active": true,
  "is_verified": true,
  "created_at": ISODate,
  "last_login": ISODate
}
```
**Indexes**: email (unique)

#### `products`
```json
{
  "_id": ObjectId,
  "product_id": 12345678,
  "name": "Product Name",
  "brand": "Brand Name",
  "category": "Women → Stitched",
  "normalized_category": "kurta",
  "product_category": "Kurtis",
  "price": 2500.0,
  "image_url": "https://...",
  "image_path": "https://...",
  "product_url": "https://...",
  "description": "...",
  "gender": "w",
  "embedding": [0.1, 0.2, ...],
  "scraped_at": ISODate,
  "created_at": ISODate,
  "broken_link": false
}
```

#### `otps`
```json
{
  "_id": ObjectId,
  "email": "user@gmail.com",
  "otp_code": "123456",
  "expires_at": ISODate,
  "is_used": false,
  "created_at": ISODate
}
```
**Indexes**: expires_at (TTL), email

#### `refresh_tokens`
```json
{
  "_id": ObjectId,
  "user_id": "user_id_string",
  "token": "jwt_token_string",
  "expires_at": ISODate,
  "created_at": ISODate
}
```
**Indexes**: expires_at (TTL), user_id

#### `admins`
```json
{
  "_id": ObjectId,
  "email": "admin@dupefinder.com",
  "hashed_password": "$2b$...",
  "created_at": ISODate
}
```

#### `search_history`
```json
{
  "_id": ObjectId,
  "uploaded_image_path": "/data/uploads/...",
  "embedding": [0.1, 0.2, ...],
  "results": [
    {
      "product_id": ObjectId,
      "similarity_score": 0.95
    }
  ],
  "timestamp": ISODate,
  "search_time_ms": 123.45,
  "user_email": "user@gmail.com"
}
```

#### `scraping_history`
```json
{
  "_id": ObjectId,
  "job_id": "uuid-string",
  "status": "completed",
  "brands": [
    {
      "brand_name": "Brand Name",
      "brand_url": "https://...",
      "category": "Women → Stitched"
    }
  ],
  "brands_completed": 5,
  "brands_total": 5,
  "products_added": 150,
  "started_at": ISODate,
  "completed_at": ISODate,
  "logs": ["Starting scrape...", "Found 30 products..."]
}
```

---

## How Each File Plays Its Part

### Backend Files

1. **`main.py`**: Orchestrates entire backend
   - Connects to database
   - Registers all routes
   - Handles CORS
   - Serves static files

2. **`config.py`**: Provides configuration
   - All other files import settings
   - Centralized configuration management

3. **`database.py`**: Database access layer
   - All routes use collection helpers
   - Manages connection lifecycle

4. **`security.py`**: Authentication layer
   - Used by auth routes
   - Validates JWT tokens
   - Protects admin routes

5. **`auth.py` (routes)**: User authentication
   - Handles signup/login flow
   - Integrates with email service
   - Manages tokens

6. **`admin_new.py` (routes)**: Admin functionality
   - Uses scraper service for auto-sync
   - Manages products/users
   - Coordinates ML training

7. **`scraper_service.py`**: Web scraping engine
   - Called by admin scraping endpoint
   - Extracts products from websites
   - Stores in database

8. **`email_service.py`**: Email communication
   - Called by auth routes
   - Sends OTP emails
   - Manages OTP storage

9. **`category_normalizer.py`**: Data normalization
   - Used by scraper service
   - Standardizes categories
   - Helps with filtering

10. **`search.py` (routes)**: Image search
    - Uses ML engine feature extractor
    - Compares embeddings
    - Returns similar products

### Frontend Files

1. **`AdminDashboard.jsx`**: Main container
   - Renders active module
   - Manages navigation
   - Handles logout

2. **`ScrapingManagement.jsx`**: Auto-sync UI
   - Fetches brands from API
   - Starts scraping jobs
   - Monitors progress
   - Displays history

3. **`ProductManagement.jsx`**: Product UI
   - CSV import interface
   - Product list display
   - Delete/cleanup actions

4. **`UserManagement.jsx`**: User UI
   - User list display
   - Activate/deactivate/delete

5. **`AuthContext.jsx`**: State management
   - Stores auth state
   - Provides to components

### Mobile Files

1. **`main.dart`**: App entry
   - Sets up routing
   - Checks auth state
   - Initializes app

2. **`api_service.dart`**: API communication
   - All screens use this
   - Handles token storage
   - Platform-aware URLs

3. **`login_screen.dart`**: Login UI
   - Real-time validation
   - Calls API service
   - Navigates on success

4. **`register_screen.dart`**: Registration UI
   - Multi-step form
   - OTP verification
   - Real-time validation

### ML Engine Files

1. **`feature_extractor.py`**: Image processing
   - Used by search endpoint
   - Generates embeddings
   - Core of similarity search

2. **`image_preprocessor.py`**: Image preparation
   - Used by feature extractor
   - Standardizes images
   - Required for ResNet50

3. **`similarity_searcher.py`**: Search algorithm
   - Currently used in search endpoint
   - Calculates similarities
   - Returns top-K results

---

## Summary

This codebase implements a complete fashion search platform with:

1. **User Authentication**: Signup, email verification, login with JWT
2. **Admin Dashboard**: 4 modules for managing users, products, ML training, and auto-scraping
3. **Auto-Scraping**: Automated product extraction from brand websites
4. **Image Search**: AI-powered similarity search using ResNet50
5. **Mobile App**: Flutter app with real-time validation
6. **Product Management**: CSV import, broken link detection, category management

All components work together to provide a seamless experience for users finding affordable fashion alternatives and admins managing the product catalog.

