import 'package:flutter/material.dart';

/// Stats Screen - shows charts and historical data (placeholder)
class StatsScreen extends StatelessWidget {
  const StatsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Statistics')),
      body: const Center(
        child: Text('Charts will be displayed here\n(Requires historical data)'),
      ),
    );
  }
}
