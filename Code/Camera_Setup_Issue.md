# Camera Setup Issue — SC230AI Stereo Camera on RDK S100

**Date:** 2026-03-08 (Updated)
**Board:** D-Robotics RDK S100 V1P0
**Camera:** RDK Stereo Camera Module (SC230AI dual)
**Project:** Pocket ASHA — AI for Bharat Hackathon
**Status:** ❌ BLOCKED — MIPI HS reception fails; sensor initializes but no video data received
**Next Action:** 🔧 Flip DIP switch SW2200 from LPWM → MCLK (hardware fix — see Section 11)

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

## 6. The MCLK Problem — Deep Dive

### 6.1 Current State

The SC230AI sensor config requests `mclk = 24` (24 MHz). The MIPI host driver logs `[RX0]: mclk 24 ignore` because:

1. The stock DTB has **no clock or pinctrl properties** on mipi_host0/1
2. Without `clocks`, `clock-names`, `pinctrl-names`, `pinctrl-0`, and `snrclk-idx` in the DTB, the driver **cannot enable MCLK output** from the SoC
3. The only available `cam_clkout_func` pinctrl uses pin `cam_lpwm1_dout3`, which is **already claimed by the Ethernet controller**
4. Writing to `/sys/class/vps/mipi_host0/param/snrclk_freq` returns **I/O error** (no clock provider)

### 6.2 Failure Chain

```
SC230AI needs 24 MHz MCLK to drive internal PLL
    → PLL drives MIPI transmitter
    → MIPI outputs HS data to SoC RX PHY

Without MCLK:
    Sensor powers up (enough for I2C register access)
    → Sensor is told to "start streaming" via I2C register writes
    → But with no MCLK, the PLL cannot lock, MIPI transmitter stays idle
    → SoC MIPI RX checks for High-Speed data
    → Finds nothing → error 0x10000 → pipeline start fails
```

### 6.3 Pin Conflict — cam_lpwm1_dout3

The SoC's only `cam_clkout` pinctrl group (`cam_clkout_func`, phandle `0xf0`) routes through pin `cam_lpwm1_dout3`:

```dts
cam_clkout_func {
    phandle = <0xf0>;
    pinmux { function = "cam_clkout"; pins = "cam_lpwm1_dout3"; };
    pinconf { pins = "cam_lpwm1_dout3"; drive-strength = <0x01>; };
};
```

This pin is **claimed by the Ethernet controller** (`ethernet@0x33100000`):

```dts
cam_emac_mdio_hsi1_1_func {
    phandle = <0x3d>;
    pinmux { function = "cam_emac_mdio_hsi1_1"; pins = "cam_lpwm1_dout2\0cam_lpwm1_dout3"; };
};
```

The ethernet1 interface (`33100000.ethernet`) is actually **unused** (DOWN, NO-CARRIER), while eth0 (`32110000.ethernet`) is the active network interface. But the DTB still claims the pin.

### 6.4 DTB Modification Attempt #1 — MCLK Pinctrl (FAILED — Pin Conflict)

**What was tried:** Added MCLK pinctrl (`cam_clkout_func`, phandle `0xf0`) directly to mipi_host0 and mipi_host1 without addressing the Ethernet pin conflict.

```dts
/* Added to mipi_host@0x37420000 */
clocks = <0x6f>;           /* cam0_dummy_clk — fixed 24MHz */
clock-names = "snrclk";
pinctrl-names = "default";
pinctrl-0 = <0xf0>;        /* cam_clkout_func — uses cam_lpwm1_dout3 */
snrclk-idx = <0x00>;
```

**Result:** Pin conflict destroyed mipi_host0/1 probe:
```
s100-pinctrl 370f3000.pinctrl: pin LPWM1_DOUT3 already requested by 33100000.ethernet;
cannot claim for 37420000.mipi_host
```
Only mipi_host4 remained. **DTB reverted to stock.**

### 6.5 DTB Modification Attempt #2 — Disable Ethernet1 + cam0_dummy_clk (FAILED — Virtual Clock)

**What was tried:** A three-part DTB modification:
1. **Disabled ethernet@0x33100000** (ethernet1) → freed pin `cam_lpwm1_dout3`
2. **Added clock config to mipi_host0:** `clocks = <0x6f>` (`cam0_dummy_clk` at 24MHz), `clock-names = "snrclk"`, `pinctrl-names = "default"`, `pinctrl-0 = <0xf0>` (`cam_clkout_func`), `snrclk-idx = <0x00>`
3. **Added clock config to mipi_host1:** `clocks = <0x6f>`, `clock-names = "snrclk"`, `snrclk-idx = <0x01>`

Modified DTB compiled successfully (151,414 bytes vs stock 151,259 bytes). Installed and rebooted.

**Post-reboot results — partial success:**
- ✅ eth0 remained UP (192.168.0.174) — network preserved
- ✅ eth1 absent (disabled correctly) — no pin conflict
- ✅ No pin conflict errors in dmesg
- ✅ Both SC230AI sensors still responsive on I2C
- ❌ **`[RX0]: snrclk not support`** — NEW error (appeared twice at boot, lines 2962 and 3022)
- ❌ `mclk 24 ignore` — still present
- ❌ `hs reception check error 0x10000` — same failure
- ❌ `snrclk_freq: 0` (was 24000000 with stock DTB)
- ❌ `snrclk_en: 0`

**Root cause discovered:** `cam0_dummy_clk` (phandle `0x6f`) is a **virtual fixed-clock**:
```dts
cam0_dummy_clk {
    compatible = "fixed-clock";
    clock-frequency = <0x16e3600>;  /* 24000000 = 24 MHz */
    #clock-cells = <0x00>;
    clock-output-names = "cam0_dummy_clk";
    phandle = <0x6f>;
};
```
This is a Linux clock framework abstraction — it does NOT drive any physical hardware pin. The kernel registers it (`cam0_dummy_clk: 24000000 Hz` in clk_summary) but it has zero enable count and `deviceless` association. The MIPI host driver cannot use it to generate a real clock signal on the cam_clkout pin.

### 6.6 Deep Kernel Driver Analysis — The Real Story

Investigation of the MIPI host driver (`hobot_mipicsi.ko`) revealed the critical finding:

```
$ nm hobot_mipicsi.ko | grep ' U ' | grep clk
                 U vio_clk_disable
                 U vio_clk_enable
                 U vio_get_clk_rate
                 U vio_set_clk_rate
```

The driver does **NOT** use the standard Linux clock framework at all. There are no calls to `devm_clk_get()`, `clk_prepare_enable()`, or `clk_set_rate()`. Instead, it uses a proprietary VIO (Video I/O) clock subsystem exported by `hobot_vio_common.ko`.

The VIO common module does use Linux `devm_clk_bulk_get_all()` internally, but its camera system clock operations are **all empty stubs**:
```
[I|VPF|hobot_vpf_manager_linux.c+895]: empty_camsys_clk_disable: empty function
[I|VPF|hobot_vpf_manager_linux.c+895]: empty_camsys_clk_disable: empty function
```

This means:
1. **Adding `clocks`/`clock-names` to DTB nodes has ZERO effect** — the MIPI driver never reads them with `devm_clk_get()`
2. **Neither `cam0_dummy_clk` nor any SCMI clock can provide MCLK through software** — the clock management pipeline is not implemented for the camera subsystem
3. The `snrclk not support` message means "I have no hardware clock control capability"
4. The `mclk 24 ignore` message means "sensor config requests MCLK but I can't deliver it"

**DTB reverted to stock after this finding.**

### 6.7 SCMI Clock Controller Investigation

The real hardware clock controller on the S100 SoC is the SCMI (System Control and Management Interface) controller:
```dts
protocol@14 {
    reg = <0x14>;
    #clock-cells = <0x01>;
    phandle = <0x3e>;
};
```

All real hardware clocks (I2C, SPI, UART, ISP, GPU, etc.) reference `<0x3e CLOCK_ID>`. Camera-related SCMI clocks found:

| Clock Name | Frequency | Description |
|-----------|-----------|-------------|
| ATcamextref | 26 MHz | Camera external reference |
| ATcamlpwm | 1,200 MHz | LPWM base clock |
| ATcamrxcdphytxe | 24 MHz | MIPI RX PHY TX escape clock |
| ATcammipiphytxr | 24 MHz | MIPI PHY TX reference clock |
| ATcammipiphycfg | 24 MHz | MIPI PHY configuration clock |
| ATcamclpym | — | PYM (pyramid scaler) clock |
| ATcamclgdc | — | GDC (geometric distortion correction) clock |
| ATcamclsth | — | Stitch clock |
| ATcamclpix | — | Pixel clock |
| AGcamc0mipi0-3 | — | Camera channel 0 MIPI clocks |
| AGcamc1mipi0-3 | — | Camera channel 1 MIPI clocks |

None of these are named "snrclk" or "cam_clkout." The ISP node uses:
```dts
clocks = <0x3e 0x07 0x3e 0x7d 0x3e 0x7e>;
clock-names = "isp_pix\0isp_noc\0isp_apb";
```

But the MIPI host nodes in the stock DTB have **no clock references at all** — confirming that the S100 BSP was not designed to output MCLK from the SoC to external sensors.

### 6.8 cam_top Register Scan

Direct register reads of the camera subsystem top-level registers at `0x37010000` (cam_top):

| Address | Value | Notes |
|---------|-------|-------|
| 0x37010000 | 0x00000007 | CPE0 control |
| 0x37010004 | 0x00000002 | CPE0 status |
| 0x37010044 | 0x0000001C | CPE0 config |
| 0x37010070 | 0x310A0000 | Version/ID register |
| 0x37010100 | 0x00000007 | CPE1 control |
| 0x37010200 | 0x00000007 | CPE_lite control |
| 0x37010300 | 0x0BADBEEF | Sentinel/magic value |
| 0x37010310 | 0x0000007F | Interrupt mask |
| 0x37010330-338 | 0x0003FFFF | Watchdog thresholds |

No MCLK output control registers found in the cam_top register space.

### 6.9 LPWM1 — Not a Clock Source

LPWM1 (`370f1000.lpwm1`) is present and functional with 4 PWM channels (via `pwmchip4`), clocked by ATcamlpwm at 1.2 GHz. However:
- LPWM outputs **pulse width modulation signals**, not a clean clock
- LPWM1 uses pinctrl `cam_lpwm1_dout01_func` (pins dout0, dout1 only — channels 0 and 1 are enabled)
- The sensor needs a continuous 24MHz clock, not PWM pulses
- LPWM channel config: `channel = <0x01 0x01 0x00 0x00>` (channels 0,1 enabled; 2,3 disabled)

---

## 7. Complete List of Everything Tried

| # | Attempt | Result | Details |
|---|---------|--------|---------|
| 1 | `open_cam(0, -1, 30, 1920, 1080)` via libsrcampy | ❌ | Detects as OVX8B (wildcard chip_id=0xA55A), fails -65666 |
| 2 | `open_cam(0, 0, 30, 1920, 1080)` via libsrcampy | ❌ | Same OVX8B mismatch, fails -65665/-65666 |
| 3 | Various `open_cam()` parameter combinations | ❌ | Python API cannot reach SC230AI — not in `libhbspdev.so` sensor list |
| 4 | Created OVX8B ISP calibration stub (`lib_CL_OX8GB_L121_067_L.so`) | ❌ | Proprietary binary format, 8368-byte stub can't be used as real calibration |
| 5 | Removed OVX8B ISP calibration stub | ✅ | Cleaned up irrelevant OVX8B artifact |
| 6 | Direct I2C chip ID read (registers 0x3107/0x3108) | ✅ | Confirmed both sensors are SC230AI (chip ID 0xCB34), NOT OVX8B |
| 7 | `get_vin_data -s 6` (SC230AI sensor index) | ✅/❌ | Correct detection and driver init, but MIPI HS reception error -36 |
| 8 | DTB mod #1: Add MCLK pinctrl to mipi_host0/1 (cam_clkout_func) | ❌ | Pin conflict: `cam_lpwm1_dout3` claimed by ethernet@0x33100000; mipi_host0/1 failed to probe |
| 9 | DTB reverted to stock after attempt #8 | ✅ | mipi_host0/1 restored |
| 10 | Write to sysfs `snrclk_freq`/`snrclk_en` | ❌ | I/O error — no clock provider registered in DTB |
| 11 | Verified DIP switches at default (SW2200=LPWM, SW2201=3.3V) | ✅ | Matches official SC230AI docs |
| 12 | DTB mod #2: Disabled ethernet1 + cam0_dummy_clk + cam_clkout_func | ❌ | Pin conflict resolved, but `cam0_dummy_clk` is a virtual fixed-clock — `snrclk not support` |
| 13 | DTB reverted to stock after attempt #12 | ✅ | Clean baseline restored |
| 14 | Investigated SCMI clock controller (phandle 0x3e, protocol@14) | ❓ | Found 97+ SCMI clocks but none named "snrclk" or "cam_clkout"; no SCMI clock ID for sensor MCLK |
| 15 | Analyzed MIPI driver binary (`hobot_mipicsi.ko`) with `nm` and `strings` | ✅ | **Critical finding:** Driver does NOT use Linux clock framework; uses proprietary `vio_clk_enable()` from `hobot_vio_common.ko` |
| 16 | Analyzed VIO common module (`hobot_vio_common.ko`) | ✅ | Camera clock operations are empty stubs: `empty_camsys_clk_enable: empty function` |
| 17 | Scanned cam_top registers (0x37010000–0x37010FFF) via `devmem` | ✅ | Found control/status/watchdog registers, NO MCLK output control register |
| 18 | Investigated all 165 SCMI clock names from `clk_summary` | ✅ | Mapped camera clocks (ATcamextref 26MHz, ATcamrxcdphytxe 24MHz, etc.) — none control cam_clkout pin |
| 19 | Checked LPWM1 as potential clock source | ❌ | LPWM outputs PWM signals, not clean clock; only channels 0,1 enabled (pins dout0/dout1) |
| 20 | Checked camsys module (`hobot_camsys.ko`) for clock handling | ❌ | No clock-related symbols; manages cam_subsys watchdog/reset only |
| 21 | Ran tuning_bin with dual SC230AI config | ❌ | Same failure: `mclk 24 ignore` → `hs reception check error 0x10000` for both sensors |
| 22 | Diffed V1P0 vs V1.2 DTBs | ✅ | V1.2 has Ethernet disabled but identical mipi_host config (still no MCLK clock/pinctrl) |
| 23 | Checked alternate DTBs (`rdk-s100-v1-2.dtb`, `rdk-s100-v1-21.dtb`) | ❓ | Smaller files (150,772 bytes); V1.2 disables ethernet1 but still has no MCLK for mipi_host |
| 24 | Searched for TogetheROS.Bot (tros) ROS2 packages | ❌ | Not available in apt repos for this BSP version |
| 25 | Expert's fix_rdk_s100_stereo_camera.sh script | Partial | OVX8B cleanup done; ROS2/tros packages not available |

### Summary of Key Findings from All Attempts

1. **The MIPI host driver (`hobot_mipicsi.ko`) cannot output MCLK in software.** It doesn't use `devm_clk_get()` or the Linux clock framework. The VIO camera clock operations are empty stubs. No amount of DTB modification can make the SoC output a clock signal on `cam_clkout`.

2. **The `cam_clkout_func` pinctrl only routes the pin — it does not generate a clock.** Even if the pin conflict is resolved (by disabling ethernet1), there is no SoC clock generator connected to `cam_clkout`.

3. **`cam0_dummy_clk` is fake.** It's a Linux `fixed-clock` node that exists only as a clock tree placeholder — it cannot enable/disable or change frequency on any real hardware pin.

4. **The SCMI clock controller manages real SoC clocks** (I2C, SPI, ISP, GPU, etc.) but has no clock ID for "sensor MCLK output." This confirms the S100 BSP was not designed to output MCLK from the SoC.

5. **The only way to provide MCLK is from the Camera Expansion Board hardware** — via the onboard 24 MHz crystal oscillator, switched by DIP SW2200.

---

## 8. Current System State (After All Debugging)

| Component | State | Notes |
|-----------|-------|-------|
| DTB | ✅ Stock/clean | Reverted after both DTB modification attempts |
| Ethernet eth0 | ✅ UP | Active network interface (192.168.0.174) |
| Ethernet eth1 | ✅ Present | Re-enabled after DTB revert (was disabled in attempt #12) |
| mipi_host0 | ✅ Probed, available | `/sys/class/vps/mipi_host0` |
| mipi_host1 | ✅ Probed, available | `/sys/class/vps/mipi_host1` |
| SC230AI left sensor | ✅ I2C bus 1, addr 0x30 | Chip ID 0xCB34 confirmed |
| SC230AI right sensor | ✅ I2C bus 2, addr 0x32 | Chip ID 0xCB34 confirmed |
| SC230AI sensor driver | ✅ Loaded | `libsc230ai.so.1.0.0` (23,864 bytes) |
| SC230AI ISP calibration | ✅ Loaded | `lib_sc230ai_linear.so` (77,088 bytes) |
| OVX8B stub | ✅ Removed | Was at `/usr/hobot/lib/sensor/lib_CL_OX8GB_L121_067_L.so` |
| MCLK from SoC | ❌ **Impossible** | Driver has no clock framework support; cam_clkout has no clock generator |
| snrclk_freq (mipi_host0) | 24000000 | Value from sensor config, but `snrclk: not support` |
| snrclk_en (mipi_host0) | 0 | Cannot be enabled — no hardware support |
| MIPI data reception | ❌ Error 0x10000 | No High-Speed data from sensor |
| libsrcampy SC230AI | ❌ Not available | Not in `libhbspdev.so` compiled sensor list |
| `get_vin_data -s 6` | ✅/❌ | Detects SC230AI correctly, but pipeline fails at MIPI HS check |
| DIP SW2200 | LPWM (UP) | **Needs to be flipped to MCLK (DOWN)** |
| DIP SW2201 | 3.3V (UP) | Correct — do not change |
| Stock DTB backup | ✅ Safe | `/boot/hobot/rdk-s100-v1p0.dtb.stock-backup` (151,259 bytes) |
| Rollback script | ✅ Ready | `/home/sunrise/rollback_dtb.sh` (executable) |
| Test script | ✅ Ready | `/home/sunrise/test_camera_after_reboot.sh` (executable) |

---

## 9. Root Cause Analysis — Final Verdict

### The Problem

The SC230AI sensor requires a 24 MHz external master clock (MCLK) to drive its internal PLL and generate MIPI lane data. Without MCLK, the sensor can respond to I2C commands (chip ID reads, register writes, streaming start) but **cannot output any MIPI High-Speed data**.

### Why SoC MCLK Is Impossible on the RDK S100

Through exhaustive investigation, we have conclusively determined that **the RDK S100 BSP cannot output MCLK from the SoC to external sensors**:

1. **The MIPI host driver (`hobot_mipicsi.ko`) has no clock framework support.** It does not call `devm_clk_get()`, `clk_prepare_enable()`, or any standard Linux clock API. It uses only the proprietary VIO clock subsystem (`vio_clk_enable()` from `hobot_vio_common.ko`).

2. **The VIO camera clock operations are empty stubs.** The camera subsystem clock enable/disable/set_rate callbacks all point to `empty_camsys_clk_*` functions that do nothing. Kernel log confirms: `empty_camsys_clk_disable: empty function`.

3. **There is no hardware clock generator connected to `cam_clkout`.** The `cam_clkout_func` pinctrl can route a pin, but there's no clock source driving it. The SCMI clock controller (which manages all real SoC clocks) has no clock ID for "sensor MCLK output."

4. **`cam0_dummy_clk` is a Linux clock tree placeholder, not a hardware clock.** It's a `fixed-clock` node that reports 24MHz but has no physical connection to any pin — it's virtual.

5. **The `cam_clkout` pin (`cam_lpwm1_dout3`) is also claimed by the Ethernet controller.** Even if a clock generator existed, there's a pin conflict. Disabling ethernet1 resolves the conflict but doesn't create a clock source.

### The Solution: Hardware MCLK from Camera Expansion Board

The Camera Expansion Board has a **24 MHz active crystal oscillator** that can output MCLK directly to the camera sensor connectors (J2200/J2201, Pin 5). This is controlled by DIP switch **SW2200**.

When SW2200 is set to MCLK (DOWN position), the expansion board's crystal oscillator provides 24 MHz directly to each camera sensor **through the connector hardware**, completely bypassing the SoC. The `mclk 24 ignore` kernel message is then harmless — the sensor gets its clock from the board, not the SoC.

---

## 10. Questions for Expert / D-Robotics Community

1. **Confirm SW2200=MCLK is correct for SC230AI on S100?** The official docs say LPWM, but the S100 SoC cannot output MCLK through software. Is the documentation wrong for the S100, or is there a different mechanism?

2. **Is there an updated BSP/DTB for S100 with SC230AI MCLK support?** The current BSP has empty camera clock stubs. Was MCLK support planned but not yet implemented?

3. **Why is SC230AI missing from `libhbspdev.so` (Python API)?** The C API (`get_vin_data`) has it at index 6, but `libsrcampy` only has `imx219`, `ar0820std`, and `ovx8bstd`.

4. **Can `mclk = 0` in the sensor config bypass the `mclk 24 ignore` check?** If the expansion board provides MCLK externally, the SoC shouldn't need to configure it.

---

## 11. Next Steps — DIP Switch SW2200 Fix

### Instructions (HARDWARE FIX — Must be done physically)

```
1. Power OFF the RDK S100 completely (SW1 to OFF, unplug DC power)
2. Locate DIP switch SW2200 on the Camera Expansion Board
   - Small 2-position DIP switch near the MIPI camera connectors
   - Currently set to LPWM (both switches in UP position)
3. Flip BOTH switches on SW2200 to the MCLK position (DOWN)
   - Switch 1 = MCLK for MIPI Cam 1 (J2200, left sensor)
   - Switch 2 = MCLK for MIPI Cam 2 (J2201, right sensor)
4. Confirm SW2201 is still at 3.3V (both UP) — do NOT change this
5. Power ON the board and wait for boot
6. Test:
   cd /app/multimedia_samples/sample_vin/get_vin_data
   sudo ./get_vin_data -s 6
7. Check kernel log:
   dmesg | grep -E "mclk|hs reception|sc230"
```

### Expected Outcome If SW2200=MCLK Works

- `[RX0]: mclk 24 ignore` — still appears (SoC side) but harmless
- `[RX0]: check hs reception` → **succeeds** (no error 0x10000)
- `get_vin_data` captures frames and writes raw image files
- Camera pipeline starts successfully (no ret -36)

### Expected Outcome If SW2200=MCLK Does NOT Work

- Same `hs reception check error 0x10000` — means MCLK from SW2200 either doesn't reach the sensor via Pin 5, or the sensor requires a different MCLK routing
- In this case, contact D-Robotics support with this full issue document

---

## 12. Relevant File Paths

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

/boot/hobot/
├── rdk-s100-v1p0.dtb                                   # Active DTB (stock, no MCLK) ✅
├── rdk-s100-v1p0.dtb.stock-backup                      # Verified stock backup (151,259 bytes)
├── rdk-s100-v1-2.dtb                                   # Alternate DTB (ethernet1 disabled)
└── rdk-s100-v1-21.dtb                                  # Alternate DTB

/lib/modules/6.1.112-rt43-DR-4.0.4/hobot-drivers/camsys/
├── mipi/hobot_mipicsi.ko                               # MIPI host driver
├── mipi/hobot_mipidbg.ko                               # MIPI debug module
├── mipi/hobot_mipiphy.ko                               # MIPI PHY driver
├── vpf/hobot_vio_common.ko                             # VIO common (empty cam clock stubs)
├── cam_subsys/hobot_camsys.ko                          # Camera subsystem manager
├── adapter/hobot_camsys_adapter.ko                     # Camera system adapter
├── sensor_drv/hobot_sensor.ko                          # Sensor framework
└── ... (22 modules total)

/usr/local/lib/python3.10/dist-packages/hobot_vio/
├── libsrcampy.so                                       # Python camera wrapper
└── libhbspdev.so                                       # Sensor detection (missing SC230AI!)

/tmp/
├── v1p0.dts                                            # Stock DTB decompiled source
├── v1p0_mclk_fix.dts                                   # Modified DTS from attempt #12
└── running.dts                                         # Currently running DTB decompiled

/home/sunrise/
├── test_camera_after_reboot.sh                         # Post-reboot camera test script ✅
└── rollback_dtb.sh                                     # DTB rollback script ✅
```

---

## 13. Kernel Module Analysis

### MIPI Host Driver — `hobot_mipicsi.ko`
```
Location: /lib/modules/6.1.112-rt43-DR-4.0.4/hobot-drivers/camsys/mipi/
Dependencies: hobot_mipidbg, hobot_mipiphy, hobot_vin_vnode, hobot_vio_common

Imported clock symbols (nm output):
  U vio_clk_disable       ← proprietary VIO clock API (NOT Linux clk framework)
  U vio_clk_enable
  U vio_get_clk_rate
  U vio_set_clk_rate

Relevant strings:
  "snrclk"                 ← clock name it looks for
  "snrclk not support"     ← printed when clock lookup fails
  "snrclk_en"              ← sysfs parameter
  "snrclk_freq"            ← sysfs parameter
  "mclk"                   ← internal reference
  "cfg_clock", "ref_clock", "snr_clock", "ipi_clock", "add_clock"

Does NOT import:
  - devm_clk_get()
  - clk_prepare_enable()
  - clk_set_rate()
  - of_clk_get()
```

### VIO Common — `hobot_vio_common.ko`
```
Location: /lib/modules/6.1.112-rt43-DR-4.0.4/hobot-drivers/camsys/vpf/

Exported clock symbols:
  T vio_clk_enable         ← called by MIPI driver
  T vio_clk_disable
  T vio_get_clk_rate
  T vio_set_clk_rate
  T vio_hw_get_clk_gate

Internal clock handling:
  U devm_clk_bulk_get_all  ← uses Linux clock framework internally
  U clk_bulk_enable/disable/prepare/unprepare
  U clk_get_rate

Camera subsystem callbacks (ALL EMPTY):
  t empty_camsys_clk_set_rate
  t empty_camsys_clk_get_rate
  t empty_camsys_clk_disable
  t empty_camsys_clk_enable
```

### Loaded Camera Modules (lsmod)
```
hobot_mipidbg         262144   0
hobot_mipicsi         327680   1  hobot_mipidbg
hobot_mipiphy         786432   2  hobot_mipidbg,hobot_mipicsi
hobot_vin_vnode       327680   4  hobot_mipicsi,hobot_vin_vcon,hobot_cim,hobot_lpwm
hobot_camsys_adapter  327680   5  hobot_gdc,hobot_pym_jplus,hobot_ynr,hobot_cim,hobot_isp
hobot_camsys          327680   3  hobot_idu_drm,hobot_idu_vnode,hobot_isp
hobot_vio_common      393216  15  (all camera modules depend on this)
```

---

## 14. Summary

The RDK Stereo Camera Module contains **SC230AI** sensors (chip ID `0xCB34`), not OVX8B. All software components for SC230AI (sensor driver, ISP calibration, tuning configs) are present on the system. The SC230AI sensor initializes correctly and is properly detected by the C sample programs.

**The single remaining blocker is MCLK — the sensor master clock.** After exhaustive debugging (25 separate attempts documented above), we have conclusively determined that:

1. **The RDK S100 SoC cannot output MCLK to external sensors through software.** The MIPI host driver does not implement Linux clock framework support, and the VIO camera clock operations are empty stubs.

2. **There is no hardware clock generator in the SoC connected to `cam_clkout`.** The SCMI clock controller, which manages all real SoC clocks, has no clock ID for sensor MCLK output.

3. **Two DTB modification attempts failed:** The first (adding pinctrl without resolving Ethernet pin conflict) broke mipi_host probing. The second (disabling ethernet1 + using cam0_dummy_clk) resolved the pin conflict but discovered that cam0_dummy_clk is a virtual fixed-clock with no hardware backing, resulting in `snrclk not support`.

4. **The MCLK must come from the Camera Expansion Board's 24 MHz crystal oscillator**, controlled by DIP switch SW2200. Flipping SW2200 from LPWM (UP) to MCLK (DOWN) should provide 24 MHz directly to the camera sensors through the MIPI connector Pin 5, bypassing the SoC entirely.

**Next action: Physically flip DIP switch SW2200 to MCLK position and retest.**
