#!/usr/bin/env python3
"""
sync_manager.py - Background data synchronization for Pocket ASHA.
Checks connectivity periodically and uploads pending encounters to S3.
"""

import threading
import time
from typing import Optional

from utils import get_logger, check_internet

_log = None
_sync_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()

SYNC_INTERVAL_SEC = 60


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


class SyncManager:
    """Manages background sync of encounters to AWS."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self):
        """Start the background sync thread."""
        if self._running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._sync_loop, daemon=True, name="sync-manager")
        self._thread.start()
        self._running = True
        _logger().info("[SYNC] Background sync started (interval=%ds)", SYNC_INTERVAL_SEC)

    def stop(self):
        """Stop the background sync thread."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._running = False
        _logger().info("[SYNC] Background sync stopped")

    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def _sync_loop(self):
        """Periodically check connectivity and sync pending data."""
        while not self._stop.is_set():
            try:
                if check_internet():
                    self._sync_pending()
            except Exception as e:
                _logger().error("[SYNC] Loop error: %s", e)
            self._stop.wait(timeout=SYNC_INTERVAL_SEC)

    def _sync_pending(self):
        """Upload all pending encounters."""
        from storage_manager import StorageManager
        from aws_handler import upload_encounter

        sm = StorageManager()
        pending = sm.get_pending_encounters()
        if not pending:
            return

        _logger().info("[SYNC] Found %d pending encounters", len(pending))
        for enc in pending:
            eid = enc.get("encounter_id", "")
            if not eid:
                continue
            folder = sm.get_encounter_folder(eid)
            if not folder.exists():
                _logger().warning("[SYNC] Folder missing for %s", eid)
                continue
            try:
                success = upload_encounter(eid, str(folder))
                if success:
                    sm.update_encounter(eid, sync_status="synced")
                    _logger().info("[SYNC] Synced encounter %s", eid)
                    # Trigger Lambda for clinical notes
                    try:
                        from aws_handler import invoke_lambda
                        invoke_lambda({"encounter_id": eid, "action": "generate_notes"})
                        _logger().info("[SYNC] Lambda triggered for %s", eid)
                    except Exception as le:
                        _logger().warning("[SYNC] Lambda trigger failed for %s: %s", eid, le)
                else:
                    _logger().warning("[SYNC] Partial sync for %s", eid)
            except Exception as e:
                _logger().error("[SYNC] Failed to sync %s: %s", eid, e)

    def sync_now(self) -> dict:
        """Trigger an immediate sync. Returns status dict."""
        result = {"online": False, "synced": 0, "failed": 0, "pending": 0}
        if not check_internet():
            _logger().info("[SYNC] No internet — cannot sync now")
            from storage_manager import StorageManager
            result["pending"] = len(StorageManager().get_pending_encounters())
            return result

        result["online"] = True
        from storage_manager import StorageManager
        from aws_handler import upload_encounter

        sm = StorageManager()
        pending = sm.get_pending_encounters()
        result["pending"] = len(pending)

        for enc in pending:
            eid = enc.get("encounter_id", "")
            if not eid:
                continue
            folder = sm.get_encounter_folder(eid)
            if not folder.exists():
                result["failed"] += 1
                continue
            try:
                if upload_encounter(eid, str(folder)):
                    sm.update_encounter(eid, sync_status="synced")
                    result["synced"] += 1
                else:
                    result["failed"] += 1
            except Exception:
                result["failed"] += 1

        result["pending"] = result["pending"] - result["synced"]
        _logger().info("[SYNC] Manual sync: %s", result)
        return result

    def get_status(self) -> dict:
        """Get current sync status."""
        from storage_manager import StorageManager
        sm = StorageManager()
        pending = sm.get_pending_encounters()
        return {
            "running": self.is_running,
            "online": check_internet(),
            "pending_count": len(pending),
        }
