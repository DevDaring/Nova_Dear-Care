# Fit-U Flutter App

Health companion mobile app for the Dear-Care AI Assistant system.

## Features

- **Real-time Health Tracking**
  - 👣 Step counting via phone pedometer
  - 📍 GPS location tracking
  - 📏 Distance calculation
  - ⚡ Speed monitoring
  - 🏃 Activity detection (walking, running, stopped)

- **AWS Integration**
  - Auto-sync health data every 60 seconds
  - Graceful offline mode with queue
  - Dear-Care verdict display with triage levels

- **Notifications**
  - Local notifications for urgent verdicts
  - Firebase Cloud Messaging ready (placeholder)

## Architecture

```
lib/
├── main.dart                 # App entry point
├── app.dart                  # MaterialApp configuration
├── models/                   # Data models
│   ├── health_snapshot.dart  # Sensor data model
│   └── verdict.dart          # Dear-Care verdict model
├── services/                 # Business logic
│   ├── sensor_service.dart   # Sensor data collection
│   ├── aws_sync_service.dart # AWS API Gateway client
│   ├── offline_queue_service.dart  # SQLite offline queue
│   └── notification_service.dart  # Local notifications
├── providers/                # State management
│   ├── health_provider.dart  # Sensor data & sync state
│   └── verdict_provider.dart # Verdict state
├── screens/                  # UI screens
│   ├── home_screen.dart      # Main dashboard
│   ├── stats_screen.dart     # Statistics (placeholder)
│   ├── verdict_screen.dart   # Verdicts list
│   └── settings_screen.dart  # Worker ID config
└── widgets/                  # Reusable widgets
    ├── health_card.dart      # Health stat card
    └── sync_status_badge.dart # Sync status indicator
```

## Setup

1. **Install dependencies**
   ```bash
   flutter pub get
   ```

2. **Configure API Gateway URL**
   Edit `lib/services/aws_sync_service.dart`:
   ```dart
   static const String _defaultApiUrl = 'https://YOUR_API_GATEWAY_URL/prod/fitu-health';
   ```

3. **Run the app**
   ```bash
   flutter run
   ```

## Permissions

The app requires:
- **Step counter** (Android/iOS)
- **Location** (GPS for distance/speed)
- **Notifications** (for verdict alerts)

## Data Flow

```
Phone Sensors → SensorService → HealthProvider
                                     ↓
                               AwsSyncService → API Gateway → Lambda → DynamoDB
                                     ↓
                                      SNS → (Future: FCM) → Local Notification
```

## Testing Mode

To test without AWS:
- The app gracefully handles connection failures
- Data is queued in local SQLite
- Sync retries automatically when connection restored

## Firebase Integration (Future)

To enable FCM push notifications:
1. Add `firebase_messaging` to `pubspec.yaml`
2. Configure Firebase project
3. Replace `handleFcmMessage()` with actual FCM handler
4. Update `_firebaseMessagingBackgroundHandler` in `main.dart`
