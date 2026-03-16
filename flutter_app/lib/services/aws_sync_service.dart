import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/health_snapshot.dart';
import '../models/verdict.dart';
import 'offline_queue_service.dart';

/// AWS Sync Service - sends health data to API Gateway and fetches verdicts
/// Works gracefully offline - adds to queue when sync fails
class AwsSyncService {
  static const String _defaultApiUrl =
      'https://YOUR_API_GATEWAY_URL.execute-api.us-east-1.amazonaws.com/prod/fitu-health';
  String _apiGatewayUrl = _defaultApiUrl;
  final OfflineQueueService _offlineQueue = OfflineQueueService();

  AwsSyncService({String? apiUrl}) {
    if (apiUrl != null && apiUrl.isNotEmpty) {
      _apiGatewayUrl = apiUrl;
    }
    _loadApiUrl();
  }

  /// Load API URL from SharedPreferences (set in Settings)
  Future<void> _loadApiUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('api_gateway_url') ?? '';
      if (saved.isNotEmpty) {
        _apiGatewayUrl = saved;
      }
    } catch (e) {
      debugPrint('[AWS] Could not load API URL: $e');
    }
  }

  /// Update the API Gateway URL at runtime
  void updateApiUrl(String url) {
    if (url.isNotEmpty) {
      _apiGatewayUrl = url;
    }
  }

  /// Check if API URL is configured (not placeholder)
  bool get isConfigured =>
      _apiGatewayUrl.isNotEmpty && !_apiGatewayUrl.contains('YOUR_API_GATEWAY_URL');

  /// Sync health snapshot to AWS
  Future<bool> syncSnapshot(HealthSnapshot snapshot) async {
    if (!isConfigured) {
      debugPrint('[AWS] API URL not configured - queuing offline');
      await _offlineQueue.addToQueue(snapshot);
      return false;
    }

    debugPrint('[AWS] Syncing snapshot...');

    try {
      final response = await http.post(
        Uri.parse(_apiGatewayUrl),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(snapshot.toJson()),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200 || response.statusCode == 201) {
        debugPrint('[AWS] SUCCESS: Snapshot synced');
        // Retry any pending items
        _retryOfflineQueue();
        return true;
      } else {
        debugPrint('[AWS] FAILED: ${response.statusCode}');
        await _offlineQueue.addToQueue(snapshot);
        return false;
      }
    } catch (e) {
      debugPrint('[AWS] ERROR: $e');
      await _offlineQueue.addToQueue(snapshot);
      return false;
    }
  }

  /// Retry all pending offline items
  Future<void> _retryOfflineQueue() async {
    final pending = await _offlineQueue.getPendingItems();
    debugPrint('[AWS] Retrying ${pending.length} pending items');

    for (var item in pending) {
      try {
        final snapshot = HealthSnapshot.fromJson(json.decode(item['payload']));
        final response = await http.post(
          Uri.parse(_apiGatewayUrl),
          headers: {'Content-Type': 'application/json'},
          body: json.encode(snapshot.toJson()),
        ).timeout(const Duration(seconds: 10));

        if (response.statusCode == 200 || response.statusCode == 201) {
          await _offlineQueue.removeItem(item['id'] as int);
          debugPrint('[AWS] Retry SUCCESS for item ${item['id']}');
        }
      } catch (e) {
        debugPrint('[AWS] Retry FAILED for item ${item['id']}: $e');
      }
    }
  }

  /// Fetch latest verdict for a worker
  Future<DearCareVerdict?> fetchLatestVerdict(String workerId) async {
    try {
      final url = '$_apiGatewayUrl/verdict?worker_id=$workerId';
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        return DearCareVerdict.fromJson(json);
      }
    } catch (e) {
      debugPrint('[AWS] Fetch verdict error: $e');
    }
    return null;
  }
}
