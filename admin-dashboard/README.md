# DupeFinder Admin Dashboard

React-based administrative dashboard for managing the DupeFinder platform.

## Features

- **Product Management**
  - Bulk upload/import
  - Edit product details
  - Manage categories and tags
  - Duplicate detection and cleanup

- **Analytics & Insights**
  - User engagement metrics
  - Search trends
  - Popular products
  - Revenue/savings tracking
  - Geographic heatmaps

- **Review Moderation**
  - Review approval/rejection
  - Spam detection
  - User reputation management

- **User Management**
  - View user accounts
  - Manage permissions
  - Activity monitoring

- **System Management**
  - ML model monitoring
  - API performance
  - Database health
  - Error logs

## Project Structure

```
admin-dashboard/
├── public/
├── src/
│   ├── components/        # Reusable UI components
│   ├── pages/             # Dashboard pages
│   ├── services/          # API services
│   ├── utils/             # Utility functions
│   ├── App.js
│   └── index.js
└── package.json
```

## Setup Instructions

### Prerequisites
- Node.js 16+
- Admin API access

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Add your admin API endpoint
```

3. Start development server:
```bash
npm start
```

Access at: http://localhost:3001

## Key Pages

- **Dashboard** - Overview and key metrics
- **Products** - Product catalog management
- **Analytics** - Data visualization and insights
- **Reviews** - Review moderation
- **Users** - User management
- **Settings** - System configuration

## Authentication

Admin dashboard requires authentication with elevated privileges.

## Data Visualization

Using Recharts for charts and graphs.

## Deployment

```bash
npm run build
```

## Security

- Role-based access control
- Audit logging
- Secure API communication
- Session management

## License

[To be determined]

