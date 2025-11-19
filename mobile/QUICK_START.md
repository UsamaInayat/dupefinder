# Quick Start - Mobile App

## Prerequisites Check

Before running the mobile app, make sure you have:

1. ✅ **Flutter installed** (see `FLUTTER_INSTALL_WINDOWS.md`)
2. ✅ **Backend server running** on `http://localhost:8000`
3. ✅ **Android Studio** or **Xcode** (for iOS)

## Step 1: Install Flutter Dependencies

```powershell
cd mobile
flutter pub get
```

## Step 2: Check Flutter Setup

```powershell
flutter doctor
```

Fix any issues shown (usually Android licenses or Android Studio setup).

## Step 3: Configure API URL

Edit `lib/services/api_service.dart`:

- **Android Emulator**: `http://10.0.2.2:8000/api` (already set)
- **iOS Simulator**: `http://localhost:8000/api`
- **Physical Device**: `http://YOUR_COMPUTER_IP:8000/api`

To find your computer's IP:
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter
```

## Step 4: Start Backend Server

In a separate terminal:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 5: List Available Devices

```powershell
flutter devices
```

## Step 6: Run the App

### Android Emulator:
```powershell
flutter run -d android
```

### iOS Simulator (Mac only):
```powershell
flutter run -d ios
```

### Physical Device:
```powershell
flutter run -d <device-id>
```

## Testing Flow

1. **Register** a new user in the mobile app
2. **Verify OTP** from email
3. **Login** with credentials
4. **Check Admin Portal** → User Management → User should appear!

## Common Issues

### "flutter: command not found"
- Flutter not installed or not in PATH
- See `FLUTTER_INSTALL_WINDOWS.md`

### "No devices found"
- Start Android emulator from Android Studio
- Or connect physical device via USB

### "Connection refused" or API errors
- Check backend is running on port 8000
- Verify API URL in `api_service.dart`
- For physical device, use computer's IP address

### "Android licenses not accepted"
```powershell
flutter doctor --android-licenses
```

