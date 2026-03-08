# Camera Setup Issue — OVX8B Stereo Camera on RDK S100

**Date:** 2026-03-08  
**Board:** D-Robotics RDK S100 V1P0  
**Project:** Pocket ASHA — AI for Bharat Hackathon  
**Status:** ❌ BLOCKED — Camera pipeline initialization fails with `hbn_camera_create` error

---

## 1. System Specifications

### 1.1 Board & SoC
| Item | Value |
|------|-------|
| Board | D-Robotics RDK S100 V1P0 |
| SoC | D-Robotics (Horizon Robotics) |
| CPU | 6× ARM Cortex-A78AE (aarch64) |
| RAM | 9.3 GB LPDDR5 |
| Storage | 64 GB eMMC (`/dev/mmcblk0p17`, 45 GB partition, 29 GB free) |
| Architecture | aarch64 (Little Endian) |

### 1.2 OS & Kernel
| Item | Value |
|------|-------|
| OS | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| Kernel | `6.1.112-rt43-DR-4.0.4-2510152230-gb381cb-g6c4511` |
| Kernel Type | SMP PREEMPT_RT |
| Build Date | Oct 15, 2025 |
| Python | 3.10.12 (system) |

### 1.3 D-Robotics SDK Packages (Installed)
| Package | Version |
|---------|---------|
| hobot-camera | 4.0.4-20250915222135 |
| hobot-multimedia | 4.0.4-20250915222043 |
| hobot-multimedia-dev | 4.0.2-20250818223743 |
| hobot-multimedia-samples | 4.0.4-20250827112435 |
| hobot-spdev | 4.0.4-20251015222413 |
| hobot-sp-samples | 4.0.4-20251015222430 |
| hobot-dnn | 4.0.4-20250916113831 |
| hobot-firmware | 4.0.3-20250818222930 |
| hobot-io | 4.0.3-20250729214623 |
| hobot-configs | 4.0.4-20250915222545 |
| hobot-models-basic | 4.0.6 |
| hobot-utils | 4.0.4-20250827111619 |

### 1.4 Key Libraries
| Library | Path | Version |
|---------|------|---------|
| libcam.so | `/usr/hobot/lib/libcam.so.1.2.0` | 1.2.0 |
| libvpf.so | `/usr/hobot/lib/libvpf.so.1` | — |
| libvio.so | `/usr/hobot/lib/libvio.so.1` | — |
| libhbmem.so | `/usr/hobot/lib/libhbmem.so.1` | — |
| libsrcampy (Python) | `hobot_vio.libsrcampy` | via hobot-spdev 4.0.4 |

---

## 2. Camera Hardware

### 2.1 Camera Expansion Board
| Item | Value |
|------|-------|
| Connector | 100-pin J25 (board-to-board, J2000 on expansion board) |
| Power LED (D2000) | ✅ GREEN (confirmed powered) |
| Camera connectors | J2200 (MIPI RX PHY 0) and J2201 (MIPI RX PHY 1) |
| DIP Switch SW2200 | Set to **LPWM** (default) — controls MCLK/LPWM selection |
| DIP Switch SW2201 | Set to **3.3V** (default) — camera I/O voltage |
| Supported cameras | SC132GS, SC230AI, OVX8B (stereo pairs on J2200+J2201) |

### 2.2 Camera Sensors Detected
**Both OVX8B stereo sensors are physically detected on I2C:**

| Bus | Address | Device | Role |
|-----|---------|--------|------|
| I2C Bus 1 | 0x30 | **OVX8B sensor** (left) | MIPI RX PHY 0 |
| I2C Bus 1 | 0x50 | EEPROM | Module EEPROM |
| I2C Bus 1 | 0x58 | EEPROM | Calibration EEPROM |
| I2C Bus 2 | 0x32 | **OVX8B sensor** (right) | MIPI RX PHY 1 |
| I2C Bus 2 | 0x50 | EEPROM | Module EEPROM |
| I2C Bus 2 | 0x58 | EEPROM | Calibration EEPROM |
| I2C Bus 2 | 0x68 | Unknown | (possibly RTC or other) |

### 2.3 I2C Bus Scan Results
```
Bus 1:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: 30 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: 50 -- -- -- -- -- -- -- 58 -- -- -- -- -- -- --

Bus 2:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: -- -- 32 -- -- -- -- -- -- -- -- -- -- -- -- --
50: 50 -- -- -- -- -- -- -- 58 -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
```

### 2.4 EEPROM Data (Bus 1, addr 0x50)
```
0x00: 0x43    (mostly unprogrammed — all 0xFF after byte 1)
0x01: 0x2f
0x02-0x0f: 0xFF (unprogrammed)
```
The EEPROM appears to be **unprogrammed/partially programmed**, which affects which ISP calibration library the sensor driver selects.

---

## 3. Sensor Driver Specifications

### 3.1 Sensor Drivers Available
| Driver | Path | Size |
|--------|------|------|
| libovx8bstd.so | `/usr/hobot/lib/sensor/libovx8bstd.so.1.2.0` | 156,392 bytes |
| libovx8b.so | `/usr/hobot/lib/sensor/libovx8b.so.1.2.0` | 132,152 bytes |

### 3.2 Auto-Detection Result
The sensor auto-detection succeeds:
```
Searching camera sensor on device: /proc/device-tree/soc/vcon@0 i2c bus: 1 mipi rx phy: 0
[0] INFO: Found sensor name:ovx8bstd-30fps on mipi rx csi 0, i2c addr 0x30,
    config_file:linear_1920x1080_raw12_30fps_1lane.c
```
**Sensor IS found. The problem occurs AFTER detection, during pipeline creation.**

### 3.3 ISP Calibration Libraries Required by libovx8bstd.so
The sensor driver `libovx8bstd.so` tries to `dlopen()` one of these ISP calibration libraries based on the camera module's EEPROM data:

| Library Name | Lens Module | Status |
|-------------|-------------|--------|
| `lib_CL-OX8GB-L121+067-L.so` | CL type, L121 lens | ❌ **NOT SHIPPED** in hobot-camera package |
| `lib_CL-OX8GB-L030+017-L.so` | CL type, L030 lens | ❌ **NOT SHIPPED** |
| `lib_CW-OX8GB-A120+065-L.so` | CW type, A120 lens | ❌ **NOT SHIPPED** |
| `lib_CW-OX8GB-A030+017-L.so` | CW type, A030 lens | ❌ **NOT SHIPPED** |
| `lib_CO-OX8GB-A121+055-L.so` | CO type, A121 lens | ❌ **NOT SHIPPED** |
| `lib_CH-OX8GB-A120+065-L.so` | CH type, A120 lens | ❌ **NOT SHIPPED** |
| `lib_CH-OX8GB-A030+017-L.so` | CH type, A030 lens | ❌ **NOT SHIPPED** |

### 3.4 ISP Calibration Libraries Shipped in hobot-camera 4.0.4
Only two calibration libraries are included in the package:
| Library | Sensor | Size |
|---------|--------|------|
| `lib_CH_OX3GB_O100_065_L.so` | OVX3C | 78,200 bytes |
| `lib_CW_A82GB_A120_065_L_W20.so` | AR0820 | 131,120 bytes |

**None of the 7 OVX8B calibration libraries referenced by `libovx8bstd.so` are included.**

---

## 4. Device Tree Configuration

### 4.1 Active DTB
```
/boot/hobot/rdk-s100-v1p0.dtb  (151,275 bytes)
Model: "D-Robotics RDK S100 V1P0"
Compatible: "drobot,s100-rdk"
```

### 4.2 Available DTBs
```
rdk-s100-v0p5.dtb    (151,275 bytes)
rdk-s100-v0p6.dtb    (151,275 bytes)
rdk-s100-v1-2.dtb    (150,772 bytes)  ← different size, may have camera changes
rdk-s100-v1-21.dtb   (150,772 bytes)  ← different size, may have camera changes
rdk-s100-v1p0.dtb    (151,275 bytes)  ← ACTIVE
rdk-s100p-v0p5.dtb   (151,275 bytes)
rdk-s100p-v0p6.dtb   (151,275 bytes)
rdk-s100p-v1p0.dtb   (151,275 bytes)
```

### 4.3 VCON (Video Connector) Configuration
```dts
vcon@0 {
    compatible = "hobot,vin-vcon";
    type = <0x00>;           // NORMAL sensor type
    bus = <0x01>;            // I2C bus 1
    rx_phy = <0x01 0x00>;   // MIPI RX PHY 0
    status = "okay";
    gpio_poc = <0x00>;
    gpio_des = <0x00>;
    sensor_err = <0x00>;
    lpwm_chn = <0x00>;
};

vcon@1 {
    compatible = "hobot,vin-vcon";
    type = <0x00>;           // NORMAL sensor type
    bus = <0x02>;            // I2C bus 2
    rx_phy = <0x01 0x01>;   // MIPI RX PHY 1
    status = "okay";
    gpio_poc = <0x00>;
    gpio_des = <0x00>;
    sensor_err = <0x00>;
    lpwm_chn = <0x01>;
};
```

### 4.4 MIPI Host 0 Configuration
```dts
mipi_host@0x37420000 {
    compatible = "hobot,mipi-host";
    reg = <0x00 0x37420000 0x00 0x10000 0x00 0x37200000 0x00 0x40000>;
    interrupts-name = "mipi-rx0";
    hw-mode = <0x01>;
    status = "okay";
    ports {
        port@0 {
            endpoint {
                clock-lanes = <0x00>;
                data-lanes = <0x01 0x02>;      // 2 data lanes
                lane-rate = <0x6c0>;           // 1728 Mbps
                vc_id = <0x00>;
                emb-en = <0x01>;               // Embedded data enabled
            };
        };
    };
};
```
**NOTE:** No `pinctrl-names` or MCLK pinctrl defined for MIPI host — this causes the "mipi mclk is not configed" warning.

### 4.5 MIPI Host Sysfs State
```
/sys/class/vps/mipi_host0/status/cfg = "not inited"
/sys/class/vps/mipi_host0/param/snrclk_freq = 0
/sys/class/vps/mipi_host0/param/snrclk_en = 0
```

---

## 5. The Error — Detailed Trace

### 5.1 Error Sequence
```python
from hobot_vio import libsrcampy
cam = libsrcampy.Camera()
ret = cam.open_cam(0, 0, 30, 1920, 1080)
# Returns: -1
```

### 5.2 Full Console Output
```
[CamInitParam][0296] set camera fps: 30, width: -1, height: -1
mipi mclk is not configed.
Searching camera sensor on device: /proc/device-tree/soc/vcon@0  i2c bus: 1  mipi rx phy: 0
[0] INFO: Found sensor name:ovx8bstd-30fps on mipi rx csi 0, i2c addr 0x30,
    config_file:linear_1920x1080_raw12_30fps_1lane.c
[CamInitPymParam][0259] Setting PYM channel:0: crop_x:0, crop_y:0,
    input_width:1920, input_height:1080, dst_w:1920, dst_h:1080
ERROR [vp_vin_init][0042] hbn_camera_create failed, ret(-65666)
ERROR [OpenCamera][0422] vp_vin_init failed error(-65666)
```

### 5.3 Error Code Analysis
| Error Code | Hex | Constant | Meaning |
|-----------|-----|----------|---------|
| -65665 | 0x10081 | `HBN_STATUS_CAM_MOD_DLOPEN_ERROR` | Calibration .so file not found (initial error before stub) |
| **-65666** | **0x10082** | **`HBN_STATUS_CAM_MOD_CHECK_ERROR`** | **Calibration .so loaded but validation FAILED** (current error) |
| -65667 | 0x10083 | `HBN_STATUS_CAM_MOD_VERSION_ERROR` | Calibration version mismatch |

**Error progression:**
1. Initially: `-65665` (`DLOPEN_ERROR`) — the ISP calibration library `lib_CL_OX8GB_L121_067_L.so` did not exist at all
2. We created a stub library with correct symbol but zeroed data → error changed to `-65666` (`CHECK_ERROR`)
3. We created a structured stub with name/magic/version → still `-65666` (`CHECK_ERROR`)
4. The calibration data format is proprietary and cannot be easily stubbed

### 5.4 Strace dlopen() Trace
```
# Sensor driver loads successfully:
openat("/usr/hobot/lib/sensor/libovx8bstd.so", O_RDONLY|O_CLOEXEC) = 8   ✅

# Then it tries to dlopen the ISP calibration library:
openat("/usr/lib/aarch64-linux-gnu/lib_CL_OX8GB_L121_067_L.so") = ENOENT  ❌
openat("/lib/aarch64-linux-gnu/lib_CL_OX8GB_L121_067_L.so")     = ENOENT  ❌
openat("/usr/hobot/lib/sensor/lib_CL_OX8GB_L121_067_L.so")      = 8       ✅ (our stub)

# Stub loads, but camera_calib_config_check() fails → ret(-65666)
```

### 5.5 Calibration Validation (Disassembly of camera_calib_config_check)
From disassembling `libcam.so`, `camera_calib_config_check()` validates:
1. Loads calibration struct pointer from `cammod_ovx8bstd[120]` (byte offset)
2. Checks magic number `0x4863616d` ("macH") at byte offset 100 within the calibration structure
3. Checks version field at byte offset 104 — (`value >> 16) & 0xFF` must equal `1`
4. Loads additional data pointers from byte offset 184

The `cammod_calibration` exported symbol in the calib .so has 32 bytes containing 4 pointers (64-bit) to:
- Name string (108 bytes, CAMERA_MODULE_NAME_LEN)
- Version/magic struct
- Calibration operations vtable
- ISP tuning data (large binary blob, ~60-120 KB)

**The ISP tuning data is a proprietary binary blob specific to each lens+sensor module combination. It cannot be stubbed or fabricated.**

---

## 6. What We've Tried

### 6.1 Attempted Fixes — All Failed
| Attempt | Result |
|---------|--------|
| `open_cam(0, 0, 30, 1920, 1080)` | ERROR -65665 (no calib .so) |
| `open_cam(0, -1, 30, 1920, 1080)` (auto-detect) | ERROR -65665 |
| `open_cam(0, 0, 30, 640, 480)` (lower resolution) | ERROR -65665 |
| `open_cam(0, 0, 30, -1, -1)` (native resolution) | ERROR -65665 + PYM invalid |
| `open_cam(0, 0, 15, 1920, 1080)` (lower FPS) | Sensor not found at 15fps |
| Run with `sudo` | Same error |
| Set `MCLK` env variable | No effect |
| Created zeroed stub `lib_CL_OX8GB_L121_067_L.so` with `cammod_calibration` symbol | ERROR changed to -65666 (check fail) |
| Created structured stub with name/magic/version fields | ERROR -65666 (check fail) |
| Tried `video_idx=1` (second camera on bus 2) | Same error |

### 6.2 MCLK Issue
The device tree does not define MCLK pinctrl for the MIPI hosts:
- `"mipi mclk is not configed"` warning appears on every attempt
- The vcon nodes have no `pinctrl-names` property
- MIPI host sysfs shows `snrclk_freq = 0` and `snrclk_en = 0`
- Attempting to write to sysfs (`echo 24000000 > .../snrclk_freq`) returns **I/O error**
- This may be because the DIP switch SW2200 is set to LPWM instead of MCLK
- However, the OVX8B sensor IS detected on I2C (so it has some clock), and the error occurs AFTER detection

---

## 7. Root Cause Analysis

### 7.1 Primary Cause — Missing ISP Calibration Library
The `hobot-camera 4.0.4` package **does not include any OVX8B ISP calibration libraries**. It only ships calibrations for OVX3C and AR0820. The sensor driver `libovx8bstd.so` requires a calibration library matching the camera module (determined by EEPROM data), but none of the 7 possible OVX8B calibration .so files are included.

### 7.2 Secondary Cause — MCLK Not Configured
The device tree lacks MCLK pinctrl configuration for the MIPI hosts. This generates the `"mipi mclk is not configed"` warning. While the sensor is still detectable via I2C, the camera may need MCLK to actually stream data. The DIP switch SW2200 on the Camera Expansion Board controls whether the pin is used for MCLK or LPWM.

### 7.3 Calibration Library Format
The ISP calibration library exports a single symbol `cammod_calibration` (32 bytes) which contains 4 pointers to:
1. **Module name** — 108-byte string identifying the lens module (e.g., "CL_OX8GB_L121_067_L")
2. **Version struct** — Contains magic "macH" (`0x4863616d`), version numbers, and flags
3. **Ops vtable** — Calibration operation function pointers
4. **ISP tuning data** — Large proprietary binary blob (60-120 KB) with:
   - Auto white balance (AWB) parameters
   - Auto exposure (AE) tables
   - Color correction matrices (CCM)
   - Lens shading correction (LSC) tables
   - Noise reduction parameters
   - Gamma curves
   - Sensor-specific timing/register configurations

This data is sensor+lens module specific and **cannot be fabricated**.

---

## 8. VIN/ISP Device Nodes Present
```
/dev/vin0_cap    /dev/vin0_src    /dev/vin0_emb    /dev/vin0_roi
/dev/vin1_cap    /dev/vin1_src    /dev/vin1_emb    /dev/vin1_roi
/dev/vin4_cap    /dev/vin4_src    /dev/vin4_emb    /dev/vin4_roi
/dev/isp0_cap    /dev/isp0_src    /dev/isp_hw0_control[0-11]   /dev/isp_hw0_sbuf[0-11]
/dev/isp1_cap    /dev/isp1_src    /dev/isp_hw1_control[0-11]   /dev/isp_hw1_sbuf[0-11]
```

---

## 9. Questions for D-Robotics / RDK Community

1. **Where are the OVX8B ISP calibration libraries?** The `hobot-camera` package (v4.0.4) ships `libovx8bstd.so` sensor driver but none of the 7 calibration .so files it references (`lib_CL-OX8GB-*.so`, `lib_CW-OX8GB-*.so`, etc.). Is there a separate package, an OTA update, or a download location for these?

2. **Is MCLK required for the OVX8B on the Camera Expansion Board?** The device tree has no MCLK pinctrl, and `snrclk_freq/snrclk_en` sysfs writes fail with I/O error. Should DIP switch SW2200 be set to MCLK? Does the OVX8B use an external oscillator or does it need the SoC-provided MCLK?

3. **Which camera modules are officially supported on the RDK S100 Camera Expansion Board?** The documentation mentions SC132GS and SC230AI. Is the OVX8B officially supported, or does it require a different expansion board?

4. **Is there a way to bypass ISP calibration for raw capture?** Can the camera pipeline be initialized without the calibration library (e.g., raw sensor data capture, bypassing ISP)?

5. **Are the `rdk-s100-v1-2.dtb` or `rdk-s100-v1-21.dtb` DTBs meant for the Camera Expansion Board?** They are 503 bytes smaller than the v1p0 DTB — do they include different MIPI/MCLK pinctrl or camera support?

---

## 10. File Tree (Relevant Paths)
```
/usr/hobot/lib/
├── libcam.so.1.2.0                    # Camera framework library
├── libvpf.so.1                        # Video Processing Framework
├── libvio.so.1                        # Video I/O library
├── libhbmem.so.1                      # Memory management
└── sensor/
    ├── libovx8bstd.so → libovx8bstd.so.1.2.0    # OVX8B sensor driver (156 KB)
    ├── libovx8b.so → libovx8b.so.1.2.0          # OVX8B alt driver (132 KB)
    ├── lib_CH_OX3GB_O100_065_L.so                # OVX3C ISP calib (78 KB) ✅
    ├── lib_CW_A82GB_A120_065_L_W20.so            # AR0820 ISP calib (131 KB) ✅
    ├── lib_CL_OX8GB_L121_067_L.so                # OVX8B ISP calib STUB (8 KB) ❌ doesn't work
    ├── libsc132gs.so.1.0.0                       # SC132GS driver
    ├── libsc230ai.so.1.0.0                       # SC230AI driver
    ├── libimx219.so.1.0.0                        # IMX219 driver
    └── ... (30+ other sensor drivers)

/boot/hobot/
├── rdk-s100-v1p0.dtb                  # Active device tree blob
├── rdk-s100-v1-2.dtb                  # Alt DTB (smaller, may differ)
└── rdk-s100-v1-21.dtb                 # Alt DTB (smaller, may differ)

/usr/hobot/include/
├── hbn_error.h                        # Error code definitions
├── hb_camera_error.h                  # Camera-specific errors
├── hb_camera_data_config.h            # camera_config_t structure
└── hb_camera_interface.h              # Camera API

/app/multimedia_samples/
├── sample_vin/get_vin_data/           # C sample for VIN data capture
├── vp_sensors/vp_sensors.c            # Sensor auto-detection code
└── sunrise_camera/                    # Full camera demo app

/sys/class/vps/
├── mipi_host0/param/snrclk_freq       # Sensor clock frequency (= 0)
├── mipi_host0/param/snrclk_en         # Sensor clock enable (= 0)
├── mipi_host0/status/cfg              # "not inited"
├── mipi_host1/                        # Second MIPI host
└── mipi_host4/                        # Third MIPI host (for GMSL)
```

---

## 11. Summary

| Component | Status |
|-----------|--------|
| Camera Expansion Board power (D2000 LED) | ✅ GREEN |
| OVX8B Sensor #1 detected on I2C bus 1 (addr 0x30) | ✅ FOUND |
| OVX8B Sensor #2 detected on I2C bus 2 (addr 0x32) | ✅ FOUND |
| Sensor driver `libovx8bstd.so` loaded | ✅ OK |
| Sensor auto-detection (name, config_file) | ✅ OK |
| MIPI MCLK configured | ⚠️ WARNING "not configed" |
| ISP calibration library `lib_CL_OX8GB_L121_067_L.so` | ❌ **NOT SHIPPED** in hobot-camera |
| `hbn_camera_create()` | ❌ **FAILS** with -65666 (CHECK_ERROR) |
| Camera pipeline (VIN → ISP → PYM) | ❌ **BLOCKED** |
| Image capture | ❌ **BLOCKED** |

**The camera hardware is correctly connected and both sensors are detected. The blocker is the missing proprietary OVX8B ISP calibration library that is not included in the `hobot-camera` package.**
