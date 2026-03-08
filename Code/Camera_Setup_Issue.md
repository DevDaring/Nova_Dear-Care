# Camera Setup Issue — SC230AI Stereo Camera on RDK S100

**Date:** 2026-03-08
**Board:** D-Robotics RDK S100 V1P0
**Camera:** RDK Stereo Camera Module (SC230AI dual)
**Project:** Pocket ASHA — AI for Bharat Hackathon
**Status:** ❌ BLOCKED — MIPI HS reception fails; sensor initializes but no video data received

---

## 1. Hardware Specifications

### 1.1 Board — D-Robotics RDK S100 V1P0

| Item | Value |
|------|-------|
| Board | D-Robotics RDK S100 V1P0 |
| SoC | D-Robotics S100 (Horizon Robotics) |
| CPU | 6× ARM Cortex-A78AE (aarch64) |
| RAM | 9.3 GB LPDDR5 |
| Storage | 64 GB eMMC (`/dev/mmcblk0p17`, 45 GB partition, 28 GB free) |
| OS | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| Kernel | `6.1.112-rt43-DR-4.0.4-2510152230-gb381cb-g6c4511` (SMP PREEMPT_RT) |
| Python | 3.10.12 (system) |

### 1.2 Camera — RDK Stereo Camera Module (SC230AI)

| Item | Value |
|------|-------|
| Module Name | RDK Stereo Camera Module |
| Sensor IC | **SmartSens SC230AI** (×2, stereo pair) |
| Chip ID Register | `0x3107` (high byte), `0x3108` (low byte) |
| Chip ID Value | **`0xCB34`** (confirmed on BOTH sensors via I2C) |
| Resolution | 1920 × 1080 (2 MP per sensor) |
| Format | RAW10 (Bayer) |
| Frame Rate | 30 fps |
| MIPI Interface | 1 data lane per sensor, 810 Mbps |
| MCLK Requirement | 24 MHz external master clock |
| I/O Voltage | 3.3V (per official D-Robotics camera expansion board table) |
| Left Sensor | I2C Bus 1, address `0x30`, MIPI RX PHY 0 |
| Right Sensor | I2C Bus 2, address `0x32`, MIPI RX PHY 1 |
| EEPROM (left) | I2C Bus 1, address `0x50` (module), `0x58` (calibration) |
| EEPROM (right) | I2C Bus 2, address `0x50` (module), `0x58` (calibration) |
| Product Links | [Waveshare](https://www.waveshare.com/rdk-stereo-camera-module.htm), [Hubtronics](https://hubtronics.in/rdk-stereo-camera-module) |

**IMPORTANT: This camera was previously misidentified as "OVX8B" in earlier debugging. The sensor auto-detection system matched the OVX8B driver (which uses a wildcard chip_id=0xA55A) before actually confirming the real chip ID. Direct I2C register reads prove both sensors are SC230AI (chip ID 0xCB34).**

### 1.3 Camera Expansion Board

| Item | Value |
|------|-------|
| Connector | 100-pin J25 (board-to-board, J2000 on expansion board) |
| Power LED (D2000) | ✅ GREEN (confirmed powered) |
| Camera connectors | J2200 (MIPI RX PHY 0) and J2201 (MIPI RX PHY 1) |
| DIP Switch SW2200 | **LPWM** (UP) — official setting for SC230AI |
| DIP Switch SW2201 | **3.3V** (UP) — official setting for SC230AI |

**Official DIP switch settings per D-Robotics documentation:**

| Camera Model | SW2200 | SW2201 |
|:--|:--|:--|
| SC132GS | LPWM | 3.3V |
| **SC230AI Stereo** | **LPWM** | **3.3V** |
| OVX8B | (not documented for expansion board) | — |

Source: [D-Robotics RDK S100 Camera Expansion Board docs](https://developer.d-robotics.cc/rdk_doc/en/rdk_s/Quick_start/hardware_introduction/rdk_s100_camera_expansion_board/)

### 1.4 I2C Bus Scan Results

```
Bus 1:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: 30 -- -- -- -- -- -- --
50: 50 -- -- -- -- -- -- -- 58 -- -- -- -- -- -- --

Bus 2:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: -- -- 32 -- -- -- -- --
50: 50 -- -- -- -- -- -- -- 58 -- -- -- -- -- -- --
```

### 1.5 Chip ID Verification (Definitive)

```bash
# Left sensor (Bus 1, addr 0x30):
$ sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x07 r1   → 0xcb
$ sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x08 r1   → 0x34
# Chip ID = 0xCB34 → SC230AI ✅

# Right sensor (Bus 2, addr 0x32):
$ sudo i2ctransfer -f -y 2 w2@0x32 0x31 0x07 r1   → 0xcb
$ sudo i2ctransfer -f -y 2 w2@0x32 0x31 0x08 r1   → 0x34
# Chip ID = 0xCB34 → SC230AI ✅
```

---

## 2. Software Environment

### 2.1 D-Robotics SDK Packages

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
| hobot-configs | 4.0.4-20250915222545 |

### 2.2 SC230AI Driver & Calibration Files (ALL PRESENT ✅)

| File | Path | Size | Status |
|------|------|------|--------|
| Sensor driver | `/usr/hobot/lib/sensor/libsc230ai.so.1.0.0` | 23,864 B | ✅ Present |
| ISP calibration | `/usr/hobot/lib/sensor/lib_sc230ai_linear.so` | 77,088 B | ✅ Present |
| Sensor config (.c) | `/app/multimedia_samples/vp_sensors/sc230ai/linear_1920x1080_raw10_30fps_1lane.c` | 5,153 B | ✅ Present |
| GDC binary | `../gdc_bin/sc230ai_gdc.bin` | — | Referenced |
| Tuning config | `/app/tuning_tool/cfg/matrix/tuning_sc230ai_dual_cim_isp_1080p/` | — | ✅ Present |

### 2.3 SC230AI Sensor Config Parameters

From `linear_1920x1080_raw10_30fps_1lane.c`:

```c
// MIPI config
.lane = 1,          // 1 MIPI data lane
.datatype = 0x2B,   // RAW10
.fps = 30,
.mclk = 24,         // Requests 24MHz MCLK from SoC
.mipiclk = 810,     // 810 Mbps link rate
.width = 1920,
.height = 1080,
.settle = 22,

// Camera config
.name = "sc230ai",
.addr = 0x30,
.eeprom_addr = 0x51,
.sensor_mode = 6,
.calib_lname = "lib_sc230ai_linear.so",

// ISP config
.hw_id = 0,
.slot_id = 4,

// VIN node config
.vcon_attr.bus_main = 2,
.cim_attr.mipi_rx = 0,
```

### 2.4 Official Dual SC230AI Config (Tuning Tool)

From `/app/tuning_tool/cfg/matrix/tuning_sc230ai_dual_cim_isp_1080p/hb_j6dev.json`:

```json
{
    "port_0": {
        "sensor_name": "sc230ai",
        "sensor_addr": "0x30",
        "eeprom_addr": "0x51",
        "calib_lname": "lib_sc230ai_linear.so",
        "sensor_mode": 6,
        "fps": 30,
        "width": 1920,
        "height": 1080
    },
    "port_1": {
        "sensor_name": "sc230ai",
        "sensor_addr": "0x32",
        "eeprom_addr": "0x51",
        "calib_lname": "lib_sc230ai_linear.so",
        "sensor_mode": 6,
        "fps": 30,
        "width": 1920,
        "height": 1080
    }
}
```

### 2.5 MIPI Host Status

```
/sys/class/vps/mipi_host0  → present ✅ (MIPI RX PHY 0, left sensor)
/sys/class/vps/mipi_host1  → present ✅ (MIPI RX PHY 1, right sensor)
/sys/class/vps/mipi_host4  → present ✅ (unused, for AR0820)
```

---

## 3. Device Tree Configuration

### 3.1 Active DTB

```
/boot/hobot/rdk-s100-v1p0.dtb  (reverted to clean/stock — no MCLK modifications)
Model: "D-Robotics RDK S100 V1P0"
```

### 3.2 VCON (Video Connector) Configuration

```dts
vcon@0 {
    compatible = "hobot,vin-vcon";
    type = <0x00>;           // NORMAL sensor type (no deserializer)
    bus = <0x01>;            // I2C bus 1
    rx_phy = <0x01 0x00>;   // MIPI RX PHY 0
    status = "okay";
    lpwm_chn = <0x00>;
};

vcon@1 {
    compatible = "hobot,vin-vcon";
    type = <0x00>;           // NORMAL sensor type
    bus = <0x02>;            // I2C bus 2
    rx_phy = <0x01 0x01>;   // MIPI RX PHY 1
    status = "okay";
    lpwm_chn = <0x01>;
};
```

### 3.3 MIPI Host 0 Configuration (Stock/Clean DTB)

```dts
mipi_host@0x37420000 {
    compatible = "hobot,mipi-host";
    reg = <0x00 0x37420000 0x00 0x10000 0x00 0x37200000 0x00 0x40000>;
    interrupts-name = "mipi-rx0";
    hw-mode = <0x01>;
    status = "okay";
    /* NOTE: No clocks, pinctrl-names, pinctrl-0, or snrclk-idx properties */
    /* This means the SoC cannot output MCLK to the sensor */
};
```

### 3.4 MCLK Pin Conflict (Previous DTB Modification — REVERTED)

A previous attempt added MCLK pinctrl (`cam_clkout_func`, phandle `0xf0`) to mipi_host0 and mipi_host1. **This BROKE both MIPI hosts** because:

- `cam_clkout_func` uses pin `cam_lpwm1_dout3` (pin-7 in the camera pinctrl domain)
- Pin `cam_lpwm1_dout3` is **already claimed by the Ethernet controller** (`33100000.ethernet`)
- Kernel error: `s100-pinctrl 370f3000.pinctrl: pin LPWM1_DOUT3 already requested by 33100000.ethernet; cannot claim for 37420000.mipi_host`
- Result: mipi_host0 and mipi_host1 completely failed to probe (only mipi_host4 remained)
- **Fix applied: DTB reverted to stock. mipi_host0/1 are now working again.**

---

## 4. The Current Error — Detailed Trace

### 4.1 Test Command

```bash
$ cd /app/multimedia_samples/sample_vin/get_vin_data
$ sudo ./get_vin_data -s 6    # sensor index 6 = sc230ai-30fps
```

### 4.2 Console Output

```
Using index:6  sensor_name:sc230ai-30fps  config_file:linear_1920x1080_raw10_30fps_1lane.c
mipi mclk is not configed.
Searching camera sensor on device: /proc/device-tree/soc/vcon@0 i2c bus: 1 mipi rx phy: 0
mipi rx used phy: 00000000
INFO: Found sensor_name:sc230ai-30fps on mipi rx csi 0, i2c addr 0x30,
      config_file:linear_1920x1080_raw10_30fps_1lane.c
create_and_run_vflow(301) failed, ret -36
create_and_run_vflow failed for sensor 6. ret = -36
```

### 4.3 Kernel Log (dmesg) During Test

```
[SENSOR0]: sc230ai open i2c1@0x30                                    ✅ Sensor driver opened
[SENSOR0]: camera_tuning_update_param done                            ✅ ISP tuning loaded
[SENSOR0]: ctrl_mode set to user                                      ✅
[SENSOR0]: camera_init_result cmd: done wake                          ✅ Sensor initialized
[SENSOR0]: camera_set_intrinsic_param port 0 done                     ✅
[SENSOR0]: sensor_attach flow0 ctx0 to sensor0 sc230ai                ✅ Attached to pipeline
[VCON0]: flow0.ctx0 attach sensor0 done                               ✅
[RX0]: init cmd: 0 real                                               ✅ MIPI RX init
[RX0]: 1 lane 1920x1080 30fps datatype 0x2b                           ✅ Config correct
[RX0]: mclk 24 ignore                                                 ⚠️  MCLK IGNORED (no pinctrl)
[RX0]: ipiclk limit 48352500 up to 102000000                          ✅
[RX0]: ipiclk set 102000000 get 600000000                             ✅
[RX0]: dphy 810Mbps/1lane: ppi 8bit settle 22                         ✅ PHY configured
[RX0]: ipi config hsa: 8, hbp: 8, hsd: 1                              ✅
[RX0]: config 1/1 ipi done                                            ✅
[RX0]: check phy stop state                                           ✅
[RX0]: init end                                                       ✅ MIPI init complete
[SENSOR0]: sensor_start sc230ai flow0 start done                      ✅ Sensor started streaming
[VCON0]: sensor0 start real done                                      ✅
[RX0]: start cmd: 0 real                                              ✅ MIPI RX started
[RX0]: check hs reception                                             ⏳ Checking for data...
[RX0]: hs reception check error 0x10000                               ❌ NO MIPI DATA RECEIVED
[RX0]: hs reception state error                                       ❌
[RX0]: start error: -1                                                ❌
vin_node_start mipi start fail                                        ❌ Pipeline start failed
```

### 4.4 Error Analysis

| Step | Status | Detail |
|------|--------|--------|
| I2C communication | ✅ | Chip ID reads correctly (0xCB34) |
| Sensor driver load | ✅ | `libsc230ai.so.1.0.0` loaded |
| ISP calibration load | ✅ | `lib_sc230ai_linear.so` loaded |
| Sensor initialization | ✅ | All register writes succeed |
| MIPI RX PHY init | ✅ | 810Mbps, 1 lane, settle=22 |
| **MCLK output** | ❌ | **`mclk 24 ignore` — SoC cannot provide MCLK** |
| Sensor streaming start | ✅ | Driver writes streaming register |
| **MIPI HS reception** | ❌ | **`hs reception check error 0x10000` — No data on MIPI lane** |

**Root Cause: The sensor is told to stream, but the MIPI RX PHY receives no high-speed data. The most likely cause is that the sensor has no MCLK to drive its PLL and generate MIPI output.**

### 4.5 Python API (libsrcampy) — Same Issue

```python
from hobot_vio import libsrcampy
cam = libsrcampy.Camera()
ret = cam.open_cam(0, -1, 30, 1920, 1080)   # Returns -1, detects as "ovx8bstd-30fps"
```

**Note:** The `libhbspdev.so` library (used by `libsrcampy`) does NOT include SC230AI in its compiled sensor list. It only has `imx219`, `ar0820std`, and `ovx8bstd`. The OVX8B config's wildcard `chip_id=0xA55A` matches any sensor, so it catches the SC230AI before the correct driver can match.

The C sample `get_vin_data` has the full sensor list including SC230AI (index 6) and correctly detects it.

---

## 5. Why OVX8B Was Previously Misidentified

The sensor auto-detection works by iterating through a compiled list of sensor configs and checking each sensor's chip ID:

```c
// From vp_sensors.c — sensor detection logic
if (sensor_config->chip_id == 0xA55A ||   // WILDCARD — matches ANY sensor
    ((chip_id & 0xFF) == (sensor_config->chip_id >> 8 & 0xFF)) ||
    ((chip_id & 0xFF) == (sensor_config->chip_id & 0xFF))) {
    return addr;  // Sensor "matched"
}
```

The `libhbspdev.so` sensor list:
```
0: imx219        (chip_id_reg=0x0000, chip_id=0x0219)
1: ar0820std     (chip_id_reg=0x3000, chip_id=0x0A20)
2: ovx8bstd      (chip_id_reg=0x0000, chip_id=0xA55A)  ← WILDCARD!
```

Since **SC230AI is not in this list**, the wildcard OVX8B entry matches first. The OVX8B driver then fails because:
1. It tries to load `lib_CL_OX8GB_L121_067_L.so` (OVX8B-specific ISP calibration) — doesn't exist
2. Error: `hbn_camera_create failed, ret(-65666)` (CHECK_ERROR)

The `get_vin_data` sample has the full list (including SC230AI at index 6), and properly detects it using `chip_id_reg=0x3107, chip_id=0xcb34`.

---

## 6. The MCLK Problem

### 6.1 Current State

The SC230AI sensor config requests `mclk = 24` (24 MHz). The MIPI host driver logs `[RX0]: mclk 24 ignore` because:

1. The stock DTB has **no clock or pinctrl properties** on mipi_host0/1
2. Without `clocks`, `clock-names`, `pinctrl-names`, `pinctrl-0`, and `snrclk-idx` in the DTB, the driver **cannot enable MCLK output** from the SoC
3. The only available `cam_clkout_func` pinctrl uses pin `cam_lpwm1_dout3`, which is **already claimed by the Ethernet controller**
4. Writing to `/sys/class/vps/mipi_host0/param/snrclk_freq` returns **I/O error** (no clock provider)

### 6.2 Key Question: Does SC230AI Need External MCLK?

**Evidence FOR the sensor having MCLK already:**
- Both sensors respond to I2C with correct chip ID → they have power and some clock
- The official DIP switch setting is SW2200=LPWM (not MCLK) → D-Robotics docs say LPWM, not MCLK
- I2C communication works without any MCLK configuration

**Evidence AGAINST:**
- MIPI HS reception completely fails → sensor may only have power for I2C, not enough clock for MIPI streaming
- The sensor config explicitly requests `mclk = 24`
- SC230AI datasheet specifies 6-27 MHz external MCLK input
- The `mclk 24 ignore` message suggests the framework knows MCLK is needed but can't provide it

### 6.3 Possible MCLK Sources

| Source | Pin/Method | Status |
|--------|-----------|--------|
| SoC `cam_clkout` | Pin `cam_lpwm1_dout3` | ❌ Conflicts with Ethernet on S100 |
| SoC alternative pin | Unknown | ❓ No other `cam_clkout` pinctrl defined in DTB |
| Camera module oscillator | Onboard crystal | ❓ Unknown if present on this module |
| Expansion board oscillator | Pin 5 of MIPI connector | ❓ SW2200=LPWM sends LPWM signal, not clock |
| DIP SW2200 → MCLK position | Pin 5 = SoC MCLK output | ⚠️ But SoC still needs DTB config to output clock |

### 6.4 Failed DTB Modification Attempt

Previous attempt to add MCLK support to DTB:
```dts
/* Added to mipi_host@0x37420000 — CAUSED PROBE FAILURE */
clocks = <0x6f>;           /* cam0_dummy_clk — fixed 24MHz */
clock-names = "snrclk";
pinctrl-names = "default";
pinctrl-0 = <0xf0>;        /* cam_clkout_func — uses cam_lpwm1_dout3 */
snrclk-idx = <0x00>;
```

**Result:** Pin conflict destroyed mipi_host0/1 probe. Reverted.

---

## 7. What Has Been Tried

| # | Attempt | Result |
|---|---------|--------|
| 1 | `open_cam(0, -1, 30, 1920, 1080)` via libsrcampy | ❌ Detects as OVX8B (wildcard), fails -65666 |
| 2 | `open_cam(0, 0, 30, 1920, 1080)` via libsrcampy | ❌ Same OVX8B mismatch, fails -65665/-65666 |
| 3 | Created OVX8B ISP calibration stub | ❌ Proprietary binary format, can't be faked |
| 4 | `get_vin_data -s 6` (SC230AI index) | ✅ Correct detection! But ❌ MIPI HS reception error |
| 5 | DTB mod: add MCLK pinctrl to mipi_host0/1 | ❌ Pin conflict with Ethernet, broke mipi_host0/1 |
| 6 | DTB reverted to stock | ✅ mipi_host0/1 restored |
| 7 | Write to sysfs `snrclk_freq` / `snrclk_en` | ❌ I/O error (no clock provider in DTB) |
| 8 | Verified DIP switches at default (LPWM + 3.3V) | ✅ Matches official SC230AI docs |

---

## 8. Current System State (After All Fixes)

| Component | State |
|-----------|-------|
| DTB | ✅ Stock/clean (no MCLK mod) |
| mipi_host0 | ✅ Probed, available in sysfs |
| mipi_host1 | ✅ Probed, available in sysfs |
| SC230AI left sensor | ✅ Detected on I2C bus 1, addr 0x30, chip_id=0xCB34 |
| SC230AI right sensor | ✅ Detected on I2C bus 2, addr 0x32, chip_id=0xCB34 |
| SC230AI sensor driver | ✅ Loaded, initializes sensor successfully |
| SC230AI ISP calibration | ✅ `lib_sc230ai_linear.so` present and loads |
| MCLK from SoC | ❌ Cannot be provided (no DTB config, pin conflict) |
| MIPI data reception | ❌ `hs reception check error 0x10000` |
| libsrcampy SC230AI | ❌ Not in compiled sensor list (only OVX8B wildcard) |
| `get_vin_data -s 6` | ✅ Detects SC230AI correctly, but pipeline fails at MIPI start |

---

## 9. Questions for Expert / D-Robotics Community

1. **How does the SC230AI stereo camera module receive MCLK on the RDK S100 Camera Expansion Board?**
   - The only `cam_clkout` pinctrl in the DTB uses a pin (`cam_lpwm1_dout3`) that's claimed by Ethernet
   - DIP SW2200 is set to LPWM (official setting), not MCLK
   - Does the camera module have an onboard oscillator?
   - Is there a different SoC pin that can provide MCLK without conflicting with Ethernet?

2. **Is there a working DTB or overlay for SC230AI on the RDK S100 Camera Expansion Board?**
   - The stock `rdk-s100-v1p0.dtb` has no MCLK configuration for mipi_host0/1
   - Are `rdk-s100-v1-2.dtb` or `rdk-s100-v1-21.dtb` (which are smaller — 150,772 bytes vs 151,259 bytes) meant for the camera expansion board?

3. **Why is `cam_lpwm1_dout3` shared between `cam_clkout_func` and the Ethernet controller?**
   - Is this a DTB bug or intentional design?
   - Can the Ethernet controller use a different pin?

4. **Why is SC230AI missing from the `libhbspdev.so` sensor list (used by libsrcampy)?**
   - The C sample `get_vin_data` includes it, but the Python API doesn't
   - Can `libhbspdev.so` be rebuilt with SC230AI, or is there an updated package?

5. **Can the `mclk = 24` be set to `mclk = 0` in the sensor config to skip MCLK configuration?**
   - If the camera module has its own oscillator, the SoC shouldn't need to output MCLK
   - Would this change the `mclk 24 ignore` behavior and allow MIPI to work?

---

## 10. Relevant File Paths

```
/usr/hobot/lib/sensor/
├── libsc230ai.so → libsc230ai.so.1.0.0       # SC230AI sensor driver (24 KB) ✅
├── lib_sc230ai_linear.so                       # SC230AI ISP calibration (77 KB) ✅
├── libovx8bstd.so → libovx8bstd.so.1.2.0     # OVX8B sensor driver (156 KB)
├── libovx8b.so → libovx8b.so.1.2.0           # OVX8B alt driver (132 KB)
└── ... (30+ other sensor drivers)

/app/multimedia_samples/
├── vp_sensors/
│   ├── sc230ai/linear_1920x1080_raw10_30fps_1lane.c   # SC230AI config ✅
│   ├── ovx8bstd/linear_1920x1080_raw12_30fps_1lane.c  # OVX8B config (wrong sensor)
│   └── vp_sensors.c                                    # Sensor list & detection logic
├── sample_vin/get_vin_data/get_vin_data                # Working binary with SC230AI
└── sunrise_camera/                                     # WebSocket camera app

/app/tuning_tool/cfg/matrix/
├── tuning_sc230ai_dual_cim_isp_1080p/                  # Official dual SC230AI tuning config ✅
│   ├── hb_j6dev.json                                   # Sensor addresses & calibration
│   ├── mipi.json                                       # MIPI lane config
│   ├── vpm_config.json                                 # Full pipeline config
│   └── lpwm_30fps.json                                 # LPWM timing config
└── tuning_sc230ai_cim_isp_1080p/                       # Single SC230AI config

/boot/hobot/rdk-s100-v1p0.dtb                           # Active DTB (stock, no MCLK)

/usr/local/lib/python3.10/dist-packages/hobot_vio/
├── libsrcampy.so                                       # Python camera wrapper
└── libhbspdev.so                                       # Sensor detection (missing SC230AI!)
```

---

## 11. Summary

The RDK Stereo Camera Module contains **SC230AI** sensors (chip ID `0xCB34`), not OVX8B. All software components for SC230AI (sensor driver, ISP calibration, tuning configs) are present on the system. The SC230AI sensor initializes correctly and is properly detected by the C sample programs.

**The single remaining blocker is MIPI HS reception failure.** The most likely cause is that the sensor cannot output MIPI data because it has no MCLK. The SoC's only `cam_clkout` pin conflicts with the Ethernet controller, and the stock DTB has no MCLK configuration for the MIPI hosts. The official DIP switch documentation says SC230AI should use LPWM (not MCLK), which suggests either (a) the camera module has its own oscillator that should provide MCLK, or (b) there is a DTB configuration we're missing that enables MCLK through a different mechanism.
