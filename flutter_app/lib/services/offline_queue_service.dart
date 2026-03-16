import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../models/health_snapshot.dart';

/// Offline queue service for storing failed sync attempts in SQLite
class OfflineQueueService {
  static const String _dbName = 'fitu_queue.db';
  static const String _tableName = 'sync_queue';
  Database? _database;

  Future<Database> get _db async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final directory = await getApplicationDocumentsDirectory();
    final path = join(directory.path, _dbName);

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE $_tableName (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0
          )
        ''');
      },
    );
  }

  /// Add a failed sync item to the queue
  Future<void> addToQueue(HealthSnapshot snapshot) async {
    final db = await _db;
    await db.insert(_tableName, {
      'worker_id': snapshot.workerId,
      'payload': json.encode(snapshot.toJson()),
      'created_at': DateTime.now().toIso8601String(),
      'retry_count': 0,
    });
    debugPrint('[Queue] Added item to offline queue');
  }

  /// Get all pending items from queue
  Future<List<Map<String, dynamic>>> getPendingItems() async {
    final db = await _db;
    return await db.query(_tableName);
  }

  /// Remove an item from queue
  Future<void> removeItem(int id) async {
    final db = await _db;
    await db.delete(_tableName, where: 'id = ?', whereArgs: [id]);
    debugPrint('[Queue] Removed item $id');
  }

  /// Clear all items from queue
  Future<void> clearAll() async {
    final db = await _db;
    await db.delete(_tableName);
    debugPrint('[Queue] Cleared all items');
  }
}
