# DupeFinder Project - Files Documentation

This document provides a one-line description of each file in the project (Backend, Frontend, and Mobile).

---

## 📁 Backend Files

### Root Level
- `backend/main.py` - Legacy main entry point for FastAPI application
- `backend/start_server.py` - Server startup script with uvicorn configuration
- `backend/create_admin.py` - Script to create admin user in database
- `backend/init_auth_collections.py` - Initializes authentication collections in MongoDB
- `backend/requirements.txt` - Python dependencies list for backend
- `backend/README.md` - Backend documentation and setup instructions

### app/ Directory
- `backend/app/__init__.py` - Python package initialization for app module
- `backend/app/main.py` - Main FastAPI application entry point with CORS and routing

### app/api/routes/
- `backend/app/api/routes/__init__.py` - Package initialization for API routes
- `backend/app/api/routes/admin.py` - Admin dashboard API endpoints (legacy)
- `backend/app/api/routes/admin_new.py` - New admin dashboard API endpoints with 4 modules (User Management, Product Catalogue, ML Training, Auto Sync)
- `backend/app/api/routes/auth.py` - User authentication endpoints (login, signup, JWT tokens)
- `backend/app/api/routes/database.py` - Database initialization and management endpoints
- `backend/app/api/routes/health.py` - Health check endpoints for monitoring system status
- `backend/app/api/routes/products.py` - Product CRUD operations and management endpoints
- `backend/app/api/routes/search.py` - Image-based product search endpoints using ML embeddings

### app/core/
- `backend/app/core/__init__.py` - Package initialization for core module
- `backend/app/core/config.py` - Application configuration settings and environment variables
- `backend/app/core/database.py` - MongoDB connection management and database utilities
- `backend/app/core/security.py` - Security utilities for password hashing and JWT tokens

### app/dependencies/
- `backend/app/dependencies/auth.py` - Authentication dependency functions for route protection

### app/models/
- `backend/app/models/__init__.py` - Package initialization for models
- `backend/app/models/admin.py` - Pydantic models for admin-related data structures
- `backend/app/models/auth_schemas.py` - Pydantic schemas for authentication requests/responses
- `backend/app/models/mongodb_models.py` - MongoDB document models and schemas
- `backend/app/models/schemas.py` - General Pydantic schemas for API requests/responses
- `backend/app/models/user.py` - User data models and schemas

### app/services/
- `backend/app/services/__init__.py` - Package initialization for services
- `backend/app/services/category_normalizer.py` - Service to normalize and standardize product categories
- `backend/app/services/email_service.py` - Email sending service for notifications
- `backend/app/services/mongodb_service.py` - MongoDB operations service
- `backend/app/services/scraper_service.py` - Web scraping service for extracting product data from Excel files

### app/utils/
- `backend/app/utils/__init__.py` - Package initialization for utils
- `backend/app/utils/auth.py` - Authentication utility functions (token creation, validation)

---

## 📁 Frontend Files

### Root Level
- `frontend-app/package.json` - Node.js dependencies and scripts configuration
- `frontend-app/vite.config.js` - Vite build tool configuration
- `frontend-app/index.html` - HTML entry point for the React application

### src/
- `frontend-app/src/main.jsx` - React application entry point that renders AppWithAuth
- `frontend-app/src/index.css` - Global CSS styles for the application
- `frontend-app/src/App.jsx` - Main App component with image search functionality
- `frontend-app/src/AppWithAuth.jsx` - Authentication wrapper component that handles login state

### src/components/admin/
- `frontend-app/src/components/admin/MLTraining.jsx` - ML model training interface component for admin dashboard
- `frontend-app/src/components/admin/Overview.jsx` - Admin dashboard overview component showing statistics
- `frontend-app/src/components/admin/ProductManagement.jsx` - Product catalogue management component (import, delete, repair links)
- `frontend-app/src/components/admin/ScrapingManagement.jsx` - Auto sync/rescraping management component with brand selection and history
- `frontend-app/src/components/admin/UserManagement.jsx` - User management component for admin to view and manage users

### src/context/
- `frontend-app/src/context/AuthContext.jsx` - React context for managing authentication state across the app

### src/pages/
- `frontend-app/src/pages/AdminDashboard.jsx` - Main admin dashboard page with navigation and module routing
- `frontend-app/src/pages/AdminDashboardPro.jsx` - Alternative/legacy admin dashboard page
- `frontend-app/src/pages/AdminLogin.jsx` - Admin login page component
- `frontend-app/src/pages/Dashboard.jsx` - User dashboard page after login
- `frontend-app/src/pages/Login.jsx` - User login page component
- `frontend-app/src/pages/Signup.jsx` - User registration/signup page component

### src/styles/
- `frontend-app/src/styles/AdminDashboard.css` - CSS styles for admin dashboard (black & white theme)
- `frontend-app/src/styles/AdminPro.css` - CSS styles for alternative admin dashboard
- `frontend-app/src/styles/Auth.css` - CSS styles for authentication pages (login, signup)
- `frontend-app/src/styles/Dashboard.css` - CSS styles for user dashboard

---

## 📁 Mobile Files

### Root Level
- `mobile/pubspec.yaml` - Flutter project dependencies and configuration
- `mobile/pubspec.lock` - Locked versions of Flutter dependencies
- `mobile/analysis_options.yaml` - Dart code analysis configuration
- `mobile/README.md` - Mobile app documentation

### lib/
- `mobile/lib/main.dart` - Flutter application entry point and main app widget

### android/
- `mobile/android/build.gradle.kts` - Android build configuration (Kotlin DSL)
- `mobile/android/gradle.properties` - Android Gradle properties
- `mobile/android/settings.gradle.kts` - Android Gradle settings

### test/
- `mobile/test/widget_test.dart` - Flutter widget testing file

---

## 📁 ML Engine Files

### Root Level
- `ml-engine/__init__.py` - Package initialization for ML engine
- `ml-engine/config.yaml` - ML engine configuration file
- `ml-engine/requirements.txt` - Python dependencies for ML engine
- `ml-engine/README.md` - ML engine documentation

### ml-engine/embeddings/
- `ml-engine/embeddings/__init__.py` - Package initialization for embeddings module
- `ml-engine/embeddings/feature_extractor.py` - Feature extraction service using ResNet50/EfficientNet models

### ml-engine/preprocessing/
- `ml-engine/preprocessing/__init__.py` - Package initialization for preprocessing module
- `ml-engine/preprocessing/image_preprocessor.py` - Image preprocessing utilities (resize, normalize, etc.)

### ml-engine/similarity/
- `ml-engine/similarity/__init__.py` - Package initialization for similarity module
- `ml-engine/similarity/similarity_searcher.py` - FAISS-based similarity search implementation

---

## 📁 Configuration & Setup Files

### Root Level
- `README.md` - Main project documentation and overview
- `docker-compose.yml` - Docker Compose configuration for multi-container setup
- `.gitignore` - Git ignore rules for the project

### docker/
- `docker/Dockerfile.backend` - Dockerfile for building backend container
- `docker/Dockerfile.frontend` - Dockerfile for building frontend container
- `docker/Dockerfile.admin` - Dockerfile for building admin dashboard container

### scripts/
- `scripts/setup.sh` - Unix/Mac setup script for project initialization
- `scripts/setup.ps1` - Windows PowerShell setup script for project initialization

### database/schemas/
- `database/schemas/mongodb_schema.js` - MongoDB database schema definitions
- `database/schemas/postgresql_schema.sql` - PostgreSQL database schema definitions
- `database/schemas/sqlite_schema.sql` - SQLite database schema definitions

### docs/
- `docs/API_DOCUMENTATION.md` - API endpoints documentation
- `docs/ARCHITECTURE.md` - System architecture documentation
- `docs/PROJECT_STRUCTURE.md` - Detailed project structure documentation

---

## 📁 Data Files

### data/
- `data/product_catalog.csv` - Product catalog CSV file
- `data/embeddings/product_embeddings.pkl` - Pre-computed product embeddings (pickle format)
- `data/embeddings/test_embeddings.pkl` - Test embeddings file
- `data/similarity/product_search_index.pkl` - FAISS search index for products
- `data/similarity/test_index.pkl` - Test search index file

### Root Level Data Files
- `local_brands_links.csv` - CSV file containing local brand links for scraping
- `men dataset.xlsx` - Excel file with men's fashion product data
- `women links dataset.xlsx` - Excel file with women's fashion product links
- `Untitled spreadsheet - Sheet1.csv` - Additional product data CSV file

---

## 📁 Other Directories

### admin-dashboard/
- `admin-dashboard/package.json` - Separate admin dashboard package configuration
- `admin-dashboard/src/App.js` - Admin dashboard React app entry point
- `admin-dashboard/src/index.js` - Admin dashboard React app initialization
- `admin-dashboard/README.md` - Admin dashboard documentation

### frontend/
- `frontend/package.json` - Alternative frontend package configuration
- `frontend/src/App.js` - Alternative frontend React app entry point
- `frontend/src/index.js` - Alternative frontend React app initialization
- `frontend/README.md` - Frontend documentation

### mobile-app/
- `mobile-app/App.js` - React Native mobile app entry point
- `mobile-app/package.json` - React Native mobile app dependencies

### tests/
- `tests/test_e2e_workflow.py` - End-to-end workflow testing script

---

## Summary

- **Backend Files**: 33 Python files
- **Frontend Files**: 15 JSX/JS files + 4 CSS files
- **Mobile Files**: 1 Dart file (main.dart) + configuration files
- **ML Engine Files**: 6 Python files
- **Configuration Files**: Docker, setup scripts, schemas
- **Documentation Files**: README files and markdown documentation

**Total Project Files**: 100+ files across backend, frontend, mobile, ML engine, and configuration directories.

