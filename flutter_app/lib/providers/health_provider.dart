import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/health_snapshot.dart';
import '../services/sensor_service.dart';
import '../services/aws_sync_service.dart';

/// Health Provider - manages sensor data and sync state
class HealthProvider extends ChangeNotifier {
  final SensorService _sensorService = SensorService();
  late AwsSyncService _awsService;

  HealthProvider() {
    _awsService = AwsSyncService();
  }

  // State
  int _steps = 0;
  double _distanceKm = 0.0;
  double _speedKmh = 0.0;
  String _activity = 'unknown';
  double _latitude = 0.0;
  double _longitude = 0.0;
  bool _isSyncing = false;
  DateTime? _lastSyncTime;
  String _syncStatus = 'synced'; // "synced" | "syncing" | "offline" | "error"

  Timer? _syncTimer;

  // Getters
  int get steps => _steps;
  double get distanceKm => _distanceKm;
  double get speedKmh => _speedKmh;
  String get activity => _activity;
  double get latitude => _latitude;
  double get longitude => _longitude;
  bool get isSyncing => _isSyncing;
  DateTime? get lastSyncTime => _lastSyncTime;
  String get syncStatus => _syncStatus;

  /// Initialize and start sensors
  Future<void> initialize({required String workerId}) async {
    // Reload AWS service with latest API URL from settings
    final prefs = await SharedPreferences.getInstance();
    final apiUrl = prefs.getString('api_gateway_url') ?? '';
    if (apiUrl.isNotEmpty) {
      _awsService = AwsSyncService(apiUrl: apiUrl);
    }

    await _sensorService.initialize(workerId: workerId);

    // Listen to sensor updates
    _sensorService.healthStream.listen((snapshot) {
      _steps = snapshot.steps;
      _distanceKm = snapshot.distanceKm;
      _speedKmh = snapshot.speedKmh;
      _activity = snapshot.activity;
      _latitude = snapshot.latitude;
      _longitude = snapshot.longitude;
      notifyListeners();
    });

    // Start auto-sync timer (every 60 seconds)
    _startSyncTimer(workerId);
  }

  void _startSyncTimer(String workerId) {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(const Duration(seconds: 60), (_) {
      syncNow(workerId: workerId);
    });
  }

  /// Manually trigger sync to AWS
  Future<void> syncNow({required String workerId}) async {
    if (_isSyncing) return;

    _isSyncing = true;
    _syncStatus = 'syncing';
    notifyListeners();

    final snapshot = HealthSnapshot(
      workerId: workerId,
      timestamp: DateTime.now(),
      steps: _steps,
      distanceKm: _distanceKm,
      speedKmh: _speedKmh,
      activity: _activity,
      latitude: _latitude,
      longitude: _longitude,
    );

    final success = await _awsService.syncSnapshot(snapshot);

    if (success) {
      _syncStatus = 'synced';
      _lastSyncTime = DateTime.now();
    } else {
      _syncStatus = 'offline';
    }

    _isSyncing = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
    _sensorService.dispose();
    super.dispose();
  }
}
