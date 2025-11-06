# DupeFinder Frontend

React-based web application for DupeFinder.

## Features

- Image upload and search
- Product browsing and filtering
- User authentication
- Favorites and comparison
- Reviews and ratings
- Savings tracking
- Responsive design

## Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── assets/            # Images, fonts, etc.
│   ├── components/        # Reusable components
│   ├── pages/             # Page components
│   ├── services/          # API services
│   ├── styles/            # Global styles
│   ├── utils/             # Utility functions
│   ├── App.js             # Main app component
│   └── index.js           # Entry point
└── package.json           # Dependencies
```

## Setup Instructions

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your API endpoint
```

3. Start development server:
```bash
npm start
```

The app will open at: http://localhost:3000

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Key Pages

- **Home** - Landing page with search
- **Search Results** - Display matching products
- **Product Detail** - Detailed product view
- **Profile** - User profile and favorites
- **Comparison** - Side-by-side comparison
- **Auth** - Login/Register

## State Management

Using Zustand for lightweight state management.

## API Integration

API calls are centralized in `src/services/` directory.

## Styling

Using CSS Modules for component-scoped styles.

## Testing

```bash
npm test
```

## Deployment

```bash
npm run build
```

Build artifacts will be in the `build/` directory.

## License

[To be determined]

