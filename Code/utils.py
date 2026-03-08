#!/usr/bin/env python3
"""
utils.py - Utility functions for Pocket ASHA System
"""

import gc
import os
import sys
import time
import signal
import socket
import logging
from pathlib import Path
from datetime import datetime

_running = True
_logger = None


def free_memory():
    """Force garbage collection to free memory."""
    gc.collect()


def check_internet(host="s3.amazonaws.com", port=443, timeout=3):
    """Check internet connectivity by attempting a socket connection."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (OSError, socket.timeout):
        return False


def get_timestamp():
    """Get current ISO format timestamp."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def get_timestamp_compact():
    """Get compact timestamp for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def setup_logging(log_dir=None):
    """Set up logging to file and console."""
    global _logger
    if _logger:
        return _logger

    from config import LOG_DIR
    log_dir = log_dir or str(LOG_DIR)
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    log_file = os.path.join(log_dir, f"asha_{get_timestamp_compact()}.log")

    _logger = logging.getLogger("pocket_asha")
    _logger.setLevel(logging.INFO)

    # Prevent duplicate handlers on repeated calls
    if not _logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        # Only log to file; stdout goes through tee when piped
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", "%H:%M:%S")
        fh.setFormatter(fmt)
        _logger.addHandler(fh)

        # Add stdout handler only if NOT piped (i.e. no tee)
        if sys.stdout.isatty():
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            ch.setFormatter(fmt)
            _logger.addHandler(ch)

    return _logger


def get_logger():
    """Get the application logger."""
    global _logger
    if not _logger:
        _logger = setup_logging()
    return _logger


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global _running
    print("\n[ASHA] Shutting down gracefully...")
    _running = False


def is_running():
    """Check if the application should continue running."""
    return _running


def stop_running():
    """Signal the application to stop."""
    global _running
    _running = False


def install_signal_handlers():
    """Install signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def get_disk_usage():
    """Get disk usage info for the data partition."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free
        percent = (used / total) * 100 if total > 0 else 0
        return {
            "total_gb": round(total / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "used_percent": round(percent, 1),
        }
    except Exception:
        return {"total_gb": 0, "free_gb": 0, "used_percent": 0}


def get_memory_usage():
    """Get current process memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return round(process.memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return 0


def generate_encounter_id():
    """Generate a unique encounter ID."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    pid = os.getpid() % 1000
    return f"ENC_{ts}_{pid:03d}"


def generate_patient_id():
    """Generate a unique patient ID."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PAT_{ts}"


def cleanup_temp():
    """Remove stale files from temp directory on startup."""
    from config import TEMP_DIR
    try:
        for f in Path(TEMP_DIR).glob("*"):
            if f.is_file() and f.name != ".gitkeep":
                f.unlink()
        get_logger().info("[INIT] Temp directory cleaned")
    except Exception:
        pass
