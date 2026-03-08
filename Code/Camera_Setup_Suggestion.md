# Solution Guide — SC230AI Stereo Camera on RDK S100

**Date:** 2026-03-08  
**Board:** D-Robotics RDK S100 V1P0  
**Camera:** RDK Stereo Camera Module (SC230AI dual, from RDK X5 kit)  
**Project:** Pocket ASHA — AI for Bharat Hackathon  
**Issue:** MIPI HS reception fails — sensor initializes but receives no video data  

---

## Current Situation at a Glance

The debugging journey has been long. Here is exactly where things stand right now:

**What works:**
- Camera Expansion Board is powered (LED D2000 GREEN)
- Both SC230AI sensors respond on I2C (Bus 1 @ 0x30, Bus 2 @ 0x32, chip ID 0xCB34 confirmed)
- SC230AI sensor driver (`libsc230ai.so`) loads and initializes correctly
- SC230AI ISP calibration (`lib_sc230ai_linear.so`) loads successfully
- MIPI RX PHY 0 and PHY 1 are initialized with correct parameters (810 Mbps, 1 lane, RAW10)
- The C sample `get_vin_data -s 6` detects SC230AI correctly

**What fails:**
- `[RX0]: mclk 24 ignore` — the SoC cannot output MCLK because the stock DTB has no clock/pinctrl config for mipi_host0/1
- `[RX0]: hs reception check error 0x10000` — MIPI RX sees no high-speed data from the sensor
- The sensor is told to stream but has no master clock to drive its internal PLL and generate MIPI output
- `libsrcampy` (Python API) does not include SC230AI in its compiled sensor list, so it misidentifies as OVX8B via wildcard match

**What was already tried and eliminated:**
- OVX8B ISP calibration stubs — irrelevant, problem is SC230AI not OVX8B
- DTB modification to add MCLK pinctrl — pin `cam_lpwm1_dout3` conflicts with Ethernet controller, breaks mipi_host0/1
- sysfs writes to `snrclk_freq`/`snrclk_en` — returns I/O error because no clock provider exists in DTB
- Various `open_cam()` parameter combinations — Python API cannot reach SC230AI at all
- DTB has been reverted to stock and mipi_host0/1 are functional again

---

## Root Cause Analysis

The failure chain is:

```
SC230AI needs 24 MHz MCLK to drive PLL → PLL drives MIPI transmitter → MIPI outputs HS data
         ↑                                                                       ↓
    No MCLK provided                                              MIPI RX checks for HS data
    (DTB has no config,                                           finds nothing → error 0x10000
     SoC pin conflicts)                                           → pipeline start fails
```

The SC230AI datasheet specifies 6–27 MHz external MCLK input. Without it, the sensor powers up enough for I2C register access (which only needs the I2C clock) but cannot generate MIPI lane data. The sensor config file explicitly requests `mclk = 24`, and the kernel log confirms `mclk 24 ignore` — the framework knows MCLK is needed but cannot deliver it.

The fundamental hardware conflict: on the RDK S100 V1P0, the only `cam_clkout_func` pinctrl group routes through pin `cam_lpwm1_dout3`, which is already allocated to the Ethernet controller (`33100000.ethernet`). This is either a design oversight specific to the S100 V1P0 DTB or a deliberate trade-off where MCLK is expected to come from the Camera Expansion Board itself.

---

## Solution Path 1 (HIGHEST PRIORITY): Switch DIP SW2200 from LPWM to MCLK

### Why this is most likely correct

The Camera Expansion Board has a **24 MHz active crystal oscillator onboard** that can output either LPWM or 24 MHz MCLK to Pin 5 of the MIPI camera connectors (J2200/J2201). This is controlled by DIP switch SW2200.

Key evidence:
- The D-Robotics Camera Expansion Board documentation states: *"MIPI camera interface connectors support switching between LPWM and MCLK (24MHz) functions"*
- The expansion board has its own oscillator — the MCLK does NOT need to come from the SoC
- When SW2200 is set to MCLK, Pin 5 outputs 24 MHz from the expansion board's crystal, directly to the camera
- The `mclk 24 ignore` message from the SoC is then harmless — the camera gets its clock from the expansion board, not the SoC

The official docs say SC230AI uses LPWM, but this may be because on the RDK X5, the SoC provides MCLK through a different mechanism (the X5 DTB likely has proper MCLK pinctrl without Ethernet pin conflicts). On the S100 where SoC MCLK is broken, the expansion board's oscillator via SW2200=MCLK is the only viable clock source.

### Steps

```
1. Power OFF the RDK S100 completely (SW1 to OFF, unplug DC)
2. Locate DIP switch SW2200 on the Camera Expansion Board
   - It is a 2-position DIP switch near the MIPI connectors
   - Currently set to LPWM (both switches in UP position)
3. Flip BOTH switches on SW2200 to the MCLK position (DOWN)
   - Switch 1 = MCLK for MIPI Cam 1 (J2200, left sensor)
   - Switch 2 = MCLK for MIPI Cam 2 (J2201, right sensor)
4. Confirm SW2201 is still at 3.3V (both UP) — do not change this
5. Power ON the board
6. Test with get_vin_data:
   cd /app/multimedia_samples/sample_vin/get_vin_data
   sudo ./get_vin_data -s 6
7. Check dmesg for the critical line:
   dmesg | grep -E "mclk|hs reception"
```

**Expected outcome if this works:**
- `[RX0]: mclk 24 ignore` may still appear (SoC side) but the sensor now has its own 24 MHz clock
- `[RX0]: check hs reception` → should succeed (no error 0x10000)
- `get_vin_data` should capture frames and write raw files

**Expected outcome if this does NOT work:**
- Same `hs reception check error 0x10000` — meaning the MCLK from SW2200 either does not reach Pin 5 correctly, or the sensor requires MCLK through a different pin
- In this case, proceed to Solution Path 2

---

## Solution Path 2: Try Alternate DTBs (rdk-s100-v1-2.dtb or rdk-s100-v1-21.dtb)

### Why this might work

The `/boot/hobot/` directory contains DTBs with different sizes:
- `rdk-s100-v1p0.dtb` — 151,259 bytes (current, stock)
- `rdk-s100-v1-2.dtb` — 150,772 bytes (487 bytes smaller)
- `rdk-s100-v1-21.dtb` — 150,772 bytes (same smaller size)

The size difference suggests different peripheral configurations. These alternate DTBs might resolve the MCLK pin conflict by either routing `cam_clkout` to a different pin, or removing the Ethernet claim on `cam_lpwm1_dout3`, or including a proper camera-specific pinctrl group.

### Steps

```bash
# STEP 1: Backup current DTB
sudo cp /boot/hobot/rdk-s100-v1p0.dtb /boot/hobot/rdk-s100-v1p0.dtb.backup

# STEP 2: Decompile both DTBs and diff them to understand the differences
dtc -I dtb -O dts -o /tmp/v1p0.dts /boot/hobot/rdk-s100-v1p0.dtb
dtc -I dtb -O dts -o /tmp/v1-2.dts /boot/hobot/rdk-s100-v1-2.dtb
diff /tmp/v1p0.dts /tmp/v1-2.dts | head -200

# STEP 3: Look specifically for MCLK, clock, and pinctrl differences
diff /tmp/v1p0.dts /tmp/v1-2.dts | grep -A5 -B5 -iE "mclk|clkout|snrclk|cam_clk|pinctrl"

# STEP 4: If the diff shows camera/MCLK differences, try the alternate DTB
# Find the boot config file that selects the DTB:
cat /boot/hobot/board_config.conf 2>/dev/null || \
cat /boot/config.txt 2>/dev/null || \
cat /boot/hobot/env.txt 2>/dev/null

# STEP 5: Switch DTB (exact method depends on bootloader config format)
# Option A: If using board_config.conf
sudo sed -i 's/rdk-s100-v1p0.dtb/rdk-s100-v1-2.dtb/' /boot/hobot/board_config.conf

# Option B: If using env.txt
sudo sed -i 's/rdk-s100-v1p0.dtb/rdk-s100-v1-2.dtb/' /boot/hobot/env.txt

# Option C: Direct symlink/copy approach
sudo cp /boot/hobot/rdk-s100-v1-2.dtb /boot/hobot/rdk-s100-v1p0.dtb

# STEP 6: Reboot and test
sudo reboot
# After reboot:
cd /app/multimedia_samples/sample_vin/get_vin_data
sudo ./get_vin_data -s 6
dmesg | grep -E "mclk|hs reception|pin.*already"
```

**Before switching DTB blindly, always decompile and diff first.** The diff will immediately reveal whether the alternate DTB has different MCLK/pinctrl configuration.

---

## Solution Path 3: Create a Proper DTB Overlay for MCLK Without Pin Conflict

If the alternate DTBs don't help, we need to find a non-conflicting MCLK pin. The previous attempt used `cam_clkout_func` (phandle `0xf0`) which routes through `cam_lpwm1_dout3` — the pin claimed by Ethernet.

### Steps

```bash
# STEP 1: Find all available pinctrl groups related to camera clocks
dtc -I dtb -O dts /boot/hobot/rdk-s100-v1p0.dtb | grep -B2 -A10 "cam.*clk\|snrclk\|cam_clkout"

# STEP 2: Find which pins the Ethernet controller actually uses
dtc -I dtb -O dts /boot/hobot/rdk-s100-v1p0.dtb | grep -A20 "33100000.ethernet"

# STEP 3: Check if there are alternative cam_clkout pinctrl groups
# that use different physical pins
dtc -I dtb -O dts /boot/hobot/rdk-s100-v1p0.dtb | grep -B5 -A15 "cam_clkout"

# STEP 4: Check for cam0/cam1 specific clock outputs
dtc -I dtb -O dts /boot/hobot/rdk-s100-v1p0.dtb | grep -B2 -A10 "cam0_clk\|cam1_clk\|snrclk_idx"

# STEP 5: If a non-conflicting pinctrl group exists, create overlay
cat > /tmp/mclk_overlay.dts << 'EOF'
/dts-v1/;
/plugin/;

/ {
    fragment@0 {
        target-path = "/soc/mipi_host@0x37420000";
        __overlay__ {
            /* Replace <PHANDLE> with the actual non-conflicting pinctrl phandle */
            clocks = <CLOCK_PHANDLE>;
            clock-names = "snrclk";
            pinctrl-names = "default";
            pinctrl-0 = <NON_CONFLICTING_PINCTRL_PHANDLE>;
            snrclk-idx = <0x00>;
        };
    };
    fragment@1 {
        target-path = "/soc/mipi_host@0x37430000";
        __overlay__ {
            clocks = <CLOCK_PHANDLE>;
            clock-names = "snrclk";
            pinctrl-names = "default";
            pinctrl-0 = <NON_CONFLICTING_PINCTRL_PHANDLE>;
            snrclk-idx = <0x01>;
        };
    };
};
EOF
# Compile: dtc -I dts -O dtb -o /boot/hobot/overlays/mclk.dtbo /tmp/mclk_overlay.dts
# Enable: Add dtoverlay=mclk to /boot/config.txt
```

This requires finding the correct phandle values from the decompiled DTB. The key discovery needed is whether the S100 SoC has alternative camera clock output pins that don't conflict with Ethernet.

---

## Solution Path 4: Modify SC230AI Sensor Config to Skip SoC MCLK

If the Camera Expansion Board IS already providing 24 MHz via its oscillator (with SW2200 set to MCLK), the sensor might already have its clock, but the MIPI host driver may be failing the HS reception check too early or the sensor start sequence expects SoC-side MCLK acknowledgment.

### Steps

```bash
# STEP 1: Check if sensor config can be modified to set mclk=0
# This tells the framework "don't try to configure SoC MCLK, sensor has its own"
cd /app/multimedia_samples/vp_sensors/sc230ai/

# STEP 2: Back up the original config
sudo cp linear_1920x1080_raw10_30fps_1lane.c linear_1920x1080_raw10_30fps_1lane.c.bak

# STEP 3: Check if get_vin_data uses compiled-in configs or reads from .c files
# If compiled in, we need to modify the binary or use the tuning tool JSON configs instead

# STEP 4: Try using the tuning tool configs which have a complete dual-camera setup
ls /app/tuning_tool/cfg/matrix/tuning_sc230ai_dual_cim_isp_1080p/
cat /app/tuning_tool/cfg/matrix/tuning_sc230ai_dual_cim_isp_1080p/hb_j6dev.json
cat /app/tuning_tool/cfg/matrix/tuning_sc230ai_dual_cim_isp_1080p/mipi.json

# STEP 5: Check if the tuning tool has a different MCLK setting
cat /app/tuning_tool/cfg/matrix/tuning_sc230ai_dual_cim_isp_1080p/vpm_config.json | python3 -m json.tool | grep -i mclk

# STEP 6: If the tuning tool has its own pipeline launcher:
ls /app/tuning_tool/
# Try running the tuning tool pipeline directly
```

---

## Solution Path 5: Use ROS2 TogetheROS.Bot Stereo Pipeline

The ROS2 `hobot_stereonet` package may handle the camera initialization differently from the low-level C samples and `libsrcampy`. Specifically, it may:
- Use a different camera initialization path that properly configures MCLK
- Include SC230AI in its sensor detection list (unlike `libhbspdev.so`)
- Handle the stereo camera as a single logical unit rather than two independent sensors

### Steps

```bash
# STEP 1: Ensure TogetheROS.Bot is installed and updated
sudo apt update
sudo apt upgrade -y

# Remove old stereonet if present
sudo apt-get remove -y tros-humble-stereonet-model 2>/dev/null
sudo dpkg --remove --force-all tros-humble-stereonet-model 2>/dev/null

# Install fresh
sudo apt install -y tros-humble-hobot-stereonet
sudo apt install -y tros-humble-mipi-cam
sudo apt install -y tros-humble-hobot-stereo-mipi-cam 2>/dev/null

sudo reboot

# STEP 2: After reboot, try the official RDK S100 stereo depth command
source /opt/tros/humble/setup.bash

ros2 launch hobot_stereonet stereonet_model_web_v2.1.launch.py \
    mipi_image_width:=640 \
    mipi_image_height:=352 \
    mipi_lpwm_enable:=True \
    mipi_image_framerate:=30.0 \
    need_rectify:=False \
    height_min:=-10.0 \
    height_max:=10.0 \
    pc_max_depth:=5.0 \
    uncertainty_th:=0.1

# View at http://<RDK_IP>:8000

# STEP 3: If the above fails, try the stereo MIPI camera node alone
source /opt/tros/humble/setup.bash
ros2 launch hobot_stereo_mipi_cam stereo_mipi_cam.launch.py

# STEP 4: If that also fails, try single MIPI cam with explicit sensor type
source /opt/tros/humble/setup.bash
ros2 launch mipi_cam mipi_cam.launch.py mipi_video_device:=sc230ai
```

### Important version note

The stereo algorithm has platform-specific versions. For RDK S100, use only the **v2.1** launch files:
- `stereonet_model_web_v2.1.launch.py` — S100 only
- `stereonet_model_web_visual_v2.1.launch.py` — S100 only
- Do NOT use v2.0, v2.2, v2.3, or v2.4 — these are for RDK X5 only

Source: https://developer.d-robotics.cc/rdk_doc/en/Robot_development/boxs/spatial/hobot_stereonet/

---

## Solution Path 6: Contact D-Robotics for Official DTB/Package Fix

If all software paths fail, the MCLK pin conflict may require an official fix from D-Robotics.

### What to include in the support request

Post on the D-Robotics English developer forum (https://developer.d-robotics.cc/en) with:

1. **Board:** RDK S100 V1P0, RDK OS 4.0.4-Beta
2. **Camera:** RDK Stereo Camera Module (SC230AI, originally from RDK X5 kit)
3. **Expansion Board:** Camera Expansion Board with SW2200=LPWM, SW2201=3.3V
4. **Problem:** `get_vin_data -s 6` detects SC230AI correctly, sensor initializes, but MIPI HS reception fails with error 0x10000
5. **Root Cause:** Stock DTB has no MCLK pinctrl for mipi_host0/1. The only available `cam_clkout_func` uses pin `cam_lpwm1_dout3` which is already claimed by the Ethernet controller (`33100000.ethernet`)
6. **Kernel log excerpt:**
   ```
   [RX0]: mclk 24 ignore
   [RX0]: hs reception check error 0x10000
   ```
7. **Questions:** (a) Should SW2200 be MCLK for SC230AI on S100? (b) Is there a non-conflicting MCLK pin? (c) Are the v1-2/v1-21 DTBs meant for the Camera Expansion Board?

Also file at: https://github.com/D-Robotics/x5-hobot-camera/issues

---

## Recommended Execution Order

Try each solution in this order — stop as soon as one works:

```
┌─────────────────────────────────────────────────────────────────┐
│  PRIORITY 1: Switch SW2200 to MCLK (2 minutes, zero risk)      │
│  → Power off → flip both SW2200 switches to MCLK → power on    │
│  → sudo ./get_vin_data -s 6                                    │
│  → Check: dmesg | grep "hs reception"                          │
├─────────────────────────────────────────────────────────────────┤
│  PRIORITY 2: Diff and try alternate DTBs (15 minutes)           │
│  → dtc -I dtb -O dts both DTBs → diff → look for MCLK changes │
│  → If promising, switch DTB and test                            │
├─────────────────────────────────────────────────────────────────┤
│  PRIORITY 3: ROS2 stereonet v2.1 pipeline (10 minutes)         │
│  → apt install packages → ros2 launch stereonet v2.1           │
│  → This may use a different init path that handles MCLK         │
├─────────────────────────────────────────────────────────────────┤
│  PRIORITY 4: Inspect tuning tool configs (10 minutes)           │
│  → Check if tuning tool pipeline handles MCLK differently      │
│  → Try running with mclk=0 if config is editable               │
├─────────────────────────────────────────────────────────────────┤
│  PRIORITY 5: DTB overlay with non-conflicting pin (30 minutes)  │
│  → Requires finding alternative cam_clkout pin in DTB           │
│  → Only if decompiled DTB reveals one                           │
├─────────────────────────────────────────────────────────────────┤
│  PRIORITY 6: Post to D-Robotics forum (immediate, async)        │
│  → Do this in parallel with other attempts                      │
│  → Include full kernel log and pin conflict details             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference — Commands for Each Test

```bash
# Test with C sample (correct SC230AI detection)
cd /app/multimedia_samples/sample_vin/get_vin_data
sudo ./get_vin_data -s 6

# Check kernel log for MCLK and MIPI status
dmesg | tail -50
dmesg | grep -E "mclk|hs reception|pin.*already|sensor|MIPI"

# Check MIPI host status
cat /sys/class/vps/mipi_host0/status/cfg

# Verify I2C sensor presence
sudo i2cdetect -r -y 1
sudo i2cdetect -r -y 2

# Read SC230AI chip ID (should return 0xcb, 0x34)
sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x07 r1
sudo i2ctransfer -f -y 1 w2@0x30 0x31 0x08 r1

# ROS2 stereo depth (S100 only — v2.1)
source /opt/tros/humble/setup.bash
ros2 launch hobot_stereonet stereonet_model_web_v2.1.launch.py \
    mipi_image_width:=640 mipi_image_height:=352 \
    mipi_lpwm_enable:=True mipi_image_framerate:=30.0 \
    need_rectify:=False height_min:=-10.0 height_max:=10.0 \
    pc_max_depth:=5.0 uncertainty_th:=0.1

# Decompile DTB for inspection
dtc -I dtb -O dts -o /tmp/current.dts /boot/hobot/rdk-s100-v1p0.dtb
grep -A10 "mipi_host@0x37420000" /tmp/current.dts
```

---

## Why This Camera (RDK X5 Stereo) Is Causing Issues on S100

The RDK Stereo Camera Module (SC230AI) was designed for the RDK X5. On the X5:
- The SoC has proper MCLK output pins that do not conflict with Ethernet
- The X5 DTB includes `clocks`, `clock-names`, `pinctrl-names`, `pinctrl-0`, and `snrclk-idx` on its MIPI host nodes
- `libhbspdev.so` on X5 includes SC230AI in its sensor detection list
- The camera works plug-and-play

On the RDK S100:
- The SoC's `cam_clkout` pin collides with the Ethernet controller — a design constraint of the S100 board layout
- The stock DTB intentionally omits MCLK config for mipi_host0/1 (probably because the expansion board oscillator was meant to be the MCLK source)
- `libhbspdev.so` was compiled without SC230AI in its sensor list (only OVX8B wildcard matches)
- The Camera Expansion Board's onboard 24 MHz oscillator (accessed via SW2200=MCLK) is likely the intended MCLK source for MIPI cameras on S100

This is why **switching SW2200 to MCLK is the highest-priority fix** — it is the designed hardware solution for exactly this problem.