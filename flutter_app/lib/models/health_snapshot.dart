/// Represents one health/fitness reading from phone sensors.
/// This is the data that gets sent to AWS before Dear-Care processing.
class HealthSnapshot {
  final String workerId;
  final DateTime timestamp;
  final int steps;
  final double distanceKm;
  final double speedKmh;
  final String activity; // "walking" | "running" | "stopped" | "unknown"
  final double latitude;
  final double longitude;
  final double? heartRateEstimated;

  HealthSnapshot({
    required this.workerId,
    required this.timestamp,
    required this.steps,
    required this.distanceKm,
    required this.speedKmh,
    required this.activity,
    required this.latitude,
    required this.longitude,
    this.heartRateEstimated,
  });

  Map<String, dynamic> toJson() => {
    'worker_id': workerId,
    'timestamp': timestamp.toUtc().toIso8601String(),
    'steps': steps,
    'distance_km': distanceKm,
    'speed_kmh': speedKmh,
    'activity': activity,
    'latitude': latitude,
    'longitude': longitude,
    if (heartRateEstimated != null) 'heart_rate_estimated': heartRateEstimated,
  };

  factory HealthSnapshot.fromJson(Map<String, dynamic> json) => HealthSnapshot(
    workerId: json['worker_id'] ?? '',
    timestamp: DateTime.parse(json['timestamp']),
    steps: json['steps'] ?? 0,
    distanceKm: (json['distance_km'] ?? 0.0).toDouble(),
    speedKmh: (json['speed_kmh'] ?? 0.0).toDouble(),
    activity: json['activity'] ?? 'unknown',
    latitude: (json['latitude'] ?? 0.0).toDouble(),
    longitude: (json['longitude'] ?? 0.0).toDouble(),
    heartRateEstimated: json['heart_rate_estimated']?.toDouble(),
  );
}
