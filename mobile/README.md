# DupeFinder Mobile

Flutter-based mobile application for iOS and Android.

## Features

- Camera and gallery image upload
- Image-based product search
- Browse product catalog
- User authentication
- Favorites management
- Product comparison
- Reviews and ratings
- Push notifications
- Offline support

## Project Structure

```
mobile/
├── lib/
│   ├── models/            # Data models
│   ├── screens/           # Screen widgets
│   ├── widgets/           # Reusable widgets
│   ├── services/          # API and business logic
│   ├── utils/             # Utilities and helpers
│   └── main.dart          # App entry point
├── assets/                # Images, fonts, etc.
├── test/                  # Test files
└── pubspec.yaml           # Dependencies
```

## Setup Instructions

### Prerequisites
- Flutter SDK 3.0+
- Dart 3.0+
- Android Studio / Xcode
- iOS Simulator / Android Emulator

### Installation

1. Install Flutter dependencies:
```bash
flutter pub get
```

2. Create environment configuration:
```bash
# Create lib/config/environment.dart
# Add your API endpoints and keys
```

3. Run the app:
```bash
# For Android
flutter run -d android

# For iOS
flutter run -d ios

# For specific device
flutter devices
flutter run -d <device-id>
```

## Screens

- **Splash** - Loading screen
- **Onboarding** - First-time user guide
- **Home** - Main search and browse
- **Camera/Upload** - Image capture/selection
- **Search Results** - Product matches
- **Product Detail** - Detailed view
- **Profile** - User account
- **Favorites** - Saved products
- **Comparison** - Compare products
- **Settings** - App settings

## State Management

Using Provider pattern for state management.

## API Integration

API service layer in `lib/services/api_service.dart`

## Testing

```bash
# Run all tests
flutter test

# Run specific test
flutter test test/widget_test.dart
```

## Build for Release

### Android
```bash
flutter build apk --release
# or
flutter build appbundle --release
```

### iOS
```bash
flutter build ios --release
```

## Platform-Specific Setup

### Android
- Update `android/app/build.gradle`
- Configure permissions in `AndroidManifest.xml`

### iOS
- Update `ios/Runner/Info.plist`
- Configure signing in Xcode

## Required Permissions

- Camera access
- Photo library access
- Internet access
- Storage access

## License

[To be determined]

