# DupeFinder - Affordable Alternatives for Luxury Wearables

![DupeFinder Logo](docs/logo.png)

> **Final Year Project**: An intelligent mobile/web application that helps users discover affordable, high-quality alternatives to luxury fashion products through AI-powered image search and recommendation.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

DupeFinder bridges the gap between luxury fashion admiration and affordability by:
- Providing intelligent image-based search for luxury alternatives
- Highlighting savings potential through price comparison
- Offering multi-level filtering (category, gender, city, size, budget)
- Creating a review-driven ecosystem for trust and community engagement
- Generating data-driven insights on consumer preferences

**Target Accuracy**: 80%+ in top-3 product matches

## ✨ Features

### User Features
- 📸 **Image-Based Search**: Upload or capture photos of luxury items
- 🔍 **Smart Matching**: AI-powered visual similarity search
- 💰 **Savings Insights**: Compare luxury vs. dupe prices
- ⭐ **Favorites & Wishlist**: Save products for later
- 📊 **Comparison Tool**: Side-by-side product comparison
- 💬 **Community Platform**: Request and share dupes
- ⭐ **Reviews & Ratings**: Community-driven product validation

### Admin Features
- 📦 **Product Management**: Bulk upload, edit, and organize catalog
- 📈 **Analytics Dashboard**: Engagement metrics and trends
- 🛡️ **Review Moderation**: Spam detection and approval system
- 👥 **User Management**: Account and permission management
- 🤖 **ML Monitoring**: Model performance tracking

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Mobile    │────▶│   Backend   │────▶│  PostgreSQL │
│  (Flutter)  │     │  (FastAPI)  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
┌─────────────┐            │             ┌─────────────┐
│     Web     │────────────┤            ▶│   MongoDB   │
│   (React)   │            │             │ (Embeddings)│
└─────────────┘            │             └─────────────┘
                           │
┌─────────────┐            │             ┌─────────────┐
│    Admin    │────────────┤            ▶│   ML Engine │
│ Dashboard   │            │             │   (PyTorch) │
└─────────────┘            │             └─────────────┘
                           │
                     ┌─────▼─────┐
                     │   Redis   │
                     │  (Cache)  │
                     └───────────┘
```

## 🛠️ Tech Stack

### Frontend
- **Web**: React 18.x
- **Mobile**: Flutter 3.x
- **Admin**: React 18.x with Recharts

### Backend
- **API**: FastAPI (Python)
- **Authentication**: JWT
- **File Upload**: Multipart

### Database
- **Relational**: PostgreSQL 15
- **Document**: MongoDB 7
- **Cache**: Redis 7

### Machine Learning
- **Framework**: PyTorch
- **Models**: ResNet50/EfficientNet
- **Vector Search**: FAISS
- **Image Processing**: OpenCV, Pillow

### DevOps
- **Containerization**: Docker & Docker Compose
- **CI/CD**: (To be configured)
- **Cloud**: AWS/GCP (planned)

## 📁 Project Structure

```
dupefinder/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Configuration
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── tests/             # Backend tests
│   └── main.py            # Entry point
│
├── frontend-app/          # React admin dashboard (Vite)
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components (AdminDashboard, AdminLogin)
│   │   ├── services/      # API services
│   │   └── styles/        # CSS styles
│   └── package.json
│
├── mobile/                # Flutter app
│   ├── lib/
│   │   ├── models/        # Data models
│   │   ├── screens/       # Screen widgets
│   │   ├── widgets/       # Reusable widgets
│   │   └── services/      # API services
│   └── pubspec.yaml
│
├── ml-engine/             # ML models
│   ├── models/            # Trained models
│   ├── preprocessing/     # Image preprocessing
│   ├── embeddings/        # Embedding generation
│   └── similarity/        # Similarity search
│
├── database/
│   └── schemas/           # Database schemas
│
├── docker/                # Dockerfiles
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── docker-compose.yml     # Docker services
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Flutter SDK 3.0+
- Docker & Docker Compose
- PostgreSQL 15+
- MongoDB 7+

### Quick Start with Docker

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/dupefinder.git
cd dupefinder
```

2. **Set up environment variables**:
```bash
cp backend/.env.example backend/.env
cp frontend-app/.env.example frontend-app/.env  # If exists
# Edit .env files with your configurations
```

3. **Start all services**:
```bash
docker-compose up -d
```

4. **Access the applications**:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Dashboard: http://localhost:5173 (run `cd frontend-app && npm run dev`)

### Manual Setup

See individual README files in each module:
- [Backend Setup](backend/README.md)
- [Mobile Setup](mobile/README.md)
- [ML Engine Setup](ml-engine/README.md)
- Admin Dashboard: See `frontend-app/` directory

## 💻 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Admin Dashboard Development
```bash
cd frontend-app
npm install
npm run dev
```

### Mobile Development
```bash
cd mobile
flutter pub get
flutter run
```

### ML Engine Development
```bash
cd ml-engine
pip install -r requirements.txt
# Run training/testing scripts
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Admin Dashboard tests (if configured)
cd frontend-app
npm test

# Mobile tests
cd mobile
flutter test
```

## 📊 Database Setup

### Initialize PostgreSQL
```bash
psql -U postgres -f database/schemas/postgresql_schema.sql
```

### Initialize MongoDB
```bash
# MongoDB schemas are applied automatically
# See database/schemas/mongodb_schema.js for reference
```

## 📈 Project Milestones

- [ ] Phase 1: Project Setup & Infrastructure ✓
- [ ] Phase 2: Backend Foundation
- [ ] Phase 3: Frontend Foundation
- [ ] Phase 4: ML Engine Implementation
- [ ] Phase 5: Admin Dashboard
- [ ] Phase 6: Testing & Documentation
- [ ] Phase 7: Deployment
- [ ] Phase 8: Final Presentation

## 🤝 Contributing

This is a Final Year Project. Contributions are currently limited to team members.

## 📄 License

[To be determined]

## 👥 Team

- [Your Name] - Project Lead & Full Stack Developer
- [Team Member] - ML Engineer
- [Team Member] - Mobile Developer
- [Team Member] - UI/UX Designer

## 📞 Contact

For questions or support, please contact: [your-email@example.com]

---

**Note**: This project is developed as part of a Final Year Project (FYP) requirement.

