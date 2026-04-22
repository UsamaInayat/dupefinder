### Current Status / Progress Tracking — Executor Update (Apr 22, 2026, Railway: split Docker + API↔scraper wiring)

- Implemented **two-container split** for Railway size limits:
  - `Dockerfile.railway-api` installs `backend/requirements-railway-api.txt` (no Playwright layer).
  - Added `Dockerfile.railway-scraper` + `backend/app/scraper_worker_app.py` (FastAPI worker; Playwright Chromium install).
- Wired admin scraping (`backend/app/api/routes/admin_new.py`) to call scraper worker via **`POST {SCRAPER_SERVICE_URL}/scrape/url`** with **`X-Scraper-Token`** when `SCRAPER_SERVICE_URL` + `SCRAPER_SERVICE_TOKEN` are set; otherwise falls back to in-process `ProductScraper` (local parity).
- Fixed accidental invalid first line in `backend/app/core/config.py` (`image.png"""` → proper module docstring) which would break imports.
- Updated `docs/railway.md` with env var matrix + behavior notes (Mongo writes + reindex remain on API).

### Executor's Feedback or Assistance Requests — Apr 22, 2026 (Railway split)

- Please deploy **two Railway services** from repo root:
  - API: `Dockerfile.railway-api`
  - Scraper: `Dockerfile.railway-scraper`
- Set **`SCRAPER_SERVICE_TOKEN` identically** on both services; set **`SCRAPER_SERVICE_URL`** on API only.
- After deploy, run one admin scrape job and confirm logs show `Using remote scraper worker: ...` and that products persist + reindex triggers.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, FYP report Markdown to Word conversion)

- User requested converting `C:\Users\US\Desktop\FYP\DupeFinder_FYP_Report_Full_Template.md` to a Word document.
- `pandoc` CLI was unavailable on PATH, so executor used Python package `pypandoc-binary` to perform conversion.
- Output generated and verified: `C:\Users\US\Desktop\FYP\DupeFinder_FYP_Report_Full_Template.docx`.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (FYP report Markdown to Word conversion)

- Conversion milestone is complete. Please open the `.docx` and confirm formatting/content look correct; if needed, executor can run a style-tuned conversion pass.
# DupeFinder Project - Scratchpad

## Background and Motivation

**Project**: DupeFinder - Affordable Alternatives for Luxury Wearables

**Goal**: Build a smart mobile/web application that helps users discover affordable, high-quality alternatives to luxury fashion products through image-based search and intelligent matching.

**Core Value Proposition**:
- Image-based search for luxury alternatives
- Price comparison and savings insights
- Multi-level filtering (category, gender, city, size, budget)
- Community-driven reviews and trust
- Analytics for users and admins

**Target**: Final Year Project (FYP) with 80%+ accuracy in top-3 matches

---

## NEW REQUIREMENTS - November 11, 2025

**Major Architecture Changes Requested**:

1. **UI Theme Overhaul**: Complete black and white color scheme across entire application
2. **Authentication-First Flow**: Login/Signup as landing page (before image upload functionality)
3. **JWT + Email OTP Authentication**: 
   - New user signup requires email verification via OTP
   - OTP sent to registered email
   - Success message after verification, then redirect to login
   - Login with registered credentials opens admin dashboard
4. **Admin Dashboard with 4 Core Modules**:
   - **Module 1**: Manage Mobile App Users - view login data, deactivate accounts
   - **Module 2**: Product Catalogue Management - add products via CSV, cleanup missing links, manage category tags
   - **Module 3**: Model Training Dashboard - adjust train/test split with sliders, retrain model, view performance metrics
   - **Module 4**: Auto Sync - select brands for rescraping, monitor progress, view new records added to MongoDB

**Email Configuration for OTP**:
- Sender Email: ussamainayat@gmail.com
- App Password: kqsh zlyu xiuf mfwe

**Impact**: This changes the project from a public demo tool to a secure admin platform with authentication and comprehensive management capabilities.

---

## 40% Milestone Strategy (Current Focus)

**Updated: November 8, 2025 - Planner Mode**

### What Constitutes the 40% Milestone?

For an effective FYP demonstration at 40% completion, we need to focus on **CORE FUNCTIONALITY** that proves the concept works. The 40% should include:

**✅ MUST HAVE (Critical for 40%)**:
1. **Working Image Upload & Matching**: Users can upload an image and get similar product recommendations
2. **Basic Product Catalog**: 50-100 sample products with images, metadata (category, price, brand)
3. **Functional ML Model**: Pre-trained CNN (ResNet/EfficientNet) that extracts embeddings and finds similar items
4. **Simple Web Interface**: Clean UI for upload, view results, see product details
5. **Core Backend API**: Endpoints for upload, search, product retrieval
6. **Basic Database**: **MongoDB** with product data, embeddings, and image metadata
7. **Demo-Ready**: Can demonstrate end-to-end flow in 5-10 minutes

**❌ DEFER to 60-100% (Not needed for 40%)**:
- Mobile app (Flutter) → Focus on web first
- User authentication & profiles → Skip for demo
- Community reviews & ratings → Defer
- Admin dashboard → Manual data entry is OK
- Advanced filtering (city, size, gender) → Keep simple
- Analytics dashboards → Skip
- Docker deployment → Local development is fine
- Price tracking & auto-refresh → Static prices OK
- FAISS vector search → Can use simpler similarity methods initially

### Success Criteria for 40% Milestone

**Technical Demonstration**:
1. Upload any fashion item image → System returns 3-5 similar affordable alternatives
2. Results show: product image, name, price, brand/store, similarity score
3. System responds within 5-10 seconds
4. Accuracy: At least 60-70% of results are visually similar (aiming for 80% but 60% acceptable at 40%)

**Deliverables**:
1. Working web application (React frontend + FastAPI backend)
2. ML model integrated and functional
3. Database with 50-100 sample products
4. Demo video showing complete workflow
5. Technical documentation of architecture
6. Presentation slides explaining approach

### Strategic Approach (Planner's Recommendation)

**Priority 1 - Proof of Concept (Weeks 1-2)**:
- Get ML model working with sample data
- Prove that image similarity search works
- Create minimal UI to test

**Priority 2 - Core Features (Weeks 3-4)**:
- Build proper backend API
- Create clean frontend UI
- Populate database with real product data

**Priority 3 - Polish & Demo (Week 5)**:
- Refine UI/UX
- Test with various images
- Prepare demo and presentation

**Philosophy**: Start simple, prove it works, then enhance. Don't over-engineer at 40%.

## Key Challenges and Analysis

### NEW REQUIREMENTS ANALYSIS (November 11, 2025)

**Planner Assessment**: This is a MAJOR architectural shift requiring substantial backend and frontend changes.

#### 1. Authentication & Security Challenges
**What's Required**:
- JWT token generation and validation (access + refresh tokens)
- Email OTP system with SMTP integration (Gmail)
- Secure password hashing (bcrypt/argon2)
- Token expiration and refresh logic
- Protected routes on both backend and frontend
- Session management

**Technical Considerations**:
- Gmail SMTP requires SSL/TLS connection (port 465 or 587)
- OTP needs temporary storage (Redis ideal, MongoDB acceptable with TTL)
- OTP should expire (5-10 minutes typical)
- Rate limiting on OTP generation (prevent spam)
- JWT secret key management

**Complexity**: MEDIUM - Standard patterns exist, but requires careful implementation

#### 2. UI Theme Change (Black & White)
**What's Required**:
- Update all CSS variables/theme files
- Change color palette across frontend-app
- Ensure text contrast meets accessibility standards
- Update hover states, borders, shadows
- Maintain visual hierarchy with grayscale

**Technical Considerations**:
- Current app uses colors (blue, green, etc.)
- Need to test readability (black text on white, white on black)
- Buttons, inputs, cards, modals all need updates
- Consider using CSS variables for easy theme management

**Complexity**: LOW - Mostly CSS changes, time-consuming but straightforward

#### 3. Admin Dashboard Architecture
**What's Required**:
- 4 distinct modules with different functionalities
- Each module needs its own UI, API endpoints, and business logic
- Data visualization for metrics (Module 3)
- File upload handling (Module 2 - CSV)
- Background job processing (Module 4 - rescraping)

**Module Breakdown**:

**Module 1 - User Management**:
- List all registered users (from mobile app)
- View login history, last login, activity
- Deactivate/activate accounts
- Search/filter users
- Backend: User CRUD endpoints, status management
- Frontend: Data table with actions

**Module 2 - Product Catalogue Management**:
- CSV upload for bulk product import
- Validate and parse CSV data
- Detect and cleanup missing/broken image links
- Add/edit/delete category tags
- View product list with filtering
- Backend: File upload, CSV parsing, database operations, image validation
- Frontend: File upload component, data grid, tag management UI

**Module 3 - Model Training Dashboard**:
- Interactive sliders for train/test split ratio
- Trigger model retraining
- Display performance metrics (accuracy, precision, recall, F1)
- Show training progress (with WebSocket or polling)
- Visualize metrics (charts/graphs)
- Backend: ML pipeline integration, training job queue, metrics storage
- Frontend: Interactive controls, real-time progress, charts (Chart.js/D3)

**Module 4 - Auto Sync/Rescraping**:
- List available brands
- Select brands for rescraping
- Trigger rescraping job
- Monitor progress (brands done, products added)
- View new records added to database
- Backend: Web scraping logic, job queue, progress tracking
- Frontend: Brand selection UI, progress bars, logs display

**Complexity**: HIGH - Each module is a mini-project with unique requirements

#### 4. Authentication Flow Change
**Current Flow**: 
- Home page → Image upload → Results

**New Flow**:
- Landing page (Login/Signup) → 
- Signup: Email → OTP verification → Success → Login
- Login: Email + Password → JWT token → Admin Dashboard
- Admin Dashboard → 4 modules + Image search functionality

**Impact on Existing Code**:
- frontend-app/src/App.jsx needs major restructuring
- Need to add AuthContext for token management
- All existing pages need to be protected routes
- Image upload page becomes a module in dashboard

**Complexity**: MEDIUM - Requires frontend routing changes and state management

---

### Technical Challenges (Full Project - 100%)
1. **Image Similarity Engine**: Implementing CNN-based deep learning with ResNet/EfficientNet + FAISS for fast similarity search
2. **Hybrid Data Model**: Managing PostgreSQL (structured data) + MongoDB (unstructured/images) efficiently
3. **Real-time Price Tracking**: Dynamic pricing updates and stock availability
4. **Cold Start Problem**: Handling limited initial product catalog
5. **Multi-platform Development**: React web + Flutter mobile consistency

### Business Logic Challenges (Full Project - 100%)
1. Data acquisition from local/online stores
2. Product metadata enrichment and tagging
3. Review moderation and spam filtering
4. Community platform for user-generated dupe recommendations

---

### Challenges for 40% Milestone (Simplified)

**Technical Focus**:
1. ✅ **Image Similarity** - Use pre-trained ResNet50 with cosine similarity (no FAISS needed yet)
2. ✅ **Simple Data Model** - MongoDB for products, embeddings, and metadata (unified storage)
3. ✅ **Static Pricing** - No real-time tracking, manually curated product list
4. ✅ **Small Dataset** - 50-100 products sufficient to prove concept
5. ✅ **Web Only** - Skip mobile complexity, focus on React web app

**Business Logic Focus**:
1. ✅ **Manual Data Collection** - Scrape/collect 50-100 product images manually
2. ✅ **Basic Metadata** - Just name, category, price, brand (no advanced tagging)
3. ✅ **No Reviews Yet** - Defer community features to 60%+
4. ✅ **No User Accounts** - Public demo, no authentication

**Key Simplifications for 40%**:
- Pre-compute all embeddings offline (no real-time embedding generation initially)
- Use numpy/scipy for similarity search (defer FAISS to 60%)
- Local file storage for images (defer cloud storage to 60%)
- Manual product curation (defer automated scraping to 60%)
- Basic UI with minimal styling (enhance UX at 60%)

## High-level Task Breakdown - NEW REQUIREMENTS

**Created: November 11, 2025 - Planner Mode**
**Focus**: Authentication + Admin Dashboard + Black/White Theme

---

### PHASE A: Backend Authentication System [CRITICAL - Week 1]

**Goal**: Implement JWT + Email OTP authentication system

- [ ] **Task A.1**: Set up authentication dependencies and configuration
  - Install: PyJWT, python-jose, passlib[bcrypt], python-multipart, aiosmtplib
  - Create .env file with JWT_SECRET, EMAIL credentials, OTP expiration time
  - Add email configuration to backend config
  - **Success Criteria**: Dependencies installed, .env file configured
  - **Test**: Import all auth libraries successfully

- [ ] **Task A.2**: Create MongoDB collections for auth
  - Collection: users (email, password_hash, is_active, is_verified, created_at, last_login)
  - Collection: otps (email, otp_code, expires_at, is_used, created_at) with TTL index
  - Collection: refresh_tokens (user_id, token, expires_at) with TTL index
  - **Success Criteria**: Collections created with proper indexes
  - **Test**: Can insert and query test documents

- [ ] **Task A.3**: Implement password hashing and JWT utilities
  - Create utils/auth.py with hash_password(), verify_password()
  - Create JWT token generation (access token 30min, refresh token 7 days)
  - Create JWT token validation and decoding functions
  - **Success Criteria**: Can hash/verify passwords, generate/validate JWT tokens
  - **Test**: Hash password, verify it; Generate token, decode it

- [ ] **Task A.4**: Implement OTP generation and email sending
  - Create services/email_service.py with SMTP configuration
  - Generate 6-digit random OTP
  - Send email using Gmail SMTP (ussamainayat@gmail.com)
  - Store OTP in database with 10-minute expiration
  - **Success Criteria**: Can send OTP email, store in database
  - **Test**: Send test OTP to email, verify received and stored

- [ ] **Task A.5**: Create signup endpoint with OTP
  - POST /api/auth/signup - accepts email, password
  - Validate email format, password strength (min 8 chars)
  - Check if email already registered
  - Hash password, create user (is_verified=False)
  - Generate and send OTP
  - **Success Criteria**: Endpoint returns success, OTP sent to email
  - **Test**: Signup with valid email, receive OTP

- [ ] **Task A.6**: Create OTP verification endpoint
  - POST /api/auth/verify-otp - accepts email, otp_code
  - Validate OTP (correct code, not expired, not used)
  - Mark user as verified (is_verified=True)
  - Mark OTP as used
  - **Success Criteria**: Endpoint verifies OTP, activates user
  - **Test**: Verify with correct OTP (success), wrong OTP (fail)

- [ ] **Task A.7**: Create login endpoint
  - POST /api/auth/login - accepts email, password
  - Validate credentials, check if user is_verified
  - Generate access token + refresh token
  - Update last_login timestamp
  - Return tokens + user info
  - **Success Criteria**: Endpoint returns JWT tokens for valid credentials
  - **Test**: Login with verified account (success), unverified account (fail)

- [ ] **Task A.8**: Create token refresh endpoint
  - POST /api/auth/refresh - accepts refresh_token
  - Validate refresh token
  - Generate new access token
  - **Success Criteria**: Endpoint returns new access token
  - **Test**: Refresh with valid token (success), expired token (fail)

- [ ] **Task A.9**: Create authentication middleware
  - Create dependencies/auth.py with get_current_user()
  - Extract token from Authorization header
  - Validate token, decode user info
  - Return user object or raise 401 error
  - **Success Criteria**: Middleware validates tokens on protected routes
  - **Test**: Access protected route with valid token (success), no token (401)

- [ ] **Task A.10**: Create logout endpoint
  - POST /api/auth/logout - accepts refresh_token
  - Invalidate refresh token (delete from database)
  - **Success Criteria**: Endpoint invalidates token
  - **Test**: Logout, then try to refresh (should fail)

---

### PHASE B: Admin Dashboard Backend Endpoints [CRITICAL - Week 2]

**Goal**: Create API endpoints for 4 admin dashboard modules

#### Module 1: User Management

- [ ] **Task B.1**: Create user listing endpoint
  - GET /api/admin/users - returns all users with pagination
  - Include: email, is_active, is_verified, created_at, last_login
  - Support search (by email) and filter (by status)
  - Requires authentication (admin only)
  - **Success Criteria**: Endpoint returns paginated user list
  - **Test**: Fetch users, verify pagination and filtering

- [ ] **Task B.2**: Create user deactivation endpoint
  - PUT /api/admin/users/{user_id}/deactivate - sets is_active=False
  - PUT /api/admin/users/{user_id}/activate - sets is_active=True
  - Requires authentication (admin only)
  - **Success Criteria**: Endpoint toggles user status
  - **Test**: Deactivate user, verify login fails; Activate, verify login works

#### Module 2: Product Catalogue Management

- [ ] **Task B.3**: Create CSV product import endpoint
  - POST /api/admin/products/import-csv - accepts CSV file
  - Parse CSV (columns: name, category, brand, price, image_url, description)
  - Validate each row (required fields, valid URL format)
  - Bulk insert products into MongoDB
  - Return summary (total, success, errors)
  - **Success Criteria**: Endpoint imports products from CSV
  - **Test**: Upload valid CSV, verify products in database

- [ ] **Task B.4**: Create missing links cleanup endpoint
  - POST /api/admin/products/cleanup-links - scans all products
  - Check each image_url (HTTP HEAD request)
  - Mark products with broken links (add "broken_link" flag)
  - Return list of broken links
  - **Success Criteria**: Endpoint identifies broken image links
  - **Test**: Add product with broken link, run cleanup, verify flagged

- [ ] **Task B.5**: Create category tags management endpoints
  - GET /api/admin/categories - returns all unique categories
  - POST /api/admin/categories - adds new category
  - PUT /api/admin/categories/{id} - updates category name
  - DELETE /api/admin/categories/{id} - removes category
  - **Success Criteria**: CRUD operations for categories
  - **Test**: Create category, update it, delete it

- [ ] **Task B.6**: Create product listing with filtering
  - GET /api/admin/products - returns all products with pagination
  - Support filter by category, brand, broken_link flag
  - Support search by name
  - **Success Criteria**: Endpoint returns filtered product list
  - **Test**: Filter by category, search by name

#### Module 3: Model Training Dashboard

- [ ] **Task B.7**: Create model training trigger endpoint
  - POST /api/admin/ml/train - accepts train_split (0.0-1.0)
  - Validate train_split (must be between 0.5 and 0.95)
  - Trigger ML training in background (async task)
  - Return job_id for tracking
  - **Success Criteria**: Endpoint starts training job
  - **Test**: Trigger training, verify job created

- [ ] **Task B.8**: Create training progress endpoint
  - GET /api/admin/ml/training-status/{job_id}
  - Return: status (pending/running/completed/failed), progress %, current_epoch
  - **Success Criteria**: Endpoint returns training status
  - **Test**: Check status during and after training

- [ ] **Task B.9**: Create metrics retrieval endpoint
  - GET /api/admin/ml/metrics - returns latest training metrics
  - Include: accuracy, precision, recall, f1_score, train_split, timestamp
  - Return last 10 training runs with chart data
  - **Success Criteria**: Endpoint returns performance metrics
  - **Test**: Fetch metrics, verify data format

- [ ] **Task B.10**: Implement background training job
  - Create services/ml_training_service.py
  - Load products from database, split by train_split ratio
  - Re-train ResNet50 or fine-tune on new products
  - Calculate metrics (accuracy, precision, recall, F1)
  - Save metrics to database (ml_metrics collection)
  - Update job status throughout process
  - **Success Criteria**: Training runs in background, updates status
  - **Test**: Trigger training, monitor logs, verify completion

#### Module 4: Auto Sync / Rescraping

- [ ] **Task B.11**: Create brand listing endpoint
  - GET /api/admin/scraping/brands - returns all available brands
  - Include: brand_name, last_scraped_at, product_count
  - **Success Criteria**: Endpoint returns brand list
  - **Test**: Fetch brands, verify data

- [ ] **Task B.12**: Create scraping trigger endpoint
  - POST /api/admin/scraping/start - accepts brand_ids[]
  - Validate brand_ids exist
  - Start scraping job in background for selected brands
  - Return job_id for tracking
  - **Success Criteria**: Endpoint starts scraping job
  - **Test**: Trigger scraping for 1 brand, verify job created

- [ ] **Task B.13**: Create scraping progress endpoint
  - GET /api/admin/scraping/status/{job_id}
  - Return: status, brands_completed, brands_total, products_added
  - **Success Criteria**: Endpoint returns scraping progress
  - **Test**: Check status during scraping

- [ ] **Task B.14**: Implement web scraping service
  - Create services/scraping_service.py
  - Implement scrapers for configured brands/websites
  - Extract product data (name, image, price, etc.)
  - Save to MongoDB, update existing products if duplicate
  - Track progress (brands done, products added)
  - **Success Criteria**: Scraping service adds products to database
  - **Test**: Run scraper for 1 brand, verify products added

---

### PHASE C: Frontend Authentication UI [CRITICAL - Week 3]

**Goal**: Create login/signup pages with OTP verification flow

- [ ] **Task C.1**: Set up authentication context
  - Create context/AuthContext.jsx
  - Manage state: user, token, isAuthenticated, loading
  - Functions: login(), signup(), logout(), refreshToken()
  - Store token in localStorage
  - **Success Criteria**: AuthContext provides auth state and functions
  - **Test**: Access auth state from any component

- [ ] **Task C.2**: Create Login page
  - Create pages/Login.jsx
  - Form: email input, password input, submit button
  - Validation: email format, required fields
  - On submit: call /api/auth/login, store token
  - Show error messages for invalid credentials
  - Link to Signup page
  - **Success Criteria**: Can login with valid credentials
  - **Test**: Login with correct email/password, redirect to dashboard

- [ ] **Task C.3**: Create Signup page
  - Create pages/Signup.jsx
  - Form: email input, password input, confirm password, submit button
  - Validation: email format, password match, min 8 chars
  - On submit: call /api/auth/signup, show OTP form
  - **Success Criteria**: Can signup, triggers OTP email
  - **Test**: Signup with new email, receive OTP

- [ ] **Task C.4**: Create OTP verification component
  - Create pages/VerifyOTP.jsx (shown after signup)
  - Form: 6-digit OTP input, verify button
  - On submit: call /api/auth/verify-otp
  - On success: show success message, redirect to login
  - Resend OTP button (with cooldown timer)
  - **Success Criteria**: Can verify OTP, account activated
  - **Test**: Enter correct OTP (success), wrong OTP (error)

- [ ] **Task C.5**: Create protected route wrapper
  - Create components/ProtectedRoute.jsx
  - Check if user is authenticated (token exists)
  - If not, redirect to login page
  - If yes, render protected component
  - **Success Criteria**: Unauthenticated users redirected to login
  - **Test**: Access dashboard without login (redirect), with login (access)

- [ ] **Task C.6**: Update App.jsx with authentication routing
  - Set Login as default route (/)
  - Add routes: /signup, /verify-otp, /dashboard/* (protected)
  - Wrap dashboard routes with ProtectedRoute
  - Remove old home page
  - **Success Criteria**: App starts with login page
  - **Test**: Open app, see login page; Login, see dashboard

---

### PHASE D: Admin Dashboard Frontend [CRITICAL - Week 3-4]

**Goal**: Create dashboard layout and 4 module UIs

- [ ] **Task D.1**: Create dashboard layout
  - Create pages/Dashboard.jsx
  - Sidebar navigation with 5 items: Overview, Users, Products, ML Training, Scraping
  - Top bar with user info and logout button
  - Main content area for modules
  - **Success Criteria**: Dashboard layout with navigation
  - **Test**: Navigate between modules

- [ ] **Task D.2**: Create Overview/Home module
  - Create pages/DashboardHome.jsx
  - Show welcome message
  - Display quick stats: total users, products, last training date
  - Quick links to other modules
  - **Success Criteria**: Overview page shows stats
  - **Test**: View overview, verify stats displayed

- [ ] **Task D.3**: Create Module 1 - User Management UI
  - Create pages/UserManagement.jsx
  - Data table with columns: email, status, verified, created, last login
  - Search bar (filter by email)
  - Action buttons: Activate/Deactivate
  - Pagination controls
  - **Success Criteria**: Can view users and toggle status
  - **Test**: View users, deactivate one, verify status changed

- [ ] **Task D.4**: Create Module 2 - Product Management UI
  - Create pages/ProductManagement.jsx
  - CSV upload component with drag-and-drop
  - Button: "Check Broken Links"
  - Product data table with filters (category, broken links)
  - Category management section (add/edit/delete tags)
  - **Success Criteria**: Can upload CSV, manage categories
  - **Test**: Upload CSV with 10 products, verify imported

- [ ] **Task D.5**: Create Module 3 - ML Training Dashboard UI
  - Create pages/MLTraining.jsx
  - Train/Test split slider (50% to 95%)
  - "Start Training" button
  - Progress bar (when training active)
  - Metrics display: accuracy, precision, recall, F1
  - Line chart showing metric history (last 10 runs)
  - **Success Criteria**: Can trigger training, view progress and metrics
  - **Test**: Start training, watch progress, verify metrics displayed

- [ ] **Task D.6**: Create Module 4 - Auto Sync/Scraping UI
  - Create pages/ScrapingManagement.jsx
  - Brand selection list with checkboxes
  - "Start Scraping" button
  - Progress display: brands completed, products added
  - Logs/console showing activity
  - Table showing new products added
  - **Success Criteria**: Can trigger scraping, monitor progress
  - **Test**: Select 1 brand, start scraping, view progress

- [ ] **Task D.7**: Move image upload to dashboard
  - Create pages/ImageSearch.jsx (existing functionality)
  - Add as 5th navigation item: "Product Search"
  - Keep existing upload, search, results functionality
  - **Success Criteria**: Image search accessible from dashboard
  - **Test**: Upload image from dashboard, get results

---

### PHASE E: Black & White Theme Implementation [Week 4]

**Goal**: Apply black and white color scheme across entire application

- [ ] **Task E.1**: Create black & white CSS theme variables
  - Create styles/theme.css with CSS variables
  - Colors: --bg-primary (#FFFFFF), --bg-secondary (#F5F5F5), --bg-dark (#000000)
  - Text: --text-primary (#000000), --text-secondary (#666666), --text-light (#FFFFFF)
  - Borders: --border-color (#E0E0E0), --border-dark (#333333)
  - Shadows: --shadow-sm (light gray), --shadow-md, --shadow-lg
  - **Success Criteria**: Theme variables defined
  - **Test**: Import theme, apply variables

- [ ] **Task E.2**: Update global styles
  - Update styles/index.css to use theme variables
  - Set body background: white
  - Set default text color: black
  - Update input, button base styles
  - **Success Criteria**: Base UI uses black/white
  - **Test**: View any page, verify black/white

- [ ] **Task E.3**: Update Login/Signup pages styling
  - Replace colors with black/white theme
  - White background, black text, gray borders
  - Black buttons with white text (hover: invert)
  - **Success Criteria**: Auth pages are black/white
  - **Test**: View login/signup, verify theme

- [ ] **Task E.4**: Update Dashboard layout styling
  - Sidebar: black background, white text
  - Top bar: white background, black text, gray border
  - Main content: white background
  - **Success Criteria**: Dashboard layout is black/white
  - **Test**: View dashboard, verify theme

- [ ] **Task E.5**: Update all module pages styling
  - Update UserManagement, ProductManagement, MLTraining, ScrapingManagement
  - Tables: white background, black text, gray borders
  - Buttons: black with white text
  - Cards: white with gray border
  - **Success Criteria**: All modules use black/white theme
  - **Test**: Visit each module, verify theme

- [ ] **Task E.6**: Update charts and data visualizations
  - Configure Chart.js colors: black lines, gray fill
  - Ensure chart text is black
  - **Success Criteria**: Charts are black/white/gray
  - **Test**: View ML Training charts, verify colors

- [ ] **Task E.7**: Test contrast and accessibility
  - Verify text contrast ratio (WCAG AA: 4.5:1 minimum)
  - Test on light and dark mode (if applicable)
  - Ensure hover states are visible
  - **Success Criteria**: All text is readable
  - **Test**: Use contrast checker tool, verify all passes

---

### PHASE F: Integration, Testing & Polish [Week 5]

**Goal**: End-to-end testing and bug fixes

- [ ] **Task F.1**: End-to-end authentication flow testing
  - Test: Signup → OTP verification → Login → Dashboard access
  - Test: Wrong OTP, expired OTP, resend OTP
  - Test: Login with unverified account (should fail)
  - Test: Logout, token refresh
  - **Success Criteria**: Auth flow works flawlessly
  - **Test**: Complete signup to dashboard 5 times

- [ ] **Task F.2**: Test all admin modules functionality
  - Test Module 1: View users, deactivate/activate
  - Test Module 2: Upload CSV, check broken links, manage categories
  - Test Module 3: Trigger training, monitor progress, view metrics
  - Test Module 4: Trigger scraping, monitor progress
  - **Success Criteria**: All modules work as expected
  - **Test**: Perform 3 actions in each module

- [ ] **Task F.3**: Test UI theme consistency
  - Check all pages for color consistency
  - Verify no colored elements remain (except intentional accents)
  - Test responsive design on mobile
  - **Success Criteria**: Consistent black/white theme everywhere
  - **Test**: Browse entire app, note any color issues

- [ ] **Task F.4**: Performance and security testing
  - Test with 1000+ users, 1000+ products
  - Check page load times, API response times
  - Test JWT token expiration handling
  - Test rate limiting on OTP generation
  - **Success Criteria**: App performs well, secure
  - **Test**: Load test, security audit

- [ ] **Task F.5**: Error handling and edge cases
  - Test invalid inputs on all forms
  - Test network errors (API down)
  - Test concurrent operations (2 trainings at once)
  - **Success Criteria**: Graceful error handling
  - **Test**: Try to break the app, verify error messages

- [ ] **Task F.6**: Documentation and deployment guide
  - Update README with new authentication flow
  - Document email configuration
  - Document admin dashboard modules
  - Create deployment checklist
  - **Success Criteria**: Clear documentation
  - **Test**: Follow docs to set up on new machine

---

### 📦 Summary

**Total Tasks**: 57 tasks across 6 phases
**Estimated Timeline**: 5 weeks
- Week 1: Backend Authentication (Phase A)
- Week 2: Admin Backend Endpoints (Phase B)
- Week 3: Frontend Auth + Dashboard Structure (Phase C + D.1-D.2)
- Week 4: Dashboard Modules + Theme (Phase D.3-D.7 + Phase E)
- Week 5: Integration Testing + Polish (Phase F)

**Dependencies Required**:
- Backend: PyJWT, python-jose, passlib, aiosmtplib, pandas (CSV), celery (optional for background jobs)
- Frontend: react-router-dom, axios, chart.js (for metrics visualization)

---

## High-level Task Breakdown (40% MILESTONE FOCUSED)

**Revised: November 8, 2025 - Focused on Core MVP**
**NOTE**: This section is now superseded by the new requirements above. Keeping for reference.

---

### ✅ Phase 1: Project Setup & Infrastructure [COMPLETED]
- [x] **Task 1.1**: Create project directory structure
- [x] **Task 1.2**: Initialize configuration files
- [x] **Task 1.3**: Set up version control with proper .gitignore files

---

### 🎯 Phase 2: ML Engine - Proof of Concept [CRITICAL - Week 1-2]

**Goal**: Prove that image similarity search works with real fashion images

- [ ] **Task 2.1**: Set up ML environment and install dependencies
  - Install PyTorch/TensorFlow, torchvision, PIL, numpy
  - Download pre-trained ResNet50 or EfficientNet-B0 model
  - **Success Criteria**: Can import libraries and load pre-trained model without errors
  - **Test**: Run simple inference on a test image

- [ ] **Task 2.2**: Create image preprocessing pipeline
  - Write function to resize, normalize, and prepare images for model input
  - Handle different image formats (JPG, PNG, WebP)
  - **Success Criteria**: Can process any uploaded image into model-ready tensor
  - **Test**: Process 10 different images successfully

- [ ] **Task 2.3**: Implement feature extraction (embedding generation)
  - Extract deep features from pre-trained CNN (last layer before classification)
  - Save embeddings as numpy arrays
  - **Success Criteria**: Can extract 2048-dim (ResNet50) or 1280-dim (EfficientNet) feature vectors
  - **Test**: Extract embeddings from 5 images, verify correct shape

- [ ] **Task 2.4**: Implement similarity calculation
  - Use cosine similarity to compare embeddings
  - Create function to find top-K similar images
  - **Success Criteria**: Given one image, can rank all other images by similarity
  - **Test**: Upload a bag image, verify similar bags rank higher than shoes

- [ ] **Task 2.5**: Create sample product dataset (50-100 items)
  - Collect fashion images from free sources (Unsplash, Pexels, public datasets)
  - Mix: bags, shoes, watches, clothing, accessories
  - Include both "luxury look" and "affordable alternatives"
  - **Success Criteria**: 50-100 product images with basic metadata (name, category, price)
  - **Test**: Can load and view all images

- [ ] **Task 2.6**: Pre-compute embeddings for product catalog
  - Run feature extraction on all catalog images
  - Store embeddings with product IDs
  - **Success Criteria**: All product images have pre-computed embeddings saved
  - **Test**: Can load embeddings quickly (< 1 second for 100 products)

---

### 🗄️ Phase 3: Database & Backend API [CRITICAL - Week 2-3]

**Goal**: Store products and serve search results via API

**DATABASE CHANGED TO MONGODB** (November 9, 2025 - PostgreSQL installation issues)

- [ ] **Task 3.1**: Set up local MongoDB database
  - Install MongoDB Community Edition locally
  - Create database: `dupefinder`
  - **Success Criteria**: Can connect to database from Python using pymongo
  - **Test**: Run connection test successfully

- [ ] **Task 3.2**: Design and create Products collection schema
  - Collection: products (id, name, category, brand, price, image_path, embedding, description, created_at)
  - Store embeddings directly in MongoDB (2048-dim array)
  - **Success Criteria**: Collection created with proper indexes
  - **Test**: Can insert and query sample product with embedding

- [ ] **Task 3.3**: Create data import script
  - Script to bulk insert products from CSV with embeddings
  - Store product metadata AND embeddings in same document
  - **Success Criteria**: Can import all 100 products with embeddings into MongoDB
  - **Test**: Query returns correct count of products with embeddings

- [ ] **Task 3.4**: Set up FastAPI backend structure
  - Create main.py with basic app initialization
  - Add CORS middleware for frontend access
  - Create health check endpoint: GET /health
  - **Success Criteria**: Server starts without errors on port 8000
  - **Test**: curl http://localhost:8000/health returns {"status": "ok"}

- [ ] **Task 3.5**: Create image upload endpoint
  - POST /api/search/upload - accepts image file
  - Save uploaded image temporarily
  - Return file path or success message
  - **Success Criteria**: Can upload image via Postman/curl
  - **Test**: Upload test image, verify it's saved

- [ ] **Task 3.6**: Create similarity search endpoint
  - POST /api/search/similar - accepts image, returns top-K similar products
  - Extract embedding from uploaded image
  - Compare with all product embeddings
  - Return products sorted by similarity score
  - **Success Criteria**: Endpoint returns JSON with product details and similarity scores
  - **Test**: Upload bag image, verify similar bags in top 5 results

- [ ] **Task 3.7**: Create products listing endpoint
  - GET /api/products - returns all products (for testing)
  - GET /api/products/{id} - returns single product details
  - **Success Criteria**: Can fetch product data via API
  - **Test**: Fetch all products, verify count matches database

---

### 🎨 Phase 4: Frontend Web Interface [CRITICAL - Week 3-4]

**Goal**: Create clean, functional UI for image upload and results display

- [ ] **Task 4.1**: Set up React development environment
  - Install Node.js dependencies
  - Configure API base URL
  - **Success Criteria**: React app runs on port 3000
  - **Test**: Access http://localhost:3000 shows welcome page

- [ ] **Task 4.2**: Create image upload component
  - Drag-and-drop file upload or browse button
  - Image preview before search
  - "Search for Alternatives" button
  - **Success Criteria**: Can select/drag image, see preview
  - **Test**: Select image, verify preview displays correctly

- [ ] **Task 4.3**: Integrate upload with backend API
  - Send image to backend /api/search/similar endpoint
  - Handle loading state during search
  - Handle errors gracefully
  - **Success Criteria**: Clicking search sends image to backend
  - **Test**: Upload image, check network tab for API call

- [ ] **Task 4.4**: Create search results display component
  - Grid layout showing similar products
  - Each product card shows: image, name, price, brand, similarity %
  - **Success Criteria**: Results render in clean grid layout
  - **Test**: Mock API response, verify UI displays all fields

- [ ] **Task 4.5**: Add basic styling and responsiveness
  - Use CSS/Tailwind for clean, modern design
  - Mobile-responsive layout
  - Loading spinner during search
  - **Success Criteria**: App looks professional and works on mobile browsers
  - **Test**: View on desktop and mobile, verify layout adapts

- [ ] **Task 4.6**: Create product detail modal/page
  - Click on product to see full details
  - Show larger image, full description, price, purchase link (if available)
  - **Success Criteria**: Can view individual product details
  - **Test**: Click product card, modal/page opens with details

---

### 🧪 Phase 5: Integration Testing & Refinement [Week 4-5]

**Goal**: Test end-to-end workflow and fix bugs

- [ ] **Task 5.1**: End-to-end workflow testing
  - Test with 20+ different fashion images
  - Verify results are relevant
  - Document accuracy (% of relevant results in top 5)
  - **Success Criteria**: 60-70% of searches return relevant results
  - **Test**: Create test report with accuracy metrics

- [ ] **Task 5.2**: Performance optimization
  - Measure search response time
  - Optimize if > 10 seconds
  - Add caching for pre-computed embeddings
  - **Success Criteria**: Search completes in < 10 seconds
  - **Test**: Time 10 searches, calculate average

- [ ] **Task 5.3**: Error handling and edge cases
  - Handle invalid image formats
  - Handle empty search results
  - Handle backend unavailable
  - **Success Criteria**: App doesn't crash on errors, shows user-friendly messages
  - **Test**: Test with invalid inputs, verify error messages

- [ ] **Task 5.4**: UI/UX improvements based on testing
  - Fix any visual bugs
  - Improve button placement, text clarity
  - Add helpful instructions for first-time users
  - **Success Criteria**: App is intuitive to use
  - **Test**: Ask someone unfamiliar to use it, observe confusion points

---

### 📊 Phase 6: Demo Preparation & Documentation [Week 5]

**Goal**: Prepare impressive demonstration and documentation

- [ ] **Task 6.1**: Create demo video (3-5 minutes)
  - Show opening homepage
  - Upload luxury item image
  - Show search results
  - Click on alternative to see details
  - Explain the technology briefly
  - **Success Criteria**: Professional-looking video demonstrating all features
  - **Test**: Watch video, verify all features are shown clearly

- [ ] **Task 6.2**: Write technical documentation
  - Update ARCHITECTURE.md with actual implementation
  - Document ML model choice and accuracy
  - Document API endpoints with examples
  - Add setup instructions for running locally
  - **Success Criteria**: Another developer can understand and run the project
  - **Test**: Have someone else try to set up using docs

- [ ] **Task 6.3**: Create presentation slides
  - Problem statement and motivation
  - Solution approach (high-level architecture)
  - Technology stack
  - ML model explanation
  - Live demo
  - Results and accuracy metrics
  - Future work (remaining 60%)
  - **Success Criteria**: 15-20 slides covering all aspects
  - **Test**: Present to friend, get feedback on clarity

- [ ] **Task 6.4**: Prepare test scenarios for live demo
  - Select 5-7 test images that work well
  - Prepare backup screenshots in case of technical issues
  - Test on presentation environment
  - **Success Criteria**: Can complete demo in 5-10 minutes without issues
  - **Test**: Do dry run 3 times, time yourself

---

### 📦 DEFERRED TO 60-100% (Out of Scope for 40%)

- Flutter mobile app
- User authentication and profiles
- Community reviews and ratings system
- Admin dashboard for product management
- Advanced filtering (gender, city, size, budget)
- Analytics dashboards
- Docker deployment
- FAISS vector database (using simple numpy similarity for now)
- Price tracking and auto-refresh
- Multiple image upload
- Wishlist/favorites functionality
- Social sharing features

## Project Status Board

**Updated: March 16, 2026 — FashionCLIP switch complete, Ranking + Reindex implemented**

---

### Progress Log — March 15–16, 2026

#### March 15, 2026 (previous session)
- **FashionCLIP isolated pipeline fully planned** — separate `ml-engine/fashionclip/` module created with its own extractor, config, requirements, and generation script (using PyTorch DataLoader with `num_workers=4` to fix the 2-hour I/O bottleneck from previous attempt)
- **Backend isolated FashionCLIP route** created at `/api/search/fashionclip/similar` — ran in parallel with live ResNet50 route for evaluation
- **Local backend fixes**: FashionCLIP startup loading moved to `threading.Thread` to prevent FastAPI lifespan from blocking the event loop (previously backend froze on startup)
- **Planned mobile app ML integration** (Mobile-ML-1, Mobile-ML-2, Mobile-ML-3) — deferred to execution

#### March 16, 2026 (today)
- **New Vast.ai instance** (2x RTX 4090) — connected, uploaded `ml-engine/`, fixed `ml-engine/config.yaml` missing `mongodb` section
- **23,056 product images downloaded** from MongoDB to Vast.ai instance (~16 min, 16 workers)
- **FashionCLIP embeddings generated** in ~5 minutes on 2x 4090 using PyTorch DataLoader — confirmed fix worked vs 2-hour I/O bottleneck
- **20 FAISS indices + 20 ID maps** (46MB) downloaded to `backend/app/ml/fashionclip_indices/` + `fashionclip_id_maps/`
- **Side-by-side comparison report** generated at `ml-engine/evaluation/comparison_results.html`
- **ResNet50 fully removed** from the project — all code, files, and FAISS indices backed up to `C:\Users\US\Desktop\FYP\dupefinder-backup\Resnet\`
- **`search.py` rewritten** to use FashionCLIP as the sole search engine at `/api/search/similar`
- **`main.py` cleaned up** — single background thread for FashionCLIP loading, removed ResNet thread
- **`search_fashionclip.py` deleted** (merged into main `search.py`)
- **`ml-engine/config.yaml`** updated to FashionCLIP config (512-dim, CLIP normalization)
- **`ml-engine/embeddings/__init__.py`** updated to export `FashionCLIPExtractor`
- **`ml-engine/data/catalogue_images/`** deleted (local sample images no longer needed — real data lives on Vast.ai)
- **Multi-signal ranking system implemented** in `search.py`:
  - `_rerank()` function: `final_score = 0.7*sim + 0.2*price_score + 0.1*attr_score`
  - `final_score` field added to `SearchResult` model
  - Ranking weights `w_sim/w_price/w_attr` configurable via query params (default 0.7/0.2/0.1)
  - Thread-safe `_index_lock` added to protect all reads/writes to in-memory FAISS dicts
  - `hot_reload_indices()` function added — replaces in-memory indices from disk without restart
- **Incremental reindex pipeline implemented**:
  - `ml-engine/scripts/reindex_new_products.py` — standalone CLI script (manual use, `--migrate-existing`, `--dry-run`, `--limit`, `--category` flags)
  - `_run_reindex_task()` + `_sync_reindex()` added to `admin_new.py` — auto-triggered as `asyncio.create_task` after `run_scraping_job` completes
  - Uses `fashionclip_indexed: True` MongoDB field as tracking flag
  - All new scraped products are automatically embedded and appended to FAISS indices, then `hot_reload_indices()` swaps live in-memory indices with zero downtime
  - **Run once after this deploy**: `python ml-engine/scripts/reindex_new_products.py --migrate-existing` to mark all 23,056 existing products as indexed

---

#### Remaining Tasks
- [ ] **Mobile-ML-1**: Add `searchSimilarImages()` to `api_service.dart` (see plan below)
- [ ] **Mobile-ML-2**: Build `image_search_screen.dart`
- [ ] **Mobile-ML-3**: Wire into app navigation
- [ ] `phase4-ranking` ✅ done
- [ ] `phase4-reindex` ✅ done

---

**Updated: March 15, 2026 - ML FAISS Pipeline Plan added**

### 🔖 DEFERRED — Mobile App ML Integration (FashionCLIP) — Plan Ready, Not Yet Executed

> Updated March 16, 2026: Switched from ResNet50 to FashionCLIP. Backend `/api/search/similar` now uses FashionCLIP. Tasks below updated accordingly.

**Backend is ready**: `POST /api/search/similar` is live and serving FashionCLIP results (512-dim, 20 category indices).

---

#### Mobile-ML-1: `api_service.dart` — Add `searchSimilarImages()`

**File**: `mobile/lib/services/api_service.dart`

**What to add**: A new method that sends a multipart POST to `/api/search/similar` with the user's image file and optional filters including ranking weight overrides.

**Method signature**:
```dart
Future<Map<String, dynamic>> searchSimilarImages({
  required File imageFile,   // from image_picker
  int topK = 5,              // number of results
  String? category,          // optional display_category filter
  double? minPrice,          // optional price filter
  double? maxPrice,
  double wSim   = 0.7,       // ranking: visual similarity weight
  double wPrice = 0.2,       // ranking: price affordability weight
  double wAttr  = 0.1,       // ranking: attribute match weight
})
```

**Implementation notes**:
- Use `http.MultipartRequest('POST', uri)` — same `http` package already in pubspec
- Detect MIME from extension: `.png` → `image/png`, else → `image/jpeg`
- Include `Authorization: Bearer $token` header if user is logged in
- Endpoint: `$baseUrl/search/similar?top_k=5&category=...&w_sim=0.7&w_price=0.2&w_attr=0.1`
- **Response shape**:
  ```json
  {
    "query_image": "...",
    "search_time_ms": 620.5,
    "total_results": 5,
    "category_searched": "Women Kurta",
    "results": [
      {
        "product_id": "123",
        "name": "Embroidered Kurta",
        "brand": "Gul Ahmed",
        "price": 2500.0,
        "image_url": "https://...",
        "product_url": "https://...",
        "display_category": "Women Kurta",
        "similarity_score": 0.87,
        "final_score": 0.74
      }
    ]
  }
  ```
- **`final_score`** is the primary ranking field (combines similarity + price + attributes). Display this as the match % to users.
- **`similarity_score`** is the raw visual match (0–1). Can be shown as a secondary detail.
- **Package needed**: add `http_parser: ^4.0.0` to `pubspec.yaml` (for `MediaType`)

**Success criteria**: calling `searchSimilarImages(imageFile: file)` returns a parsed list of product maps with both `similarity_score` and `final_score`.

---

#### Mobile-ML-2: `image_search_screen.dart` — Build Image Search UI

**File**: `mobile/lib/screens/search/image_search_screen.dart`

**Flow**:
1. User taps camera or gallery icon
2. `image_picker` opens (already in pubspec? — check first)
3. Selected image is shown as preview thumbnail
4. Optional: category dropdown (20 options matching backend slugs), price range sliders
5. Tap "Find Similar" → calls `ApiService().searchSimilarImages()`
6. Loading spinner while waiting (FashionCLIP inference takes ~1–3s on backend CPU)
7. Results displayed as a scrollable grid of product cards

**Product card should show**:
- Product image (from `image_url`)
- Product name + brand
- Price in PKR
- Match % badge: use `final_score * 100` rounded (e.g. "74% match") — this combines visual + price + attributes
- Optional secondary detail: raw visual similarity `similarity_score * 100` (e.g. "87% visual")
- Tap → opens `product_url` in browser (use `url_launcher`)

**State management**: use `StatefulWidget` + `setState` — no need for a provider for a single screen.

**Packages needed** (check pubspec first):
- `image_picker` — camera/gallery access
- `url_launcher` — open product URLs in browser

**Success criteria**: User can pick an image, see a spinner, then see at least 1 product card with a name, price, and similarity score.

---

#### Mobile-ML-3: Wire search screen into app navigation

**File**: `mobile/lib/main.dart` or bottom nav bar file

**What to do**: Add the image search screen as a tab or FAB in the main app navigation.
- Suggested entry point: a camera/search icon in the bottom navigation bar, or a dedicated "Search" tab
- Requires reading the existing navigation structure first before implementing

**Success criteria**: Tapping the search icon navigates to `ImageSearchScreen`.

---

#### Notes on index / embedding consistency (MongoDB ↔ FAISS)

- Currently FashionCLIP has **23,056 products** indexed across 20 categories
- When the scraper adds new products to MongoDB, the FAISS indices become stale
- **Re-indexing plan** (separate task `phase4-reindex`):
  1. Script queries MongoDB for products added after last index timestamp
  2. Downloads new product images
  3. Extracts FashionCLIP embeddings (batch)
  4. Rebuilds affected category FAISS indices
  5. Saves new `.index` + `.pkl` files to `backend/app/ml/fashionclip_indices/`
  6. Hot-reloads in-memory indices (or restarts backend)
- Until re-indexing is implemented: new scraped products won't appear in search results

---

- [x] **Mobile-ML-1**: Add `searchSimilarImages()` to `api_service.dart` ✅ (March 2026)
- [x] **Mobile-ML-2**: Build `image_search_screen.dart` — image picker, category filter, results grid with match %, price, url_launcher ✅
- [x] **Mobile-ML-3**: Wire search screen into app navigation (route `/search`, Home "Find Similar" → ImageSearchScreen) ✅
- **Prerequisite**: Backend running with FashionCLIP indices loaded ✅ (already done)

---

### Mobile App Modules (FYP Proposal Alignment) — March 2026

**Source**: FYP Proposal — DupeFinder Affordable Alternatives for Luxury Wearables

| FYP Module | Mobile Implementation | Status |
|------------|------------------------|--------|
| **User Experience** | Upload/capture image, filters (category, gender, budget), personalized recommendations | Mobile-ML-1/2/3 (image search) |
| **User Experience** | Wishlist (save favorites) | Planned — screen + local/API storage |
| **User Experience** | Compare options (side-by-side) | Planned — compare screen |
| **User Experience** | Social sharing (share links) | Planned — url_launcher + share_plus |
| **Image Matching & Recommendation** | CNN-based search, hybrid ranking (style → affordability → popularity) | Backend ✅; Mobile calls `/api/search/similar` |
| **Pricing & Availability** | Show price, “Best Savings”, last-updated; availability alerts | In product cards + detail (later) |
| **Community Reviews & Trust** | Ratings, reviews; in-app “ask for dupes” / reply with store links | Defer — needs backend endpoints |
| **Analytics (user side)** | Average savings, top categories, trending alternatives | Defer — needs backend endpoints |

**Mobile build order (current focus)**:
1. **Image Search** (Mobile-ML-1, 2, 3) — upload/capture → filters → results with match %, price, link.
2. **Product detail** — tap result → full product view, open product_url (url_launcher).
3. **Wishlist** — save favorites (local list or backend when endpoint exists).
4. **Compare** — select 2+ products, comparison screen.
5. **Profile / Insights** — placeholder; hook for future analytics.
6. **Community** — placeholder; hook for “ask for dupes” when backend ready.

---

**Updated: November 11, 2025 - NEW REQUIREMENTS: Authentication + Admin Dashboard**

### ✅ Previously Completed (40% Milestone)
- **Phase 1: Project Setup & Infrastructure** [100% Complete]
- **Phase 2: ML Engine POC** [100% Complete]
- **Phase 3: Database & Backend API** [100% Complete]
- **Phase 4: Frontend Web Interface** [100% Complete]

**Note**: The above phases represent the initial 40% milestone that was completed. The following new requirements represent a major architectural shift.

---

### 🎯 NEW REQUIREMENTS - Status Tracking

**Current Phase**: PLANNING COMPLETE - Ready for Execution
**Next Phase**: Phase A - Backend Authentication System

---

### ✅ PHASE A: Backend Authentication System [COMPLETE] 🎉
**Status**: Complete - 100%
**Timeline**: Completed November 11, 2025

- [x] Task A.1: Set up authentication dependencies and configuration ✅
- [x] Task A.2: Create MongoDB collections for auth ✅
- [x] Task A.3: Implement password hashing and JWT utilities ✅
- [x] Task A.4: Implement OTP generation and email sending ✅
- [x] Task A.5: Create signup endpoint with OTP ✅
- [x] Task A.6: Create OTP verification endpoint ✅
- [x] Task A.7: Create login endpoint ✅
- [x] Task A.8: Create token refresh endpoint ✅
- [x] Task A.9: Create authentication middleware ✅
- [x] Task A.10: Create logout endpoint ✅

**Progress**: 10/10 tasks completed (100%)

**Achievement**: Complete authentication system with JWT + Email OTP!
- All 6 auth endpoints working
- Password hashing with bcrypt
- JWT access (30min) and refresh tokens (7 days)
- Email OTP verification via Gmail SMTP
- MongoDB with TTL indexes for auto-expiry
- Protected route middleware

---

### 📋 PHASE B: Admin Dashboard Backend Endpoints [IN PROGRESS] 🚧
**Status**: In Progress - Backend Complete
**Timeline**: Week 2 (Estimated: 7-10 days)

#### Module 1: User Management
- [ ] Task B.1: Create user listing endpoint
- [ ] Task B.2: Create user deactivation endpoint

#### Module 2: Product Catalogue Management
- [ ] Task B.3: Create CSV product import endpoint
- [ ] Task B.4: Create missing links cleanup endpoint
- [ ] Task B.5: Create category tags management endpoints
- [ ] Task B.6: Create product listing with filtering

#### Module 3: Model Training Dashboard
- [ ] Task B.7: Create model training trigger endpoint
- [ ] Task B.8: Create training progress endpoint
- [ ] Task B.9: Create metrics retrieval endpoint
- [ ] Task B.10: Implement background training job

#### Module 4: Auto Sync / Rescraping
- [ ] Task B.11: Create brand listing endpoint
- [ ] Task B.12: Create scraping trigger endpoint
- [ ] Task B.13: Create scraping progress endpoint
- [ ] Task B.14: Implement web scraping service

**Progress**: 0/14 tasks completed

---

### 📋 PHASE C: Frontend Authentication UI [PENDING]
**Status**: Not Started
**Timeline**: Week 3 (Estimated: 5-7 days)

- [ ] Task C.1: Set up authentication context
- [ ] Task C.2: Create Login page
- [ ] Task C.3: Create Signup page
- [ ] Task C.4: Create OTP verification component
- [ ] Task C.5: Create protected route wrapper
- [ ] Task C.6: Update App.jsx with authentication routing

**Progress**: 0/6 tasks completed

---

### 📋 PHASE D: Admin Dashboard Frontend [PENDING]
**Status**: Not Started
**Timeline**: Week 3-4 (Estimated: 7-10 days)

- [ ] Task D.1: Create dashboard layout
- [ ] Task D.2: Create Overview/Home module
- [ ] Task D.3: Create Module 1 - User Management UI
- [ ] Task D.4: Create Module 2 - Product Management UI
- [ ] Task D.5: Create Module 3 - ML Training Dashboard UI
- [ ] Task D.6: Create Module 4 - Auto Sync/Scraping UI
- [ ] Task D.7: Move image upload to dashboard

**Progress**: 0/7 tasks completed

---

### 📋 PHASE E: Black & White Theme Implementation [PENDING]
**Status**: Not Started
**Timeline**: Week 4 (Estimated: 3-4 days)

- [ ] Task E.1: Create black & white CSS theme variables
- [ ] Task E.2: Update global styles
- [ ] Task E.3: Update Login/Signup pages styling
- [ ] Task E.4: Update Dashboard layout styling
- [ ] Task E.5: Update all module pages styling
- [ ] Task E.6: Update charts and data visualizations
- [ ] Task E.7: Test contrast and accessibility

**Progress**: 0/7 tasks completed

---

### 📋 PHASE F: Integration, Testing & Polish [PENDING]
**Status**: Not Started
**Timeline**: Week 5 (Estimated: 5-7 days)

- [ ] Task F.1: End-to-end authentication flow testing
- [ ] Task F.2: Test all admin modules functionality
- [ ] Task F.3: Test UI theme consistency
- [ ] Task F.4: Performance and security testing
- [ ] Task F.5: Error handling and edge cases
- [ ] Task F.6: Documentation and deployment guide

**Progress**: 0/6 tasks completed

---

### 📊 Overall Progress Summary

**Total Phases**: 6 (A through F)
**Completed**: 0 phases
**In Progress**: 0 phases
**Pending**: 6 phases

**Total Tasks**: 57 tasks
**Completed**: 0 tasks
**Remaining**: 57 tasks

**Estimated Total Time**: 5 weeks (25-35 working days)

**Current Status**: ✅ PLANNING COMPLETE - Ready to begin execution

## Current Status / Progress Tracking

**Updated: November 11, 2025 - Planner Mode → Ready for Executor**

**Current Phase**: PLANNING PHASE [COMPLETE] ✅
**Next Phase**: Phase A - Backend Authentication System [READY TO START]
**Overall Progress**: Planning Complete (0/57 implementation tasks)
**Status**: Comprehensive plan created with 57 tasks across 6 phases. Ready to begin execution.

---

### Planning Summary (What Planner Has Done)

1. ✅ **Analyzed New Requirements**: Broke down all 4 major requirements
2. ✅ **Assessed Technical Complexity**: Identified challenges for each component
3. ✅ **Created Detailed Task Breakdown**: 57 specific tasks with clear success criteria
4. ✅ **Defined Phase Structure**: 6 phases with logical dependencies
5. ✅ **Estimated Timeline**: 5 weeks total (realistic timeline)
6. ✅ **Updated Scratchpad**: Documented everything for Executor reference

### Key Architectural Decisions

**Authentication Strategy**:
- JWT tokens (access: 30min, refresh: 7 days)
- Email OTP via Gmail SMTP (10-minute expiration)
- MongoDB for user/OTP storage (with TTL indexes)
- Bcrypt for password hashing

**Admin Dashboard Strategy**:
- 4 independent modules + 1 image search module
- Background job processing for training and scraping
- Real-time progress tracking (polling or WebSocket)
- CSV-based bulk product import

**Theme Strategy**:
- CSS variables for easy theme management
- Pure black/white/gray palette
- Maintain WCAG AA accessibility standards

**Technology Stack**:
- Backend: FastAPI + PyJWT + aiosmtplib + pandas
- Frontend: React + react-router-dom + axios + Chart.js
- Database: MongoDB (existing)
- ML: Existing ResNet50 pipeline (integrate with training module)

---

### Execution Strategy

**Recommended Approach**:
1. **Week 1**: Complete Phase A (Backend Auth) - 10 tasks
   - Critical foundation for everything else
   - Test each endpoint thoroughly before moving on
   
2. **Week 2**: Complete Phase B (Admin Backend) - 14 tasks
   - Build all 4 module backends
   - Focus on getting basic functionality working
   - Can parallelize some tasks (different modules)
   
3. **Week 3**: Complete Phase C + D.1-D.2 (Frontend Auth + Dashboard Shell)
   - Get authentication flow working end-to-end
   - Create dashboard layout
   - By end of week 3: Can login and see empty dashboard
   
4. **Week 4**: Complete Phase D.3-D.7 + Phase E (Dashboard Modules + Theme)
   - Build UI for all 4 modules
   - Apply black/white theme throughout
   - By end of week 4: Fully functional app with new theme
   
5. **Week 5**: Complete Phase F (Testing & Polish)
   - End-to-end testing
   - Bug fixes
   - Documentation
   
**Critical Path**:
- Phase A must complete before Phase C can start
- Phase B must complete before Phase D.3-D.6 can fully function
- Phase E can be done in parallel with Phase D (but better after for clarity)

**Risk Mitigation**:
- Email sending might have Gmail security issues → Test early (Task A.4)
- Background jobs need proper implementation → Start simple with threading, enhance later
- ML training can take time → Implement progress tracking early (Task B.8)
- CSV import might have edge cases → Validate thoroughly (Task B.3)

---

### Ready for Executor

**Executor should now**:
1. Start with Task A.1 (Set up authentication dependencies)
2. Complete Phase A tasks one by one (A.1 → A.10)
3. Test each task's success criteria before moving to next
4. Update scratchpad after each task completion
5. Report blockers or questions immediately

**Planner will**:
- Monitor progress
- Adjust plan if issues arise
- Provide guidance when Executor has questions
- Validate completion at end of each phase

---

### ✅ Completed
**Phase 1: Project Setup & Infrastructure [100%]**
- ✓ Task 1.1: Created complete project directory structure
  - Backend (FastAPI) with proper module organization
  - Frontend (React) with component structure
  - Mobile (Flutter) with screen/widget organization
  - ML Engine with preprocessing, embeddings, similarity modules
  - Admin Dashboard (React)
  - Database schemas directory
  - Docker configuration directory
  - Documentation directory
  - Scripts directory

- ✓ Task 1.2: Initialized all configuration files
  - Backend: requirements.txt, main.py, README.md
  - Frontend: package.json, index.html, App.js, README.md
  - Mobile: pubspec.yaml, main.dart, README.md
  - ML Engine: requirements.txt, config.yaml, README.md
  - Admin Dashboard: package.json, index.html, App.js, README.md
  - Docker: docker-compose.yml, Dockerfiles for all services
  - Database: PostgreSQL schema, MongoDB schema definitions
  - Documentation: README.md, ARCHITECTURE.md, API_DOCUMENTATION.md
  - Setup scripts: setup.sh (Unix/Mac), setup.ps1 (Windows)

- ✓ Task 1.3: Set up version control
  - Git repository initialized
  - Comprehensive .gitignore created
  - All files staged for initial commit
  - 44 files ready to commit

**Phase 2: ML Engine POC [33% - Tasks 2.1 & 2.2 Complete]**
- ✓ Task 2.1: Set up ML environment and install dependencies
  - PyTorch 2.9.0 + TorchVision 0.24.0 installed (CPU version)
  - All ML dependencies installed (NumPy 2.2.6, SciPy 1.16.3, OpenCV 4.12.0, Pillow, PyYAML)
  - Pre-trained ResNet50 model downloaded (97.8 MB)
  - Created test_setup.py verification script
  - All 5 verification tests passed
  - Updated requirements.txt with flexible version constraints
  - Fixed Windows console encoding issues (ASCII-friendly output)

- ✓ Task 2.2: Create image preprocessing pipeline
  - Created ImagePreprocessor class (350+ lines)
  - Supports 7+ image formats (JPG, PNG, WebP, BMP, GIF, TIFF)
  - Handles 4 input types: file path, bytes, PIL Image, numpy array
  - Proper image resizing (256→224 center crop) and normalization
  - Converts all images to RGB (handles grayscale, RGBA)
  - Batch processing capability
  - ImageNet normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
  - Robust error handling (FileNotFoundError, ValueError for corrupt images)
  - Created test_preprocessing.py with 6 comprehensive tests
  - All tests passed: 7 image formats, 4 input methods, batch processing, error handling, image info, normalization
  - Processing speed: 30-430ms per image depending on size

- ✓ Task 2.3: Implement feature extraction (embedding generation)
  - Created FeatureExtractor class (420+ lines)
  - Loads pre-trained ResNet50 model (23.5M parameters)
  - Removes classification layer to extract 2048-dim feature vectors
  - Supports CPU/GPU/MPS (Apple Silicon) with auto-detection
  - Extracts embeddings from path, bytes, or tensor inputs
  - Batch processing with progress bar (configurable batch size)
  - Save/load functionality with metadata (pickle format)
  - Model initialization: 1.4-2s, Embedding extraction: 580-1400ms per image (CPU)
  - Created test_feature_extraction.py with 7 comprehensive tests
  - All tests passed: initialization, single/batch extraction, save/load, uniqueness, consistency, input types
  - Different images produce unique embeddings (cosine similarity: ~0.94)
  - Same image produces identical embeddings (max diff: 0.0)

- ✓ Task 2.4: Implement similarity calculation
  - Created SimilaritySearcher class (430+ lines)
  - Cosine similarity computation using scipy
  - Top-K search with configurable threshold
  - Metadata integration for filtering by category
  - Save/load search index functionality
  - Batch similarity computation
  - Created test_similarity.py with 7 comprehensive tests
  - All tests passed: initialization, similarity computation, top-K search, threshold filtering, metadata search, save/load, performance
  - Search performance: 0.29ms per query, 3,446 queries/second (20 items)

- ✓ Task 2.5: Create sample product dataset (50-100 items)
  - Created create_product_dataset.py script (380+ lines)
  - Generated 100 sample product images (800x800 pixels)
  - 5 categories: bags, shoes, watches, clothing, accessories (20 each)
  - Created product_catalog.csv with full metadata (id, name, category, brand, price, description)
  - Total dataset size: ~2.1 MB
  - Organized directory structure: data/products/{category}/
  - Created DATASET_README.md documentation

- ✓ Task 2.6: Pre-compute embeddings for product catalog
  - Created precompute_embeddings.py script (340+ lines)
  - Extracted embeddings for all 100 products
  - Total extraction time: 44.8 seconds (448ms per image)
  - Created similarity search index with all products
  - Saved product_embeddings.pkl (embeddings + metadata)
  - Saved product_search_index.pkl (ready-to-use search index)
  - Tested similarity search with 3 random queries:
    * 99-100% similarity within same category
    * 4/4 similar results from same category
  - Performance benchmark: 2.77ms avg search time, 361 queries/second (100 items)

---

### 🎉 PHASE 2 COMPLETE
All ML Engine components are functional and tested!

### ✅ COMPLETED: Phase 3 - Database & Backend API [100% COMPLETE] 🎉
**Status**: **PHASE 3 COMPLETE!** All 7 tasks done!
**Goal**: Store products and serve search results via API ✅ **ACHIEVED!**

- [x] Task 3.1: Set up local MongoDB database ✅
- [x] Task 3.2: Design MongoDB schema for products collection ✅
- [x] Task 3.3: Create data import script ✅
- [x] Task 3.4: Set up FastAPI backend structure ✅
- [x] Task 3.5: Create image upload endpoint ✅
- [x] Task 3.6: Create similarity search endpoint ✅
- [x] Task 3.7: Create products listing endpoint ✅

**Achievement**: Complete backend API with 12 endpoints, MongoDB with 100 products, running on http://localhost:8000!

---

### 🔄 In Progress
- None (Phase 3 complete, ready for Phase 4 - Frontend)

---

### 🚫 Blocked
- None

---

### 📈 Progress Summary
- **Total Phases for 40% Milestone**: 6 phases
- **Completed**: 1 phase (Phase 1)
- **Remaining**: 5 phases (Phases 2-6)
- **Estimated Time**: 5 weeks total
  - Week 1-2: ML Engine POC (Phase 2)
  - Week 2-3: Database & Backend API (Phase 3)
  - Week 3-4: Frontend (Phase 4)
  - Week 4-5: Testing & Refinement (Phase 5)
  - Week 5: Demo Preparation (Phase 6)

## Executor's Feedback or Assistance Requests

### EXECUTOR: Mobile “Cannot reach backend” (Apr 17, 2026)

**Cause (typical)**: Android hides Wi‑Fi IPv4 without **Location** permission → LAN scan never gets the right `/24`, so login failover exhausts guesses.

**Done**: `permission_handler` + `ACCESS_COARSE_LOCATION` in Android manifest; `resolveBaseUrl()` requests `locationWhenInUse` once on physical Android when Wi‑Fi IP is null, then re-reads `getWifiIP()`. Login now treats any `_isConnectionFailure` like Socket/timeout and runs LAN failover; failover loop skips all connection-style errors; user-facing error text lists firewall / `0.0.0.0:8000` / browser smoke test.

**Follow-up**: LAN v2 migration no longer blindly deletes `backend_ip` — it keeps the saved IP if `GET http://ip:8000/` still returns DupeFinder (fixes “pehle login ho gaya tha” after an update when discovery is flaky).

**Apr 18, 2026 — Perf (Community / Wishlist / Compare)**: Wishlist + Compare use `snapshotForUi()` (disk or warm memory) then `getSavedProducts`/`getList()` so the grid appears without waiting on `getUserData()`; service TTL 20→60s. Community: coalesced `_load` (skip overlapping polls; force-refresh waits), `RepaintBoundary` per feed card, `cacheWidth`/`cacheHeight` on feed + sheet + composer preview images, `ResizeImage` on avatars; Compare `CachedNetworkImage` gets `memCacheWidth: 400`.

**User verify**: Hot restart app → allow Location when prompted → PC `uvicorn --host 0.0.0.0 --port 8000` + firewall TCP 8000 → phone browser `http://<PC-ip>:8000/` shows DupeFinder JSON.

### EXECUTOR: Frontend–Backend connectivity (March 2, 2025)

**Issue**: Backend + MongoDB connected (terminal shows OK) but frontend still not "connected" (data not showing / unclear why).

**Done**:
1. **Admin dashboard connectivity check**: On load, frontend first calls `GET http://localhost:8000/ping` (no auth). If that fails (e.g. network), a clear banner shows: "Backend reachable nahi hai. Please ensure server is running on http://localhost:8000."
2. **Auth error**: If `GET /api/admin/stats` returns 401, banner shows "Session expired. Please log out and log in again."
3. All dashboard API URLs in `AdminDashboardPro.jsx` use a single `API_BASE = 'http://localhost:8000'`.
4. **Backend**: FastAPI deprecation fixed in `admin_new.py`: `Query(..., regex=...)` → `Query(..., pattern=...)` for `brand_type`.

**User action**: Open admin dashboard; if backend is not reachable or session expired, the new banners should explain. If banners do not appear but data still doesn’t load, check browser F12 → Network for requests to `localhost:8000` and their status (200 / 401 / failed).

---

### ✅ EXECUTOR: UI Updates and Feature Enhancements - November 30, 2025

**Status**: COMPLETE ✅

**What Was Implemented**:

1. ✅ **Currency Conversion (USD to PKR)**
   - Changed all product price displays from dollar ($) to PKR
   - Applied conversion rate: 1 USD = 280 PKR
   - Updated files:
     - `frontend-app/src/components/admin/ProductManagement.jsx` (2 locations)
     - `frontend-app/src/App.jsx`
     - `frontend-app/src/pages/AdminDashboardPro.jsx`
   - All prices now display as "PKR {amount}" instead of "${amount}"

2. ✅ **Auto Sync Page - Brand Type Selection**
   - Removed "Pakistani Designer Brands" and "Luxury/International Brands" options
   - Kept only "Local Affordable Brands" option
   - Updated `frontend-app/src/components/admin/ScrapingManagement.jsx`
   - Brand type selector now shows only "Local Affordable Brands" (non-editable)

3. ✅ **Delete Button for Broken Links**
   - Added delete button next to repair button in broken links table
   - Implemented `handleDeleteLink` function with confirmation dialog
   - Added delete endpoint in backend: `DELETE /api/admin/products/{product_id}`
   - Updated `frontend-app/src/components/admin/ProductManagement.jsx`
   - Updated `backend/app/api/routes/admin_new.py` (added delete endpoint)

4. ✅ **Repair Link Backend with Notifications**
   - Enhanced repair functionality with success/failure notifications
   - Created `showNotification` function for popup messages
   - Success notification: "Link repaired successfully!"
   - Failure notification: "This link cannot be repaired"
   - Notifications appear as popup in top-right corner with black/white theme
   - Auto-dismiss after 3 seconds with slide-in animation
   - Updated `frontend-app/src/components/admin/ProductManagement.jsx`

**Files Modified**:
- `frontend-app/src/components/admin/ProductManagement.jsx`
- `frontend-app/src/components/admin/ScrapingManagement.jsx`
- `frontend-app/src/App.jsx`
- `frontend-app/src/pages/AdminDashboardPro.jsx`
- `backend/app/api/routes/admin_new.py`

**Success Criteria Met**:
✅ All prices display in PKR (converted from USD)
✅ Auto Sync page shows only "Local Affordable Brands"
✅ Delete button appears next to repair button
✅ Repair functionality shows success/failure notifications
✅ All changes follow black/white theme

**Next Steps**: Ready for user testing

---

### EXECUTOR: Scraper – relaxed validation (still 0 products) – March 1, 2025

**Status**: Changes applied; awaiting re-run of Auto Sync.

**What was done** (to help “still not fetching products” for Generation, Afrozeh, etc.):

1. **Price** – Default to 1999.0 PKR when price is missing or unparsed (no longer skip women’s products for missing price).
2. **Image** – Allow products without image (use placeholder). Removed “product image indicators” check that was dropping valid items.
3. **Single-word names** – Allow single words if length ≥ 8 or in extended list (e.g. pret, stitched, unstitched).
4. **Lazy-load images** – Use `data-srcset` (first URL) when `src`/`data-src` not present.
5. **Fallback product links** – Use `a[href*="/products/"], a[href*="/collections/"]` with img; accept link if `text or href.count('/') >= 3`; avoid duplicate containers.
6. **Container text** – Require only 8+ chars (was 15) so minimal product cards are kept.
7. **Last fallback (all_divs)** – Accept divs with img and either `len(text) > 5` or product/collection link with any text.

**Ask**: Please run **Auto Sync** again for the same brands and check:
- Backend/console for: `Found X potential product containers` and `Total products extracted from … : Y`.  
If X > 0 but Y = 0, extraction/validation is still failing; if X = 0, selectors don’t match the site HTML. Share those two numbers (and brand/URL) if it’s still 0 products so we can add site-specific handling or debug further.

---

### EXECUTOR: Women Short kurti / Women Luxe – product list still 0 (March 2, 2025)

**Status**: Fix applied; please restart backend and re-test.

**Changes in `backend/app/api/routes/admin_new.py`**:
1. **Exact slug regex**: Endpoint-only branch for Women Luxe and Women Short kurti now uses `^(?:slug1|slug2|...)$` so only exact `endpoint_category` values match (no substring matches).
2. **Gender normalization**: Products API accepts both "w"/"women" and "m"/"men" for gender filter (case-insensitive).
3. **Skip gender for merged categories**: When category is "Women Luxe" or "Women Short kurti", gender filter is not applied so products with the right endpoint but missing/different `gender` in DB still show.

**Ask**: Restart the backend server, then in the admin UI select **Women** + **Women Short kurti** (or **Women Luxe**) and confirm that products and Total count appear. If still 0, we need to inspect DB documents (e.g. actual `endpoint_category` and `gender` values) for those collections.

---

### EXECUTOR: Product Catalogue images still "No image" after Auto Sync – March 2, 2025

**Status**: Changes applied; please run Auto Sync again and refresh Product Catalogue.

**What was done**:
1. **Frontend (ProductManagement.jsx)** – If the primary image (local or proxy) fails to load, we now try **product.image_url** via the image-proxy once before showing "No image".
2. **Backend (_looks_like_image_url in admin_new.py)** – Relaxed validation: added path segments `/catalog/`, `/img/`, `/images/`, `/assets/`, `/static/`, `/mens/`, `/women/`, `/womens/` so more URLs (e.g. Junaid Jamshed–style) are attempted for download.

**Ask**: Run Auto Sync again for the affected brands, then refresh Product Catalogue. If many still show "No image", we can check MongoDB for `image_path` vs `image_url` on a few products.

---

### EXECUTOR: Still 0 products – local brands CSV-only + test endpoint – March 2, 2025

**Status**: Changes applied. Please test and share backend logs if still 0.

**What was done**:
1. **Local brands source** – For brand_type "local", brands are now loaded **only** from `local_brands_links.csv` (Excel is skipped). So the list and URLs in Auto Sync come only from the CSV and match the exact listing links.
2. **Invalid URL handling** – If a brand has no valid `brand_url` (empty or not starting with `http`), the job skips it and appends a log: "Skipping {name}: no valid URL".
3. **Debug endpoint** – `GET /api/admin/scraping/test-one` (no auth) runs the scraper on the **Bonanza Satrangi** CSV row and returns `{ ok, products_count, brand_url, sample }`. Open in browser: `http://localhost:8000/api/admin/scraping/test-one` after starting the backend to see if the scraper returns products for that URL.
4. **Scraper logging** – If the page has product containers but 0 products pass validation, we now log: "0 products from N containers; sample container classes: [...]" to see why extraction failed.

**Please do**:
1. Restart backend (`cd backend` then `python -m uvicorn app.main:app --reload --port 8000`).
2. Open `http://localhost:8000/api/admin/scraping/test-one` in the browser. Note `products_count` and any `error`.
3. In Auto Sync, select **Local Affordable Brands**, select one brand (e.g. Bonanza Satrangi), click **Start Scraping**. Watch backend console for "Job … brand[0]: name=… url=…" and "Found X products from …".
4. If still 0: copy from backend logs the line with "Found N potential product containers" and, if present, "0 products from N containers; sample container classes: …" and share brand name + URL.

---

### EXECUTOR: Naviforce 0 products – debug-fetch endpoint – March 2, 2025

**Status**: Diagnostic added; need your result to confirm cause.

**Cause (from prior session)**: Naviforce men page (`https://naviforcewatches.pk/men/`) may be **JS-rendered**: the product grid is not in the initial HTML, so our httpx+BeautifulSoup scraper sees no product containers. Alternatively the server may return full HTML only for certain requests (e.g. with Referer).

**What was done**:
1. **Debug endpoint** – `GET /api/admin/scraping/debug-fetch?url=<encoded_url>` (admin auth required). It uses the **same** HTTP client and headers as the scraper (Chrome UA + Referer), fetches the URL, and returns: `status_code`, `content_length`, `num_ftc_product_or_grid`, `num_product_containers`, and `body_preview` (first 600 chars).

**Please do**:
1. Restart backend, log in to Admin, then in browser open:  
   `http://localhost:8000/api/admin/scraping/debug-fetch?url=https%3A%2F%2Fnaviforcewatches.pk%2Fmen%2F`  
   (You must be logged in so the request sends the admin token, or use a tool that sends your Bearer token.)
2. Share the JSON response: especially `content_length`, `num_ftc_product_or_grid`, `num_product_containers`, and whether `body_preview` contains product markup (e.g. "ftc-product") or only nav/menu text.

**Next step**: If `num_product_containers` is 0 and `body_preview` has no product grid, the page is JS-rendered and we need either a headless browser (Playwright) or to find the site’s product API. If the backend sees full HTML with containers, the issue is elsewhere (e.g. extraction/validation).

**Follow-up (same day)**: User ran Debug fetch; backend received **543 containers** and ~906KB HTML. So the page is not JS-only—extraction/validation was dropping all 543. Changes made: (1) Added WooCommerce name selector `.woocommerce-loop-product__title`. (2) Added watch-related single words (chronograph, diver, military, sport, classic, digital, analog, quartz, automatic, luxury). (3) Allowed `/wp-content/` in image path so WooCommerce uploads URLs are not replaced with placeholder. (4) When 0 products from many containers, backend now logs **Sample skip reasons** for the first 5 containers (e.g. no_name_or_short, single_word, invalid_name). User should run Auto Sync for Naviforce again; if still 0, share backend log line containing "Sample skip reasons".

---

### EXECUTOR: Multiple links per brand (e.g. Sapphire Pret) – March 2, 2025

**Status**: Implemented ✅

**What was done**:
1. **CSV format** – `Website` column can now contain multiple URLs per brand, separated by `|` (e.g. `url1|url2|url3`). No new columns.
2. **Backend – get_available_brands** – For both men’s and women’s CSV: if `Website` has `|`, split and trim to get `brand_urls`; `brand_url` remains the first URL (for display). Both CSVs support multiple links.
3. **Backend – run_scraping_job** – For each brand we use `brand_urls` if present, else `[brand_url]`. Each URL is scraped with the same `scraper_type`; products are merged and **deduped by product_url**, then stored in MongoDB as before. Logs show e.g. "Scraping: &lt;url&gt;" per link and "Found X products from {brand} (N link(s))".
4. **Women’s CSV – Sapphire Pret** – `Website` set to the six collection URLs (rtw-smart-casual, rtw-formal, rtw-shirts, rtw-short-kurti, dupattas-shawls, ready-to-wear-outfits), pipe-separated.

**Success criteria**: Sapphire Pret (Women) in Auto Sync runs one job that scrapes all 6 links and stores merged, deduped products. Other brands with a single URL behave unchanged.

**Ask**: Please run Auto Sync for **Sapphire Pret** (Women → Local Affordable Brands) and confirm product count and logs. Mark task complete after verification.

---

### EXECUTOR: Endpoint-based categories & remove category from product card – March 2, 2025

**Status**: Implemented ✅ (awaiting Planner/user verification)

**What was done**:

1. **Backend – scraping job (`admin_new.py`)**  
   When saving products from a listing URL, each product now gets **`endpoint_category`** from the URL path (e.g. `/collections/kurta` → `"kurta"`, `/collections/ready-to-wear` → `"ready-to-wear"`). No scraper code changed; only the route that calls the scraper sets this field per product before storing.

2. **Backend – GET `/api/admin/categories`**  
   Returns distinct **`endpoint_category`** only (no legacy "Women → Stitched" etc.). Optional `gender` filter unchanged. Dropdown will show only slug-style categories (e.g. kurta, bags, ready-to-wear) once products are scraped with the new logic.

3. **Backend – GET `/api/admin/products`**  
   When `category` query param is sent, filter is now by **`endpoint_category`** (exact match).

4. **Frontend – Product card (`ProductManagement.jsx`)**  
   Removed the category label (red "Women → Stitched" style) from the product card. Card now shows only name, brand, and price in the meta line.

**Success criteria**:  
- New scrapes populate `endpoint_category` from the page URL.  
- Category dropdown shows only endpoint-based categories (e.g. Kurta, Bags).  
- Selecting a category filters products by `endpoint_category`.  
- Product cards do not show any category label.

**Note**: Existing products in DB without `endpoint_category` will not appear in the new category dropdown until they are re-scraped. Re-running Auto Sync for a brand will set `endpoint_category` for newly scraped/updated products.

---

### EXECUTOR: Men's display categories – Mens Standard Suit, Traditional Suit, Casual Wear (March 2025)

**Status**: Implemented ✅

**What was done**:
1. **Backend (`admin_new.py`)**  
   - **Mens Standard Suit**: Products from endpoint `all` (existing + future scrapes) are generalized to "Mens Standard Suit".  
   - **Mens Traditional Suit**: Products from endpoints `men`, `men-main`, `men-ready-to-wear` are merged into one display category "Mens Traditional Suit".  
   - **Mens Casual Wear**: Products from endpoint `men-products` are generalized to "Mens Casual Wear".  
2. **Scraping**: When saving products, `display_category` is set from `_display_category_from_endpoint(slug, gender)` so new scrapes get the correct display category.  
3. **APIs**: GET `/api/admin/categories` returns the new display names with counts; GET `/api/admin/products` filters by these display categories.  
4. **Sync on category list**: When the category dropdown is loaded, DB is synced so any products with `endpoint_category` in the men's sets get `display_category` set.  
5. **Backfill**: POST `/api/admin/categories/backfill-display` now includes men's bulk updates (`matched_men_standard_suit`, `matched_men_traditional_suit`, `matched_men_casual_wear`) and fallback for men products missing `display_category`.

**User action**: Call **POST** `http://localhost:8000/api/admin/categories/backfill-display` once (with admin auth) to set `display_category` on all existing men's products. After that, the frontend category dropdown will show "Mens Standard Suit", "Mens Traditional Suit", "Mens Casual Wear" with correct counts, and product list filter will work by these names.

---

### EXECUTOR: Generalize categories to "Women Kurta" / "Women Lawn" – March 2025

**Status**: Implemented ✅

**What was done**:

1. **Display category mapping (backend)**  
   - **Women Kurta**: endpoint slugs → `2-piece-essential-summer-pret-kt`, `charizma-vasal-vol-02-2026`, `eid-collection`, `essential-summer-pret`, `florence-summer-edit-26`, `luxe-2025`, `luxury-pret`, `new-arrival-summer-26`, `new-arrivals`, `pret`, `ready-to-wear`, `satori-2026`, `women`.  
   - **Women Lawn**: `eid-lawn-2026`, `lawn-in-stock`, and endpoint slugs containing both "ramadan" and "lawn".  
   - Legacy category backfill: "women → stitched" / "western" → Women Kurta; "women → unstitched" → Women Lawn.

2. **Scraping**  
   When saving products, `display_category` is set from `_display_category_from_endpoint(slug, gender)` so new scrapes get "Women Kurta" or "Women Lawn" (or the slug if unmapped, e.g. bags/jewelry).

3. **APIs**  
   - GET `/api/admin/categories`: returns distinct **display_category** with counts (dropdown shows "Women Kurta", "Women Lawn", etc.).  
   - GET `/api/admin/products`: category filter uses **display_category**.

4. **Backfill**  
   - POST `/api/admin/categories/backfill-display`: one-time backfill for existing women products: sets `display_category` from endpoint or legacy category. Run once after deploy (e.g. from browser/Postman while logged in as admin).

**User action**: Call **POST** `http://localhost:8000/api/admin/categories/backfill-display` once (with admin auth) to generalize existing DB products. Men's mapping to be added later.

---

## Progress Summary – All App Progress to Date (March 2025)

**Last updated**: March 2025. This section consolidates all progress in the app so far.

### 1. Category system (backend + frontend)

- **Men's display categories** (endpoint → display name):
  - `all` → **Men Standard Suit**
  - `men`, `men-main`, `men-ready-to-wear`, `new-arrival` → **Men Traditional Suit**
  - `men-products` → **Men Casual Wear**
  - `men-footwear` → **Men Footwear**
  - `men-shoes-shoes` → **Men Shoes**
  - `men-sweater` → **Men Sweater**
  - `mens-wrist-watches` / `men-wrist-watches` → **Men Wrist Watches**
- **Naming**: "Mens" was changed to "Men" (Men Standard Suit, Men Traditional Suit, Men Casual Wear) everywhere; backward compatibility kept for old DB values.
- **Women's display categories** (endpoint → display name):
  - Existing: Women Kurta, Women Lawn, Women Luxe, **Women Short Kurti** (capital K), Women Accessories
  - Added: **Women Anarkali Frock** (`anarkali-frock`), **Women Bottoms** (`bottoms`), **Women Bags** (`cross-body-bags`), **Women Jewelry** (`jewelry`), **Women Tops** (`tops`), **Women Unstitched** (`unstitched` + `unstitched-fabric`), **Women Western** (`western`), **Women Winter Pants** (`winter-pants`)
- **Women Short Kurti**: Display name fixed to "Women Short Kurti" (capital K) in backend and frontend; old "Women Short kurti" still matched in DB for backward compatibility.
- **Scraping**: New products get `display_category` from `_display_category_from_endpoint(slug, gender)`. Sync on category list load and POST `/api/admin/categories/backfill-display` set/update `display_category` for existing products.

### 2. Gender filter and Women Accessories

- **Category list by gender**: When Gender = Men, only men's categories are returned; when Gender = Women, only women's categories (including Women Accessories).
- **Gender param**: GET `/api/admin/categories` and products API accept `"w"`/`"women"` and `"m"`/`"men"`.
- **Women Accessories**: Treated as women-only. ECS accessories URL moved from `local_brands_links.csv` (men's) to `local_brands_links_women.csv` so it scrapes with gender "w". Endpoint-only women categories (Women Accessories, Women Luxe, Women Short Kurti) are counted without gender filter when Women is selected so they always show; product list for these categories does not filter by gender so all matching products appear.
- **Display names always shown**: When a gender is selected, all that gender's display names appear in the dropdown even if count is 0 (e.g. Women Accessories always under Women).

### 3. Product catalogue – click to brand site

- **Product card click**: In Product Catalogue, clicking the product image or the product info (name, brand, price) opens the product's page on the brand site in a new tab (`product.product_url` or `product.product_link`). Delete (×) button unchanged and does not open the link.
- **Backend**: Products already store and return `product_url` (scrape source / buy page).

### 4. CSV and scraping

- **Women's CSV**: `local_brands_links_women.csv` includes full endpoint links (e.g. ECS `https://shopecs.com/collections/accessories`) so those URLs are scraped as women's links and products show in women categories.
- **Men's CSV**: ECS accessories row removed from `local_brands_links.csv` so it exists only under women's links.

### 5. Files touched (summary)

- **Backend**: `backend/app/api/routes/admin_new.py` (category sets, filters, sync, backfill, gender handling, product list gender skip for endpoint-only women categories), `backend/scripts/list_endpoint_categories.py` (Women Short Kurti naming).
- **Frontend**: `frontend-app/src/components/admin/ProductManagement.jsx` (category merge labels, Women Short Kurti, product card click to open `product_url` in new tab).
- **Data**: `local_brands_links.csv`, `local_brands_links_women.csv`.

### 6. How to run backfill (optional)

- One-time: **POST** `http://localhost:8000/api/admin/categories/backfill-display` (with admin auth) to set `display_category` on all existing products per current endpoint → display name rules.

---

## Executor's Feedback or Assistance Requests

**Current Task**: MongoDB Atlas Connection Setup ✅ COMPLETED

**What Was Done**:
1. ✅ Created MongoDB Atlas connection configuration
   - `backend/app/core/config.py` - Settings management with Pydantic
   - `backend/app/core/database.py` - Async MongoDB connection using Motor
   - Connection string configured: `mongodb+srv://ussamainayat:ussamainayat@dupefinder.u30xrsm.mongodb.net/`
   - Database name: `dupefinder`

2. ✅ Created MongoDB models and services
   - `backend/app/models/mongodb_models.py` - Pydantic models for MongoDB documents
   - `backend/app/services/mongodb_service.py` - Service layer for database operations
   - Support for: ProductEmbedding, UserSearchAnalytics, ImageMetadata, AnalyticsEvent, MLModelLog

3. ✅ Updated backend main application
   - Added lifespan events for connection management
   - Health check endpoint now checks MongoDB connection
   - Added database router with health/stats endpoints

4. ✅ Created test script
   - `backend/test_connection.py` - Standalone connection test

5. ✅ Updated dependencies
   - Added `motor==3.3.2` for async MongoDB operations

**Next Steps**:
- Test the connection by running: `python backend/test_connection.py`
- Or start the server: `uvicorn backend.main:app --reload`
- Check health: `http://localhost:8000/health`
- Check database stats: `http://localhost:8000/api/database/stats`

**Task Completed**: Phase 1 - Project Setup & Infrastructure

---

**Updated: November 11, 2025 - Planner Mode**

---

### ✅ PLANNER: Comprehensive Plan Created

**Date**: November 11, 2025  
**Status**: PLANNING COMPLETE ✅

**What Was Planned**:

The Planner has created a complete implementation plan for the new requirements:

**Requirements Covered**:
1. ✅ Black & White UI theme across entire application
2. ✅ Login/Signup as landing page (authentication-first flow)
3. ✅ JWT + Email OTP authentication system
4. ✅ Admin Dashboard with 4 modules:
   - Module 1: User Management (view users, deactivate accounts)
   - Module 2: Product Catalogue Management (CSV import, cleanup links, manage tags)
   - Module 3: Model Training Dashboard (sliders, training, metrics)
   - Module 4: Auto Sync/Rescraping (brand selection, progress tracking)

**Planning Deliverables**:
- ✅ 57 detailed tasks with clear success criteria
- ✅ 6 phases with logical progression
- ✅ Technical architecture decisions documented
- ✅ Timeline estimation (5 weeks)
- ✅ Risk mitigation strategies identified
- ✅ Technology stack specified

**Key Technical Decisions**:
- Using PyJWT for token management
- Gmail SMTP for OTP emails (credentials provided)
- MongoDB TTL indexes for OTP expiration
- Bcrypt for password hashing
- Background jobs for ML training and scraping
- CSS variables for theme management
- Chart.js for metrics visualization

**Critical Dependencies Identified**:
- Backend: PyJWT, python-jose, passlib[bcrypt], aiosmtplib, pandas
- Frontend: react-router-dom, axios, chart.js

**Next Steps for Executor**:
1. Switch to EXECUTOR mode
2. Begin with Task A.1 (Set up authentication dependencies)
3. Work through Phase A (10 tasks)
4. Test each task's success criteria
5. Update scratchpad after each task
6. Report completion of Phase A before moving to Phase B

**Planner's Confidence**: HIGH
- All requirements are achievable with standard technologies
- Clear path from current state to desired state
- Risks identified and mitigated
- Timeline is realistic

**Awaiting**: Executor to begin implementation

---

### ✅ EXECUTOR: Phase A Complete

**Date**: November 11, 2025  
**Status**: PHASE A COMPLETE ✅

**What Was Implemented**:

**Phase A: Backend Authentication System** - ALL 10 TASKS COMPLETED

1. ✅ **Task A.1**: Dependencies installed
   - PyJWT, python-jose, passlib, bcrypt, aiosmtplib, email-validator, pandas
   - Created config.py with Settings class
   - Environment variables configured

2. ✅ **Task A.2**: MongoDB collections created
   - users collection (unique email index)
   - otps collection (TTL index for auto-expiry)
   - refresh_tokens collection (TTL index)
   - All indexes working

3. ✅ **Task A.3**: Auth utilities implemented
   - Password hashing with bcrypt
   - JWT access token (30 min expiry)
   - JWT refresh token (7 days expiry)
   - Token validation and decoding
   - All tested and working

4. ✅ **Task A.4**: Email service implemented
   - OTP generation (6 digits)
   - Gmail SMTP integration
   - HTML email templates
   - OTP storage with TTL
   - Email successfully sent and tested

5. ✅ **Task A.5**: Signup endpoint
   - POST /api/auth/signup
   - Email validation, password strength check
   - User creation with hashed password
   - Auto-send OTP
   - Returns 201 with success message

6. ✅ **Task A.6**: OTP verification endpoint
   - POST /api/auth/verify-otp
   - Validates OTP from database
   - Checks expiry (10 minutes)
   - Marks user as verified
   - Marks OTP as used

7. ✅ **Task A.7**: Login endpoint
   - POST /api/auth/login
   - Email/password validation
   - Checks if verified
   - Generates access + refresh tokens
   - Updates last_login
   - Returns tokens + user info

8. ✅ **Task A.8**: Token refresh endpoint
   - POST /api/auth/refresh
   - Validates refresh token
   - Checks database for token
   - Generates new access token
   - Returns new access token

9. ✅ **Task A.9**: Authentication middleware
   - Created dependencies/auth.py
   - get_current_user() dependency
   - Validates Bearer token
   - Extracts user from database
   - Checks if active
   - Works on protected routes

10. ✅ **Task A.10**: Logout endpoint
    - POST /api/auth/logout
    - Deletes refresh token from database
    - Returns success message

**Bonus**: Resend OTP endpoint (POST /api/auth/resend-otp)

**Test Results**:
- All endpoints tested with FastAPI TestClient
- Signup → OTP → Verification → Login → Refresh → Logout flow works perfectly
- Email OTP successfully sent to test@dupefinder.com
- JWT tokens generated and validated correctly
- Protected routes working with Bearer authentication

**Files Created/Modified**:
- backend/requirements.txt (added auth dependencies)
- backend/app/core/config.py (configuration management)
- backend/app/core/database.py (added auth collections)
- backend/app/utils/auth.py (password + JWT utilities)
- backend/app/services/email_service.py (OTP + email sending)
- backend/app/models/auth_schemas.py (Pydantic models)
- backend/app/api/routes/auth.py (all auth endpoints)
- backend/app/dependencies/auth.py (authentication middleware)
- backend/app/main.py (fixed imports)
- backend/init_auth_collections.py (DB initialization script)
- backend/test_auth_utils.py, test_email_service.py, test_auth_endpoints.py (test scripts)

**Next Steps**:
- Ready to start Phase B: Admin Dashboard Backend Endpoints (14 tasks)
- Will begin with Module 1: User Management endpoints

---

### 🎨 Phase D Progress - Admin Dashboard Frontend UI [IN PROGRESS]

**Started**: November 11, 2025 - Executor Mode

**What Was Done**:

1. ✅ **Created Main Admin Dashboard Component** (`frontend-app/src/pages/AdminDashboard.jsx`)
   - Sidebar navigation with 5 modules (Overview, Users, Products, Training, Scraping)
   - Black & white theme throughout
   - Module routing system
   - Logout functionality

2. ✅ **Created Admin Component Directory** (`frontend-app/src/components/admin/`)
   - Organized structure for all module components

3. ✅ **Implemented All 5 Admin Modules**:

   **A. Overview Module** (`Overview.jsx`):
   - Dashboard statistics (users, products, ML status, sync status)
   - Welcome section
   - Stats grid with icon cards
   - Quick action buttons

   **B. User Management Module** (`UserManagement.jsx`):
   - User listing with pagination
   - Search by email functionality
   - Status filtering (all/active/inactive)
   - Deactivate/Activate user actions
   - Shows user details: email, status, verified, created date, last login

   **C. Product Management Module** (`ProductManagement.jsx`):
   - CSV file upload for bulk product import
   - Image link cleanup checker
   - Category listing and management
   - Product table with filtering
   - Filter by category and broken links
   - Status indicators for broken links

   **D. ML Training Module** (`MLTraining.jsx`):
   - Train/Test split slider (50%-95%)
   - Start training button
   - Real-time training progress bar
   - Training history with metrics
   - Performance metrics display (accuracy, precision, recall, F1)
   - Best model highlight section

   **E. Scraping Management Module** (`ScrapingManagement.jsx`):
   - Brand selection grid with checkboxes
   - Multi-brand selection
   - Start scraping button
   - Real-time progress tracking
   - Activity logs display
   - Scraping history with status

4. ✅ **Created Comprehensive CSS** (`frontend-app/src/styles/AdminDashboard.css`)
   - Complete black & white theme
   - Responsive design
   - Sidebar navigation styling
   - Table styles
   - Card components
   - Status badges
   - Progress bars and sliders
   - Form elements
   - Buttons and interactions
   - Mobile-responsive layout

5. ✅ **Updated Application Router** (`frontend-app/src/AppWithAuth.jsx`)
   - Changed landing page to Login (per requirements)
   - After login → Admin Dashboard (not search page)
   - After signup → Login page
   - Removed old admin authentication system
   - Integrated new AdminDashboard component
   - Logout redirects to login

**Features Implemented**:
- ✅ Black & white theme throughout
- ✅ Login/Signup as landing page
- ✅ Post-login goes to Admin Dashboard
- ✅ All 4 required modules + Overview dashboard
- ✅ Interactive UI elements (sliders, checkboxes, filters)
- ✅ Real-time progress indicators
- ✅ Pagination for data tables
- ✅ Search and filtering capabilities
- ✅ Responsive design

**Backend API Integration Ready**:
- All components call backend APIs with proper authentication headers
- Uses localStorage token for JWT authentication
- Error handling in place
- Loading states implemented

**Files Created/Modified**:
- frontend-app/src/pages/AdminDashboard.jsx (NEW)
- frontend-app/src/components/admin/Overview.jsx (NEW)
- frontend-app/src/components/admin/UserManagement.jsx (NEW)
- frontend-app/src/components/admin/ProductManagement.jsx (NEW)
- frontend-app/src/components/admin/MLTraining.jsx (NEW)
- frontend-app/src/components/admin/ScrapingManagement.jsx (NEW)
- frontend-app/src/styles/AdminDashboard.css (NEW)
- frontend-app/src/AppWithAuth.jsx (MODIFIED)

**Success Criteria Met**:
✅ Landing page is login/signup (not image upload)
✅ Black & white theme applied
✅ Admin dashboard accessible after login
✅ All 4 modules present with UI
✅ User management interface ready
✅ Product catalogue interface with CSV upload
✅ ML training interface with sliders
✅ Auto sync interface with brand selection

**Next Steps**:
- Test frontend UI in browser
- Implement backend endpoints to support frontend
- Connect frontend to working backend APIs
- Test end-to-end workflows for each module

---

### ✅ EXECUTOR: Flutter Mobile App Running

**Date**: Current Session - Executor Mode  
**Status**: Flutter App Started ✅

**What Was Done**:

1. ✅ **Navigated to Mobile Folder**
   - Located Flutter project at `mobile/` directory
   - Verified `pubspec.yaml` configuration

2. ✅ **Checked Flutter Setup**
   - Ran `flutter doctor` - Flutter 3.38.1 installed and working
   - Chrome available for web development
   - Some Android toolchain warnings (not critical for web)

3. ✅ **Installed Dependencies**
   - Ran `flutter pub get`
   - Successfully installed 106 dependencies
   - All required packages downloaded

4. ✅ **Started Flutter App**
   - Running `flutter run -d chrome` in background
   - App should be accessible in Chrome browser
   - Development server started

**Next Steps**:
- Monitor app in browser for any runtime errors
- Test app functionality once fully loaded
- Verify connection to backend API if needed

**Task Completed**: Flutter mobile app running on Chrome

---

### ✅ Phase 1 Completed - Project Setup & Infrastructure

**What Was Done**:

1. **Directory Structure**: Created 70+ directories organized into:
   - Backend module (app/api/routes, core, models, services, utils)
   - Frontend module (components, pages, services, utils, styles, assets)
   - Mobile module (screens, widgets, services, models, utils)
   - ML Engine (preprocessing, embeddings, similarity, models, data)
   - Admin Dashboard (components, pages, services, utils)
   - Supporting directories (database, docker, docs, scripts)

2. **Configuration Files**: Created 44 files including:
   - Python requirements.txt for backend and ML engine
   - package.json for frontend and admin dashboard
   - pubspec.yaml for Flutter mobile app
   - docker-compose.yml and individual Dockerfiles
   - Database schema files (PostgreSQL SQL and MongoDB JS)
   - Environment variable templates (.env.example)
   - Setup scripts for Windows and Unix/Mac

3. **Documentation**: Created comprehensive documentation:
   - Root README.md with project overview
   - Individual README.md for each module
   - ARCHITECTURE.md explaining system design
   - API_DOCUMENTATION.md with endpoint specifications

4. **Code Skeleton**: Created basic entry points for all modules

5. **Version Control**: Git initialized with comprehensive .gitignore

---

### 📋 Planner's Strategic Plan for 40% Milestone

**Plan Status**: ✅ COMPLETE - Ready for Review

**What Planner Has Done**:
1. ✅ Analyzed full FYP proposal (8000+ words)
2. ✅ Identified scope for 40% milestone
3. ✅ Created focused task breakdown (6 phases, 27 specific tasks)
4. ✅ Defined clear success criteria for each task
5. ✅ Deferred unnecessary features to 60-100% milestone
6. ✅ Created 5-week timeline with phase-by-phase approach
7. ✅ Updated scratchpad with complete plan

**Key Strategic Decisions**:
- Focus on **web app only** (defer mobile to 60%)
- Use **simple similarity search** (defer FAISS to 60%)
- **No authentication** for 40% demo (defer to 60%)
- **PostgreSQL only** (defer MongoDB to 60%)
- **Local development** (defer Docker deployment to 60%)
- Start with **50-100 products** (scale up later)
- Target **60-70% accuracy** (improve to 80% later)

**Next Phase Ready**: Phase 2 - ML Engine Proof of Concept

---

### ✅ Task 2.1 Complete - ML Environment Setup

**Date**: November 8, 2025  
**Status**: SUCCESS - All tests passed

**What Was Done**:
1. Updated requirements.txt with compatible package versions
   - Changed to flexible version constraints (>= instead of ==)
   - Resolved PyTorch version compatibility (2.9.0 available vs 2.1.1 in original)
   
2. Created verification test script (test_setup.py)
   - Tests all 5 critical components
   - Windows-compatible (ASCII output instead of Unicode)
   - 290 lines of comprehensive testing code

3. Installed all ML dependencies successfully
   - PyTorch 2.9.0 (CPU version - GPU not required for 40%)
   - Pre-trained ResNet50 model auto-downloaded

4. Verified complete ML pipeline works:
   - Model loads in 59 seconds
   - Inference time: 402ms per image  
   - Embedding dimension: 2048 (correct)
   - Cosine similarity calculation functional

**Success Criteria Met**:
✅ Can import all libraries without errors  
✅ Pre-trained ResNet50 model loads successfully  
✅ Model can run inference on test images  
✅ Embeddings are correct shape (2048-dim)  
✅ Cosine similarity calculation works  

**Lessons Learned**:
- Windows PowerShell doesn't support Unicode checkmarks → use ASCII [OK]/[ERROR] format
- PyTorch versions change rapidly → use flexible version constraints (>=)
- ResNet50 model is 97.8 MB → first run takes ~1 minute to download
- CPU inference is 402ms → acceptable for 40% demo, can optimize later with GPU

**Next Task**: Task 2.2 - Create image preprocessing pipeline
**Estimated Time**: 1-2 hours
**Ready to proceed**: YES

---

## Executor's Feedback — Vast.ai ML Pipeline (March 15, 2026)

**Task**: phase3-upload — Run embedding generation on Vast.ai GPU, download FAISS artifacts

**Status**: ✅ COMPLETED (with one known issue documented below)

**What Was Done**:
1. ✅ Connected to Vast.ai server (RTX 4090, 24GB VRAM, PyTorch 2.5.1 + CUDA 12.1)
2. ✅ Uploaded `ml-engine/` to server via scp
3. ✅ Installed dependencies (faiss-cpu, pymongo, torch, etc.)
4. ✅ Ran `export_images_for_embedding.py --workers 16` → downloaded 23,058 images in ~21 min
5. ✅ Ran `generate_embeddings_vastai.py --batch-size 128` → ResNet50 extracted 2048-dim embeddings on RTX 4090
6. ✅ Built 19 FAISS `IndexFlatIP` files (one per display_category) — all saved to server
7. ✅ Downloaded all artifacts to `backend/app/ml/faiss_indices/` (181 MB, 19 `.index` files) and `backend/app/ml/id_maps/` (19 `.pkl` files)

**Known Issue — MongoDB Atlas Free Tier Storage Quota Exceeded**:
- During `push_embeddings_to_mongo` step, hit: `pymongo.errors.OperationFailure: you are over your space quota, using 533 MB of 512 MB`
- MongoDB Atlas free tier (M0) has a 512 MB limit; pushing 2048-dim vectors for 23K products (~184 MB) pushed us over
- **Impact**: Product documents in MongoDB do NOT have their `embedding` field populated
- **Mitigation**: FAISS indices + id_maps are fully functional and are the primary artifacts needed for the search service. The MongoDB embedding field is not required by the current `similarity_service.py` plan.
- **Future fix if needed**: Upgrade to M10 Atlas tier ($57/month), or store only quantized (int8) embeddings, or skip MongoDB embedding storage entirely since FAISS handles the similarity search.

**Artifacts Location**:
- `backend/app/ml/faiss_indices/*.index` — 19 category index files
- `backend/app/ml/id_maps/*.pkl` — 19 category id maps (FAISS row int → product_id)

**Next Step**: The search endpoint is now implemented directly in `backend/app/api/routes/search.py` using FAISS (no separate similarity_service.py needed). It loads indices at startup and serves per-request queries via FAISS.

---

## ML FAISS Pipeline — Remaining Todos (Recovered)

These tasks were in the deleted plan file and are restored here to avoid being lost again.

---

### phase4-ranking — Multi-Signal Ranking System [PENDING]

**What**: After FAISS returns the top-K candidates by visual similarity, re-rank them using a combined score that factors in price and product attributes alongside visual similarity.

**Formula**:
```
final_score = (w_sim * similarity_score) + (w_price * price_score) + (w_attr * attr_score)
```

- `similarity_score` — cosine similarity from FAISS (0–1, already implemented)
- `price_score` — how affordable the result is relative to a reference price: `1 - (result_price / max_price_in_results)` — cheaper = higher score
- `attr_score` — how well product attributes (gender, category) match the query context (0 or 1 for hard filters, partial for soft matches)
- Weights `w_sim`, `w_price`, `w_attr` are **configurable** (default: 0.7, 0.2, 0.1)

**Where to implement**: `backend/app/api/routes/search.py` — after the FAISS search, before returning results.

**Success criteria**: Given two results with similar visual similarity, the cheaper one ranks higher. Weights can be changed in config without code changes.

---

### phase4-reindex — Incremental Re-indexing for New Scraped Products [PENDING]

**What**: When new products are added via scraping, generate their embeddings and **add them to the existing FAISS index** without rebuilding from scratch. `faiss.IndexFlatIP` supports `.add()` incrementally.

**Trigger**: After the scraping job finishes (Admin Dashboard Auto Sync module completes), a background task should:
1. Find products in MongoDB that have no embedding (or no FAISS entry)
2. Download their images
3. Extract ResNet50 embeddings (or FashionCLIP after switch)
4. Append to the relevant category's `.index` file via `index.add(new_vecs)`
5. Append to the relevant `id_map.pkl` with new FAISS positions → product_ids
6. Save updated index + id_map back to disk

**Where to implement**: New script `ml-engine/scripts/reindex_new_products.py` + hook into Admin Dashboard scraping completion (Phase B.14).

**Success criteria**: After scraping 50 new kurtas, running the reindex script adds them to `women_kurta.index` and they appear in search results — without rebuilding the full 6,802-vector index.

---

## FashionCLIP Isolated Pipeline — In Progress (March 16, 2026)

### Files created (all local code done)

| File | Purpose |
|---|---|
| `ml-engine/fashionclip/__init__.py` | Package marker |
| `ml-engine/fashionclip/extractor.py` | FashionCLIPExtractor class (isolated, bug-fixed) |
| `ml-engine/fashionclip/config.yaml` | Model + path config |
| `ml-engine/fashionclip/requirements.txt` | Deps for Vast.ai |
| `ml-engine/fashionclip/scripts/generate_embeddings.py` | **DataLoader fix** — GPU job, ~10 min for 23k images |
| `ml-engine/fashionclip/scripts/quick_eval.py` | Side-by-side HTML comparison vs ResNet50 |
| `backend/app/ml/fashionclip_indices/` | Empty, waiting for Vast.ai indices |
| `backend/app/ml/fashionclip_id_maps/` | Empty, waiting for Vast.ai id maps |
| `backend/app/api/routes/search_fashionclip.py` | Isolated endpoint at `/api/search/fashionclip/similar` |
| `download_fashionclip_indices.py` | Download script (update SSH_HOST + SSH_PORT) |
| `vastai_fashionclip_setup.py` | Upload to Vast.ai, installs deps, launches job |
| `check_fc_progress.py` | Upload to Vast.ai, run to monitor job progress |

### Vast.ai execution steps (waiting for instance)
1. Get new Vast.ai instance (SSH details needed)
2. Update `vastai_key.pem` if new key
3. SCP: upload `ml-engine/` folder + helper scripts
4. Run `vastai_fashionclip_setup.py` on remote (installs deps, re-downloads images, launches job)
5. Monitor with `check_fc_progress.py`
6. When done: run `download_fashionclip_indices.py` locally (update SSH_HOST/PORT first)
7. Run `ml-engine/fashionclip/scripts/quick_eval.py` → open `comparison_results.html`

### Swap trigger (after evaluation)
In `backend/app/api/routes/search.py`, change 3 lines:
```python
FAISS_DIR   = ML_DIR / "fashionclip_indices"    # was: faiss_indices
ID_MAPS_DIR = ML_DIR / "fashionclip_id_maps"    # was: id_maps
from fashionclip.extractor import FashionCLIPExtractor as FeatureExtractor  # was: feature_extractor
```

---

## FashionCLIP Switch — Deferred to Next Session

First attempt was abandoned because the Vast.ai batch job took ~2 hours (I/O bottleneck — CPU reading 64 images per batch ~18s, GPU only takes 50ms).

**Root cause**: `generate_embeddings_vastai.py` uses manual PIL loops — no parallel data loading.

**Fix for next session** — replace the manual loop with PyTorch DataLoader (num_workers=4):
```python
from torch.utils.data import DataLoader, Dataset
loader = DataLoader(dataset, batch_size=64, num_workers=4, pin_memory=True)
```
This prefetches the next batch on background threads while the GPU processes the current one.
Expected speedup: ~20s/batch → ~1-2s/batch → 23k images done in ~10 min instead of 2 hours.

**Current state (what's already done — don't redo)**:
- `ml-engine/embeddings/fashion_clip_extractor.py` — already written and correct (bug fix applied)
- `ml-engine/embeddings/__init__.py` — needs to be switched back to FashionCLIP for that session
- `ml-engine/config.yaml` — needs embedding_dimension: 512
- `backend/app/api/routes/search.py` — already FAISS-based (just swap extractor import)
- Vast.ai: images already exported to remote (23,060 images in `/root/ml-engine/data/`) — **reuse if instance still available**; otherwise re-export takes ~20 min

**Steps for next session**:
1. Update `generate_embeddings_vastai.py` to use DataLoader (num_workers=4)
2. Switch imports back to FashionCLIPExtractor
3. Rent Vast.ai GPU instance, upload updated ml-engine, run generate (~10 min)
4. Download faiss_indices/ + id_maps/ → backend/app/ml/
5. Run quick_eval.py and compare with ResNet50 results

---

## Lessons

### General Lessons
- Include info useful for debugging in the program output
- Read the file before trying to edit it
- If there are vulnerabilities that appear in the terminal, run npm audit before proceeding
- Always ask before using the -force git command

### Project-Specific Lessons
- **Windows PowerShell Directory Creation**: On Windows, use `New-Item -ItemType Directory -Force -Path` instead of Unix-style `mkdir -p` for creating nested directories. The `-p` flag doesn't work the same way in PowerShell's mkdir alias.
- **Project Structure Organization**: Organizing the codebase into clear modules (backend, frontend, mobile, ml-engine, admin-dashboard) from the start makes the project much more manageable and allows parallel development.
- **Configuration Files First**: Creating all configuration files (package.json, requirements.txt, pubspec.yaml, docker-compose.yml) before writing code helps ensure all team members have consistent development environments.
- **Windows Console Unicode**: Windows PowerShell/CMD doesn't properly support Unicode characters (✓, ❌, 🎉) in Python output. Use ASCII alternatives like [OK], [ERROR], [SUCCESS] for cross-platform compatibility.
- **PyTorch Version Management**: PyTorch versions change rapidly. Use flexible version constraints (>=) instead of exact versions (==) in requirements.txt to avoid installation failures. Latest version (2.9.0) is compatible with older code.
- **ResNet50 Download**: First time running ResNet50 model downloads 97.8 MB from PyTorch model zoo. Takes ~1 minute on average internet connection. Subsequent runs are instant (cached in ~/.cache/torch/).
- **CPU vs GPU for 40% Milestone**: CPU inference (402ms per image) is sufficient for 40% demo with 50-100 products. GPU optimization can be deferred to 60% milestone when scaling up.
- **PostgreSQL Installation Issues on Windows**: PostgreSQL installation can be problematic on Windows due to permissions, antivirus, or system configurations. MongoDB is a better alternative for this project as it: (1) has easier Windows installation, (2) stores embeddings natively as arrays, (3) is more flexible for image metadata, and (4) aligns with the original proposal's architecture.
- **Product Catalogue "No image"**: If rescrape runs but most products still show "No image", (1) relax `_looks_like_image_url` to allow more path segments (e.g. `/mens/`, `/catalog/`, `/img/`) so download is attempted; (2) in frontend, on image onError try `product.image_url` via image-proxy before falling back to "No image".
- **Category filter regex (MongoDB)**: For "endpoint-only" branch (e.g. Women Luxe, Women Short kurti), use exact slug match: `^(?:slug1|slug2|slug3)$` so only those exact `endpoint_category` values match, not substrings.
- **faiss-gpu not on PyPI**: `faiss-gpu` is no longer available on PyPI (pip). Use `faiss-cpu` instead — PyTorch handles the GPU-heavy embedding extraction; FAISS CPU is perfectly fast for index building at 23K vectors.
- **Windows SSH key permissions for OpenSSH**: Use `icacls "key.pem" /inheritance:r /grant:r "DOMAIN\USER:(R)"` with the full `whoami` output (e.g. `us\us`) as the identity. The short username alone fails with "identity references could not be translated".
- **PowerShell SSH with Python -c**: PowerShell strips quotes from SSH remote commands containing Python inline code. Write Python to a temp `.py` file locally, scp it to the server, then `ssh ... python3 /path/to/file.py` instead.
- **MongoDB Atlas M0 storage limit**: Free tier is 512 MB. Storing 2048-dim float32 embeddings for 23K products adds ~184 MB. If the cluster is already near full, the bulk_write push will fail with `AtlasError code 8000`. Solution: export all products to local JSON (READ — always works), drop the collection via Atlas UI (frees space), reimport without embedding field via pymongo bulk_write. Atlas M0 blocks ALL writes (including $unset, updateMany, even from mongosh) when over quota — only dropping the collection frees space.
- **MongoDB backup/reimport pattern**: Use `json.dumps` with custom serializer (ObjectId → str, datetime → isoformat) for export. On reimport, restore `_id` as `ObjectId(str_value)` before inserting to preserve original document IDs.
- **FashionCLIP CPU cold-start**: `patrickjohncyh/fashion-clip` (600MB ViT-B/32) takes 2-3 minutes to load on CPU from disk the first time after a reboot. Once in OS RAM cache, subsequent loads take 8-10s. For the FYP demo: pre-load using the startup lifespan event in main.py so the model is warm before any user requests arrive. Per-request inference on CPU: ~200-350ms (vs ~50ms for ResNet50) — acceptable for a mobile app.
- **FashionCLIP get_image_features bug**: `CLIPModel.get_image_features()` for `patrickjohncyh/fashion-clip` returns a `BaseModelOutputWithPooling` object instead of a plain tensor. Fix: use `model.vision_model(pixel_values=pv).pooler_output` then `model.visual_projection(pooled)` explicitly — works with all CLIP checkpoints.
- **FashionCLIP embedding dimension**: 512-dim (vs ResNet50's 2048-dim). Update `config.yaml` embedding_dimension and rebuild all FAISS indices — the old 2048-dim `.index` files are incompatible.
- **FastAPI lifespan blocking the event loop**: Any synchronous heavy work (model loading, FAISS index loading) inside the `lifespan` startup event blocks the entire async event loop — the server accepts TCP connections but never responds to HTTP requests. Fix: wrap in `threading.Thread(target=..., daemon=True).start()` so startup completes immediately and loading happens in the background.
- **embeddings/__init__.py stale import**: After deleting `feature_extractor.py`, the `__init__.py` still imported from it, causing `ModuleNotFoundError` when any script in the package imported the `embeddings` module. Fix: update `__init__.py` to import only `FashionCLIPExtractor`.
- **FashionCLIP on GPU is I/O bound**: Even on 2x RTX 4090, FashionCLIP batch processing runs ~20s/batch of 64 images because CPU image-loading (PIL) and preprocessing is the bottleneck. GPU compute is milliseconds — GPU utilization shows 0% in `nvidia-smi` while CPU prepares the next batch. Expect ~2 hours for 23K images. This is a one-time cost; the FAISS indices persist indefinitely.

---

### Mobile Welcome Screen (Mar 14, 2026) — Executor

- **Done**: `welcome_screen.dart` — removed white card, duplicate top logo, welcome copy, and **Continue as Guest**. Only **Log In** + **Sign Up** aligned to bottom over full-screen `login_welcome.png` (no container). `setGuestMode` / `isGuest` kept for existing guest prefs + Me tab; new users must sign in from welcome.

**Manual check**: Run app cold → welcome shows image + two buttons only; guest link gone; no double DupeFinder at top.

---

### Mobile App: Styling, Wishlist, Compare, Community, Insights (Mar 18, 2026) — Executor

- **Sign Up**: Removed the password requirement chips line (8+ chars, A–Z, a–z, 0–9, Symbol). Validation still enforced on submit; only the visible row of chips is hidden.
- **Wishlist**: Added `WishlistService` (SharedPreferences). Search result cards have heart (save) and compare icons. **WishlistScreen** shows saved products in a grid; remove via heart, add to compare via compare icon. Tab refresh when switching to Saved.
- **Compare**: Added `CompareService` (max 4 items). Search and wishlist cards have “Add to Compare”. **CompareScreen** shows side-by-side grid with image, name, brand, price, match %; remove per item or “Clear all”. Tab refresh when switching to Compare.
- **Community**: Added `CommunityService` (local posts + replies in SharedPreferences). **CommunityScreen**: list of posts, FAB “New post”, tap post → bottom sheet with replies and reply field. Working module (no backend).
- **Insights**: **InsightsScreen** is live: loads wishlist count, compare count, search count (incremented on each image search), and shows stat cards. Fourth card “Average savings” left as placeholder.
- **Unique styling**: **AppTheme** — `AppColors.scaffoldBg`, `AppColors.cardSurface`, **AppDecor** (cardRadius, tileRadius, cardDecoration, welcomeBanner). Theme uses scaffoldBg, cardTheme with 20px radius. **Home**: welcome banner uses gradient; Explore section has blue accent bar; tiles and tip card use AppDecor. **Me**: cards use AppDecor.cardRadius. **Community/Insights**: AppBar uses cardSurface. All screens use consistent light blue/grey background and card style.

---

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026)

- **Mode**: Executor
- **Milestone completed**: Image Search screen category dropdown now includes full current category set so users can select all available Women/Men categories.
- **UI improvement**: Category and price dropdowns now have explicit menu max-height so long lists stay scrollable and accessible on small screens.
- **Files updated**: `mobile/lib/screens/search/image_search_screen.dart`
- **Verification**: `ReadLints` run on edited file — no linter errors.
- **Next step (awaiting user verification)**: Confirm on device that all categories are visible and selectable in `Find Similar`.

### Executor's Feedback or Assistance Requests — Mar 19, 2026

- I completed the **first requested subtask only** (`sari categories show honi chahiye`) per one-task-at-a-time workflow.
- Please manually test the category dropdown and confirm this milestone.
- After your confirmation, I will proceed to the **next task**: password requirement checks visibility on the signup screen.

---

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 2)

- Implemented requested mobile UX updates across profile, signup, search-history/reviews, and community feed.
- **Signup**: password requirement checks are now visibly shown in real time under password field.
- **Profile/Insights**: profile details expanded (username, joined date, login email, post/history counts), insights cards are clickable, and dedicated **Dupe History** screen added.
- **Dupe click tracking + reviews**: clicking a dupe now records history, app-start prompt asks for review, and star ratings are saved and shown in history/search cards.
- **Community feed**: switched to Instagram-like scrollable cards with image + description + username/pfp + relative time; posts older than 7 days auto-removed.
- Added local persistence buckets for community posts and review records (database-like categories in app storage).
- Validation run: `flutter test` passed (1/1). `flutter analyze` has only existing/style infos, no blocking errors.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 3)

- Community persistence moved to backend MongoDB (`/api/community/*`) so posts survive app/server restarts.
- Added authenticated user data persistence APIs (`/api/user-data`) for:
  - wishlist
  - compare list
  - dupe history (including review metadata)
- Mobile services `WishlistService`, `CompareService`, and `DupeHistoryService` now use backend storage for logged-in users with one-time local-to-backend migration.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 4)

- Fixed profile photo flow so upload still completes even if web cropper throws an error (fallback to original selected image bytes).
- Added an explicit "Edit name" option in `Me` screen so users can set display name (e.g., `Abdul Basit`) immediately.
- Home welcome subtitle now never falls back to email; it shows saved display name or `User`.
- Community author fallback now avoids email-prefix names and uses display name consistently for current user's posts/replies.
- Lint check run on edited files: no lint errors remaining.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 4)

- Please open `Me` tab and use **Edit name** to set `Abdul Basit` once, then verify:
  - Home welcome shows `Abdul Basit`
  - New community posts/replies show `Abdul Basit` (not email/prefix)
- Please test profile picture flow again with crop. If crop UI still fails on your browser, upload should still save the selected image because fallback is enabled.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 5)

- Removed `Quick Actions` section from admin overview and replaced landing page with graph-style analytics blocks:
  - usage breakdown graph (wishlist/compare/history/reviews/community)
  - 7-day community activity graph (posts vs reports)
- Added admin moderation backend APIs:
  - fetch community posts for admin
  - fetch report queue
  - resolve reports (`ignore`, `delete_post`, `ban_user`)
  - direct delete post
  - ban user + remove user posts
- Added user moderation APIs in community routes:
  - user can delete own post
  - user can report any post with reason
- Added new Admin Dashboard module: **Community Moderation** with:
  - report table + resolve actions
  - all-posts table + delete/ban actions
- Mobile community updated:
  - post menu now supports **Delete my post** or **Report post**
  - report reason dialog + success/error feedback
  - login flow now stores `user_id` in prefs to identify ownership checks.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 5)

- Please manually test:
  1. Mobile: report a post and delete own post
  2. Admin: open **Community Moderation** and verify report appears
  3. Admin: resolve report via delete/ban and verify effect in mobile feed
- Note: `flutter analyze` shows existing/info-level style warnings (no new compile errors). Backend Python compile and frontend build are successful.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 6)

- Admin Overview charts upgraded from simple bars to professional chart components using `recharts`.
- Headings cleaned as requested:
  - `Usage Breakdown` (removed "(Graph)")
  - `7-Day Community Activity` (removed "(Graph)")
- Added:
  - proper `BarChart` for usage metrics
  - proper `LineChart` for posts vs reports trend
  - legend, tooltip, axis labels, and grid for readability
- Frontend build re-run after changes: successful.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 6)

- `npm audit` reports 2 moderate vulnerabilities due to current `vite`/`esbuild` chain; automated fix requires `npm audit fix --force` (breaking major upgrade). Please confirm before I apply any force upgrade.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 7)

- Removed `e.g. Abdul Basit` hint from Edit Name dialog as requested.
- Implemented stronger name mapping for existing + new users:
  - backend auth now exposes `/api/auth/me`
  - login response now returns `_id`, `full_name`, and fallback fields (`name`, `username`)
  - mobile now syncs profile from backend after login (`syncUserProfileFromBackend`) and stores `user_name`, `user_email`, `user_id`
  - home/me/community now avoid raw `User` fallback whenever backend/email name can be resolved.
- Updated profile image flow:
  - after crop (or fallback), app now shows preview dialog with **Cancel** and **Upload**
  - image saves only when user taps **Upload**.
- Restarted mobile app on Chrome with latest code.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 7)

- Please test with an old registered account: logout/login again and verify full name appears on Home + Community.
- Please test profile image flow: pick image → adjust crop → tap **Upload** in preview dialog and verify avatar updates.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 8)

- Root-cause addressed: profile/name persistence now moved to backend profile API (instead of local-only behavior).
- Backend updates:
  - Added `GET/PUT /api/user-data/profile` for `display_name` + `profile_image`
  - `PUT /profile` also syncs `users.full_name` so signup-name/edit-name remain consistent in auth responses.
- Mobile updates:
  - `UserProfileService` now syncs profile from backend on load.
  - `setDisplayName` and `setProfileImageFromBytes` now persist to backend for logged-in users.
  - Login/profile sync now consumes both `/api/auth/me` and `/api/user-data/profile`.
- Relaunched mobile app on Chrome after these fixes.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 8)

- Please do one clean verification path:
  1. Sign out → Sign in again with existing account
  2. Check Home + Me name (should come from backend full name/profile)
  3. Edit name → Save → re-open Home
  4. Upload profile pic → restart backend/app → verify image still present

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 9)

- Implemented refresh/tab consistency:
  - Main shell now persists selected bottom-tab index in prefs and restores after page refresh.
- Implemented bottom-nav profile avatar:
  - `Me` tab icon now shows user's profile picture (if available) in the navigation bar.
- Improved community ownership logic:
  - Own post detection now checks `author_user_id` plus fallback name/email-prefix matching for legacy posts.
  - Own post menu: **Edit my post** + **Delete my post**
  - Other users' post menu: **Report post** only
- Added backend endpoint for own-post edit:
  - `PUT /api/community/posts/{post_id}` for editing post description with ownership checks.
- Improved dupe history persistence resilience:
  - Added backend-cache fallback on mobile so history does not appear empty during transient backend reload issues.
- Improved legacy full-name fallback on backend auth:
  - if `full_name` equals email-prefix, backend tries better name fallback from user profile/community data.
- Relaunched mobile app on Chrome with latest fixes.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 10)

- Admin dashboard UI simplified as requested:
  - Removed `ML Training` module from sidebar and routing in `frontend-app/src/pages/AdminDashboard.jsx`.
  - Removed top `Admin Panel` header bar from admin main content area.
- Product Catalogue page cleaned:
  - Removed `Import Products from CSV` section.
  - Removed `Image Link Cleanup` section.
  - Page now shows filters and products listing section only (plus existing catalogue actions like clear-all).
- Verification:
  - Frontend production build completed successfully via `npm run build`.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 10)

- Please refresh admin dashboard and verify:
  1. `ML Training` menu item is fully removed.
  2. Product Catalogue only shows filters + products list (no CSV import, no broken-link cleanup blocks).
  3. Top `Admin Panel` strip is gone.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 11)

- Product card alignment improved in admin Product Catalogue so price row sits consistently at the same vertical level across cards.
- CSS update applied in `frontend-app/src/styles/AdminDashboard.css`:
  - `.product-card-item` set to full-height card behavior.
  - `.product-info-wrapper` set to flex-grow layout.
  - `.product-meta` changed to `margin-top: auto` to pin price row to bottom consistently.
- Verification:
  - Frontend build successful via `npm run build`.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 11)

- Please refresh Product Catalogue and verify product prices are now aligned in one line/level across the grid cards.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 12)

- Admin **Community Moderation** now shows **current** author names (from `user_app_data.display_name` + `users.full_name` via `_effective_name_for_user`) instead of the stale `author` string stored on each post/report snapshot.
- Backend: `backend/app/api/routes/admin_new.py` — `_community_user_display_name_map` + updated `GET /api/admin/community/posts` and `GET /api/admin/community/reports` (`post_author_name` resolved the same way).
- Verification: `python -m py_compile` on `admin_new.py` succeeded.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 12)

- Restart backend, refresh Community Moderation, and confirm **All Community Posts** author column matches the app (e.g. `Abdul Basit` instead of `ab887812` / `qa`) when `author_user_id` is present on the post.

### Current Status / Progress Tracking — Executor Update (Mar 19, 2026, Batch 13)

- Fixed Android crash in profile image crop flow by registering uCrop activity in app manifest.
- File updated: `mobile/android/app/src/main/AndroidManifest.xml`
  - Added `com.yalantis.ucrop.UCropActivity` under `<application>`.
- Root cause addressed from runtime log:
  - `ActivityNotFoundException: ... UCropActivity ... not declared in AndroidManifest.xml`
- Verification:
  - Confirmed manifest now contains `UCropActivity` entry.

### Executor's Feedback or Assistance Requests — Mar 19, 2026 (Batch 13)

- Please run mobile app on Android again and test: `Me -> Change profile picture -> crop -> upload`.
- If crash persists, share fresh log after this manifest fix so I can handle the next layer immediately.

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 14)

- Community UX consistency fixes implemented for both Android and Chrome in `mobile/lib/screens/community_screen.dart`:
  - Added auto URL detection + clickable links in post descriptions and replies.
  - Improved reply composer visibility with keyboard-aware `AnimatedPadding` using `viewInsets.bottom`.
  - Set explicit reply input text/cursor colors so typed text remains clearly visible.
- Added reusable `_LinkText` renderer with URL regex + `url_launcher` tap handling.
- Verification:
  - Lint check run on updated screen file; no linter errors.

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 14)

- Please verify on both Android and Chrome:
  1. Post/reply containing `https://...` or `www...` opens when tapped.
  2. While typing reply, text is visible and input area stays above keyboard.
  3. Same behavior is consistent across both platforms.

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 15)

- Community post image rendering adjusted to show full uploaded image (no center-crop cut-off) in both feed cards and detail sheet.
- Updated `mobile/lib/screens/community_screen.dart`:
  - Changed post image fit from `BoxFit.cover` to `BoxFit.contain`.
  - Added neutral background container behind images for cleaner letterbox space.
- Result: user-uploaded images now remain fully visible (mobile + Chrome share same Flutter UI codepath).
- Verification: lints checked for updated screen file; no errors.

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 15)

- Please verify on Android and Chrome that community post images now display completely (not half-cut/cropped).

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 16)

- Implemented requested multi-fix batch for mobile + Chrome consistency:
  1. **Community reply overflow fix** (`mobile/lib/screens/community_screen.dart`)
     - Post detail bottom sheet now uses safer sizing (`initialChildSize` increased, `minChildSize` adjusted, `useSafeArea: true`).
     - Removed extra keyboard-bottom inset that was causing render overflow when reply box opened.
  2. **Insights updates** (`mobile/lib/screens/insights_screen.dart`)
     - Removed **Dupe history & reviews** card/tab from Insights.
     - **Trending alternatives** now uses most-clicked dupes (from click history), not wishlist brands.
     - Trending alternatives card is now openable and shows actual items list in a bottom sheet; tapping item opens product link.
  3. **Dupe click counting** (`mobile/lib/services/dupe_history_service.dart`)
     - Added `clickCount` in history entries and increment logic on repeated product clicks.
  4. **Find Similar image + link reliability** (`mobile/lib/screens/search/image_search_screen.dart`)
     - Product links now resolve from multiple fields (`product_url`, `product_link`, `url`) and normalize missing scheme.
     - Product image URL resolution improved with backend origin logic, local `image_path` support, and proxy fallback for external image URLs.

- Verification:
  - Lints on edited files checked.
  - `flutter analyze` on changed files returned only existing/info-level warnings (no compile-blocking errors).

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 16)

- Please test these exact flows on **Android and Chrome**:
  1. Community post detail -> type reply with keyboard open (no overflow, typed text visible).
  2. Insights -> no Dupe History card; Trending alternatives opens list and items open on tap.
  3. Find Similar -> product cards open product links; previously missing images should now load more reliably.

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 17)

- Follow-up fix for persisted community overflow issue:
  - Added explicit max-height constraints to community post images in both feed card and post detail sheet.
  - File: `mobile/lib/screens/community_screen.dart`
  - Feed image max-height: `260`
  - Detail image max-height: `280`
- This keeps images fully visible with `BoxFit.contain` while preventing `RenderFlex overflow` on smaller Android screens.
- Verification: lint check run on updated file; no errors.

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 17)

- Please retest the same post on Android:
  1. Open post detail with large image.
  2. Confirm yellow/black overflow strip is gone.
  3. Confirm reply box remains usable and typed text visible.

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 18)

- Implemented **delete own comment/reply** functionality for community posts (backend + mobile):
  - Backend: `DELETE /api/community/posts/{post_id}/replies/{reply_id}`
  - Added reply `id` in backend serialization and creation.
  - Ownership check enforced (by `author_user_id` or author-name fallback).
  - Mobile API/service wired with `deleteCommunityReply` and `deleteReply`.
  - Community detail UI now shows **Delete my reply** option on own replies and refreshes list after deletion.
- Improved post image presentation (Instagram-like, no forced gray side fill):
  - Removed custom gray background wrapper behind community post images.
  - Kept full-image display behavior with `BoxFit.contain` + max-height bounds.
- Validation:
  - Backend `community.py` compiles successfully.
  - Lint checks on updated mobile files: no lint errors.

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 18)

- Please test:
  1. Create a new reply from same user, then open menu on that reply and delete it.
  2. Confirm community images now show without gray side fill in feed and detail.

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 19)

- Added reply-avatar support so whenever a user replies, their profile picture is sent and rendered with the reply.
- Backend (`backend/app/api/routes/community.py`):
  - `CommunityReplyIn` now accepts `author_pfp`.
  - Reply document persists `author_pfp`.
  - Reply serialization now returns `authorPfp`.
- Mobile API/Service:
  - `addCommunityReply` now sends `author_pfp`.
  - `CommunityService.addReply` passes current profile image from prefs.
  - `CommunityReply` model updated with `authorPfp`.
- Mobile UI (`mobile/lib/screens/community_screen.dart`):
  - Reply row now shows `CircleAvatar` with reply author profile pic (fallback icon when missing).

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 19)

- Please test by posting a fresh reply from a user with profile pic set; avatar should appear next to that reply.

### Current Status / Progress Tracking — Executor Update (Mar 26, 2026, Batch 20)

- Reply UX stability + visibility polish (`mobile/lib/screens/community_screen.dart`):
  - Reply input now explicitly high-contrast (filled white field + strong text color + focused border).
  - Input is disabled while sending (`_sendingReply`) to prevent accidental rapid duplicate sends.
  - Send via keyboard submit now also respects `_sendingReply` guard.
- Profile notification bottom-message behavior (`mobile/lib/screens/me_screen.dart`):
  - On opening Me/Profile, latest unread notification now appears as bottom SnackBar message.
  - SnackBar includes **Open** action; tapping it navigates to related community post/reply flow already wired in MainShell.
  - Added simple de-dup guard so same notification snackbar does not spam repeatedly.
- Existing already-wired behavior remains active:
  - notification tap routes to Community post
  - target reply is highlighted for a few seconds

### Executor's Feedback or Assistance Requests — Mar 26, 2026 (Batch 20)

- Please verify on Android + Chrome:
  1. While typing reply, text is clearly visible.
  2. Single tap on send does not duplicate reply.
  3. Open Me tab with unread comment notification: bottom message appears, and **Open** goes to your post with new reply highlight.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 20)

- Implemented duplicate-reply protection for community replies (backend + app):
  - UI send button now enters a short loading/lock state after one tap so accidental double-click does not create repeated replies.
  - Backend now performs short-window idempotency check (same author + same body within a few seconds) and ignores rapid duplicate submissions.
- Added community notifications when someone replies on your post:
  - Backend now creates notifications for post owner on new replies.
  - New APIs added:
    - `GET /api/community/notifications?limit=&unread_only=`
    - `POST /api/community/notifications/{notification_id}/read`
- Profile (`Me`) screen now shows reply notifications near bottom:
  - "Recent notifications" cards appear with message + preview.
  - Tapping a notification marks it as read and opens the related community post.
- Deep-link to post + reply highlight implemented in community screen:
  - App opens the target post from notification.
  - The new reply is highlighted for a few seconds for easy visibility.
- Added profile tab notification dot/badge in bottom navigation when unread community notifications exist.
- Validation run:
  - Python syntax compile passed for `backend/app/api/routes/community.py`.
  - Dart formatting run on all edited files.
  - Flutter analyze reports only existing/info-level style hints; no new blocking compile errors.

### Executor's Feedback or Assistance Requests — Mar 27, 2026 (Batch 20)

- Please manually test this milestone before moving to next task:
  1. Open one post from User A and reply to it from User B.
  2. In User A profile (`Me`), confirm notification appears under "Recent notifications" and red dot appears on profile tab.
  3. Tap notification: it should open the exact post and highlight the new reply briefly.
  4. In post detail, tap send once quickly (or double tap): confirm duplicate reply is no longer created.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 21)

- Added community reply interaction enhancements requested by user:
  - **Reply back** option on each reply (prefills mention in reply box).
  - **Report reply** action for non-own replies.
  - **Block user** action for non-own replies.
- Backend additions in `community.py`:
  - `POST /api/community/posts/{post_id}/replies/{reply_id}/report`
  - `POST /api/community/users/{target_user_id}/block`
  - Block-list filtering inside `GET /api/community/posts` so blocked users' posts/replies are hidden for blocker.
  - Added `community_user_blocks` collection + indexes.
- Mobile/web (shared Flutter code) additions:
  - Reply item menu now supports `Reply back`, `Report reply`, and `Block user`.
  - Report reason dialog integrated for reply report flow.
  - Mention hint appears in input when replying back to a specific user.
- Validation:
  - `python -m py_compile backend/app/api/routes/community.py` passed.
  - `dart format` applied on edited files.
  - Lint check on edited files: no lint errors.

### Executor's Feedback or Assistance Requests — Mar 27, 2026 (Batch 21)

- Please verify this milestone:
  1. On another user's reply, use **Reply back** and confirm mention text auto-fills.
  2. Use **Report reply** and confirm success toast appears.
  3. Use **Block user** and confirm that user's content disappears from your community feed.
  4. Confirm same behavior on mobile and web build.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 22)

- Fixed community detail close behavior causing unnecessary feed refresh.
- Change implemented in `mobile/lib/screens/community_screen.dart`:
  - Parent community list now refreshes **only when a mutation actually occurs** (reply/add/edit/delete/block) via `onMutated` callback.
  - Plain dismiss/minimize (tap outside sheet) no longer triggers `_load()` refresh.
  - Post delete from detail returns with explicit mutation signal and refreshes correctly.
- Validation:
  - Dart format run on updated file.
  - Lint check: no lint errors.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 23)

- Improved community interaction to avoid full-page refresh even after mutations.
- `mobile/lib/screens/community_screen.dart` now uses in-place state sync:
  - Post detail sheet sends updated post back via callback (`onPostChanged`).
  - Parent feed updates only the affected post card locally.
  - On post delete, parent removes only that post locally (`onPostDeleted`).
- Result:
  - Dismiss/minimize does not refresh.
  - Reply/add/edit/delete/block changes appear in feed immediately without reloading whole community list.
- Validation:
  - Dart format run.
  - Lint check clean on edited file.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 24)

- Implemented Instagram-style nested reply threading for community comments.
- Backend (`backend/app/api/routes/community.py`):
  - Reply payload now supports `parent_reply_id`.
  - Reply serialization now returns `parentReplyId`.
  - Duplicate-reply guard now also matches parent thread context.
- Mobile/web shared app (`mobile/lib`):
  - `CommunityReply` model now includes `parentReplyId`.
  - `addReply`/API now send optional `parentReplyId`.
  - `Reply back` now targets a specific reply id (not only text mention).
  - Post detail renders replies in threaded order; child replies appear directly under parent with indentation.
- Validation:
  - `python -m py_compile backend/app/api/routes/community.py` passed.
  - `dart format` run on updated files.
  - Lint check on edited files: no lint errors.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 25)

- Added requested threaded-comment visual polish in community detail:
  - Vertical thread indicator for nested replies.
  - "Replying to @username" badge shown on child replies.
  - Collapsible nested replies with max visible depth; users can tap "View more replies" and "Hide nested replies".
- Applied in shared Flutter screen so behavior is consistent on mobile + web.
- Validation:
  - `dart format` applied to `community_screen.dart`.
  - `flutter analyze` run on file (only existing/info-level style hints, no blocking errors).

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 26)

- Optimized Saved/Wishlist and Compare tab open performance.
- Main cause fixed:
  - Bottom-tab navigation previously forced refresh keys for Saved/Compare every time user opened tab.
  - Removed forced per-open refresh in `main_shell.dart`; tabs now reuse existing in-memory state for instant switch.
- Added lightweight in-memory cache in services:
  - `WishlistService` and `CompareService` now cache list data with short TTL (20s).
  - Cache is updated immediately on add/remove/clear, reducing repeated backend fetch latency.
- Result:
  - Opening Saved/Compare after first load is significantly faster.
  - Data still updates on user actions and pull-to-refresh remains available.
- Validation:
  - `dart format` run on updated files.
  - Lint check on edited files: no lint errors.

### Current Status / Progress Tracking — Executor Update (Mar 27, 2026, Batch 27)

- Applied requested consistency + stability updates (web + app):
  1. **Web Admin Overview cards now clickable** (`Overview.jsx`) to jump to relevant modules.
  2. **User deletion now performs deep cleanup** in backend admin routes (`admin.py`, `admin_new.py`):
     - removes `user_app_data` (profile image, display name, wishlist/compare/history)
     - removes refresh tokens
     - removes authored community posts and authored replies
     - removes related community reports, notifications, and block relations
     - removes OTP records for deleted email
  3. **Profile stale image fix after account changes**:
     - mobile profile sync now removes local `user_profile_image` when backend profile image is empty.
     - logout now clears `user_name`, `user_id`, `user_profile_image` alongside tokens/email.
  4. **Saved/Compare performance + reliability tuning**:
     - tab open refresh restored with lightweight path (silent refresh; no blocking loader when list already present).
     - short-lived in-memory cache retained in services for fast repeated tab switches.
     - backend fetch failures now gracefully fallback to local data to avoid “nothing appears until restart”.
  5. **Compare pull-to-refresh fixed**:
     - compare page switched to a refresh-friendly scroll structure.
  6. **Search product links click behavior fixed**:
     - links now use platform-default launch mode and URL normalization for web/app compatibility.
- Validation:
  - Python compile passed for updated admin routes.
  - Frontend build passed (`npm run build`).
  - Dart format run for edited mobile files.
  - Lint checks on edited files: no lint errors.

### Current Status / Progress Tracking — Executor Update (Mar 31, 2026, Batch 28)

- Community reply UX/performance hotfixes applied for mobile/web shared Flutter app:
  1. **Reply now appears instantly without manual refresh**
     - `community_screen.dart` reply flow updated to optimistic UI (temporary local reply is shown immediately).
     - On API success, optimistic state is replaced with backend-confirmed post payload.
     - On API failure, optimistic item is rolled back with error snackbar.
  2. **Reply posting delay reduced**
     - Removed intentional post-send wait delay in `_sendReply()` (the previous artificial cooldown caused visible lag).
     - Stopped full post-list re-fetch on every reply send path; now uses returned updated post directly.
  3. **Community service call latency reduced**
     - Removed repeated `syncUserProfileFromBackend()` calls from hot paths in `CommunityService` (`getPosts`, `addPost`, `addReply`) to avoid extra network round trips before normal actions.
     - `addReply()` now returns updated `CommunityPost` for immediate in-place render.
- Files updated:
  - `mobile/lib/screens/community_screen.dart`
  - `mobile/lib/services/community_service.dart`
- Validation:
  - `flutter analyze` on edited files completed with no blocking errors (info-level existing style warnings only).

### Executor's Feedback or Assistance Requests — Mar 31, 2026 (Batch 28)

- Please manually verify this milestone before I mark it complete:
  1. Open Community and post a reply: it should show immediately in thread (without page reload).
  2. Confirm first reply-post action feels fast (no extra waiting spinner after send).
  3. Re-open Community tab multiple times and check if initial load feels faster than before.
- If this is verified, next executor step will be a broader app-wide latency pass (Home/Search/Saved/Compare/Me) with targeted caching + prefetch tuning per screen.

### Lessons

- Community interaction flows should avoid full-list refetch right after single-item mutations; returning and applying the updated entity keeps UI real-time and faster.

### Current Status / Progress Tracking — Executor Update (Mar 31, 2026, Batch 29)

- Implemented startup/perceived-performance optimization for mobile app first-load lag:
  - Updated `mobile/lib/screens/main_shell.dart` to **lazy-load tabs** instead of initializing all tab screens at startup.
  - Added `_loadedTabs` tracking so only the current tab is built initially; other pages initialize only when opened first time.
  - Preserved fast tab switching after first open by keeping already-loaded tabs in `IndexedStack`.
  - Updated Home AppBar search icon flow to use `_openTab(1)` so lazy-load state remains consistent.
- Expected UX impact:
  - App launch and first screen render become faster.
  - Initial delay on first app open should reduce significantly because heavy tabs (Community/Compare/Saved/Me) no longer all fetch at once.
- Validation:
  - `flutter analyze lib/screens/main_shell.dart` run successfully (no blocking errors; only existing info-level style hints).

### Current Status / Progress Tracking — Executor Update (Mar 31, 2026, Batch 30)

- Implemented app-wide first-load responsiveness optimizations (mobile):
  1. **Unified user-data API cache** in `mobile/lib/services/api_service.dart`
     - Added short in-memory cache (TTL 20s) for `getUserData()`.
     - Added incremental cache update/invalidation on `putWishlist`, `putCompare`, `putDupeHistory`, `putUserProfileData`, and logout token cleanup.
     - Effect: Saved/Compare/History/Insights flows avoid repeated immediate backend calls on quick navigation.
  2. **Community posts cache + stale fallback** in `mobile/lib/services/community_service.dart`
     - Added in-memory posts cache (TTL 12s) with `forceRefresh` option.
     - Mutation paths now invalidate/update cache (`addPost`, `addReply`, `deleteReply`, `deletePost`, `editPost`, `blockUser`).
     - Failure path now returns cached posts instead of empty state where possible.
  3. **Community screen loading behavior smoothing** in `mobile/lib/screens/community_screen.dart`
     - `_load()` now shows full spinner only when no existing posts are present.
     - Refreshes for mutation detail use `forceRefresh: true`, while normal open path benefits from cache for instant render.
  4. **Parallelized independent data fetches** for faster page readiness:
     - `mobile/lib/screens/insights_screen.dart` `_load()` changed from sequential awaits to `Future.wait(...)`.
     - `mobile/lib/screens/me_screen.dart` `_load()` changed to parallel fetch of preferences/profile/history.
- Validation:
  - `flutter analyze` run across edited files; no blocking compile/analyzer errors (only existing info-level lint hints).

### Executor's Feedback or Assistance Requests — Mar 31, 2026 (Batch 30)

- Please verify with a fresh app restart:
  1. First open app -> Home should appear quicker.
  2. First transition across tabs should be smoother than before (especially Community/Me/Insights).
  3. Community open + reply flow should feel near-instant without manual reload.
- If any specific tab still feels slow, share exact tab + action and I will do targeted micro-optimization on that path next (API payload trimming, memoized parsing, and prefetch timing adjustments).

### Current Status / Progress Tracking — Executor Update (Apr 11, 2026, Women scrape / Limelight Formal)

- **Issue**: `Limelight Formal` used `https://www.limelight.pk/collections/women-formal`, which returns **HTTP 404** (collection removed or renamed), so scraper got **0 products**.
- **Fix**: Updated `local_brands_links_women.csv` to `https://www.limelight.pk/collections/formal-wear` (200; `products.json` returns items).
- **Verification**: Local `ProductScraper.scrape_exact_listing_url(..., scraper_type=shopify_json)` returned **33** products for the new URL.
- **User action**: Restart backend if needed, re-run admin scrape for **Limelight Formal**; Mongo counts should update after successful run.

### Lessons

- For Limelight Shopify collections, verify the listing URL with a simple GET: old handles like `women-formal` may 404 while `formal-wear` remains valid.

### Current Status / Progress Tracking — Executor Update (Apr 11, 2026, formal-wear → Women Lawn)

- **User request**: Products that appeared under the **formal-wear** endpoint (Limelight Formal scrape) should show under **Women Lawn** in the admin catalogue.
- **Code**: Added `"formal-wear"` to `WOMEN_LAWN_ENDPOINTS` in `backend/app/api/routes/admin_new.py`; `GET /api/admin/categories` now syncs all lawn endpoints (plus ramadan+lawn regex) to `display_category: Women Lawn` for `gender: w`, matching backfill behavior.
- **DB**: Ran `update_many` for `gender=w` + `endpoint_category` matching `formal-wear` → **33** documents updated to `display_category: Women Lawn`.
- **ml-engine**: Mirrored `formal-wear` in `scripts/backfill_display_category.py` lawn set for offline backfills.

### Current Status / Progress Tracking — Executor Update (Apr 11, 2026, Community post detail theme)

- **User feedback**: Post detail / reply sheet colors did not match app theme (pink / blue / teal).
- **Changes** in `mobile/lib/screens/community_screen.dart`:
  - `_PostDetailSheet`: subtle pink–teal gradient sheet background + soft shadow; themed divider; avatars use pink/teal fallbacks; reply highlight uses pink wash + teal border; thread accent border teal; “Replying to @…” chip uses pink–teal gradient pill; “View more replies” / “Hide nested replies” use pink / teal text; reply `TextField` rounded borders (teal enabled, pink focus) and `DupePalette` hint/cursor; send control uses `DupePalette.ctaGradient` circle instead of flat blue `IconButton.filled`.
  - `_LinkText`: hashtags styled `DupePalette.pinkDeep`, URLs `DupePalette.teal`, default body `DupePalette.textPrimary`.
- **Planner**: Please confirm after manual QA on device/web that the sheet matches the rest of the app.

### Current Status / Progress Tracking — Executor Update (Apr 11, 2026, Community feed layout)

- **User request**: Community page structure should match **first reference** (Instagram-style card: badge, full-bleed square image, like/comment/share row, bold name + caption), not the older layout (big gradient header + trending pills + compact card).
- **Changes** in `mobile/lib/screens/community_screen.dart`:
  - Removed in-body “Community” gradient title, subtitle, add-user shortcut, and horizontal **trending hashtag** strip.
  - Feed background: soft **mint / teal–blue** gradient (`0xFFEEF9F6` + palette tints).
  - Each post: white rounded card with shadow; header row (avatar, name, time, **pink→blue gradient badge** `New` / `N tips`, menu); **1:1** image (edge-to-edge, tap opens detail); **heart** (pink; local toggle + display count from stable hash + optional +1), **comments** (real reply count), **share** (copy caption to clipboard); caption row **bold author** + `_LinkText` / “No description.”
  - **FAB**: pink→blue gradient pill + “New post” (matches reference vibe).
  - **embedded**: single Playfair “Community” title above list (shell has no app bar there).
- **Note**: Like counts are **not from the server** (no likes API); they are **deterministic per post id** for feed polish, plus a **local +1** when the user taps the heart.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Mobile search result click/tap fix)

- **User issue**: On mobile app, search result items were not opening the product website when tapped, while web/Chrome worked.
- **Root cause hypothesis**: Link open flow in `mobile/lib/screens/search/image_search_screen.dart` used `canLaunchUrl()` gate before `launchUrl()`. On some Android devices this returns false for valid `https` links, causing tap to silently do nothing.
- **Code fix**:
  - Updated `_openProductUrl()` to normalize URL and parse URI, then attempt `launchUrl(..., mode: LaunchMode.externalApplication)` first.
  - Added fallback to `LaunchMode.platformDefault` if external launch returns false.
  - Added user-visible `SnackBar` messages and `debugPrint` failure log for easier debugging if opening still fails.
- **Validation**:
  - `flutter analyze lib/screens/search/image_search_screen.dart` run after change.
  - File-level lints show no new diagnostics in editor checks.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Mobile search tap fix)

- Please test on your physical mobile device:
  1. Open app -> Find Similar search -> run a search image.
  2. Tap any product card once.
  3. Confirm browser opens target `product_url`.
- If still not opening, please share:
  - Android version + device model
  - One sample result URL (copy from card/backend response)
  - Whether you see snack bar text like "Could not open link ..." or "Failed to open link ..."

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Mobile lazy loading pass 1)

- **User request**: Mobile app interactions are slow; improve lazy loading and reduce wait on each functionality.
- **Root cause found** in `mobile/lib/screens/main_shell.dart`:
  - `_loadedTabs` had all tabs pre-marked (`{0,1,2,3,4,5}`), so all major tab screens were effectively built at startup.
  - Non-critical startup calls (review prompt check + community notification count) were triggered immediately after first frame.
  - Profile image refresh I/O ran on every tab switch even when Me tab was not opened.
- **Changes implemented (single focused task)**:
  - Enabled **true tab lazy loading**: `_loadedTabs` now starts as `{0}` and adds tabs only when visited.
  - Deferred non-critical startup work by ~700ms after first frame before running prompt/notification refresh.
  - Limited profile refresh disk read to Me tab open only (`targetIndex == 5`).
- **Validation**:
  - `flutter analyze lib/screens/main_shell.dart` => **No issues found**.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Mobile lazy loading pass 1)

- Please test on physical device after full app restart:
  1. Open app cold start: check Home appears faster.
  2. Tap Search/Saved/Compare/Community/Me one-by-one: first open may take slightly longer, but subsequent opens should feel faster.
  3. Confirm general scrolling/tap response improved on first 1-2 minutes of use.
- If a specific screen is still slow, share exact path (e.g., "Home -> Community -> open post detail"), and I will do **pass 2** targeted optimization for that path.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Login reliability fix)

- **User issue**: Login was not working on mobile.
- **Fix 1 (UI validation alignment)** in `mobile/lib/screens/login_screen.dart`:
  - Removed login-time password minimum-length guard from client form.
  - Login now validates only non-empty password and lets backend decide correctness.
  - This avoids blocking legacy users at client side before request is sent.
- **Fix 2 (network/debug visibility)** in `mobile/lib/services/api_service.dart`:
  - Added login request timeout (`12s`) so spinner does not hang too long on bad network/backend state.
  - Added explicit error handling for `TimeoutException` and `SocketException`.
  - Error text now includes endpoint info (`.../auth/login`) and actionable network hint for debugging.
- **Validation**:
  - `flutter analyze` run on edited files; no blocking compile errors.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Login reliability fix)

- Please verify on device:
  1. Open Login screen and try valid credentials.
  2. Confirm app navigates to Home.
  3. If login fails, share exact snackbar message (it now includes debugging details).

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Login restriction restored + backend fallback fix)

- **User correction**: Keep login password restriction (min length) in UI; previous removal was not desired.
- **Revert done**:
  - Restored login form password validator in `mobile/lib/screens/login_screen.dart` (`At least 8 characters` guard is back).
- **Actual issue identified from device screenshot**:
  - Login failed due to network timeout to one backend IP (`172.20.10.6`), not due to password validator.
- **Fix implemented** in `mobile/lib/services/api_service.dart`:
  - Added ordered backend URL list that prioritizes:
    1) currently resolved URL,
    2) saved `backend_ip`,
    3) configured candidate IPs.
  - `resolveBaseUrl()` now persists the successfully reachable IP to `SharedPreferences`.
  - On login `TimeoutException` / `SocketException`, app now automatically retries login across known backend IPs and switches to the first reachable backend.
  - If none reachable, debug message includes all attempted login endpoints.
- **Validation**:
  - `flutter analyze` run on edited files; no blocking analyzer errors.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Login network fallback fix)

- Please test login on device again with valid credentials.
- Expected behavior now:
  - If first IP is down, app should auto-try other known backend IPs and still login.
  - If all IPs are unreachable, snackbar will list attempted endpoints for quick backend/network diagnosis.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Backend unreachable root cause resolved)

- **Observed from user screenshot**: login error showed all known endpoints unreachable.
- **Root cause confirmed**:
  - Backend server was not running (`127.0.0.1:8000/health` connection refused).
  - PC WiFi IP had changed to `192.168.10.8` (not in old mobile candidate list).
- **Actions completed**:
  - Started backend in LAN mode via `backend/start_lan.ps1` (`uvicorn` on `0.0.0.0:8000`).
  - Verified `/health` returns healthy with DB connected.
  - Added current LAN IP `192.168.10.8` to mobile `ApiService._candidateIPs`.
  - Re-ran app on device; logs now show successful backend resolution:
    - `Resolved backend -> http://192.168.10.8:8000/api (health HTTP 200)`.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Login retest after backend fix)

- Please retry login now on mobile.
- If any issue appears, share new snackbar text; networking path is now healthy and connected to active backend.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Community timeout + slow reload fix pass 2)

- **User report**: Community tab still slow to reload; timeout errors while fetching posts.
- **Log evidence** from terminal:
  - `CommunityService.getPosts failed: ClientException: Software caused connection abort ... /api/community/posts`
- **Fixes implemented**:
  - `mobile/lib/services/api_service.dart`:
    - Reworked `getCommunityPosts()` to use backend **failover loop** across ordered known API roots (resolved + saved + candidates), not just single endpoint.
    - Added timeout handling per attempt and automatic resolved-IP persistence on success.
    - Added one final `resolveBaseUrl()` re-probe pass before failing, with explicit attempted endpoints in error.
  - `mobile/lib/screens/community_screen.dart`:
    - Made post-detail return refresh **non-blocking** (`unawaited(_load(forceRefresh: true))`) so UI comes back instantly and feed refreshes in background.
- **Expected outcome**:
  - Community feed should stop hanging on one stale IP and recover faster on network changes.
  - Returning from post detail should feel immediate (no blocking wait for network round-trip).

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, API saved-IP + community retry hardening)

- **`resolveBaseUrl()`**: When every `/health` probe fails (e.g. app resumed quickly, Wi‑Fi still waking), `_resolvedUrl` now falls back to **`SharedPreferences` `backend_ip`** instead of blindly using the first hardcoded candidate. Reduces “wrong IP / nothing loads” after background.
- **`getCommunityPosts()`**: Inner loop now **`catch (_) { continue; }`** for **any** error (not only socket/timeout/client), then **`resolveBaseUrl()`** and a **second full URL pass** before throwing. Error message lists all endpoints tried.
- **Welcome / hero**: Already on **`BoxFit.contain`** + **`Scaffold` / `ColoredBox` `DupePalette.tealWall`** so both people stay visible and letterboxing matches backdrop (no white “frame”).
- **Analyzer**: `flutter analyze` on `main.dart`, `welcome_screen.dart`, `api_service.dart` — no errors (info-level only).

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Retest Community + cold start)

- Rebuild/run on device; open **Community** twice (cold + after switching Wi‑Fi).
- If it still fails, copy the snackbar / log line that shows **“Tried: …”** — that list is the fastest way to see which hosts the phone actually hit.
- Confirm **PC backend** is running (`backend/start_lan.ps1`); without it, retries will still eventually fail.

### Lessons — Apr 17, 2026

- **Partial exception handling is risky**: `ClientException` / JSON / HTTP errors must all advance the failover loop, not only `SocketException` / `TimeoutException`.
- **Probe-all-fail fallback**: Prefer **saved** `backend_ip` over first static candidate when health checks all time out.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Community feed payload size)

- **Symptom**: Community tab showed “feed unreachable” while `/health` and other tabs worked — all `/api/community/posts` attempts failed.
- **Cause**: Feed JSON included **full `imageBase64`** for every post → very large response → mobile **timeouts / connection abort**; other endpoints stayed small so they felt “fast”.
- **Fix**:
  - **Backend** `community.py`: list handler returns **lite** serialization (`imageBase64` omitted, `hasImage` flag). New **`GET /api/community/posts/{post_id}`** returns full post (with image) for detail/hydration.
  - **Mobile**: `CommunityPost.hasImage`; feed shows **“Photo — tap to load”** when lite; detail sheet **hydrates** image via `fetchPostById`; `_refreshPost` **merges** hydrated bytes so lite refresh does not strip the image. `ApiService.getCommunityPost` with same URL failover as feed.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Community live counts + reply sheet + register readability)

- **Community like/comment counts**: Feed timer now every **10s** and calls `_load(forceRefresh: true, showErrorSnack: false)` so counts sync from the server while the Community tab is active. **`feedPollActive: _index == 4`** in `main_shell.dart` avoids polling when another tab is selected; switching back to Community triggers a refresh in `didUpdateWidget`. **`_load`** gained optional **`showErrorSnack`** so background polls do not spam snackbars on empty/error.
- **Post detail / reply sheet**: **`DraggableScrollableSheet`** sizes reduced (**initial 0.58**, **min 0.38**, **max 0.86**); sheet **`decoration`** is **solid white** with a neutral shadow; modal uses **`barrierColor`** ~32% black so the feed does not bleed through; reply field fill uses **`DupePalette.scaffoldLight`** (opaque).
- **Register screen**: Removed full-screen glass-on-gradient; **`Scaffold`** **`backgroundColor: DupePalette.scaffoldLight`**, form on **`AppDecor.cardDecoration`** (white card), **`_solidField`** inputs with dark text, **`_passwordChecksSolid`** panel on light grey.
- **Validation**: `dart analyze` on `register_screen.dart`, `community_screen.dart`, `main_shell.dart` — no errors (info-level only).

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Community UI + register)

- Please hot-restart the app and confirm: (1) like/reply counts update within ~10s when another device changes them, (2) reply sheet is white, smaller, and readable, (3) register/OTP screens are easy to read on device.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Register revert + Welcome container fix)

- **User clarification**: The “container” that should be solid/smaller was the **Welcome** bottom CTA panel (Register / Log In), not the **Register** form screen. Register changes were **reverted** (`git checkout HEAD -- mobile/lib/screens/register_screen.dart`).
- **Welcome** (`welcome_screen.dart`): Removed **BackdropFilter** / translucent glass `Material`; bottom block is now a **compact** card (**`maxWidth: 300`**, tighter padding), **solid** **`DupePalette.cardSurface`** with shadow. **Log In** uses light grey fill + border so it reads on white.

### Merge note — `origin/main` LAN discovery (merged into `api_service.dart`)

- **Upstream**: Wi‑Fi /24 + gateway scan, `device_info_plus` / `network_info_plus`, one-time `backend_ip` migration (`dupefinder_lan_discovery_v2`), `resolveBaseUrl({bool force})`, `_postAuthWithRetry` for auth POSTs, lightweight **`GET /`** probe (not heavy `/health`).
- **Kept from local**: **`_orderedApiUrls()`** for community feed + post fetch and login fallback over **resolved + normalized saved** API roots; **`_tryLoginAcrossKnownBackends`** after `TimeoutException` / `SocketException`; **`resolveBaseUrl(force: true)`** before community URL re-walk.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Mobile UX batch)

- **Welcome hero** (`welcome_screen.dart`): `Image.asset` **`alignment: Alignment.bottomCenter`** (still **`BoxFit.contain`**) so the couple stays visible above the CTA card on tall screens without cropping the artwork.
- **Login → Home tab** (`main_shell.dart`, `login_screen.dart`): Exposed **`MainShell.lastTabPreferenceKey`**; on successful login **`SharedPreferences.remove(MainShell.lastTabPreferenceKey)`** so **`_restoreState`** defaults to tab **0 (Home)** instead of last session’s **Me**.
- **Community feed card** (`community_screen.dart`): Post body (author + message) is **above** the like / comment / share row.
- **Home trending dupes** (`home_tab.dart`): Removed **Explore** 2×2 tiles; **`_loadTrendingDupes`** merges up to **12** unique products from **`shopBrowse`** across **dresses / bags / accessories / jewelry**; horizontal cards with image, brand, name, price; tap opens store URL (same resolution as category browse). **`HomeTab`** now only takes **`onOpenSearch`**. **`main_shell.dart`**: dropped unused **`_openInsightsPage`** / **`InsightsScreen`** import (Insights still reachable elsewhere if linked from Me).
- **Checks**: `dart analyze` on touched screens — **exit 0** (info-level hints only).

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Mobile UX batch)

- Please hot-restart and verify: (1) welcome hero framing on a tall and a short phone, (2) after login you land on **Home**, (3) Community actions are under the post text, (4) Home shows horizontal **Trending Dupes** from the API when the backend is reachable. **Planner**: confirm whether task set is complete after user sign-off.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin web theme + perf)

- **Theme (`AdminDashboard.css`, `theme.css` tokens)**: Data tables use **white cards**, **nav gradient** headers, zebra rows (blue/teal tints), **Dupe CTA gradient** for primary/search/pagination/scrape/train/upload; **destructive** actions stay red. Auto Sync **brand cards** and **product grid** aligned to scaffold + card surfaces; **gender pills** new classes **`admin-gender-pill`**. **Community** page: added **`.section-title`** + **`.content-section`** in admin CSS; fixed **`.section-card *`** overriding CTA text via explicit button color overrides.
- **Charts**: **`OverviewCharts.jsx`** lazy-loaded from **`Overview.jsx`** so **Recharts** (~112 kB gzip) is a separate chunk; chart colors/tooltips match light mobile-style UI.
- **Speed**: **`AdminDashboard.jsx`** prefetches **all** admin route chunks via **`requestIdleCallback`** (fallback `setTimeout`); removed **per-render `console.log`** from **`ScrapingManagement.jsx`** brand list IIFE.
- **Build**: `npm run build` in **`frontend-app`** — **exit 0**.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Admin web)

- **Planner / user**: Hard-refresh the admin app (`npm run dev` → browser) and confirm tables, Auto Sync, Product Catalogue, and Community Moderation match the mobile palette. First visit to **Overview** may still briefly show “Loading charts…” while the **`OverviewCharts`** chunk loads (usually fast after idle prefetch). **Planner** to confirm task complete after sign-off.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin login speed)

- **`AdminLogin.jsx`**: Login POST now uses **`/api/admin/login`** (Vite dev proxy → same host as the UI) with optional **`VITE_API_BASE`** for production-style full-URL API; **25s axios timeout**; clearer message on timeout / unreachable API.
- **`admin_new.py`**: **`admin_login`** changed from **`async def`** to **`def`** so PyMongo + bcrypt run on FastAPI’s **threadpool** instead of blocking the asyncio event loop (helps when other heavy work shares the worker).

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Admin login speed)

- **Planner / user**: Hard-refresh admin login; confirm login feels snappier and still succeeds. If you deploy the static build without a proxy, set **`VITE_API_BASE`** to your API origin (no trailing slash). If login is still slow, next suspect is **MongoDB network latency** (Atlas region) or **first `get_db()` reconnect** after a failed startup connect.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin Auto Sync + Community perf)

- **Auto Sync (`ScrapingManagement.jsx`)**: Removed **`requestIdleCallback`** delay for history on first paint; **brands** and **history** now load **in parallel**. All scraping admin calls use **`adminApiUrl()`** → **`/api/admin/...`** via Vite proxy when appropriate.
- **Community (`CommunityModeration.jsx`)**: One **`GET /api/admin/community/moderation`** (bundle) replaces two sequential requests; **`adminApiUrl`**, loading line, silent refetch after actions unchanged pattern.
- **Backend (`admin_new.py`)**: New **`GET /community/moderation`**; shared **`_format_community_*`** helpers; **`/community/reports`** and **`/community/posts`** refactored to **`def`** (threadpool). **`/scraping/brands`** and **`/scraping/history`** changed from **`async def`** to **`def`** (heavy sync CSV + PyMongo off event loop).
- **Shared**: **`frontend-app/src/lib/adminApiUrl.js`**.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Admin Auto Sync + Community perf)

- **Planner / user**: Hard-refresh admin app; open **Auto Sync** and **Community Moderation** and confirm faster first load. Mobile/other clients still use old separate report/post endpoints if needed.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin perf checklist)

- **Checklist analysis**: Route splitting + prefetch is valid; **TanStack Query** valid for cache/dedupe; **react-window** valid for long lists; **source-map-explorer** is bundle **audit only** (not runtime).
- **Applied**: `React.lazy` + `Suspense` for all five admin modules in **`AdminDashboard.jsx`** with **hover/focus + staggered prefetch** + prefetch active tab; **`QueryClientProvider`** in **`AppWithAuth.jsx`**; **`Overview`** + **`CommunityModeration`** use **`useQuery`** (`staleTime` 60s / 20s); community mutations **`invalidateQueries`** for moderation + **overview**; **`react-window`** `FixedSizeList` for **community posts** when **> 24** rows; **`npm run analyze`** (`vite build --sourcemap` + source-map-explorer HTML report).

### Lessons — Apr 17, 2026 (Admin community 405 + Recharts)

- **`GET /api/admin/community/moderation` returned 405** in the browser while `app.routes` showed `GET` registered — likely **stale API process** or **non-repo server on :8000**; **CommunityModeration** was switched back to **parallel `GET /community/reports` + `GET /community/posts`** (always supported). Backend **`GET /community/moderation`** bundle kept for optional use.
- **Admin posts list**: use **`$project` + `$size`** on `replies` so moderation does not transfer full reply arrays (cuts timeouts on large threads).
- **Recharts `width(-1) height(-1)`**: parent needs **`minWidth: 0`** and **`ResponsiveContainer`** with explicit **`height={320}`** (not only `height="100%"`) in flex layouts.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin web batch 2)

- **No fire-engine red**: `--dupe-destructive-gradient` (pink→violet) for **`.action-btn.danger`**, **product delete**, **broken** badges, **history failed**; toasts/confirm dialogs in **Product** / **Scraping** use pink/fuchsia instead of `#EF4444`.
- **Perf**: **`AdminDashboard.jsx`** now **static-imports** all five admin modules (no tab **Suspense** wait); removed **`key={activeModule}`** remount; still prefetches **`OverviewCharts`**. **`Overview`**: default zeros, **no full-page loading gate**. **`UserManagement`**: **submittedSearch** (no refetch per keystroke), **stale-while-revalidate** table opacity, **optimistic delete**. **`ProductManagement`**: **`fetchProducts({ silent })`** after first load; grid stays mounted with dim during refresh; **optimistic product delete**; **`await fetchProducts`** after clear-all. **`CommunityModeration`**: **optimistic** post delete / ban posts; resolve still **`load()`** sync.
- **Build**: `npm run build` — admin UI in main **`index-*.js`** chunk (~72 kB gzip); charts chunk unchanged ~112 kB gzip.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin login UI revert)

- **User request**: Revert the recent “flat controls on full-screen art” admin login change.
- **Restored**: **`AdminLogin.jsx`** again uses **`auth-box admin-login-card`**, **`auth-header`**, **`auth-form`**, **`form-group`**, **`auth-error`**, **`auth-button admin-login-submit`** on top of **`login.png`** (same **`@login-root`** import + **`.admin-login-bg`**).
- **`Auth.css`**: Restored glass **`auth-box`** / **`.admin-login--fullbg`** rules (**`.admin-login-card`**, **`.admin-login-input-wrap`**, **`.admin-login-submit`**, responsive inner).
- **Build**: `npm run build` in **`frontend-app`** — **exit 0**.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Admin login UI revert)

- **Planner / user**: Hard-refresh **`/admin/login`** (or dev equivalent) and confirm the **frosted card** layout is back. **Planner** to mark task complete after sign-off.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin login centered + readability)

- **`Auth.css`**: **`admin-login--fullbg`** container uses **`align-items` / `justify-content: center`** with safe-area padding; **`.admin-login-full-inner`** uses **`justify-content: center`**, symmetric padding, **`flex: 0 1 auto`** so the card sits **middle of viewport** (not left-aligned).
- **Readability**: **`.admin-login-card`** on fullbg gets **darker slate glass** (`rgba(15,23,42,0.52)`), **stronger blur**, deeper shadow; **title / subtitle / labels** with **text-shadow** and **heavier weights**; **inputs** darker fill + clearer borders; **focus ring** teal-tinted.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Admin login centered + readability)

- **Planner / user**: Hard-refresh admin login; confirm card is **centered** and text/fields read clearly on bright background. **Planner** to confirm after sign-off.

### Current Status / Progress Tracking — Executor Update (Apr 17, 2026, Admin Auto Sync + Community static bundle)

- **`AdminDashboard.jsx`**: **`ScrapingManagement`** and **`CommunityModeration`** are **static-imported** (same chunk as dashboard) so opening **Auto Sync** / **Community Moderation** no longer waits on **lazy `Suspense`** chunk download; **`Suspense`** removed for those two panels only.
- **Prefetch**: Idle stagger now only **`overview` / `users` / `products`** (starts **120ms** + **80ms** steps) since scraping/moderation ship with main admin JS.
- **Build**: `npm run build` — **`index-*.js`** ~**260 kB** (~**84 kB gzip**); separate **`ScrapingManagement`** / **`CommunityModeration`** chunks removed from dist.

### Executor's Feedback or Assistance Requests — Apr 17, 2026 (Admin Auto Sync + Community static bundle)

- **Planner / user**: Hard-refresh admin; first open **Auto Sync** and **Community Moderation** — should show UI immediately (any delay is API/data only, not “Loading … split bundle”). **Planner** to confirm after sign-off.
### Executor — Apr 3, 2026: `git pull` + stash pop conflict in `api_service.dart`

- **Resolved** remaining `<<<<<<<` / `>>>>>>>` blocks: **`baseUrl`** uses upstream null/empty/`unresolvable.invalid` check; **`_postAuthWithRetry`** keeps upstream **`resolveBaseUrl(fullLanScan: false)`** then forced **`fullLanScan: true`** when still no base, with **`postOnce(String api)`** + **`_requireBaseUrl()`** on both attempts; **`shopBrowse`** restored with **`await _requireBaseUrl()`** and **`$api/products/shop-browse`**.
- **`flutter analyze lib/services/api_service.dart`**: no errors (info: `avoid_print` only).
- **Git**: file was still **unmerged** until staged; run **`git add mobile/lib/services/api_service.dart`** to mark resolved. **`pubspec.lock`** / **`windows/flutter/generated_*`** changed from `flutter pub get` — include or **`git restore`** those if you do not want them in the commit. **`git stash list`**: drop the stash entry after you confirm the working tree.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, pull cleanup + commit request)

- User requested to discard `mobile/lib/services/api_service.dart` local changes and keep them out of GitHub. Executor ran `git restore --staged` + `git restore` on that file; it is now removed from local/staged diffs.
- Remaining changes prepared for commit/push are non-`api_service.dart` artifacts: `.cursor/scratchpad.md`, `mobile/pubspec.lock`, windows generated plugin files, index files, and run logs.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (pull cleanup + push)

- Executor is proceeding to commit and push remaining files per user instruction. Planner can review post-push state if needed.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, frontend missing deps fix)

- User reported Vite import-analysis failures in `frontend-app` for `@tanstack/react-query` and `react-window` (`AppWithAuth.jsx`, `queryClient.js`, `CommunityModeration.jsx` imports).
- Installed missing packages: `npm install @tanstack/react-query react-window`.
- Per project lesson, ran `npm audit` after install (4 moderate vulnerabilities reported; non-blocking for current fix, with `npm audit fix` / `npm audit fix --force` suggestions).
- Verification: `npm run build` in `frontend-app` now succeeds (Vite build completes with transformed modules and output assets), confirming the import errors are resolved.

### Lessons — Apr 20, 2026 (Frontend dependency/import failures)

- If Vite reports unresolved imports for new libraries (e.g., `@tanstack/react-query`, `react-window`), install them in `frontend-app` first, then re-run build/dev.
- When terminal shows vulnerabilities after `npm install`, run `npm audit` before proceeding and record findings/suggested remediation.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, mobile splash movement)

- Updated `mobile/lib/screens/welcome_screen.dart` so the hero image now pans horizontally across the screen (right to left, then back) using `AnimationController` + `AnimatedBuilder` with alignment tween.
- Validation: `flutter analyze lib/screens/welcome_screen.dart` reports no issues.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (mobile splash movement)

- Please hot-restart the app and confirm the welcome/splash hero now moves smoothly across the mobile screen and no longer looks static/awkward. If needed, I can tune speed and travel distance.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, splash full-screen fix)

- User reported splash still not filling the full mobile screen. Updated `mobile/lib/screens/welcome_screen.dart` hero image from `BoxFit.contain` to `BoxFit.cover` so it is full-bleed on portrait phones.
- Kept right-to-left movement but tuned pan range/speed for a more natural look on `cover` (`begin: 0.3`, `end: -0.3`, 10s loop).
- Validation: `flutter analyze lib/screens/welcome_screen.dart` passes with no issues.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (splash full-screen fix)

- Please hot-restart and verify the splash now fills the whole screen without teal empty bands. If framing still feels off, share one screenshot and I will tune vertical alignment/pan range quickly.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, splash pan tweak)

- User reported the animation still drifts too far and clips part of the girl’s face. Adjusted the right-side starting alignment in `welcome_screen.dart` from `begin: 0.3` to `begin: 0.42` so the hero starts further right and keeps her face in frame longer.
- Validation: `flutter analyze lib/screens/welcome_screen.dart` passes with no issues.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (splash pan tweak)

- Please hot-restart once and check framing again. If needed, I can do one more micro-adjustment (e.g., `begin: 0.46` or slightly reduce left travel).

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, login label clipping fix)

- User reported the `Log In` button text descender was clipped (`g` cut). Applied a minimal text-only fix in `mobile/lib/screens/welcome_screen.dart`: `TextStyle(height: 1.2)` for the `Log In` label to preserve descender space.
- Validation: `flutter analyze lib/screens/welcome_screen.dart` passes with no issues.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, start backend + mobile app)

- Executor started backend successfully from `backend` using `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
- Backend runtime confirmed healthy (`Uvicorn running on http://0.0.0.0:8000`, startup complete).
- Executor detected physical Android device via Flutter (`974cd4fd0506`) and attempted `flutter run -d 974cd4fd0506`.
- Mobile launch is currently blocked by Windows symlink requirement: Flutter output says "Building with plugins requires symlink support" and requests enabling Developer Mode.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (start backend + mobile app blocker)

- Please enable Windows Developer Mode once: run `start ms-settings:developers` and turn on **Developer Mode**.
- After you confirm it is enabled, I will immediately rerun `flutter run -d 974cd4fd0506` and keep it running on your phone.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, start backend + mobile app retry)

- Retried mobile launch after blocker step: `flutter run -d 974cd4fd0506` now succeeds.
- Flutter app built (`app-debug.apk`), installed on device `21061119AG`, and entered live debug session (hot reload/hot restart keys available).
- Backend remains running on `http://0.0.0.0:8000`.
- Runtime log confirms app is attempting backend usage from saved LAN URL: `http://192.168.10.8:8000/api`.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (start backend + mobile app milestone)

- Milestone complete for this step: backend + mobile app are both running.
- Please do a quick manual check on phone (open app, try login or any API-backed screen) and confirm everything is working end-to-end; after your confirmation, Planner can mark this task complete.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, mobile UI/data fixes batch)

- **Community feed photo first-paint fix** (`mobile/lib/screens/community_screen.dart`): added background hydration for posts that have `hasImage=true` but no inline bytes, so feed cards load uploaded images without requiring first tap.
- **Community reply sheet overflow fix** (`mobile/lib/screens/community_screen.dart`): adjusted draggable sheet max size and composer bottom padding to include keyboard insets; this targets the `BOTTOM OVERFLOWED` issue while replying.
- **Shop by Category image fix** (`mobile/lib/screens/category_browse_screen.dart`, `mobile/lib/screens/home_tab.dart`, `mobile/lib/screens/search/image_search_screen.dart`): normalized `image_path` values that already start with `data/` to avoid broken `.../data/data/...` URLs.
- **Wishlist/Compare immediate visibility fix** (`mobile/lib/services/wishlist_service.dart`, `mobile/lib/services/compare_service.dart`, `mobile/lib/screens/main_shell.dart`): persist local copy even when logged-in, merge local+server lists on read, and force tab refresh keys when opening Saved/Compare tabs.
- **Home header + bell notifications** (`mobile/lib/screens/home_tab.dart`): replaced top title `Discover` with `DupeFinder`; added bell icon that opens a recent notifications bottom sheet (with unread dot).
- **Profile cleanup** (`mobile/lib/screens/me_screen.dart`): removed `Saved Items` row from profile menu.
- **Validation**: `ReadLints` on edited files shows no new linter errors; `flutter analyze` reports only info-level warnings in project files (no compile errors introduced by this batch).

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (mobile UI/data fixes batch)

- Please hot-restart and verify these exact flows on device:
  1. Community post image appears on feed without tapping first.
  2. Reply input in community sheet does not show bottom overflow stripe.
  3. Category pages (Bags/Accessories/Dresses/Jewellery) show product images.
  4. Add to Wishlist/Compare then open those tabs immediately (without app restart) and confirm items are visible.
  5. Home top title shows `DupeFinder`, and bell opens recent notifications list.
  6. `Saved Items` row is removed from Profile.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, follow-up fixes for remaining two issues)

- **Shop-by-category images still missing**: strengthened URL resolver logic in `category_browse_screen.dart`, `home_tab.dart`, and `search/image_search_screen.dart`:
  - if `image_path` is already absolute `http/https`, now always route through `/api/products/image-proxy`
  - if `image_path` starts with `/` or `data/`, now normalize both safely to avoid malformed `/data/...` URLs
- **Community reply overlay still occurring**: updated `_PostDetailSheet` layout in `community_screen.dart` so the top post block is in a `Flexible` + `SingleChildScrollView`; this lets content shrink/scroll under tight keyboard height instead of forcing RenderFlex overflow.
- **Validation**: `ReadLints` on updated files shows no lint errors after this follow-up patch.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (follow-up verification)

- Please do one **hot restart** and re-test:
  1. Open each Shop-by-Category page (`Dresses`, `Bags`, `Accessories`, `Jewellery`) and verify images now render.
  2. Open a community post and type a reply with keyboard open; verify no yellow/black bottom overflow appears.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, category image root-cause patch)

- Investigated live `/api/products/shop-browse` payload: records include both `image_path` and valid CDN `image_url`.
- Root cause: mobile resolver still preferred `image_path` first; local files are often unavailable on device/backend storage, so cards showed placeholders.
- Fix applied in `category_browse_screen.dart`, `home_tab.dart`, and `search/image_search_screen.dart`: now **prefer `image_url` first** (proxied via `/api/products/image-proxy`), fallback to normalized local `image_path`.
- Community follow-up: reduced composer bottom inflation in `_PostDetailSheet` (`community_screen.dart`) so reply bar no longer over-expands with keyboard.
- App restarted on device after patch; Flutter debug session is active and ready for manual verification.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, Home bell deep-link behavior)

- Implemented Home bell functional flow with minimal-scope edits:
  - `mobile/lib/screens/home_tab.dart`
  - `mobile/lib/screens/main_shell.dart`
- Home bell now:
  - polls recent notifications every 20s (silent refresh),
  - shows unread red dot based on `isRead == false`,
  - opens notification list bottom sheet,
  - on notification tap: closes sheet, marks notification read, and deep-links to Community post/reply via existing MainShell navigation callback.
- Reused existing `MainShell._openCommunityFromNotification` flow to avoid changing Community navigation logic.
- Validation:
  - `ReadLints` reports no lint errors in edited files.
  - `flutter analyze` on edited files shows only existing info-level const suggestions; no build-blocking issues.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (Home bell deep-link verification)

- Please verify this flow on device:
  1. Trigger a new community notification (reply/interaction),
  2. Open Home bell and tap that notification,
  3. Confirm app navigates to Community and opens the related post/reply.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, Admin Auto Sync: cancel + batched DB save)

- **Backend** (`backend/app/api/routes/admin_new.py`):
  - `POST /scraping/start` accepts optional `product_batch_size` (clamped 5–200, default 50); job document includes `cancel_requested`, phase/batch fields.
  - `POST /scraping/cancel/{job_id}` sets cooperative cancel (honored before next URL or before next save batch).
  - Mongo persistence uses the same Pass 1→2→3 logic as before, applied per batch via `_persist_product_batches_for_job`; `_flush_scraping_job_progress_mongo` updates history after each batch.
  - Cancelled jobs end with `status: cancelled`, no FashionCLIP reindex task started; full success path unchanged except extra progress fields.
- **Frontend** (`frontend-app/src/components/admin/ScrapingManagement.jsx`): batch size control, Cancel job button, phase + dual progress (brands + save batches), `cancelled` status handling and history badge color.
- **Validation**: `python -m py_compile` on `admin_new.py` OK; `ReadLints` clean on edited files.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (Admin scraping cancel/batch)

- Planner/user: please run one full scrape (no cancel) to confirm behavior matches pre-change, then a cancel mid-save-batch and confirm DB has partial brand data and history shows `cancelled`.
### Planner Update — Apr 20, 2026 (Mobile tab header dedup + Home top cleanup)

- **Problem analysis**: duplicate tab wording is caused by `MainShell` top `AppBar` titles plus each tab’s own embedded heading. Home top section is visually busy (`Discover`, tagline, tune icon, and search bar) and does not match requested app-name-only style.
- **Plan step 1 (Home header)**: simplify Home top to a compact branded strip with only `DupeFinder` in a suitable display font and theme-consistent gradient background.
- **Plan step 2 (Tab dedup)**: remove `MainShell` app bar titles for tab pages so each tab has one clear heading source (its own body), eliminating repeated “Find similar / Wishlist / Compare / Community / Me/Profile”.
- **Plan step 3 (Validation)**: run Flutter analyzer for touched files and manually verify each tab for single-title, cleaner presentation.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, tab header dedup cleanup)

- Implemented Home top cleanup in `mobile/lib/screens/home_tab.dart`: removed `Discover` block, tagline, tune icon, and top search bar; replaced with a concise themed header showing only `DupeFinder` in a display font.
- Implemented dedup in `mobile/lib/screens/main_shell.dart`: removed shell-level `AppBar` titles so tab pages do not repeat labels already shown in-tab (`Find Similar`, `Wishlist`, `Compare`, `Community`, `Profile`).
- Validation run: `flutter analyze` over touched/related tab screens reported info-level hints only (no compile errors).

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (tab header dedup cleanup)

- Please hot-restart and verify Home now shows only branded app name at the top, and Search/Saved/Compare/Community/Me no longer display duplicated tab wording.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, status-bar overlap fix)

- User reported tab labels were overlapping with the mobile status bar after shell app-bar removal. Added explicit top safe-area handling to embedded tab screens:
  - `search/image_search_screen.dart`: embedded mode now wrapped with `SafeArea(top: true, bottom: false)`.
  - `community_screen.dart`: body wrapped with `SafeArea(top: widget.embedded, bottom: false)` so embedded header starts below status bar.
  - `me_screen.dart`: top list padding now includes dynamic `MediaQuery.paddingOf(context).top`.
- Validation: analyzer run on touched files completed with existing info-level hints only (no compile errors).

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (status-bar overlap fix)

- Please hot-restart and verify `Find Similar`, `Community`, and `Profile` headings are now fully below the device status bar/notch with no overlap/smudging.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, wishlist/compare labels)

- Added explicit top labels for tabs that were missing after shell app-bar removal:
  - `wishlist_screen.dart`: top `Wishlist` heading with safe top inset spacing.
  - `compare_screen.dart`: top `Compare` heading with safe top inset spacing.
- Both screens now show heading first, then content below (loading / empty / populated states), matching the pattern of other tabs.
- Removed duplicate in-body heading text in empty states so labels are not repeated.
- Validation: analyzer run on both files returns info-level hints only (no compile errors).

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, Find Similar top cleanup + center upload)

- `search/image_search_screen.dart` updated per user request:
  - removed the top tagline `Upload or take a photo to discover dupes`.
  - in embedded initial state, moved upload card to center of available screen area.
- Kept behavior unchanged once an image is selected or results/errors appear (normal scroll flow resumes).
- Validation: analyzer reports only pre-existing info-level hint (`use_build_context_synchronously`), no compile errors.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, home/category image load + prefetch)

- Investigated missing images in Home **Trending Dupes** and category browse lists. Root issue: image URLs can come back as localhost-like or relative paths that are invalid on physical phones.
- Updated URL normalization in:
  - `mobile/lib/screens/home_tab.dart`
  - `mobile/lib/screens/category_browse_screen.dart`
  to retarget localhost hosts (`localhost`, `127.0.0.1`, `10.0.2.2`) to the app’s currently resolved backend origin and correctly handle relative paths.
- Added image warm prefetch in both screens for stable lists (`trending` and category browse items) via `precacheImage(CachedNetworkImageProvider(...))` to reduce empty/late-loading image placeholders.
- Switched category item thumbnails from plain `Image.network` to `CachedNetworkImage` with loading/error widgets for consistent caching + fallback behavior.
- Validation: analyzer on touched files reports info-level hints only (no compile errors).

### Planner Update — Apr 20, 2026 (Home/Category image 404 root cause + fix plan)

- **Observed runtime evidence**: mobile logs show repeated `404` for local static files like `/data/product_images/<hash>.webp` on LAN host. This confirms frontend URL formatting is no longer primary blocker; server cannot find files at requested static path.
- **Root cause hypothesis**:
  1. Mongo documents contain `image_path` values under `product_images/...` for many items.
  2. Some corresponding files are missing on disk in served `data/product_images` (likely legacy/stale DB paths or incomplete historic downloads).
  3. Home/Category API currently returns that missing `image_path` without server-side existence validation, so client tries dead URL and gets 404.

- **Planned minimal backend-first fix**:
  1. Add server-side image resolver in `products.py` used by `shop_browse`:
     - if `image_path` exists on disk, return `/data/<image_path>`.
     - else if external `image_url` exists, return proxied `/api/products/image-proxy?url=...`.
     - else return empty and let client placeholder show.
  2. Include explicit field like `image_src` (resolved URL) in `shop_browse` response so mobile no longer guesses.
  3. Keep existing `image_path` and `image_url` in response for compatibility.
  4. Optional fast repair path: background attempt to redownload missing local images for records where `image_path` file is missing but `image_url` exists.

- **Extended plan (same fix scope): audit + replace broken-image dupes in Trending/Category**
  5. Add an image-health filter in `shop_browse` query/selection flow:
     - candidate is **valid** if:
       - local `image_path` exists on disk, OR
       - external `image_url` is present and passes URL sanity checks (non-loader/non-placeholder).
     - candidate is **invalid** if neither condition is true.
  6. When building response items for each slot (`dresses`, `bags`, `accessories`, `jewelry`):
     - skip invalid candidates,
     - continue scanning older/newer docs until reaching requested `limit`,
     - return best available valid-image items instead of broken-image items.
  7. Add lightweight diagnostics in response metadata for planning/debugging:
     - counts such as `considered`, `valid_with_local`, `valid_with_proxy`, `skipped_missing_image`.
     - do not expose internal filesystem paths in response.
  8. Mobile behavior remains simple:
     - prefer backend `image_src`,
     - fallback to existing fields only for legacy responses.
     - no client-side replacement heuristics once backend filtering is in place.

- **Success criteria**:
  - Home `Trending Dupes` and category browse show images without repeated 404 spam for missing `/data/product_images/...`.
  - For products with broken local files but valid source URL, proxy image displays successfully.
  - Analyzer/tests unchanged for mobile; backend route responds with stable fields.
  - `shop_browse` returns full `limit` with valid-image products whenever enough valid candidates exist in DB.
  - Broken-image products are automatically excluded from Trending/Category lists and replaced by valid-image alternatives in the same slot.
  - Logs/metadata confirm how many items were skipped and replaced due to image issues.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (plan approval: backend image resolver)

- Planner recommends implementing backend `shop_browse` image existence check + proxy fallback + invalid-image replacement filtering next, then wiring mobile to prefer `image_src` from API. Please confirm to proceed with execution.


### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, Shop Browse Image Health)

- Implemented backend image resolver in ackend/app/api/routes/products.py for /api/products/shop-browse to return only products with resolvable images.
- Added image_src response field per item with precedence:
  - local file /data/... when image_path exists on disk
  - proxy endpoint /api/products/image-proxy?url=... when external image URL is valid
  - candidate skipped if no usable image exists
- Added debug-friendly response diagnostics in image_stats: considered, alid_with_local, alid_with_proxy, skipped_missing_image.
- Updated mobile image URL resolvers in:
  - mobile/lib/screens/home_tab.dart
  - mobile/lib/screens/category_browse_screen.dart
  to prefer backend-provided image_src first, then fallback to existing legacy fields.
- Validation in progress: run Python compile check + Flutter analyze on changed screens.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (Shop Browse Image Health)

- Milestone implementation complete for backend + mobile wiring.
- After validation commands pass, please test on device:
  1. Home -> Trending Dupes images
  2. Home -> Category chip -> category browse images
  3. Confirm missing-image products are replaced by valid-image alternatives (list remains filled up to limit when available).

### Lessons

- For mixed local/remote product media, returning a single server-resolved image_src from backend reduces repeated mobile-side URL heuristics and makes debugging missing-image inventory easier.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, Trending Dupes MIME diagnosis)

- Investigated Home Trending-only image failures by probing `/api/products/shop-browse` item-by-item.
- Confirmed specific trending dress product IDs include local `.webp` files (examples: `69b0ad2b9a535081b9f34f10`, `69b0ad379a535081b9f34f40`).
- Root cause identified on Windows backend host: `.webp` static files are served as `text/plain` instead of `image/webp`, which can break image rendering in mobile.
- Implemented backend MIME registration fix in `backend/app/main.py` before static mounting:
  - `mimetypes.add_type("image/webp", ".webp")`
  - `mimetypes.add_type("image/avif", ".avif")`

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (Trending Dupes MIME fix)

- Please restart backend so updated MIME mapping is applied, then hot restart mobile and verify Home `Trending Dupes`.
- If any specific card still fails after restart, share one product name from that card and executor will trace that exact record end-to-end.

### Current Status / Progress Tracking — Executor Update (Apr 20, 2026, wishlist/compare stale UI fix)

- User reported Saved/Compare did not update until full app restart after saving from image search.
- Root cause: each screen constructed its own `WishlistService` / `CompareService` with a 60s in-memory TTL cache; writes from Search updated one instance while Saved/Compare read another stale cache.
- Fix: added `invalidateAllMemoryCaches()` registry (weak refs) and call it after successful persistence so all instances drop memory cache and re-read prefs/server on next load.
- Files: `mobile/lib/services/wishlist_service.dart`, `mobile/lib/services/compare_service.dart`.
- Validation: `flutter analyze` on both files reports no issues.

### Executor's Feedback or Assistance Requests — Apr 20, 2026 (wishlist/compare stale UI fix)

- User confirmed behavior is fixed locally. Changes committed + pushed to GitHub (`8ae3ccb`).
