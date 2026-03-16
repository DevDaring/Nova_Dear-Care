cd D:\Contest\Nova_Dear-Care\flutter_app
```

### 2. Launch the Android emulator
```powershell
flutter emulators
```
Pick one from the list, then:
```powershell

#flutter emulators --launch Pixel_9_Pro_XL

cd C:\Users\Debz\AppData\Local\Android\Sdk\emulator
.\emulator.exe -avd Pixel_9_Pro_XL -no-snapshot-load



############# Use for application run
cd D:\Contest\Nova_Dear-Care\flutter_app

# 1. Kill ALL Kotlin daemon processes holding file locks
Get-Process | Where-Object { $_.ProcessName -match "kotlin|gradle|java" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Clean everything
flutter clean

# 3. Delete Gradle caches for this project
Remove-Item -Recurse -Force "android\.gradle" -ErrorAction SilentlyContinue

# 4. Also enable Developer Mode (Flutter warned about symlinks)
start ms-settings:developers

# 5. Get fresh deps
flutter pub get

# 6. Run
flutter run