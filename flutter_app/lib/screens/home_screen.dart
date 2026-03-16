import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/health_provider.dart';
import '../providers/verdict_provider.dart';
import '../widgets/health_card.dart';
import '../widgets/sync_status_badge.dart';

extension StringCap on String {
  String capitalize() => isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';
}

/// Main dashboard screen - shows health stats and sync status
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _workerId = '';
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _autoInitialize();
  }

  Future<void> _autoInitialize() async {
    final prefs = await SharedPreferences.getInstance();
    final workerId = prefs.getString('worker_id') ?? '';
    setState(() => _workerId = workerId);

    if (workerId.isNotEmpty && mounted) {
      context.read<HealthProvider>().initialize(workerId: workerId);
      context.read<VerdictProvider>().loadVerdicts(workerId);
      context.read<VerdictProvider>().startPolling(workerId);
      _initialized = true;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.favorite, color: Colors.green, size: 24),
            const SizedBox(width: 8),
            const Text('Fit-U'),
            const Spacer(),
            Consumer<VerdictProvider>(
              builder: (_, verdict, __) {
                if (verdict.unreadCount > 0) {
                  return Stack(
                    children: [
                      const Icon(Icons.notifications),
                      Positioned(
                        right: 0,
                        top: 0,
                        child: Container(
                          padding: const EdgeInsets.all(2),
                          decoration: BoxDecoration(
                            color: Colors.red,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                          child: Text(
                            '${verdict.unreadCount}',
                            style: const TextStyle(color: Colors.white, fontSize: 10),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                    ],
                  );
                }
                return const Icon(Icons.notifications_outlined);
              },
            ),
          ],
        ),
        leading: Consumer<HealthProvider>(
          builder: (_, health, __) => Padding(
            padding: const EdgeInsets.only(left: 16),
            child: SyncStatusBadge(status: health.syncStatus),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () async {
              await Navigator.pushNamed(context, '/settings');
              // Re-initialize after returning from settings in case worker ID changed
              _autoInitialize();
            },
          ),
        ],
      ),
      body: _workerId.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.person_add, size: 64, color: Colors.grey),
                    const SizedBox(height: 16),
                    const Text(
                      'Welcome to Fit-U!',
                      style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Please set your Worker ID and API Gateway URL in Settings to get started.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey, fontSize: 16),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () async {
                        await Navigator.pushNamed(context, '/settings');
                        _autoInitialize();
                      },
                      icon: const Icon(Icons.settings),
                      label: const Text('Open Settings'),
                    ),
                  ],
                ),
              ),
            )
          : Consumer<HealthProvider>(
        builder: (_, health, __) => SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Today's Activity header
              const Text(
                "Today's Activity",
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),

              // Health cards grid
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                children: [
                  HealthCard(icon: '👣', label: 'Steps', value: '${health.steps}'),
                  HealthCard(icon: '📏', label: 'Distance', value: '${health.distanceKm.toStringAsFixed(2)} km'),
                  HealthCard(icon: '⚡', label: 'Speed', value: '${health.speedKmh.toStringAsFixed(1)} km/h'),
                  HealthCard(icon: '🏃', label: 'Activity', value: health.activity.capitalize()),
                ],
              ),
              const SizedBox(height: 24),

              // Sync Status
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            health.lastSyncTime != null
                                ? 'Last synced: ${_formatTime(health.lastSyncTime!)}'
                                : 'Never synced',
                          ),
                          if (health.isSyncing)
                            const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: health.isSyncing
                            ? null
                            : () => health.syncNow(workerId: _workerId),
                        child: const Text('Sync Now'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Latest Verdict (if available)
              Consumer<VerdictProvider>(
                builder: (_, verdict, __) {
                  if (verdict.latestVerdict == null) return const SizedBox();
                  final v = verdict.latestVerdict!;
                  return Card(
                    color: v.triageColor.withOpacity(0.15),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text('${v.triageEmoji} ', style: const TextStyle(fontSize: 24)),
                              Text(
                                v.triageLevel,
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: v.triageColor,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            v.summary.length > 150
                                ? '${v.summary.substring(0, 150)}...'
                                : v.summary,
                          ),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () => Navigator.pushNamed(context, '/verdict'),
                            child: const Text('View Details'),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              const SizedBox(height: 16),

              // Location info
              Text(
                '📍 ${health.latitude.toStringAsFixed(4)}, ${health.longitude.toStringAsFixed(4)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.bar_chart), label: 'Stats'),
          BottomNavigationBarItem(icon: Icon(Icons.assignment), label: 'Verdicts'),
        ],
        onTap: (index) {
          if (index == 1) Navigator.pushNamed(context, '/stats');
          if (index == 2) Navigator.pushNamed(context, '/verdict');
        },
      ),
    );
  }

  String _formatTime(DateTime time) {
    final diff = DateTime.now().difference(time);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes} min ago';
    if (diff.inHours < 24) return '${diff.inHours} hr ago';
    return '${diff.inDays} day${diff.inDays > 1 ? 's' : ''} ago';
  }
}
