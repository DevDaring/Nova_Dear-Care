import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/verdict.dart';
import '../env_config.dart';
import '../services/aws_sync_service.dart';
import '../services/notification_service.dart';

/// Verdict Provider - manages Dear-Care verdicts with device polling
class VerdictProvider extends ChangeNotifier {
  final AwsSyncService _awsService = AwsSyncService();
  final NotificationService _notificationService = NotificationService();

  List<DearCareVerdict> _verdicts = [];
  DearCareVerdict? _latestVerdict;
  Timer? _pollTimer;
  final Set<String> _seenIds = {};
  bool _firstPoll = true;
  String _deviceUrl = EnvConfig.deviceUrl;

  bool _deviceReachable = true;
  int _failCount = 0;

  List<DearCareVerdict> get verdicts => _verdicts;
  DearCareVerdict? get latestVerdict => _latestVerdict;
  int get unreadCount => _verdicts.where((v) => !v.isRead).length;

  /// Load verdicts for a worker from AWS API Gateway (DynamoDB)
  Future<void> loadVerdicts(String workerId) async {
    debugPrint('[Verdict] Loading past verdicts from AWS for $workerId...');
    final results = await _awsService.fetchAllVerdicts(workerId);
    if (results.isNotEmpty) {
      for (final verdict in results) {
        if (!_seenIds.contains(verdict.encounterId)) {
          _seenIds.add(verdict.encounterId);
          _verdicts.add(verdict);
        }
      }
      _latestVerdict = _verdicts.isNotEmpty ? _verdicts.first : null;
      debugPrint('[Verdict] Loaded ${results.length} verdicts from AWS');
      notifyListeners();
    } else {
      debugPrint('[Verdict] No verdicts found in AWS');
    }
  }

  /// Start polling the Dear-Care device for new verdicts every 10 seconds
  Future<void> startPolling(String workerId) async {
    // Load device URL from preferences
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('device_url') ?? '';
      if (saved.isNotEmpty) _deviceUrl = saved;
    } catch (_) {}

    _pollTimer?.cancel();
    _firstPoll = true;
    debugPrint('[Verdict] Polling started: $_deviceUrl');

    // Poll immediately, then every 10 seconds
    _pollForVerdicts(workerId);
    _pollTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      _pollForVerdicts(workerId);
    });
  }

  /// Poll the device HTTP server for new verdicts
  Future<void> _pollForVerdicts(String workerId) async {
    // After 3 consecutive failures, slow down polling to avoid log spam
    if (!_deviceReachable) return;

    final results = await _awsService.fetchVerdictsFromDevice(_deviceUrl, workerId);
    if (results.isEmpty) {
      _failCount++;
      if (_failCount >= 3) {
        _deviceReachable = false;
        debugPrint('[Verdict] Device unreachable after $_failCount attempts, pausing polls. Use Sync Now to retry.');
      }
      return;
    }

    _failCount = 0;
    _deviceReachable = true;

    for (final verdict in results) {
      if (_seenIds.contains(verdict.encounterId)) continue;
      _seenIds.add(verdict.encounterId);

      // On first poll, just record IDs without notifications
      if (_firstPoll) continue;

      // New verdict — add and notify
      addVerdict(verdict);
    }
    _firstPoll = false;
  }

  /// Manually fetch verdicts from device (called by Sync Now button)
  Future<int> fetchFromDevice(String workerId) async {
    // Reset device reachability so polling can resume
    _deviceReachable = true;
    _failCount = 0;

    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('device_url') ?? '';
      if (saved.isNotEmpty) _deviceUrl = saved;
    } catch (_) {}

    final results = await _awsService.fetchVerdictsFromDevice(_deviceUrl, workerId);
    int newCount = 0;
    for (final verdict in results) {
      if (_seenIds.contains(verdict.encounterId)) continue;
      _seenIds.add(verdict.encounterId);
      addVerdict(verdict);
      newCount++;
    }
    return newCount;
  }

  /// Stop polling
  void stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  /// Mark a verdict as read
  void markAsRead(String encounterId) {
    final index = _verdicts.indexWhere((v) => v.encounterId == encounterId);
    if (index != -1) {
      _verdicts[index] = DearCareVerdict(
        encounterId: _verdicts[index].encounterId,
        workerId: _verdicts[index].workerId,
        triageLevel: _verdicts[index].triageLevel,
        summary: _verdicts[index].summary,
        timestamp: _verdicts[index].timestamp,
        s3Path: _verdicts[index].s3Path,
        isRead: true,
      );
      notifyListeners();
    }
  }

  /// Add a new verdict (called by polling or externally)
  void addVerdict(DearCareVerdict verdict) {
    _verdicts.insert(0, verdict);
    _latestVerdict = verdict;
    notifyListeners();

    // Show local notification
    _notificationService.showVerdictNotification(verdict);
  }

  @override
  void dispose() {
    stopPolling();
    super.dispose();
  }
}
