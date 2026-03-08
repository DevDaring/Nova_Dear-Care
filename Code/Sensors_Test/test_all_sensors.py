#!/usr/bin/env python3
"""
test_all_sensors.py - Complete Hardware Diagnostic for Pocket ASHA

Tests ALL sensors and peripherals required by the Pocket ASHA system:
  1. MAX30102   — Pulse Oximeter (SpO2 + Heart Rate) via I2C
  2. BME280     — Temperature / Humidity / Pressure via I2C
  3. MIPI Camera — Stereo camera via ROS2
  4. Jabra Mic  — USB microphone via ALSA
  5. BT Speaker — Bluetooth speaker via PulseAudio
  6. AWS Cloud  — Bedrock, S3, Polly, Transcribe connectivity

For each device:
  - Checks if CONNECTED (physically present)
  - If connected, checks if WORKING (can read data / capture / record)

Usage:
    cd ~/Documents/AI_4_Bharat/Code
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Sensors_Test/test_all_sensors.py
"""

import os
import sys
import time
import subprocess
import json

# Add parent Code/ directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# Test Result Tracking
# ============================================================

_results = []


def _record(name, connected, working, details=""):
    _results.append({
        "name": name,
        "connected": connected,
        "working": working,
        "details": details,
    })
    conn_str = "CONNECTED" if connected else "NOT CONNECTED"
    work_str = "WORKING" if working else ("NOT WORKING" if connected else "SKIPPED")
    icon = "PASS" if (connected and working) else ("FAIL" if connected else "SKIP")
    print(f"  [{icon}] {name}: {conn_str} | {work_str}")
    if details:
        print(f"         {details}")


def _header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# 1. MAX30102 — Pulse Oximeter (I2C 0x57)
# ============================================================

def test_max30102():
    _header("1. MAX30102 — Pulse Oximeter (SpO2 / Heart Rate)")

    from config import MAX30102_I2C_BUS, MAX30102_I2C_ADDR
    bus = MAX30102_I2C_BUS
    addr = MAX30102_I2C_ADDR

    # Check connection via I2C
    connected = False
    try:
        import smbus2
        b = smbus2.SMBus(bus)
        b.read_byte(addr)
        connected = True
        b.close()
    except Exception:
        pass

    if not connected:
        # Also try i2cdetect
        try:
            out = subprocess.run(
                ["i2cdetect", "-y", str(bus)],
                capture_output=True, text=True, timeout=5
            )
            addr_hex = f"{addr:02x}"
            if addr_hex in out.stdout:
                connected = True
        except Exception:
            pass

    if not connected:
        _record("MAX30102", False, False,
                f"Not found on I2C bus {bus}, addr 0x{addr:02X}. "
                "Check wiring: VIN→3.3V(Pin1), GND→Pin6, SDA→Pin3(I2C5_SDA), SCL→Pin5(I2C5_SCL)")
        return

    # Check if working — read part ID register
    working = False
    details = ""
    try:
        import smbus2
        b = smbus2.SMBus(bus)
        part_id = b.read_byte_data(addr, 0xFF)  # PART_ID register
        if part_id == 0x15:
            working = True
            details = f"Part ID: 0x{part_id:02X} (correct)"
        else:
            details = f"Unexpected Part ID: 0x{part_id:02X} (expected 0x15)"

        # Try reading a sample if working
        if working:
            # Reset sensor
            b.write_byte_data(addr, 0x09, 0x40)  # MODE_CONFIG reset
            time.sleep(0.1)
            b.write_byte_data(addr, 0x09, 0x03)  # SpO2 mode
            b.write_byte_data(addr, 0x0A, 0x27)  # SpO2 config
            b.write_byte_data(addr, 0x0C, 0x24)  # LED1 current
            b.write_byte_data(addr, 0x0D, 0x24)  # LED2 current
            time.sleep(0.5)
            # Read FIFO
            d = b.read_i2c_block_data(addr, 0x07, 6)
            red = ((d[0] << 16) | (d[1] << 8) | d[2]) & 0x03FFFF
            ir = ((d[3] << 16) | (d[4] << 8) | d[5]) & 0x03FFFF
            details += f" | Sample: RED={red}, IR={ir}"
            if ir < 5000:
                details += " (no finger detected — place finger on sensor for readings)"
            else:
                details += " (finger detected!)"
        b.close()
    except Exception as e:
        details = f"Read error: {e}"

    _record("MAX30102", connected, working, details)


# ============================================================
# 2. BME280 — Temperature / Humidity / Pressure (I2C 0x76)
# ============================================================

def test_bme280():
    _header("2. BME280 — Temperature / Humidity / Pressure")

    from config import BME280_I2C_BUS, BME280_I2C_ADDR
    bus = BME280_I2C_BUS
    addr = BME280_I2C_ADDR

    # Check connection
    connected = False
    try:
        import smbus2
        b = smbus2.SMBus(bus)
        b.read_byte(addr)
        connected = True
        b.close()
    except Exception:
        pass

    if not connected:
        try:
            out = subprocess.run(
                ["i2cdetect", "-y", str(bus)],
                capture_output=True, text=True, timeout=5
            )
            addr_hex = f"{addr:02x}"
            if addr_hex in out.stdout:
                connected = True
        except Exception:
            pass

    if not connected:
        _record("BME280", False, False,
                f"Not found on I2C bus {bus}, addr 0x{addr:02X}. "
                "Check wiring: VIN→3.3V, GND→GND, SDA→I2C1_SDA, SCL→I2C1_SCL")
        return

    # Check if working — read chip ID and take a reading
    working = False
    details = ""
    try:
        import smbus2
        b = smbus2.SMBus(bus)
        chip_id = b.read_byte_data(addr, 0xD0)
        valid_ids = {0x58: "BMP280", 0x60: "BME280"}
        chip_name = valid_ids.get(chip_id, None)

        if chip_name:
            details = f"Chip: {chip_name} (ID: 0x{chip_id:02X})"

            # Try bme280 library first
            try:
                import bme280 as bme280_lib
                calib = bme280_lib.load_calibration_params(b, addr)
                data = bme280_lib.sample(b, addr, calib)
                working = True
                details += (f" | Temp: {data.temperature:.1f}°C, "
                            f"Humidity: {data.humidity:.1f}%, "
                            f"Pressure: {data.pressure:.1f} hPa")
            except ImportError:
                # Raw register read fallback
                b.write_byte_data(addr, 0xF4, 0x25)  # Forced mode
                time.sleep(0.05)
                raw = b.read_i2c_block_data(addr, 0xFA, 3)
                raw_temp = ((raw[0] << 16) | (raw[1] << 8) | raw[2]) >> 4
                temp_approx = raw_temp / 5120.0
                working = True
                details += f" | Raw temp (approx): {temp_approx:.1f}°C (install bme280 lib for accuracy)"
        else:
            details = f"Unknown chip ID: 0x{chip_id:02X} (expected 0x58 or 0x60)"
        b.close()
    except Exception as e:
        details = f"Read error: {e}"

    _record("BME280", connected, working, details)


# ============================================================
# 3. MIPI Camera — hobot_vio libsrcampy
# ============================================================

def test_camera():
    _header("3. MIPI Camera — Stereo Camera (libsrcampy)")

    connected = False
    working = False
    details = ""

    # Check if hobot_vio is available
    try:
        from hobot_vio import libsrcampy
    except ImportError:
        _record("MIPI Camera", False, False, "hobot_vio not installed")
        return

    # Try to open the camera
    cam = None
    try:
        cam = libsrcampy.Camera()
        ret = cam.open_cam(0, -1, 30, 1920, 1080)
        if ret == 0:
            connected = True
            details = "Camera opened (pipe 0, 1920x1080@30fps)"
        else:
            # Also try video_index 0 and 1 explicitly
            for vidx in [0, 1]:
                cam2 = libsrcampy.Camera()
                ret2 = cam2.open_cam(0, vidx, 30, 1920, 1080)
                if ret2 == 0:
                    cam = cam2
                    connected = True
                    details = f"Camera opened (pipe 0, video_idx={vidx}, 1920x1080@30fps)"
                    break
            if not connected:
                hint = ("open_cam returned -1. No camera sensor found. "
                        "Steps to fix:\n"
                        "         1. Power off the board\n"
                        "         2. Reseat the MIPI ribbon cable firmly into the CAM connector\n"
                        "         3. Ensure gold contacts face the board (away from latch)\n"
                        "         4. Lock the latch and power on")
                _record("MIPI Camera", False, False, hint)
                return
    except Exception as e:
        _record("MIPI Camera", False, False, f"open_cam error: {e}")
        return

    # Try capturing a frame
    try:
        import time
        time.sleep(0.3)
        nv12_bytes = cam.get_img(2, 1920, 1080)
        if nv12_bytes is not None and len(nv12_bytes) > 0:
            import numpy as np
            import cv2
            h, w = 1080, 1920
            nv12 = np.frombuffer(nv12_bytes, dtype=np.uint8).reshape((h * 3 // 2, w))
            bgr = cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)
            test_path = "/tmp/pocket_asha_cam_test.jpg"
            cv2.imwrite(test_path, bgr)
            size = os.path.getsize(test_path)
            working = True
            details += f" | Captured frame: {bgr.shape[1]}x{bgr.shape[0]}, {size} bytes"
            os.remove(test_path)
        else:
            details += " | get_img returned no data"
    except Exception as e:
        details += f" | Capture error: {e}"
    finally:
        try:
            cam.close_cam()
        except Exception:
            pass

    _record("MIPI Camera", connected, working, details)


# ============================================================
# 4. Jabra USB Microphone
# ============================================================

def test_microphone():
    _header("4. Jabra USB Microphone")

    connected = False
    working = False
    details = ""

    # Check ALSA recording devices
    try:
        result = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, timeout=5
        )
        output = result.stdout.lower()
        if "jabra" in output or "usb" in output:
            connected = True
            # Extract card info
            for line in result.stdout.split("\n"):
                if "jabra" in line.lower() or "usb" in line.lower():
                    details = f"Device: {line.strip()}"
                    break
        else:
            details = "No Jabra/USB microphone found in ALSA devices"
    except Exception as e:
        details = f"ALSA check error: {e}"

    if not connected:
        _record("Jabra Microphone", False, False, details)
        return

    # Test recording 2 seconds
    test_file = "/tmp/pocket_asha_mic_test.wav"
    try:
        from config import JABRA_CAPTURE_DEV, AUDIO_SAMPLE_RATE
        proc = subprocess.run(
            ["arecord", "-D", JABRA_CAPTURE_DEV, "-f", "S16_LE",
             "-r", str(AUDIO_SAMPLE_RATE), "-c", "1", "-d", "2", test_file],
            capture_output=True, text=True, timeout=10
        )
        if os.path.exists(test_file):
            size = os.path.getsize(test_file)
            if size > 1000:
                working = True
                details += f" | Recording: {size} bytes (2s)"
            else:
                details += f" | Recording too small: {size} bytes"
            os.remove(test_file)
        else:
            details += f" | Recording failed: {proc.stderr}"
    except subprocess.TimeoutExpired:
        details += " | Recording timed out"
    except Exception as e:
        details += f" | Recording error: {e}"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

    _record("Jabra Microphone", connected, working, details)


# ============================================================
# 5. Bluetooth Speaker (Bose)
# ============================================================

def test_speaker():
    _header("5. Bluetooth Speaker (Bose)")

    connected = False
    working = False
    details = ""

    from config import BOSE_SINK

    # Check PulseAudio sinks
    try:
        result = subprocess.run(
            ["pactl", "list", "sinks", "short"],
            capture_output=True, text=True, timeout=5
        )
        sinks = result.stdout.strip()
        if BOSE_SINK and BOSE_SINK in sinks:
            connected = True
            details = f"Sink: {BOSE_SINK}"
        elif "bluez" in sinks.lower():
            connected = True
            for line in sinks.split("\n"):
                if "bluez" in line.lower():
                    details = f"Bluetooth sink found: {line.strip()}"
                    break
        else:
            details = f"No Bluetooth sink found. Available sinks:\n         {sinks}"
    except Exception as e:
        details = f"PulseAudio check error: {e}"

    if not connected:
        _record("Bluetooth Speaker", False, False, details)
        return

    # Test playback — generate and play a short beep
    test_file = "/tmp/pocket_asha_beep_test.wav"
    try:
        # Generate a 0.5s 440Hz beep with Python
        import struct
        import wave
        sample_rate = 16000
        duration = 0.5
        frequency = 440
        n_samples = int(sample_rate * duration)
        import math
        samples = [int(16000 * math.sin(2 * math.pi * frequency * t / sample_rate))
                   for t in range(n_samples)]
        with wave.open(test_file, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

        proc = subprocess.run(
            ["paplay", test_file],
            capture_output=True, text=True, timeout=5
        )
        if proc.returncode == 0:
            working = True
            details += " | Beep played successfully (did you hear it?)"
        else:
            details += f" | Playback failed: {proc.stderr}"
    except subprocess.TimeoutExpired:
        details += " | Playback timed out"
    except Exception as e:
        details += f" | Playback error: {e}"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

    _record("Bluetooth Speaker", connected, working, details)


# ============================================================
# 6. I2C Bus Overview
# ============================================================

def test_i2c_bus():
    _header("6. I2C Bus Scan")

    try:
        result = subprocess.run(
            ["i2cdetect", "-y", "1"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"  I2C Bus 1 devices:\n{result.stdout}")
        else:
            print(f"  i2cdetect failed: {result.stderr}")
            print("  Try: sudo apt install i2c-tools")
    except FileNotFoundError:
        print("  i2cdetect not found. Install: sudo apt install i2c-tools")
    except Exception as e:
        print(f"  I2C scan error: {e}")


# ============================================================
# 7. AWS Cloud Services
# ============================================================

def test_aws():
    _header("7. AWS Cloud Services Connectivity")

    from utils import check_internet

    online = check_internet()
    if not online:
        _record("AWS (Internet)", False, False, "No internet connection to s3.amazonaws.com")
        _record("AWS Bedrock", False, False, "Requires internet")
        _record("AWS S3", False, False, "Requires internet")
        _record("AWS Polly", False, False, "Requires internet")
        _record("AWS Transcribe", False, False, "Requires internet")
        return

    _record("AWS (Internet)", True, True, "Connected to AWS")

    # Bedrock
    try:
        from aws_handler import invoke_llm
        resp = invoke_llm("Say OK.", max_tokens=10)
        _record("AWS Bedrock", True, bool(resp), f"Response: {resp[:50]}" if resp else "No response")
    except Exception as e:
        _record("AWS Bedrock", True, False, f"Error: {e}")

    # S3
    try:
        import boto3
        from config import S3_BUCKET_NAME, AWS_REGION
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        _record("AWS S3", True, True, f"Bucket: {S3_BUCKET_NAME}")
    except Exception as e:
        _record("AWS S3", True, False, f"Error: {e}")

    # Polly
    try:
        import boto3
        from config import AWS_REGION
        polly = boto3.client("polly", region_name=AWS_REGION)
        voices = polly.describe_voices(LanguageCode="en-IN")
        count = len(voices.get("Voices", []))
        _record("AWS Polly", True, count > 0, f"{count} en-IN voices available")
    except Exception as e:
        _record("AWS Polly", True, False, f"Error: {e}")

    # Transcribe
    try:
        import boto3
        from config import AWS_REGION
        tc = boto3.client("transcribe", region_name=AWS_REGION)
        tc.list_transcription_jobs(MaxResults=1)
        _record("AWS Transcribe", True, True, "Service accessible")
    except Exception as e:
        _record("AWS Transcribe", True, False, f"Error: {e}")


# ============================================================
# 8. PaddleOCR Engine
# ============================================================

def test_paddleocr():
    _header("8. PaddleOCR Engine")

    connected = True  # Software, always "connected"
    working = False
    details = ""

    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
        working = True
        details = "PaddleOCR loaded successfully"

        # Test with a simple image if OpenCV available
        try:
            import numpy as np
            import cv2
            # Create a white image with black text
            img = np.ones((100, 400, 3), dtype=np.uint8) * 255
            cv2.putText(img, "POCKET ASHA TEST", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            test_path = "/tmp/pocket_asha_ocr_test.png"
            cv2.imwrite(test_path, img)

            result = ocr.ocr(test_path, cls=False)
            if result and result[0]:
                texts = [line[1][0] for line in result[0]]
                details += f" | OCR output: {' '.join(texts)}"
            else:
                details += " | OCR returned no text (model may need warmup)"

            os.remove(test_path)
        except Exception as e:
            details += f" | OCR test image error: {e}"

        # Cleanup
        del ocr
        import gc
        gc.collect()

    except ImportError:
        connected = False
        details = "PaddleOCR not installed. Run: pip3 install paddleocr"
    except Exception as e:
        details = f"PaddleOCR error: {e}"

    _record("PaddleOCR", connected, working, details)


# ============================================================
# Summary Report
# ============================================================

def print_summary():
    _header("DIAGNOSTIC SUMMARY")

    total = len(_results)
    passed = sum(1 for r in _results if r["connected"] and r["working"])
    not_connected = sum(1 for r in _results if not r["connected"])
    failed = sum(1 for r in _results if r["connected"] and not r["working"])

    print(f"\n  Total checks:   {total}")
    print(f"  Passed:         {passed}")
    print(f"  Not connected:  {not_connected}")
    print(f"  Failed:         {failed}")
    print()

    if failed > 0:
        print("  FAILED DEVICES (connected but not working):")
        for r in _results:
            if r["connected"] and not r["working"]:
                print(f"    - {r['name']}: {r['details']}")
        print()

    if not_connected > 0:
        print("  NOT CONNECTED:")
        for r in _results:
            if not r["connected"]:
                print(f"    - {r['name']}: {r['details']}")
        print()

    # System info
    print("  SYSTEM INFO:")
    try:
        import platform
        print(f"    Platform:  {platform.machine()} / {platform.system()} {platform.release()}")
        print(f"    Python:    {platform.python_version()}")
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line or "MemAvailable" in line:
                    print(f"    {line.strip()}")
    except Exception:
        pass
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                print(f"    Disk:      {lines[1].split()[-2]} used / {lines[1].split()[-4]} total")
    except Exception:
        pass

    print(f"\n{'='*60}")

    # Save report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostic_report.json")
    try:
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "passed": passed,
            "not_connected": not_connected,
            "failed": failed,
            "results": _results,
        }
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved to: {report_path}")
    except Exception:
        pass


# ============================================================
# Main
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("  POCKET ASHA — Full Hardware Diagnostic")
    print("  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    test_max30102()
    test_bme280()
    test_camera()
    test_microphone()
    test_speaker()
    test_i2c_bus()
    test_aws()
    test_paddleocr()
    print_summary()


if __name__ == "__main__":
    main()
