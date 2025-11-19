# Flutter Installation Guide for Windows

## Step 1: Download Flutter SDK

1. Go to: https://docs.flutter.dev/get-started/install/windows
2. Download Flutter SDK (latest stable version)
3. Extract the zip file to a location like:
   - `C:\src\flutter` (recommended)
   - OR `C:\flutter`
   - **DO NOT** install in `C:\Program Files\` (permissions issues)

## Step 2: Add Flutter to PATH

### Option A: Using GUI (Recommended)

1. Press `Windows Key + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", find "Path" and click "Edit"
5. Click "New" and add: `C:\src\flutter\bin` (or your Flutter path)
6. Click "OK" on all dialogs
7. **Restart PowerShell/Terminal**

### Option B: Using PowerShell (Temporary - Current Session Only)

```powershell
$env:Path += ";C:\src\flutter\bin"
```

## Step 3: Verify Installation

Open a **NEW** PowerShell window and run:

```powershell
flutter --version
flutter doctor
```

## Step 4: Install Additional Dependencies

Flutter doctor will tell you what's missing. Common requirements:

### Android Studio (for Android development)

1. Download: https://developer.android.com/studio
2. Install Android Studio
3. Open Android Studio → More Actions → SDK Manager
4. Install:
   - Android SDK
   - Android SDK Platform
   - Android Virtual Device (AVD)

### VS Code (Optional but Recommended)

1. Download: https://code.visualstudio.com/
2. Install Flutter extension in VS Code

## Step 5: Accept Android Licenses

```powershell
flutter doctor --android-licenses
```

Press `y` to accept all licenses.

## Step 6: Verify Everything

```powershell
flutter doctor -v
```

You should see checkmarks (✓) for:
- Flutter
- Android toolchain
- VS Code (if installed)

## Step 7: Create Android Emulator (Optional)

1. Open Android Studio
2. Tools → Device Manager
3. Create Virtual Device
4. Select a device (e.g., Pixel 5)
5. Download a system image (e.g., Android 13)
6. Finish

## Step 8: Test Flutter

```powershell
flutter create test_app
cd test_app
flutter run
```

## Quick Install Script (Alternative)

If you have Chocolatey installed:

```powershell
choco install flutter
```

## Troubleshooting

### Flutter command not found after adding to PATH

- **Restart PowerShell/Terminal** (required!)
- Check PATH: `$env:Path` should contain Flutter bin path
- Verify Flutter location: `C:\src\flutter\bin\flutter.bat` exists

### Android Studio not detected

- Make sure Android Studio is installed
- Run: `flutter config --android-studio-dir="C:\Program Files\Android\Android Studio"`

### Java/JDK issues

- Install JDK 17 or later
- Set JAVA_HOME environment variable

## After Installation

Once Flutter is installed, run:

```powershell
cd mobile
flutter pub get
flutter doctor
```

Then you can run the app:

```powershell
flutter run -d android
```

