#!/bin/bash

# DupeFinder Setup Script
# This script helps set up the development environment

echo "======================================"
echo "DupeFinder - Development Setup"
echo "======================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    echo "✓ Python 3 is installed: $(python3 --version)"
else
    echo "✗ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js is installed: $(node --version)"
else
    echo "✗ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Check Flutter
if command -v flutter &> /dev/null; then
    echo "✓ Flutter is installed: $(flutter --version | head -n 1)"
else
    echo "✗ Flutter is not installed. Please install Flutter SDK 3.0+"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed: $(docker --version)"
else
    echo "✗ Docker is not installed. Please install Docker"
fi

echo ""
echo "======================================"
echo "Setting up environment files..."
echo "======================================"

# Copy environment files
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env"
else
    echo "✓ backend/.env already exists"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "✓ Created frontend/.env"
else
    echo "✓ frontend/.env already exists"
fi

if [ ! -f admin-dashboard/.env ]; then
    cp admin-dashboard/.env.example admin-dashboard/.env
    echo "✓ Created admin-dashboard/.env"
else
    echo "✓ admin-dashboard/.env already exists"
fi

echo ""
echo "======================================"
echo "Installing dependencies..."
echo "======================================"

# Backend dependencies
echo "Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Admin dashboard dependencies
echo "Installing admin dashboard dependencies..."
cd admin-dashboard
npm install
cd ..

# Mobile dependencies
echo "Installing mobile dependencies..."
cd mobile
flutter pub get
cd ..

# ML engine dependencies
echo "Installing ML engine dependencies..."
cd ml-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env files with your configuration"
echo "2. Start services with: docker-compose up"
echo "3. Or run individual services:"
echo "   - Backend: cd backend && uvicorn main:app --reload"
echo "   - Frontend: cd frontend && npm start"
echo "   - Mobile: cd mobile && flutter run"
echo "   - Admin: cd admin-dashboard && npm start"
echo ""

