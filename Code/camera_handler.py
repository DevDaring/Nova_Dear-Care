#!/usr/bin/env python3
"""
camera_handler.py - SC230AI MIPI Camera handler for Pocket ASHA on RDK S100.

Uses the C binary `get_vin_data -s 6` (sensor index 6 = SC230AI) to capture
RAW10 frames, then decodes them using linear 10-bit bitpacked unpack + Bayer
BGGR demosaic + gamma correction + auto white balance.

Why not libsrcampy?
  The Python API (hobot_vio.libsrcampy) does NOT include SC230AI in its
  compiled sensor list. It only has imx219, ar0820std, and ovx8bstd. The
  OVX8B wildcard chip_id=0xA55A falsely matches SC230AI and fails.

Prerequisites:
  - DIP switch SW2200 on Camera Expansion Board set to MCLK (DOWN)
  - Camera ribbon cable connected to J2200 (left) / J2201 (right)
  - numpy, opencv-python-headless installed

Graceful failure: returns None if camera unavailable.
"""

import os
import glob
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils import get_logger

_log = None

# SC230AI capture binary and parameters
_GET_VIN_DATA = "/app/multimedia_samples/sample_vin/get_vin_data/get_vin_data"
_SENSOR_INDEX = 6           # SC230AI in the get_vin_data sensor list
_RAW_WIDTH = 1920
_RAW_HEIGHT = 1080
_RAW_STRIDE = 2400          # 1920 * 10 / 8 = 2400 bytes per row
_EXPECTED_RAW_SIZE = _RAW_STRIDE * _RAW_HEIGHT  # 2,592,000 bytes


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


def check_camera_available() -> bool:
    """Check if the SC230AI sensor is detected on I2C bus 1."""
    try:
        result = subprocess.run(
            ["i2cdetect", "-y", "1"],
            capture_output=True, text=True, timeout=5
        )
        # SC230AI left sensor is at address 0x30
        return " 30 " in result.stdout or " 30\n" in result.stdout
    except Exception:
        return False


def _decode_raw10(raw_path: str):
    """
    Decode a linear 10-bit bitpacked RAW10 Bayer file to a BGR image.

    RDK S100 get_vin_data outputs LINEAR 10-bit bitpacked format:
      - Each row = 2400 bytes for 1920 pixels
      - Every 5 bytes = 40-bit LE bitstream containing 4 pixels
      - pixel0 = bits[0:9], pixel1 = bits[10:19], pixel2 = bits[20:29], pixel3 = bits[30:39]

    This is NOT MIPI CSI-2 RAW10 packed (where byte4 holds LSBs separately).
    """
    import numpy as np
    import cv2

    raw = np.fromfile(raw_path, dtype=np.uint8)
    if raw.size != _EXPECTED_RAW_SIZE:
        _logger().warning("[CAMERA] RAW file size %d != expected %d", raw.size, _EXPECTED_RAW_SIZE)
        return None

    data = raw.reshape(_RAW_HEIGHT, _RAW_STRIDE)

    # Unpack 4 pixels from every 5-byte group (40-bit LE bitstream)
    packed = data.reshape(_RAW_HEIGHT, _RAW_WIDTH // 4, 5)
    b = packed.astype(np.uint64)
    val40 = b[:, :, 0] | (b[:, :, 1] << 8) | (b[:, :, 2] << 16) | (b[:, :, 3] << 24) | (b[:, :, 4] << 32)

    img = np.zeros((_RAW_HEIGHT, _RAW_WIDTH), dtype=np.uint16)
    img[:, 0::4] = ((val40 >> 0) & 0x3FF).astype(np.uint16)
    img[:, 1::4] = ((val40 >> 10) & 0x3FF).astype(np.uint16)
    img[:, 2::4] = ((val40 >> 20) & 0x3FF).astype(np.uint16)
    img[:, 3::4] = ((val40 >> 30) & 0x3FF).astype(np.uint16)

    # Scale 10-bit to 16-bit for OpenCV demosaic
    img16 = (img << 6).astype(np.uint16)

    # Bayer BGGR demosaic (SC230AI default pattern)
    color = cv2.cvtColor(img16, cv2.COLOR_BayerBG2BGR)
    color_f = color.astype(np.float32) / 65535.0

    # Gamma correction (sensor outputs linear; displays expect sRGB ~2.2)
    color_f = np.power(np.clip(color_f, 0, 1), 1.0 / 2.2)

    # Auto white balance (gray world assumption)
    means = color_f.mean(axis=(0, 1))
    gray_mean = means.mean()
    wb_gains = gray_mean / (means + 1e-6)
    color_f = np.clip(color_f * wb_gains[np.newaxis, np.newaxis, :], 0, 1)

    # Contrast stretch (1st–99th percentile)
    p1, p99 = np.percentile(color_f, (1, 99))
    if p99 > p1:
        color_f = np.clip((color_f - p1) / (p99 - p1), 0, 1)

    return (color_f * 255).astype(np.uint8)


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


def capture_image(output_path: Optional[str] = None, timeout_sec: float = 15.0) -> Optional[str]:
    """
    Capture a single image from the SC230AI camera via get_vin_data.

    Pipeline:
      1. Run `get_vin_data -s 6` to capture a RAW10 frame
      2. Decode linear 10-bit bitpacked Bayer data
      3. Demosaic (BGGR) + gamma + AWB + contrast stretch
      4. Save as JPEG

    Returns path to saved JPEG or None on failure.
    """
    try:
        import cv2
        from config import ENCOUNTER_DIR, SNAPSHOT_PREFIX

        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(ENCOUNTER_DIR / f"{SNAPSHOT_PREFIX}{ts}.jpg")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if not os.path.isfile(_GET_VIN_DATA):
            _logger().warning("[CAMERA] get_vin_data binary not found at %s", _GET_VIN_DATA)
            return None

        # Capture directory (where get_vin_data writes .raw files)
        capture_dir = os.path.dirname(_GET_VIN_DATA)

        # Remove old .raw files from previous captures
        for old in glob.glob(os.path.join(capture_dir, "handle_*.raw")):
            try:
                os.remove(old)
            except OSError:
                pass

        # Run get_vin_data: send "g" (grab frame) then "q" (quit)
        proc = subprocess.run(
            ["sudo", _GET_VIN_DATA, "-s", str(_SENSOR_INDEX)],
            input="g\nq\n",
            capture_output=True, text=True,
            timeout=timeout_sec,
            cwd=capture_dir,
        )

        if proc.returncode != 0 and "failed" in (proc.stdout + proc.stderr).lower():
            _logger().warning("[CAMERA] get_vin_data failed: %s", proc.stdout[-200:] if proc.stdout else proc.stderr[-200:])
            return None

        # Find the newly created .raw file
        raw_files = sorted(glob.glob(os.path.join(capture_dir, "handle_*.raw")), key=os.path.getmtime)
        if not raw_files:
            _logger().warning("[CAMERA] No .raw file produced by get_vin_data")
            return None
        raw_path = raw_files[-1]

        # Decode RAW10 → BGR
        bgr = _decode_raw10(raw_path)
        if bgr is None:
            _logger().warning("[CAMERA] RAW10 decode failed")
            return None

        cv2.imwrite(output_path, bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
        _logger().info("[CAMERA] Saved: %s (%dx%d)", output_path, bgr.shape[1], bgr.shape[0])

        # Clean up raw file
        try:
            os.remove(raw_path)
        except OSError:
            pass

        return output_path

    except subprocess.TimeoutExpired:
        _logger().warning("[CAMERA] get_vin_data timed out after %.0fs", timeout_sec)
        return None
    except ImportError:
        _logger().warning("[CAMERA] numpy/opencv not installed — camera unavailable")
        return None
    except Exception as e:
        _logger().error("[CAMERA] Capture error: %s", e)
        return None
