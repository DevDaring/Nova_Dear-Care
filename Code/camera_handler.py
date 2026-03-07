#!/usr/bin/env python3
"""
camera_handler.py - MIPI Stereo Camera handler via hobot_vio (libsrcampy) for Pocket ASHA on RDK S100.

Uses the D-Robotics srcampy API to capture from the on-board MIPI camera.
No ROS2 required.

Graceful failure: returns None if camera unavailable.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils import get_logger

_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


def check_camera_available() -> bool:
    """Check if the MIPI camera can be opened via libsrcampy."""
    try:
        from hobot_vio import libsrcampy
        cam = libsrcampy.Camera()
        ret = cam.open_cam(0, -1, 30, 640, 480)
        if ret == 0:
            cam.close_cam()
            return True
        return False
    except Exception:
        return False


def assess_quality(image_path: str) -> dict:
    """Assess image quality (blur, brightness). Returns dict with 'ok' bool."""
    try:
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            return {"ok": False, "reason": "Cannot read image"}
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = gray.mean()
        ok = lap_var > 50 and 30 < brightness < 235
        reason = ""
        if lap_var <= 50:
            reason = "Image is too blurry"
        elif brightness <= 30:
            reason = "Image is too dark"
        elif brightness >= 235:
            reason = "Image is too bright"
        return {"ok": ok, "blur_score": round(lap_var, 1), "brightness": round(brightness, 1), "reason": reason}
    except Exception as e:
        return {"ok": True, "reason": f"Quality check failed: {e}"}


def capture_image(output_path: Optional[str] = None, timeout_sec: float = 10.0) -> Optional[str]:
    """
    Capture a single image from the MIPI stereo camera via libsrcampy.
    Returns path to saved image or None on failure.
    """
    cam = None
    try:
        import numpy as np
        import cv2
        from hobot_vio import libsrcampy
        from config import (CAMERA_PIPE_ID, CAMERA_FPS,
                            CAMERA_WIDTH, CAMERA_HEIGHT,
                            ENCOUNTER_DIR, SNAPSHOT_PREFIX)

        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(ENCOUNTER_DIR / f"{SNAPSHOT_PREFIX}{ts}.jpg")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cam = libsrcampy.Camera()
        ret = cam.open_cam(CAMERA_PIPE_ID, -1, CAMERA_FPS, CAMERA_WIDTH, CAMERA_HEIGHT)
        if ret != 0:
            _logger().warning("[CAMERA] open_cam failed (ret=%d)", ret)
            return None

        # Allow sensor to stabilise, then grab a frame
        time.sleep(0.3)
        nv12_bytes = cam.get_img(2, CAMERA_WIDTH, CAMERA_HEIGHT)
        if nv12_bytes is None:
            _logger().warning("[CAMERA] get_img returned None")
            return None

        # NV12 → BGR
        h, w = CAMERA_HEIGHT, CAMERA_WIDTH
        nv12 = np.frombuffer(nv12_bytes, dtype=np.uint8).reshape((h * 3 // 2, w))
        bgr = cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)
        cv2.imwrite(output_path, bgr)
        _logger().info("[CAMERA] Saved: %s", output_path)
        return output_path

    except ImportError:
        _logger().warning("[CAMERA] hobot_vio not installed — camera unavailable")
        return None
    except Exception as e:
        _logger().error("[CAMERA] Capture error: %s", e)
        return None
    finally:
        if cam is not None:
            try:
                cam.close_cam()
            except Exception:
                pass
