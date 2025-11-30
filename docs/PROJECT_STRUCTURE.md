# DupeFinder Project Structure

This document provides a complete overview of the project structure created for the DupeFinder FYP.

## Directory Tree

```
dupefinder/
├── .cursor/                          # Cursor IDE configuration
│   └── scratchpad.md                # Project planning and tracking
│
├── backend/                         # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/             # API route handlers
│   │   ├── core/                   # Core configurations
│   │   ├── models/                 # Database models
│   │   ├── services/               # Business logic
│   │   └── utils/                  # Utility functions
│   ├── tests/                      # Backend tests
│   ├── main.py                     # Application entry point
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Backend documentation
│
├── frontend-app/                    # React Admin Dashboard (Vite)
│   ├── src/
│   │   ├── components/            # UI components (admin modules)
│   │   ├── pages/                 # Page components (AdminDashboard, AdminLogin)
│   │   ├── services/              # API services
│   │   ├── styles/                # CSS styles
│   │   ├── context/               # React context
│   │   ├── App.jsx                # Main app component
│   │   ├── AppWithAuth.jsx        # Auth wrapper
│   │   └── main.jsx               # Entry point
│   ├── index.html                 # HTML template
│   ├── package.json               # Node dependencies
│   └── vite.config.js             # Vite configuration
│
├── mobile/                          # Flutter Mobile App
│   ├── lib/
│   │   ├── models/                # Data models
│   │   ├── screens/               # Screen widgets
│   │   ├── widgets/               # Reusable widgets
│   │   ├── services/              # API services
│   │   ├── utils/                 # Utilities
│   │   └── main.dart              # App entry point
│   ├── assets/                    # Assets (images, fonts)
│   ├── test/                      # Tests
│   ├── pubspec.yaml               # Flutter dependencies
│   └── README.md                  # Mobile documentation
│
├── ml-engine/                       # Machine Learning Engine
│   ├── preprocessing/             # Image preprocessing
│   ├── embeddings/                # Feature extraction
│   ├── similarity/                # Similarity search
│   ├── models/                    # Trained models
│   ├── data/                      # Training data
│   ├── config.yaml                # ML configuration
│   ├── requirements.txt           # Python dependencies
│   └── README.md                  # ML documentation
│
├── database/                        # Database Schemas
│   └── schemas/
│       ├── postgresql_schema.sql  # PostgreSQL tables
│       ├── mongodb_schema.js      # MongoDB collections
│       └── sqlite_schema.sql      # SQLite schema
│
├── docker/                          # Docker Configuration
│   ├── Dockerfile.backend         # Backend container
│   ├── Dockerfile.frontend        # Frontend container (legacy)
│   └── Dockerfile.admin           # Admin container (legacy)
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md            # System architecture
│   ├── API_DOCUMENTATION.md       # API endpoints
│   └── PROJECT_STRUCTURE.md       # This file
│
├── scripts/                         # Utility Scripts
│   ├── setup.sh                   # Unix/Mac setup
│   └── setup.ps1                  # Windows setup
│
├── .gitignore                       # Git ignore rules
├── docker-compose.yml              # Docker orchestration
└── README.md                       # Project overview
```

## File Count Summary

- **Total Files Created**: 44
- **Total Directories**: 70+
- **Python Files**: 14
- **JavaScript/React Files**: 6
- **Configuration Files**: 10
- **Documentation Files**: 7
- **Database Schema Files**: 2
- **Docker Files**: 4
- **Setup Scripts**: 2

## Module Breakdown

### Backend Module
- **Language**: Python
- **Framework**: FastAPI
- **Purpose**: RESTful API server
- **Files**: 10 (including __init__.py files)
- **Dependencies**: FastAPI, SQLAlchemy, PyTorch, etc.

### Frontend Module
- **Language**: JavaScript/React
- **Framework**: React 18.x
- **Purpose**: Web user interface
- **Files**: 6
- **Dependencies**: React, React Router, Axios, etc.

### Mobile Module
- **Language**: Dart
- **Framework**: Flutter
- **Purpose**: iOS/Android app
- **Files**: 2
- **Dependencies**: Flutter, Provider, HTTP, etc.

### ML Engine Module
- **Language**: Python
- **Framework**: PyTorch
- **Purpose**: Image similarity and recommendations
- **Files**: 5
- **Dependencies**: PyTorch, FAISS, OpenCV, etc.

### Admin Dashboard Module
- **Language**: JavaScript/React
- **Framework**: React 18.x
- **Purpose**: Administrative interface
- **Files**: 4
- **Dependencies**: React, Recharts, React Table, etc.

## Database Structure

### PostgreSQL Tables (Planned)
- users
- categories
- products
- product_images
- reviews
- favorites
- search_history
- user_savings
- community_posts
- community_replies

### MongoDB Collections (Planned)
- product_embeddings
- user_search_analytics
- image_metadata
- analytics_events
- ml_model_logs

## Setup Instructions

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd dupefinder

# Run setup script
# Windows:
.\scripts\setup.ps1

# Unix/Mac:
chmod +x scripts/setup.sh
./scripts/setup.sh

# Start with Docker
docker-compose up -d
```

### Manual Setup
See individual README.md files in each module for detailed setup instructions.

## Development Workflow

1. **Backend Development**
   - Navigate to `backend/`
   - Activate virtual environment
   - Run: `uvicorn main:app --reload`

2. **Frontend Development**
   - Navigate to `frontend/`
   - Run: `npm install && npm start`

3. **Mobile Development**
   - Navigate to `mobile/`
   - Run: `flutter pub get && flutter run`

4. **Admin Dashboard**
   - Navigate to `admin-dashboard/`
   - Run: `npm install && npm start`

## Key Features Implemented

### Infrastructure
✅ Complete directory structure
✅ Configuration files for all modules
✅ Docker containerization setup
✅ Database schema definitions
✅ Version control with Git
✅ Comprehensive documentation

### Code Skeleton
✅ Backend API entry point
✅ Admin Dashboard React app (frontend-app)
✅ Mobile Flutter app skeleton
✅ Python package structure (__init__.py files)

### Documentation
✅ Project README
✅ Module-specific READMEs
✅ Architecture documentation
✅ API documentation
✅ Setup scripts

## Next Steps

1. **Phase 2**: Implement backend API endpoints
2. **Phase 3**: Build frontend components
3. **Phase 4**: Develop ML engine
4. **Phase 5**: Create admin dashboard features
5. **Phase 6**: Testing and deployment

## Technology Stack

- **Backend**: FastAPI (Python)
- **Admin Dashboard**: React 18.x (Vite)
- **Mobile**: Flutter 3.x
- **ML**: PyTorch, FAISS
- **Databases**: PostgreSQL, MongoDB
- **Cache**: Redis
- **DevOps**: Docker, Docker Compose
- **Version Control**: Git

## Project Status

**Phase 1**: ✅ Complete (Project Setup & Infrastructure)
**Phase 2**: ⏳ Pending (Backend Foundation)
**Phase 3**: ✅ Complete (Admin Dashboard Foundation)
**Phase 4**: ⏳ Pending (ML Engine)
**Phase 5**: ⏳ Pending (Admin Dashboard)
**Phase 6**: ⏳ Pending (Testing & Deployment)

---

**Last Updated**: November 6, 2025
**Project**: DupeFinder FYP
**Status**: Phase 1 Complete - Codebase Structure Created

