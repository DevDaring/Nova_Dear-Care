import 'package:flutter/foundation.dart';
import '../models/verdict.dart';
import '../services/aws_sync_service.dart';
import '../services/notification_service.dart';

/// Verdict Provider - manages Dear-Care verdicts
class VerdictProvider extends ChangeNotifier {
  final AwsSyncService _awsService = AwsSyncService();
  final NotificationService _notificationService = NotificationService();

  List<DearCareVerdict> _verdicts = [];
  DearCareVerdict? _latestVerdict;

  List<DearCareVerdict> get verdicts => _verdicts;
  DearCareVerdict? get latestVerdict => _latestVerdict;
  int get unreadCount => _verdicts.where((v) => !v.isRead).length;

  /// Load verdicts for a worker
  Future<void> loadVerdicts(String workerId) async {
    final verdict = await _awsService.fetchLatestVerdict(workerId);
    if (verdict != null) {
      _verdicts.insert(0, verdict);
      _latestVerdict = verdict;
      notifyListeners();
    }
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

  /// Add a new verdict (called by notification service)
  void addVerdict(DearCareVerdict verdict) {
    _verdicts.insert(0, verdict);
    _latestVerdict = verdict;
    notifyListeners();

    // Show notification
    _notificationService.showVerdictNotification(verdict);
  }
}
