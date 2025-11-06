# DupeFinder Setup Script for Windows
# PowerShell script to set up the development environment

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "DupeFinder - Development Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✓ Python is installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python is not installed. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Node.js
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "✓ Node.js is installed: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js is not installed. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check Flutter
if (Get-Command flutter -ErrorAction SilentlyContinue) {
    $flutterVersion = flutter --version | Select-Object -First 1
    Write-Host "✓ Flutter is installed: $flutterVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Flutter is not installed. Please install Flutter SDK 3.0+" -ForegroundColor Yellow
}

# Check Docker
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is installed: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Docker is not installed. Please install Docker Desktop" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setting up environment files..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Copy environment files
if (!(Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✓ Created backend\.env" -ForegroundColor Green
} else {
    Write-Host "✓ backend\.env already exists" -ForegroundColor Green
}

if (!(Test-Path "frontend\.env")) {
    Copy-Item "frontend\.env.example" "frontend\.env"
    Write-Host "✓ Created frontend\.env" -ForegroundColor Green
} else {
    Write-Host "✓ frontend\.env already exists" -ForegroundColor Green
}

if (!(Test-Path "admin-dashboard\.env")) {
    Copy-Item "admin-dashboard\.env.example" "admin-dashboard\.env"
    Write-Host "✓ Created admin-dashboard\.env" -ForegroundColor Green
} else {
    Write-Host "✓ admin-dashboard\.env already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Installing dependencies..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
deactivate
Set-Location ..

# Frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

# Admin dashboard dependencies
Write-Host "Installing admin dashboard dependencies..." -ForegroundColor Yellow
Set-Location admin-dashboard
npm install
Set-Location ..

# Mobile dependencies
Write-Host "Installing mobile dependencies..." -ForegroundColor Yellow
Set-Location mobile
flutter pub get
Set-Location ..

# ML engine dependencies
Write-Host "Installing ML engine dependencies..." -ForegroundColor Yellow
Set-Location ml-engine
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
deactivate
Set-Location ..

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env files with your configuration"
Write-Host "2. Start services with: docker-compose up"
Write-Host "3. Or run individual services:"
Write-Host "   - Backend: cd backend; uvicorn main:app --reload"
Write-Host "   - Frontend: cd frontend; npm start"
Write-Host "   - Mobile: cd mobile; flutter run"
Write-Host "   - Admin: cd admin-dashboard; npm start"
Write-Host ""

