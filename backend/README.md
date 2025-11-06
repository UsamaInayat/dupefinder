# DupeFinder Backend

FastAPI-based backend service for the DupeFinder application.

## Features

- RESTful API for product catalog management
- Image-based search and similarity matching
- User authentication and authorization
- Review and rating system
- Analytics and insights
- Admin functionalities

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/         # API route handlers
│   ├── core/               # Core configurations
│   ├── models/             # Database models
│   ├── services/           # Business logic services
│   └── utils/              # Utility functions
├── tests/                  # Test files
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

## Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- MongoDB 6+
- Redis (optional, for caching)

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

4. Run database migrations:
```bash
# Commands will be added when migration system is implemented
```

5. Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Products
- `GET /api/products` - List products
- `GET /api/products/{id}` - Get product details
- `POST /api/products` - Create product (admin)
- `PUT /api/products/{id}` - Update product (admin)
- `DELETE /api/products/{id}` - Delete product (admin)

### Search
- `POST /api/search/image` - Search by image upload
- `GET /api/search/text` - Text-based search
- `GET /api/search/similar/{id}` - Find similar products

### Reviews
- `GET /api/reviews/{product_id}` - Get product reviews
- `POST /api/reviews` - Create review
- `PUT /api/reviews/{id}` - Update review
- `DELETE /api/reviews/{id}` - Delete review

### Analytics
- `GET /api/analytics/trends` - Get trending products
- `GET /api/analytics/savings` - User savings statistics
- `GET /api/analytics/dashboard` - Admin dashboard data

## Testing

```bash
pytest
```

## Development

- Follow PEP 8 style guidelines
- Write tests for new features
- Update API documentation
- Use type hints

## License

[To be determined]

