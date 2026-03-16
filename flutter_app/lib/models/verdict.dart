import 'package:flutter/material.dart';

/// Represents a verdict/analysis result pushed from Dear-Care via SNS.
class DearCareVerdict {
  final String encounterId;
  final String workerId;
  final String triageLevel; // "URGENT" | "FOLLOW_UP" | "ROUTINE"
  final String summary;
  final DateTime timestamp;
  final String s3Path;
  final bool isRead;

  DearCareVerdict({
    required this.encounterId,
    required this.workerId,
    required this.triageLevel,
    required this.summary,
    required this.timestamp,
    required this.s3Path,
    this.isRead = false,
  });

  factory DearCareVerdict.fromJson(Map<String, dynamic> json) => DearCareVerdict(
    encounterId: json['encounter_id'] ?? '',
    workerId: json['worker_id'] ?? '',
    triageLevel: json['triage_level'] ?? 'ROUTINE',
    summary: json['summary'] ?? '',
    timestamp: DateTime.parse(json['timestamp']),
    s3Path: json['s3_path'] ?? '',
  );

  Color get triageColor {
    switch (triageLevel) {
      case 'URGENT': return const Color(0xFFD32F2F); // red
      case 'FOLLOW_UP': return const Color(0xFFF57C00); // orange
      default: return const Color(0xFF388E3C); // green
    }
  }

  String get triageEmoji {
    switch (triageLevel) {
      case 'URGENT': return '🚨';
      case 'FOLLOW_UP': return '⚠️';
      default: return '✅';
    }
  }
}
