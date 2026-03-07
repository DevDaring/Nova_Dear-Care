# Sensor Setup Guide — Pocket ASHA on RDK S100

> **Board:** D-Robotics RDK S100 V1P0  
> **OS:** Ubuntu 22.04.5 LTS (aarch64)  
> **Python:** 3.10.12 (system-wide, no venv)  
> **Kernel:** Linux 6.1.112-rt43

This document explains how each sensor/peripheral was set up on the RDK S100 for the Pocket ASHA project, what packages were installed, how to verify connections, and troubleshooting steps.

---

## Table of Contents

1. [General Prerequisites](#1-general-prerequisites)
2. [MAX30102 — Pulse Oximeter (SpO2 / Heart Rate)](#2-max30102--pulse-oximeter-spo2--heart-rate)
3. [BME280 — Temperature / Humidity / Pressure](#3-bme280--temperature--humidity--pressure)
4. [MIPI Stereo Camera](#4-mipi-stereo-camera)
5. [Jabra USB Microphone / Headphone](#5-jabra-usb-microphone--headphone)
6. [Bluetooth Speaker (Bose)](#6-bluetooth-speaker-bose)
7. [PaddleOCR Engine](#7-paddleocr-engine)
8. [AWS Cloud Services](#8-aws-cloud-services)
9. [Running the Diagnostic](#9-running-the-diagnostic)

---

## 1. General Prerequisites

### System Packages Installed

```bash
sudo apt update
sudo apt install -y i2c-tools python3-smbus python3-pip alsa-utils pulseaudio-utils bluez
```

### Python Packages Installed (system-wide)

```bash
pip3 install smbus2==0.6.0 bme280 numpy==1.26.4 opencv-python==4.6.0.66 \
    boto3 pyttsx3==2.99 SpeechRecognition==3.14.5 python-dotenv cryptography Flask
```

### Critical: LD_LIBRARY_PATH Conflict

The RDK S100 ships with Hobot multimedia libraries in `LD_LIBRARY_PATH` that conflict with PaddleOCR and some Python packages. **Always run Python scripts with:**

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 <script.py>
```

Without this, you will see segfaults or library version mismatches.

### I2C Bus Enable

I2C must be enabled on the board. Verify with:

```bash
ls /dev/i2c-*
# Should show: /dev/i2c-0  /dev/i2c-1  /dev/i2c-2  /dev/i2c-3  /dev/i2c-4  /dev/i2c-5
```

If I2C is not enabled, run `sudo srpi-config` → 3 (Interface Options) → I3 → Enable I2C → Reboot.

---

## 2. MAX30102 — Pulse Oximeter (SpO2 / Heart Rate)

### What It Does

Measures blood oxygen saturation (SpO2) and heart rate using infrared/red LED light through the finger.

### Connection (I2C)

| MAX30102 Pin | RDK S100 40-Pin Header | Purpose |
|---|---|---|
| VIN (Red) | Pin 1 | 3.3V Power |
| GND (Black) | Pin 6 (or 9, 14, 20, 25) | Ground |
| SDA (Green) | Pin 3 | I2C Data (I2C1 SDA) |
| SCL (Blue) | Pin 5 | I2C Clock (I2C1 SCL) |
| INT | Leave unconnected | Interrupt (optional) |

- **I2C Bus:** 1 (`/dev/i2c-1`)
- **I2C Address:** `0x57`

### Packages Installed

```bash
pip3 install smbus2==0.6.0
sudo apt install -y i2c-tools
```

### How to Verify Connection

```bash
# Scan I2C bus 1 — should show "57" in the grid
i2cdetect -y 1

# Python quick test
python3 -c "
import smbus2
bus = smbus2.SMBus(1)
part_id = bus.read_byte_data(0x57, 0xFF)
print(f'MAX30102 Part ID: 0x{part_id:02X} (expected: 0x15)')
bus.close()
"
```

### How It Works in Code

- File: `sensor_handler.py` → class `MAX30102Reader`
- Reads raw RED and IR LED values from FIFO registers
- Calculates SpO2 using R-ratio formula: `SpO2 = 110 - 25 × (RED_AC/RED_DC) / (IR_AC/IR_DC)`
- Heart rate estimated via IR signal peak detection
- Registers used: MODE_CONFIG (0x09), SPO2_CONFIG (0x0A), LED1_PA (0x0C), LED2_PA (0x0D), FIFO_DATA (0x07)

### Troubleshooting

| Problem | Fix |
|---|---|
| `0x57` not in i2cdetect | Check wiring — VIN→3.3V, GND→GND, SDA→Pin3, SCL→Pin5 |
| Part ID ≠ 0x15 | You may have a MAX30100 (0x11) — different register map |
| SpO2 reads 0 | Place finger firmly on sensor; wait 10–15s for warmup |
| "Bus error" | I2C not enabled — run `sudo srpi-config` |

### Current Status

**NOT CONNECTED** — Sensor not wired to the board yet. Wire to I2C bus 1, address 0x57.

---

## 3. BME280 — Temperature / Humidity / Pressure

### What It Does

Measures ambient temperature (°C), relative humidity (%), and barometric pressure (hPa). Used for environmental context in patient encounters.

### Connection (I2C)

| BME280 Pin | RDK S100 40-Pin Header | Purpose |
|---|---|---|
| VIN | Pin 1 | 3.3V Power |
| GND | Pin 6 (or 9, 14, 20, 25) | Ground |
| SDA | Pin 3 | I2C Data (I2C1 SDA) |
| SCL | Pin 5 | I2C Clock (I2C1 SCL) |
| CSB/CS | Leave unconnected or tie HIGH | Chip select (optional) |
| SDO | Leave unconnected or tie LOW | Address select — LOW for 0x76, HIGH for 0x77 |

- **I2C Bus:** 1 (`/dev/i2c-1`)
- **I2C Address:** `0x76` (default, SDO low) or `0x77` (SDO high)

### Packages Installed

```bash
pip3 install smbus2==0.6.0 bme280
sudo apt install -y i2c-tools
```

### How to Verify Connection

```bash
# Scan I2C bus 1 — should show "76" (or "77")
i2cdetect -y 1

# Python quick test
python3 -c "
import smbus2, bme280
bus = smbus2.SMBus(1)
calib = bme280.load_calibration_params(bus, 0x76)
data = bme280.sample(bus, 0x76, calib)
print(f'Temp: {data.temperature:.1f}°C  Humidity: {data.humidity:.1f}%  Pressure: {data.pressure:.1f} hPa')
bus.close()
"
```

### How It Works in Code

- File: `sensor_handler.py` → class `BME280Reader`
- Primary method: Uses `bme280` Python library for calibrated readings
- Fallback: Raw register reads (0xFA–0xFC for temp) if library unavailable
- Chip ID register: `0xD0` → expects `0x60` (BME280) or `0x58` (BMP280)

### Troubleshooting

| Problem | Fix |
|---|---|
| `0x76` not in i2cdetect | Check wiring; try 0x77 (SDO tied high) |
| Chip ID = 0x58 (BMP280) | BMP280 has no humidity — only temp+pressure |
| All readings = 0 | Sensor in sleep mode — code sends forced-mode command |

### Current Status

**NOT CONNECTED** — Sensor not wired to the board yet. Both MAX30102 and BME280 share the same I2C bus 1 (Pin 3 SDA, Pin 5 SCL).

---

## 4. MIPI Stereo Camera

### What It Does

Captures patient photos, prescription images (for OCR), and wound documentation.

### Connection

The RDK S100 has MIPI CSI camera connectors. The SDK auto-detects the sensor on:
- **vcon@0** → I2C bus 1, MIPI RX PHY 0
- **vcon@1** → I2C bus 2, MIPI RX PHY 1

Insert the ribbon cable into the **CAM** connector (not the DSI/display connector):
1. Power off the board
2. Lift the latch on the MIPI CSI connector
3. Insert ribbon cable with **gold contacts facing the PCB** (towards the board)
4. Close the latch firmly
5. Power on

### Packages / Libraries Used

```bash
# Pre-installed on RDK S100
# hobot-vio 4.0.4 provides libsrcampy
python3 -c "from hobot_vio import libsrcampy; print('hobot_vio OK')"
```

**Key:** The camera is accessed using `hobot_vio.libsrcampy` — the D-Robotics native camera API. **Not ROS2.**

### Supported Sensors

The SDK includes drivers for these sensors (found in `/app/multimedia_samples/vp_sensors/`):
- IMX219, SC132GS, SC230AI, SC1336, AR0820C, OVX3C

### How to Verify Connection

```bash
# Check if sensor appears on I2C bus 1 or 2
i2cdetect -y 1    # Camera connector 0
i2cdetect -y 2    # Camera connector 1

# Python quick test (must use env prefix!)
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 -c "
from hobot_vio import libsrcampy
cam = libsrcampy.Camera()
ret = cam.open_cam(0, -1, 30, 1920, 1080)
print(f'open_cam ret={ret}')
if ret == 0:
    print('Camera DETECTED and WORKING!')
    cam.close_cam()
else:
    print('Camera NOT detected — check cable')
"
```

### How It Works in Code

- File: `camera_handler.py`
- API: `libsrcampy.Camera()` → `open_cam(pipe_id, video_index, fps, width, height)` → `get_img(channel, w, h)` → `close_cam()`
- Image format: NV12 (YUV) → Converted to BGR using `cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)`
- Parameters: `pipe_id=0`, `video_index=-1` (auto-detect), `fps=30`, resolution `1920x1080`

### Troubleshooting

| Problem | Fix |
|---|---|
| `No camera sensor found` | Reseat MIPI cable; ensure correct connector (CAM, not DSI) |
| `open_cam returned -1` | Sensor not detected on I2C — ribbon cable loose or wrong connector |
| `pipeline stop failed` | Camera resource busy — reboot and try again |
| Works in C samples but not Python | Always use `env -u LD_LIBRARY_PATH -u LD_PRELOAD` |
| Which connector? | Try both MIPI connectors — board has vcon@0 (bus 1) and vcon@1 (bus 2) |

### Current Status

**NOT CONNECTED** — `open_cam()` returns -1. The SDK searches I2C bus 1 and bus 2 but finds no sensor. Physical cable needs reseating or camera may be on wrong connector. The board has multiple MIPI connectors — try the other one.

---

## 5. Jabra USB Microphone / Headphone

### What It Does

Records patient voice for speech-to-text (AWS Transcribe) and plays back TTS audio (AWS Polly / pyttsx3). The Jabra EVOLVE 20 MS is a USB headset with both microphone and speaker.

### Connection

Simply plug the Jabra USB cable into any USB port on the RDK S100.

### Packages Installed

```bash
sudo apt install -y alsa-utils pulseaudio-utils
pip3 install SpeechRecognition==3.14.5 pyttsx3==2.99
```

### How to Verify Connection

```bash
# Check ALSA capture devices — should show "Jabra EVOLVE 20 MS"
arecord -l

# Check ALSA playback — same device
aplay -l

# Check USB
lsusb | grep -i jabra

# Record 3-second test
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/test_jabra.wav

# Play it back through Jabra speaker
aplay -D plughw:1,0 /tmp/test_jabra.wav
```

### Key Configuration

- **ALSA capture device:** `plughw:1,0` (Card 1, Device 0)
- **ALSA playback device:** `plughw:1,0`
- **Sample rate:** 16000 Hz (16kHz)
- **Format:** S16_LE (16-bit signed little-endian)
- **Channels:** 1 (mono)

> **Important:** Use `plughw:1,0` not `hw:1,0`. The `plughw` wrapper allows shared access with PulseAudio/other processes. Using `hw:` will fail with "Device or resource busy" if PulseAudio is running.

### How It Works in Code

- File: `voice_handler.py`
- Recording: `arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d <seconds> <file>`
- Playback: AWS Polly generates speech → saved as MP3/WAV → played via `aplay -D plughw:1,0`
- Fallback: `pyttsx3` for offline TTS, `SpeechRecognition` for offline STT use

### Troubleshooting

| Problem | Fix |
|---|---|
| "Device or resource busy" | Use `plughw:1,0` instead of `hw:1,0`; or `pkill -9 arecord` |
| Card number changed | Run `arecord -l` to find new card number; update config |
| No sound on playback | Check PulseAudio: `pactl list sinks short` |
| Recording is silent | Unmute mic: `amixer -c 1 set Mic unmute` |

### Current Status

**CONNECTED & WORKING** — Jabra EVOLVE 20 MS detected as Card 1, Device 0. Recording confirmed (64KB for 2s).

---

## 6. Bluetooth Speaker (Bose)

### What It Does

Plays TTS audio responses and alerts to the patient/ASHA worker via Bluetooth speaker (louder than Jabra for group settings).

### Connection

```bash
# Open Bluetooth control
bluetoothctl

# Inside bluetoothctl:
power on
agent on
default-agent
scan on
# Wait for "Bose" device to appear, then:
pair 78:2B:64:DD:68:CF
trust 78:2B:64:DD:68:CF
connect 78:2B:64:DD:68:CF
quit
```

### Packages Used

```bash
sudo apt install -y pulseaudio-utils bluez
```

### How to Verify Connection

```bash
# Check PulseAudio sinks — should show bluez_sink
pactl list sinks short

# Expected sink name format:
# bluez_sink.78_2B_64_DD_68_CF.a2dp_sink

# Test playback
paplay -d bluez_sink.78_2B_64_DD_68_CF.a2dp_sink /tmp/test.wav
```

### Key Configuration

- **PulseAudio sink:** `bluez_sink.78_2B_64_DD_68_CF.a2dp_sink`
- **MAC address:** `78:2B:64:DD:68:CF`
- Set in `.env` file: `BOSE_SINK=bluez_sink.78_2B_64_DD_68_CF.a2dp_sink`

### How It Works in Code

- File: `voice_handler.py`
- Playback: `paplay -d <BOSE_SINK> <audio_file>`
- Falls back to Jabra ALSA playback if Bluetooth speaker is unavailable

### Troubleshooting

| Problem | Fix |
|---|---|
| Not showing in `pactl` | Pair again via `bluetoothctl connect <MAC>` |
| Audio stuttering | Disable WiFi power saving (see below) |
| "Connection refused" | Bose speaker might be off or paired to another device |

**Disable WiFi power saving** (prevents BT audio glitches):
```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/99-no-wifi-powersave.conf >/dev/null <<'EOF'
[connection]
wifi.powersave=2
EOF
sudo systemctl restart NetworkManager
```

### Current Status

**NOT CONNECTED** — Bose speaker not paired in this session.

---

## 7. PaddleOCR Engine

### What It Does

Offline OCR for reading prescriptions, medicine labels, and Aadhaar cards. Falls back to AWS Textract when online.

### Packages Installed

```bash
pip3 install paddlepaddle-xpu==2.6.1 paddleocr==2.7.0.3
```

> The `paddlepaddle-xpu` version is specific to the RDK S100's compute architecture.

### How to Verify

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
print('PaddleOCR loaded OK')
"
```

### Key Details

- Models auto-download to `~/.paddleocr/whl/` on first run (det, rec, cls)
- **Must** use `env -u LD_LIBRARY_PATH -u LD_PRELOAD` or PaddlePaddle crashes
- File: `ocr_handler.py` — PaddleOCR offline, AWS Textract online
- Supports: English, Hindi, and other Indian language scripts

### Current Status

**WORKING** — PaddleOCR loads and returns correct OCR text.

---

## 8. AWS Cloud Services

### What They Do

| Service | Purpose |
|---|---|
| **Bedrock** (Nova Lite) | AI-powered clinical reasoning, symptom analysis, Hindi responses |
| **S3** | Cloud storage for encounter data, photos, audio |
| **Polly** | Neural text-to-speech in Indian languages (Kajal voice) |
| **Transcribe** | Speech-to-text for patient voice in Indian English |
| **Textract** | Online OCR fallback for prescriptions |
| **Lambda** | Clinical notes generation (serverless) |

### Packages Installed

```bash
pip3 install boto3
sudo apt install -y awscli
aws configure   # Set access key, secret key, region us-east-1
```

### How to Verify

```bash
# Check AWS connectivity
aws sts get-caller-identity

# Check Bedrock
aws bedrock-runtime invoke-model \
    --model-id amazon.nova-lite-v1:0 \
    --body '{"messages":[{"role":"user","content":[{"text":"hello"}]}]}' \
    /tmp/bedrock_test.json

# Check S3 bucket
aws s3 ls s3://pocket-asha-data-343104031497/

# Check Polly voices
aws polly describe-voices --language-code en-IN --query 'Voices[*].Name'
```

### Key Configuration (in `.env`)

```
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your_key>
AWS_SECRET_ACCESS_KEY=<your_secret>
S3_BUCKET=pocket-asha-data-<account_id>
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

### Current Status

**ALL WORKING** — Bedrock, S3, Polly, Transcribe all verified.

---

## 9. Running the Diagnostic

The diagnostic script tests all sensors and services in one run:

```bash
cd ~/Documents/AI_4_Bharat/Code
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Sensors_Test/test_all_sensors.py
```

### What It Checks

| # | Test | Detection Method |
|---|---|---|
| 1 | MAX30102 | I2C probe at 0x57 on bus 1 + Part ID register read |
| 2 | BME280 | I2C probe at 0x76 on bus 1 + Chip ID register read |
| 3 | MIPI Camera | `libsrcampy.Camera().open_cam()` + frame capture |
| 4 | Jabra Mic | `arecord -l` device list + 2-second recording test |
| 5 | BT Speaker | `pactl list sinks short` + beep playback test |
| 6 | I2C Bus | Full `i2cdetect -y 1` scan |
| 7 | AWS Services | Bedrock invoke, S3 list, Polly voices, Transcribe access |
| 8 | PaddleOCR | Engine load + test image OCR |

### Output

- Console: Color-coded `[PASS]` / `[FAIL]` / `[SKIP]` per test
- JSON: `Sensors_Test/diagnostic_report.json` with full machine-readable results

### Latest Results (March 8, 2026)

```
Total checks:   11
Passed:          7  (Jabra, AWS×5, PaddleOCR)
Not connected:   4  (MAX30102, BME280, MIPI Camera, Bose BT)
Failed:          0
```

---

## Quick Reference: Pin Mapping

```
RDK S100 — 40-Pin Header (relevant pins)
═══════════════════════════════════════
 Pin 1  [3.3V Power] ● ● [5V Power]  Pin 2
 Pin 3  [I2C1 SDA]   ● ● [5V Power]  Pin 4
 Pin 5  [I2C1 SCL]   ● ● [GND]       Pin 6
 ...
 Pin 9  [GND]        ● ●             Pin 10
 ...
 Pin 14 [GND]        ● ●             Pin 15
 ...
 Pin 20 [GND]        ● ●             Pin 21
 ...
 Pin 25 [GND]        ● ●             Pin 26
═══════════════════════════════════════

Both MAX30102 and BME280 share:
  VIN → Pin 1 (3.3V)
  GND → Pin 6
  SDA → Pin 3 (I2C1 SDA)
  SCL → Pin 5 (I2C1 SCL)
```
