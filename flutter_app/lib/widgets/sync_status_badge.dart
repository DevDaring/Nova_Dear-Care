import 'package:flutter/material.dart';

/// Sync status badge widget - shows current AWS sync state
class SyncStatusBadge extends StatelessWidget {
  final String status; // "synced" | "syncing" | "offline" | "error"

  const SyncStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;
    String label;

    switch (status) {
      case 'synced':
        color = Colors.green;
        icon = Icons.cloud_done;
        label = 'Synced';
        break;
      case 'syncing':
        color = Colors.blue;
        icon = Icons.sync;
        label = 'Syncing';
        break;
      case 'offline':
        color = Colors.orange;
        icon = Icons.cloud_off;
        label = 'Offline';
        break;
      case 'error':
        color = Colors.red;
        icon = Icons.error;
        label = 'Error';
        break;
      default:
        color = Colors.grey;
        icon = Icons.cloud_queue;
        label = 'Unknown';
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (status == 'syncing')
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: color,
            ),
          )
        else
          Icon(icon, color: color, size: 16),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
