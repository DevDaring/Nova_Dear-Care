import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'providers/health_provider.dart';
import 'providers/verdict_provider.dart';
import 'services/notification_service.dart';

/// Top-level FCM background handler — MUST be a top-level function
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(dynamic message) async {
  await NotificationService().initialize();
  // Handle FCM message here
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize notifications
  await NotificationService().initialize();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => HealthProvider()),
        ChangeNotifierProvider(create: (_) => VerdictProvider()),
      ],
      child: const FitUApp(),
    ),
  );
}
