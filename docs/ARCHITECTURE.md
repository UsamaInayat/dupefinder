# DupeFinder Architecture

## Overview

DupeFinder is built using a modern microservices architecture with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
├──────────────┬──────────────┬─────────────────────────────┤
│   Web App    │  Mobile App  │    Admin Dashboard           │
│   (React)    │  (Flutter)   │      (React)                 │
└──────┬───────┴──────┬───────┴──────────┬──────────────────┘
       │              │                   │
       └──────────────┼───────────────────┘
                      │
       ┌──────────────▼──────────────┐
       │      API Gateway             │
       │      (FastAPI)              │
       └──────────────┬──────────────┘
                      │
       ┌──────────────┴──────────────┐
       │                             │
┌──────▼────────┐           ┌────────▼─────────┐
│   Business    │           │   ML Engine      │
│   Logic Layer │           │   (PyTorch)      │
└──────┬────────┘           └────────┬─────────┘
       │                             │
┌──────┴────────┬──────────┬────────┴─────────┐
│               │          │                  │
▼               ▼          ▼                  ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │ MongoDB  │ │  Redis   │ │  FAISS   │
│          │ │          │ │  Cache   │ │  Index   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## Components

### 1. Frontend Layer

#### Web Application (React)
- **Purpose**: Primary user interface for desktop/laptop users
- **Key Features**:
  - Image upload and search
  - Product browsing and filtering
  - User authentication
  - Favorites management
  - Product comparison
  - Community features

#### Mobile Application (Flutter)
- **Purpose**: Native mobile experience for iOS and Android
- **Key Features**:
  - Camera integration for instant capture
  - Image upload from gallery
  - Push notifications
  - Offline favorites
  - Location-based filtering

#### Admin Dashboard (React)
- **Purpose**: Administrative interface for platform management
- **Key Features**:
  - Product catalog management
  - Review moderation
  - Analytics and insights
  - User management
  - System monitoring

### 2. Backend Layer

#### API Server (FastAPI)
- **Purpose**: RESTful API server handling all business logic
- **Components**:
  - Authentication & Authorization (JWT)
  - Product management endpoints
  - Search and recommendation APIs
  - User management
  - Review system
  - Analytics engine

#### ML Engine (Python/PyTorch)
- **Purpose**: Image similarity and recommendation engine
- **Components**:
  - Image preprocessing
  - Feature extraction (ResNet/EfficientNet)
  - Embedding generation
  - FAISS similarity search
  - Model training pipeline

### 3. Data Layer

#### PostgreSQL
- **Purpose**: Primary relational database
- **Stores**:
  - User accounts and profiles
  - Product catalog
  - Reviews and ratings
  - Search history
  - Community posts

#### MongoDB
- **Purpose**: Document store for unstructured data
- **Stores**:
  - Product embeddings
  - Image metadata
  - Analytics events
  - ML model logs
  - User search analytics

#### Redis
- **Purpose**: Caching and session management
- **Uses**:
  - Session storage
  - API response caching
  - Rate limiting
  - Real-time data

#### FAISS
- **Purpose**: Vector similarity search
- **Uses**:
  - Fast nearest neighbor search
  - Image embedding indexing
  - Efficient similarity computation

## Data Flow

### Image Search Flow

```
1. User uploads image
   ↓
2. Frontend sends image to API
   ↓
3. API preprocesses image
   ↓
4. ML Engine extracts features
   ↓
5. Generate embedding vector
   ↓
6. FAISS finds similar vectors
   ↓
7. Fetch product details from PostgreSQL
   ↓
8. Apply filters and ranking
   ↓
9. Return results to frontend
   ↓
10. Log search analytics to MongoDB
```

### Product Creation Flow

```
1. Admin uploads product
   ↓
2. API validates data
   ↓
3. Store product in PostgreSQL
   ↓
4. Upload image to storage
   ↓
5. ML Engine processes image
   ↓
6. Generate embedding
   ↓
7. Store embedding in MongoDB
   ↓
8. Update FAISS index
   ↓
9. Return confirmation
```

## Security

### Authentication
- JWT-based authentication
- Refresh token mechanism
- Role-based access control (RBAC)

### Data Protection
- Password hashing (bcrypt)
- HTTPS/TLS encryption
- SQL injection prevention (parameterized queries)
- Input validation and sanitization
- Rate limiting

## Scalability

### Horizontal Scaling
- Stateless API servers
- Load balancing
- Database read replicas
- CDN for static assets

### Caching Strategy
- Redis for hot data
- Browser caching
- API response caching
- Image CDN caching

## Monitoring

### Application Monitoring
- API performance metrics
- Error tracking
- User analytics
- ML model accuracy tracking

### Infrastructure Monitoring
- Database performance
- Server resource usage
- API response times
- Cache hit rates

## Deployment

### Containerization
- Docker containers for each service
- Docker Compose for local development
- Kubernetes for production (planned)

### CI/CD Pipeline
- Automated testing
- Linting and code quality checks
- Automated deployment
- Rolling updates

## Future Enhancements

1. **Microservices Split**: Separate ML engine into dedicated service
2. **Message Queue**: Add RabbitMQ/Kafka for async processing
3. **CDN Integration**: AWS CloudFront for image delivery
4. **GraphQL**: Optional GraphQL API
5. **Real-time Features**: WebSocket for live updates
6. **Multi-region**: Deploy across multiple regions

