# DupeFinder Mobile App Setup

## Overview

This is a Flutter mobile app with:
- **Login/Registration** - User authentication with OTP verification
- **Home Screen** - 4 main action buttons:
  1. Add Image
  2. Compare Items
  3. Add to Wishlist
  4. View Profile

## Purpose

The app is designed to verify that registered/logged-in users appear in the Admin Portal through the backend API.

## Setup Instructions

### 1. Install Dependencies

```bash
cd mobile
flutter pub get
```

### 2. Configure API Base URL

**Important:** Update the API base URL in `lib/services/api_service.dart` based on your testing environment:

```dart
// For Android Emulator:
static const String baseUrl = 'http://10.0.2.2:8000/api';

// For iOS Simulator:
static const String baseUrl = 'http://localhost:8000/api';

// For Physical Device:
// Use your computer's IP address (e.g., 192.168.1.100)
static const String baseUrl = 'http://192.168.1.100:8000/api';
```

**To find your computer's IP:**
- Windows: `ipconfig` (look for IPv4 Address)
- Mac/Linux: `ifconfig` or `ip addr`

### 3. Start Backend Server

Make sure the backend server is running on `http://localhost:8000`:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run the Mobile App

```bash
# List available devices
flutter devices

# Run on Android
flutter run -d android

# Run on iOS
flutter run -d ios

# Run on specific device
flutter run -d <device-id>
```

## Testing User Registration

### Step 1: Register a New User

1. Open the mobile app
2. Tap "Don't have an account? Register"
3. Enter email and password
4. Tap "Register"
5. Check your email for OTP
6. Enter OTP and verify

### Step 2: Login

1. After OTP verification, go back to login screen
2. Enter email and password
3. Tap "Login"
4. You should see the Home screen with 4 buttons

### Step 3: Verify in Admin Portal

1. Open Admin Dashboard: `http://localhost:3000/admin`
2. Login with admin credentials
3. Go to "User Management" tab
4. You should see the registered user in the list!

## Features

### Home Screen Buttons

1. **Add Image** - Placeholder for image upload feature
2. **Compare Items** - Placeholder for product comparison
3. **Add to Wishlist** - Placeholder for wishlist feature
4. **View Profile** - Shows user email and verification status

### Authentication Flow

1. User registers with email/password
2. OTP sent to email
3. User verifies OTP
4. User can login
5. Token stored in SharedPreferences
6. User appears in Admin Portal

## API Endpoints Used

- `POST /api/auth/signup` - User registration
- `POST /api/auth/verify-otp` - OTP verification
- `POST /api/auth/login` - User login
- `GET /api/admin/users` - Admin portal (to verify users)

## Troubleshooting

### Connection Issues

**Problem:** App can't connect to backend

**Solutions:**
- Check if backend is running on port 8000
- Verify API base URL in `api_service.dart`
- For Android emulator, use `10.0.2.2` instead of `localhost`
- For physical device, use your computer's IP address
- Check firewall settings

### OTP Not Received

**Problem:** OTP email not arriving

**Solutions:**
- Check spam folder
- Verify email service is configured in backend
- Check backend logs for email sending errors

### Users Not Appearing in Admin Portal

**Problem:** Registered users don't show in admin portal

**Solutions:**
- Verify user completed OTP verification
- Check MongoDB `users` collection
- Verify admin portal is fetching from correct collection
- Check backend logs for errors

## File Structure

```
mobile/
├── lib/
│   ├── main.dart              # App entry point
│   ├── screens/
│   │   ├── login_screen.dart
│   │   ├── register_screen.dart
│   │   └── home_screen.dart
│   └── services/
│       └── api_service.dart   # API integration
├── pubspec.yaml
└── README.md
```

## Next Steps

- Implement image upload functionality
- Add product comparison feature
- Implement wishlist functionality
- Add product search and browse features

