import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../models/verdict.dart';

/// Notification Service - handles local notifications for Dear-Care verdicts
/// Note: Firebase Cloud Messaging integration would go here for production
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;

  /// Initialize notifications
  Future<void> initialize() async {
    if (_initialized) return;

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(initSettings);
    _initialized = true;
    debugPrint('[Notification] Initialized');
  }

  /// Show a local notification for a Dear-Care verdict
  Future<void> showVerdictNotification(DearCareVerdict verdict) async {
    if (!_initialized) await initialize();

    final androidDetails = AndroidNotificationDetails(
      'dear_care_verdicts',
      'Dear-Care Verdicts',
      channelDescription: 'Health assessment notifications from Dear-Care',
      importance: verdict.triageLevel == 'URGENT'
          ? Importance.high
          : Importance.defaultImportance,
      priority: verdict.triageLevel == 'URGENT'
          ? Priority.high
          : Priority.defaultPriority,
    );

    const iosDetails = DarwinNotificationDetails();

    final notificationDetails = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch % 100000,
      '${verdict.triageEmoji} Dear-Care: ${verdict.triageLevel}',
      verdict.summary.length > 100
          ? '${verdict.summary.substring(0, 100)}...'
          : verdict.summary,
      notificationDetails,
    );

    debugPrint('[Notification] Shown: ${verdict.triageLevel}');
  }

  /// Handle incoming FCM message (placeholder for Firebase integration)
  void handleFcmMessage(Map<String, dynamic> data) {
    if (data['notification_type'] == 'DEAR_CARE_VERDICT') {
      final verdict = DearCareVerdict.fromJson(data);
      showVerdictNotification(verdict);
    }
  }
}
