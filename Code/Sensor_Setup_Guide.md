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

### Connection (I2C via J24 40-Pin Header)

| MAX30102 Pin | RDK S100 J24 Header | Purpose |
|---|---|---|
| VIN (Red) | Pin 1 | 3.3V Power |
| GND (Black) | Pin 6 (or 9, 14, 20, 25) | Ground |
| SDA (Green) | Pin 3 | I2C Data (**I2C5_SDA_3V3**) |
| SCL (Blue) | Pin 5 | I2C Clock (**I2C5_SCL_3V3**) |
| INT | Leave unconnected | Interrupt (optional) |

- **I2C Bus:** 5 (`/dev/i2c-5`)
- **I2C Address:** `0x57`

> **Important:** The RDK S100's 40-pin header (J24) uses **I2C bus 5**, not bus 1. Bus 1 is used by the left MIPI camera (SC230AI at 0x30). This was confirmed via `i2cdetect -y 5`.

### Packages Installed

```bash
pip3 install smbus2==0.6.0
sudo apt install -y i2c-tools
```

### How to Verify Connection

```bash
# Scan I2C bus 5 — should show "57" in the grid
i2cdetect -y 5

# Verify Part ID (should return 0x15 for MAX30102)
i2cget -y 5 0x57 0xFF

# Python quick test
python3 -c "
import smbus2
bus = smbus2.SMBus(5)
part_id = bus.read_byte_data(0x57, 0xFF)
rev_id = bus.read_byte_data(0x57, 0xFE)
print(f'MAX30102 Part ID: 0x{part_id:02X} (expected: 0x15), Rev: 0x{rev_id:02X}')
bus.close()
"
```

### Dedicated Test Script

A comprehensive test script is available at `Sensors_Test/test_pulse_sensor.py`:

```bash
cd ~/Documents/AI_4_Bharat/Code
sudo python3 Sensors_Test/test_pulse_sensor.py
```

This runs 4 tests:
1. **I2C connection** — verifies device responds on bus 5, addr 0x57
2. **Part ID** — reads register 0xFF, expects 0x15 (MAX30102, revision 0x03)
3. **Temperature** — reads on-die temperature to verify register read/write
4. **Live FIFO data** — configures SpO2 mode, reads RED+IR samples for 10 seconds, estimates heart rate if finger is placed on sensor

### How It Works in Code

- File: `sensor_handler.py` → class `MAX30102`
- Reads raw RED and IR LED values from FIFO registers (6 bytes per sample, 18-bit resolution)
- Calculates SpO2 using R-ratio formula: `SpO2 = 110 - 25 × (RED_avg / IR_avg)`
- Heart rate estimated via IR signal peak detection (~50 Hz effective sample rate)
- Registers used: MODE_CONFIG (0x09), SPO2_CONFIG (0x0A), LED1_PA (0x0C), LED2_PA (0x0D), FIFO_DATA (0x07)
- Configuration: `config.py` → `MAX30102_I2C_BUS = 5`, `MAX30102_I2C_ADDR = 0x57`

### Register Configuration

| Register | Address | Value | Description |
|---|---|---|---|
| MODE_CONFIG | 0x09 | 0x03 | SpO2 mode (RED + IR LEDs) |
| SPO2_CONFIG | 0x0A | 0x27 | ADC range 4096nA, 100 sps, 18-bit pulse width |
| FIFO_CONFIG | 0x08 | 0x4F | Sample avg=4, FIFO rollover enabled |
| LED1_PA (RED) | 0x0C | 0x24 | 6.4 mA LED current |
| LED2_PA (IR) | 0x0D | 0x24 | 6.4 mA LED current |
| PART_ID | 0xFF | 0x15 | MAX30102 identifier (read-only) |
| REVISION_ID | 0xFE | 0x03 | Silicon revision (read-only) |

### I2C Bus Map (RDK S100)

| Bus | Devices | Notes |
|---|---|---|
| 0 | (empty) | — |
| 1 | 0x30, 0x50, 0x58 | Left camera (SC230AI) + EEPROM |
| 2 | 0x32, 0x50, 0x58 | Right camera (SC230AI) + EEPROM |
| 3 | (empty) | — |
| 4 | 0x32 | Internal |
| 5 | **0x57** | **MAX30102 (40-pin header J24)** |

### Troubleshooting

| Problem | Fix |
|---|---|
| `0x57` not in `i2cdetect -y 5` | Check wiring — VIN→Pin1(3.3V), GND→Pin6, SDA→Pin3, SCL→Pin5 |
| `/dev/i2c-5` not found | Enable I2C5: `sudo srpi-config` → Interface Options → I2C5 → Enable → Reboot |
| Part ID ≠ 0x15 | You may have a MAX30100 (0x11) — different register map |
| SpO2 reads 0 / no pulse detected | Place finger firmly on sensor; wait 10–15s for warmup |
| RED/IR values near zero | Check VIN is connected to 3.3V (Pin 1), not 5V |
| Permission denied | Run with `sudo` or add user to i2c group: `sudo usermod -aG i2c $USER` |

### Current Status

**CONNECTED AND WORKING** — Sensor verified on I2C bus 5, address 0x57. Part ID 0x15 (MAX30102), revision 0x03. Die temperature reads 31.4°C. RED and IR LEDs firing correctly (RED avg=950, IR avg=598). All 4 diagnostic tests pass.

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

- File: `sensor_handler.py` → class `BME280`
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

**NOT CONNECTED** — Sensor not wired to the board yet. When connected to the 40-pin header (J24), it will share I2C bus 5 with the MAX30102 (Pin 3 SDA, Pin 5 SCL).

---

## 4. MIPI Stereo Camera (SC230AI)

### What It Does

Captures patient photos, prescription images (for OCR), and wound documentation.

### Camera Hardware

| Item | Value |
|------|-------|
| Module | RDK Stereo Camera Module |
| Sensor IC | SmartSens SC230AI (×2, stereo pair) |
| Chip ID | `0xCB34` (registers 0x3107/0x3108) |
| Resolution | 1920 × 1080 (2 MP per sensor) |
| Format | RAW10 (Bayer, linear 10-bit bitpacked) |
| Frame Rate | 30 fps |
| MIPI | 1 data lane per sensor, 810 Mbps |
| MCLK | 24 MHz (provided by Camera Expansion Board crystal) |
| Left Sensor | I2C Bus 1, address `0x30`, MIPI RX PHY 0 |
| Right Sensor | I2C Bus 2, address `0x32`, MIPI RX PHY 1 |

### Step-by-Step Setup (New RDK S100 Kit)

> **CRITICAL:** Follow ALL steps in order. Skipping the DIP switch step will result in `hs reception check error 0x10000` and the camera will NOT work. This took 25+ debugging attempts to discover.

#### Step 1: Physical Camera Connection

1. **Power OFF** the RDK S100 completely (unplug DC power)
2. Attach the Camera Expansion Board to the 100-pin J25 connector on the RDK S100
3. Verify the power LED (D2000) on the expansion board lights GREEN when powered
4. Connect the stereo camera ribbon cable to connector **J2200** (left camera, MIPI RX PHY 0)
5. For stereo: also connect to **J2201** (right camera, MIPI RX PHY 1)
6. Ribbon cable: **gold contacts facing the PCB**

#### Step 2: DIP Switch Configuration (MOST IMPORTANT STEP)

> **Without this step, the camera WILL NOT output any MIPI data.** The SC230AI sensor needs a 24 MHz master clock (MCLK). The RDK S100 SoC CANNOT provide MCLK through software — the MIPI host driver has no clock framework support (empty stubs). The MCLK must come from the Camera Expansion Board's onboard 24 MHz crystal oscillator.

**SW2200 — SET TO MCLK (DOWN position):**
```
┌─────────────────────────────────────────────┐
│   DIP Switch SW2200 (on Camera Expansion Board)   │
│   Located near MIPI camera connectors J2200/J2201 │
│                                                   │
│   ┌─────┬─────┐                                   │
│   │  1  │  2  │                                   │
│   ├─────┼─────┤                                   │
│   │  ↓  │  ↓  │  ← BOTH switches DOWN = MCLK     │
│   └─────┴─────┘                                   │
│   DOWN = MCLK ✅ (provides 24 MHz clock to sensor)│
│   UP   = LPWM ❌ (NO clock — camera will fail)    │
└─────────────────────────────────────────────┘
```

**SW2201 — KEEP AT 3.3V (UP position):**
```
┌─────────────────────────────────────────────┐
│   DIP Switch SW2201 — DO NOT CHANGE          │
│   ┌─────┬─────┐                              │
│   │  ↑  │  ↑  │  ← BOTH switches UP = 3.3V  │
│   └─────┴─────┘                              │
│   UP = 3.3V ✅                               │
└─────────────────────────────────────────────┘
```

> **WARNING:** The official D-Robotics documentation says SC230AI uses SW2200=LPWM. **This is WRONG for the RDK S100.** The S100 SoC's MIPI host driver cannot output MCLK (camera clock subsystem uses empty stubs). You MUST set SW2200=MCLK to feed the 24 MHz crystal oscillator clock from the expansion board directly to the sensor.

#### Step 3: Power On and Verify I2C

```bash
# Power on the board, wait ~60 seconds for full boot

# Verify left sensor on I2C bus 1 — should show 0x30, 0x50, 0x58
sudo i2cdetect -y 1

# Verify right sensor on I2C bus 2 — should show 0x32, 0x50, 0x58
sudo i2cdetect -y 2

# Confirm chip ID = 0xCB34 (SC230AI)
sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x07 r1   # Should return 0xcb
sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x08 r1   # Should return 0x34
```

#### Step 4: Capture a Test Frame

```bash
cd /app/multimedia_samples/sample_vin/get_vin_data

# Sensor index 6 = SC230AI. Pipe "g" to capture a single frame, "q" to quit.
printf 'g\nq\n' | sudo timeout 15 ./get_vin_data -s 6
```

**Expected kernel log (check with `dmesg | tail -30`):**
```
[SENSOR0]: sc230ai open i2c1@0x30                 ✅
[RX0]: mclk 24 ignore                              ✅ (harmless — clock comes from expansion board)
[RX0]: entry hs reception                          ✅ SUCCESS — MIPI data flowing!
```

**If you see `[RX0]: hs reception check error 0x10000` → SW2200 is NOT set to MCLK. Go back to Step 2.**

#### Step 5: Decode the RAW10 Image

The captured `.raw` file is **linear 10-bit bitpacked** Bayer data (NOT MIPI CSI-2 packed). Each row = 2400 bytes for 1920 pixels (1920 × 10 bits / 8 = 2400 bytes). Every 5 bytes contain 4 pixels packed as a continuous 40-bit little-endian bitstream.

```python
import numpy as np
import cv2

# Load the RAW file (adjust filename from get_vin_data output)
raw = np.fromfile("handle_XXXXX_chn0_1920x1080_stride_2400_frameid_N_ts_XXXXXX.raw", dtype=np.uint8)
data = raw.reshape(1080, 2400)

# Unpack linear 10-bit bitpacked → 16-bit pixels
packed = data.reshape(1080, 480, 5)  # 1920/4 = 480 groups of 5 bytes
b = packed.astype(np.uint64)
val40 = b[:,:,0] | (b[:,:,1] << 8) | (b[:,:,2] << 16) | (b[:,:,3] << 24) | (b[:,:,4] << 32)

img = np.zeros((1080, 1920), dtype=np.uint16)
img[:, 0::4] = ((val40 >>  0) & 0x3FF).astype(np.uint16)
img[:, 1::4] = ((val40 >> 10) & 0x3FF).astype(np.uint16)
img[:, 2::4] = ((val40 >> 20) & 0x3FF).astype(np.uint16)
img[:, 3::4] = ((val40 >> 30) & 0x3FF).astype(np.uint16)

# Demosaic (SC230AI uses BGGR Bayer pattern) + gamma correction
img16 = (img << 6).astype(np.uint16)
color = cv2.cvtColor(img16, cv2.COLOR_BayerBG2BGR)
color_f = color.astype(np.float32) / 65535.0
color_gamma = np.power(np.clip(color_f, 0, 1), 1.0/2.2)  # Apply gamma 2.2

# Auto white balance (gray world)
means = color_gamma.mean(axis=(0,1))
wb = means.mean() / (means + 1e-6)
result = np.clip(color_gamma * wb[np.newaxis, np.newaxis, :], 0, 1)

# Contrast stretch
p1, p99 = np.percentile(result, (1, 99))
result = np.clip((result - p1) / (p99 - p1), 0, 1)

cv2.imwrite("camera_output.jpg", (result * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
print("Saved camera_output.jpg")
```

### RAW10 Format Details

> **CRITICAL for any developer decoding the image: The RDK S100 get_vin_data outputs LINEAR 10-bit bitpacked, NOT MIPI CSI-2 packed RAW10.**

| Format | Byte Layout (4 pixels) | Notes |
|--------|----------------------|-------|
| **Linear 10-bit (THIS ONE)** | 5 bytes = 40-bit LE bitstream; pixel0=bits[0:9], pixel1=bits[10:19], pixel2=bits[20:29], pixel3=bits[30:39] | Used by RDK S100 `get_vin_data` |
| MIPI CSI-2 RAW10 | 5 bytes: [P0_MSB] [P1_MSB] [P2_MSB] [P3_MSB] [P0_LSB|P1_LSB|P2_LSB|P3_LSB] | NOT what RDK S100 outputs |

If you use the wrong unpacking method, the image will look like colored noise / static. The histogram will show false peaks at 256-value intervals.

### Packages / Libraries Used

```bash
# get_vin_data is pre-installed (C binary with full sensor list including SC230AI)
ls /app/multimedia_samples/sample_vin/get_vin_data/get_vin_data

# For image decoding
pip3 install numpy opencv-python-headless Pillow
```

### Python API Limitation

> **IMPORTANT:** The Python camera API (`hobot_vio.libsrcampy`) does NOT support SC230AI — it only has `imx219`, `ar0820std`, and `ovx8bstd` in its compiled sensor list. The OVX8B wildcard chip_id=0xA55A will falsely match the SC230AI and fail. **Use the C binary `get_vin_data -s 6` instead.**

### How to Verify

```bash
# 1. I2C detection
sudo i2cdetect -y 1 | grep -q "30" && echo "Left sensor OK" || echo "Left sensor NOT found"
sudo i2cdetect -y 2 | grep -q "32" && echo "Right sensor OK" || echo "Right sensor NOT found"

# 2. Chip ID verification
LEFT_HI=$(sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x07 r1 2>/dev/null)
LEFT_LO=$(sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x08 r1 2>/dev/null)
echo "Left sensor chip ID: ${LEFT_HI}${LEFT_LO} (expect 0xcb 0x34 = SC230AI)"

# 3. Capture test frame
cd /app/multimedia_samples/sample_vin/get_vin_data
printf 'g\nq\n' | sudo timeout 15 ./get_vin_data -s 6

# 4. Check kernel log
dmesg | grep -E "hs reception|mclk|sc230" | tail -5
# SUCCESS: "entry hs reception" (no error number)
# FAILURE: "hs reception check error 0x10000" → Fix SW2200 DIP switch
```

### How It Works in Code

- File: `camera_handler.py`
- Capture: Runs `get_vin_data -s 6` via subprocess to capture RAW10 frame
- Decode: Linear 10-bit bitpacked → 16-bit → Bayer BGGR demosaic → gamma 2.2 → auto white balance
- Output: BGR image (numpy array or JPEG file)

### Troubleshooting

| Problem | Fix |
|---|---|
| `hs reception check error 0x10000` | **SW2200 not set to MCLK.** Power off, flip SW2200 DOWN (MCLK), retest |
| `mclk 24 ignore` | Normal/harmless — SoC can't output MCLK, clock comes from expansion board |
| `No sensor found on i2cdetect` | Reseat MIPI ribbon cable; gold contacts face PCB; check correct connector |
| `create_and_run_vflow failed, ret -36` | MIPI HS reception failed — fix MCLK (SW2200=MCLK) |
| Image looks like colored noise | Wrong RAW10 decode — use LINEAR 10-bit unpack, not MIPI CSI-2 |
| Image has false color / wrong tint | Try different Bayer pattern (BGGR is default for SC230AI) |
| `open_cam returned -1` (Python API) | Python API doesn't support SC230AI — use `get_vin_data -s 6` instead |
| `snrclk not support` | Expected — S100 driver has empty clock stubs. Ignore if SW2200=MCLK |
| OVX8B misidentified | SC230AI caught by OVX8B wildcard chip_id in libsrcampy. Use C API instead |

### Current Status

**CONNECTED & WORKING** — SW2200=MCLK, camera captures 1920x1080 RAW10 frames at 30fps. Decode with linear 10-bit unpack + BayerBG demosaic + gamma correction.

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
