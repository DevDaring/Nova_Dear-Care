import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/verdict_provider.dart';
import '../models/verdict.dart';

/// Verdict Screen - shows all Dear-Care verdicts
class VerdictScreen extends StatelessWidget {
  const VerdictScreen({super.key});

  Future<String> _getWorkerId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('worker_id') ?? '';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dear-Care Verdicts'),
        actions: [
          Consumer<VerdictProvider>(
            builder: (_, verdict, __) => IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: 'Fetch from device',
              onPressed: () async {
                final workerId = await _getWorkerId();
                if (workerId.isNotEmpty) {
                  final newCount = await verdict.fetchFromDevice(workerId);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(newCount > 0
                            ? '$newCount new result${newCount > 1 ? 's' : ''} received!'
                            : 'No new results'),
                      ),
                    );
                  }
                }
              },
            ),
          ),
        ],
      ),
      body: Consumer<VerdictProvider>(
        builder: (_, verdict, __) {
          if (verdict.verdicts.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.inbox, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('No verdicts yet', style: TextStyle(fontSize: 18, color: Colors.grey)),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: verdict.verdicts.length,
            itemBuilder: (context, index) {
              final v = verdict.verdicts[index];
              return _VerdictCard(
                verdict: v,
                onTap: () {
                  verdict.markAsRead(v.encounterId);
                  _showVerdictDetails(context, v);
                },
              );
            },
          );
        },
      ),
    );
  }

  void _showVerdictDetails(BuildContext context, DearCareVerdict verdict) {
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text('${verdict.triageEmoji} ', style: const TextStyle(fontSize: 32)),
                  Expanded(
                    child: Text(
                      verdict.triageLevel,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: verdict.triageColor,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Text(
                verdict.summary,
                style: const TextStyle(fontSize: 16, height: 1.5),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'ID: ${verdict.encounterId}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  Text(
                    '${verdict.timestamp.day}/${verdict.timestamp.month}/${verdict.timestamp.year}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Close'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _VerdictCard extends StatelessWidget {
  final DearCareVerdict verdict;
  final VoidCallback onTap;

  const _VerdictCard({required this.verdict, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: verdict.isRead ? null : verdict.triageColor.withOpacity(0.1),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Text(
                verdict.triageEmoji,
                style: const TextStyle(fontSize: 32),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          verdict.triageLevel,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: verdict.triageColor,
                          ),
                        ),
                        if (!verdict.isRead) ...[
                          const SizedBox(width: 8),
                          const Icon(Icons.circle, color: Colors.red, size: 8),
                        ],
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      verdict.summary.length > 80
                          ? '${verdict.summary.substring(0, 80)}...'
                          : verdict.summary,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}
