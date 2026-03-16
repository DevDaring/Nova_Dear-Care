import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:pedometer/pedometer.dart';
import '../models/health_snapshot.dart';

/// Sensor service for collecting health data from phone sensors.
/// Singleton pattern - use SensorService() to get the instance.
class SensorService {
  factory SensorService() => _instance;
  SensorService._internal();

  static final SensorService _instance = SensorService._internal();

  // State
  String _workerId = '';
  int _steps = 0;
  double _distanceKm = 0.0;
  double _speedKmh = 0.0;
  String _activity = 'unknown';
  double _latitude = 0.0;
  double _longitude = 0.0;
  Position? _lastPosition;

  // Stream controllers
  final _healthController = StreamController<HealthSnapshot>.broadcast();
  Stream<HealthSnapshot> get healthStream => _healthController.stream;

  // Subscriptions
  StreamSubscription<StepCount>? _stepSubscription;
  StreamSubscription<PedestrianStatus>? _statusSubscription;
  StreamSubscription<Position>? _positionSubscription;

  int get steps => _steps;
  double get distanceKm => _distanceKm;
  double get speedKmh => _speedKmh;
  String get activity => _activity;
  double get latitude => _latitude;
  double get longitude => _longitude;

  /// Initialize sensors and start streaming data
  Future<void> initialize({required String workerId}) async {
    _workerId = workerId;
    debugPrint('[SensorService] Initializing for worker: $workerId');

    // Initialize pedometer (not available on emulators)
    try {
      _stepSubscription = Pedometer.stepCountStream.listen(
        _onStepCount,
        onError: _onSensorError,
        cancelOnError: false,
      );
    } catch (e) {
      debugPrint('[SensorService] StepCount unavailable: $e');
    }

    try {
      _statusSubscription = Pedometer.pedestrianStatusStream.listen(
        _onPedestrianStatus,
        onError: _onSensorError,
        cancelOnError: false,
      );
    } catch (e) {
      debugPrint('[SensorService] PedestrianStatus unavailable: $e');
    }

    // Initialize GPS
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        debugPrint('[SensorService] Location service disabled');
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          debugPrint('[SensorService] Location permission denied');
        }
      }

      const locationSettings = LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10,
      );

      _positionSubscription = Geolocator.getPositionStream(locationSettings: locationSettings)
          .listen(_onPositionUpdate, onError: _onSensorError);
    } catch (e) {
      debugPrint('[SensorService] GPS error: $e');
    }

    debugPrint('[SensorService] Initialization complete');
  }

  void _onStepCount(StepCount event) {
    _steps = event.steps;
    _emitSnapshot();
  }

  void _onPedestrianStatus(PedestrianStatus event) {
    _activity = event.status.toLowerCase();
    _emitSnapshot();
  }

  void _onPositionUpdate(Position position) {
    // Calculate distance from last position
    if (_lastPosition != null) {
      double distance = Geolocator.distanceBetween(
        _lastPosition!.latitude,
        _lastPosition!.longitude,
        position.latitude,
        position.longitude,
      );
      _distanceKm += distance / 1000.0; // Convert to km
    }

    _latitude = position.latitude;
    _longitude = position.longitude;
    _speedKmh = position.speed.toDouble() * 3.6; // m/s to km/h
    _lastPosition = position;

    _emitSnapshot();
  }

  void _onSensorError(error) {
    debugPrint('[SensorService] Sensor error: $error');
  }

  void _emitSnapshot() {
    final snapshot = HealthSnapshot(
      workerId: _workerId,
      timestamp: DateTime.now(),
      steps: _steps,
      distanceKm: _distanceKm,
      speedKmh: _speedKmh,
      activity: _activity,
      latitude: _latitude,
      longitude: _longitude,
    );
    _healthController.add(snapshot);
  }

  /// Cleanup and release resources
  void dispose() {
    _stepSubscription?.cancel();
    _statusSubscription?.cancel();
    _positionSubscription?.cancel();
    _healthController.close();
  }
}
