# Solving the RDK S100 stereo camera misidentification crisis

**Your camera is almost certainly not an OVX8B sensor — it's being misidentified.** The official D-Robotics "RDK Stereo Camera Module" uses either the **SmartSens SC230AI** (color, rolling shutter, 70mm baseline) or the **SmartSens SC132GS** (mono, global shutter, 80mm baseline), depending on which version you purchased. Both sensors share the default I2C 7-bit address **0x30**, and a stereo pair uses 0x30/0x32 — exactly what your `i2cdetect` output shows. The RDK S100's `hobot-camera` auto-detection is incorrectly matching your sensor to the "ovx8bstd" profile, causing the pipeline to load nonexistent OVX8B ISP calibration libraries and fail with error -65666. The fix is to **override auto-detection** and explicitly specify the correct sensor type.

## Two stereo modules exist — only one is designed for S100

D-Robotics sells two distinct stereo camera modules under confusingly similar names. Getting this right is essential because it determines your software configuration.

The **"RDK Stereo Camera Module"** (no suffix, Waveshare SKU 29052, DFRobot FIT1026) uses dual **SC230AI** sensors — 2MP color, 1920×1080, rolling shutter, 178° diagonal FOV, 70mm baseline. Multiple retailers (DFRobot, Amazon, Waveshare) explicitly state this module is "**only compatible with RDK X5**." However, the RDK S100 Camera Expansion Board documentation does list "SC230AI Stereo Camera (V3)" as a supported configuration, suggesting hardware-level compatibility exists via the expansion board.

The **"RDK Stereo Camera Module GS130W"** (Waveshare SKU 33206) uses dual **SC132GS** sensors — 1.3MP monochrome, 1280×1080, global shutter up to 120fps, 157° diagonal FOV, 80mm baseline, semi-enclosed metal housing. This module is explicitly marketed as "**fully compatible with RDK X5 and RDK S100/S100P**." D-Robotics release notes confirm "added driver support for the Yuguang SC132GS stereo camera module."

To identify which module you have: if your images are **color** and the baseline is ~70mm with a plastic/open PCB housing, you have the SC230AI version. If images are **grayscale**, the baseline is ~80mm, and it has a **metal enclosure**, you have the GS130W (SC132GS). The back of the SC230AI module PCB should show "CDPxxx-V3" silkscreen — confirm this matches the V3 revision.

## Why auto-detection fails at 0x30

The root cause is an **I2C address collision in the auto-detection algorithm**. Both SC230AI and SC132GS default to 7-bit I2C address **0x30** (8-bit write: 0x60). OmniVision automotive sensors also commonly use 0x30 as their base SCCB address. The `hobot-camera` auto-detection probes address 0x30, and the OVX8B check apparently fires before the SC230AI/SC132GS check in the detection sequence — or the chip ID register read returns a pattern the system interprets as OVX8B.

The system then attempts to load the OVX8B ISP calibration pipeline. Your package `hobot-camera 4.0.4` ships `libovx8bstd.so` (the sensor driver stub) but **not the corresponding ISP tuning/calibration data files** that `hbn_camera_create()` requires. This produces error **-65666 (HBN_STATUS_CAM_MOD_CHECK_ERROR)** — a calibration module check failure, not a hardware problem.

The address 0x32 on I2C bus 2 is the second sensor in the stereo pair with its address pin configured to an alternate value, which is standard for dual-sensor modules.

## Step-by-step fix: override sensor detection and launch correctly

First, update all packages to ensure you have the latest camera drivers and stereo algorithm support:

```bash
sudo apt update && sudo apt upgrade
sudo reboot
```

After rebooting, verify installed camera packages and check for SC230AI/SC132GS support:

```bash
apt list --installed | grep hobot-camera
dpkg -L hobot-camera | grep -iE "sc230|sc132"
apt-cache search hobot | grep -i camera
```

### DIP switch configuration (Camera Expansion Board)

For both SC230AI and SC132GS stereo cameras, the DIP switch settings are identical:

- **SW2200** (Function Switch): Set **both** switches (1 and 2) to **LPWM** position — this provides the low-frequency PWM synchronization signal needed for stereo frame sync
- **SW2201** (Voltage Switch): Set **both** switches (1 and 2) to **3.3V** position — both SmartSens sensors operate at 3.3V logic levels

**Critical warning:** Never change DIP switches or connect/disconnect cameras while the board is powered on. Voltage mismatch on SW2201 can permanently damage the sensor or expansion board.

### ROS2 camera launch with explicit sensor override

The primary camera interface on RDK S100 is through ROS2 (TogetheROS.Bot). Install the required packages if not already present:

```bash
sudo apt install -y tros-humble-mipi-cam tros-humble-hobot-stereonet
```

Launch the camera with **explicit sensor type override** to bypass the broken auto-detection:

```bash
source /opt/tros/humble/setup.bash

# Single camera test (override auto-detection):
ros2 launch mipi_cam mipi_cam.launch.py mipi_video_device:=sc230ai

# Dual/stereo camera mode:
ros2 launch mipi_cam mipi_cam_dual_channel.launch.py

# Or manual dual camera launch with topic separation:
ros2 launch mipi_cam mipi_cam.launch.py mipi_video_device:=sc230ai
# In a second terminal:
ros2 run mipi_cam mipi_cam --ros-args -p video_device:=sc230ai --remap /image_raw:=/image_raw_alias
```

If you have the GS130W (SC132GS) module instead, substitute `sc132gs` for `sc230ai` in the commands above.

### Full stereo depth pipeline on S100

The `hobot_stereonet` package provides the complete stereo depth estimation pipeline. **Version 2.1 is the one that supports RDK S100** (internally called X100) — other versions (2.0, 2.2, 2.3) only support RDK X5:

```bash
source /opt/tros/humble/setup.bash

ros2 launch hobot_stereonet stereonet_model_web_v2.1.launch.py \
  mipi_image_width:=640 mipi_image_height:=352 \
  mipi_lpwm_enable:=True mipi_image_framerate:=30.0 \
  need_rectify:=False \
  height_min:=-10.0 height_max:=10.0 pc_max_depth:=5.0 \
  uncertainty_th:=0.1
```

View the depth map at `http://<RDK_IP>:8000` in a web browser. The node publishes stereo topics including `/camera_left_info`, `/camera_right_info`, `/image_left_raw`, `/image_right_raw`, and depth/disparity maps.

## If the ROS2 override still fails

If explicitly setting the sensor type doesn't resolve the `hbn_camera_create()` error, the underlying `hobot-camera` library may lack the ISP calibration data for your sensor on S100. Several diagnostic steps can help isolate the issue:

```bash
# Check what sensor libraries exist:
find / -name "libsc230*" -o -name "libsc132*" -o -name "libovx8b*" 2>/dev/null

# Check for ISP calibration/tuning files:
find / -name "*tuning*" -path "*/camera/*" 2>/dev/null
find / -name "*calib*" -path "*/camera/*" 2>/dev/null
ls -la /etc/hobot/ 2>/dev/null

# Verify the MIPI camera is actually accessible:
i2cdetect -r -y 1
i2cdetect -r -y 2
```

The **latest publicly documented SDK is V4.0.2** (RDKS100_LNX_SDK_V4.0.2). Your version 4.0.4-Beta isn't in the public release notes, suggesting it may be a weekly OTA update build or a pre-release. No V4.0.5 release was found publicly. The V4.0.2 release notes explicitly state that the **commercial SDK** "offers more comprehensive feature support" and "exclusive customization" — access requires filling out a questionnaire and signing an NDA.

This is significant because **ISP calibration libraries for specific sensors may only ship in the commercial SDK**. The `hbn_camera_create()` C API and detailed HBN pipeline documentation are part of the enterprise OpenExplorer SDK, which is NDA-restricted. If the ROS2-level override doesn't work, the missing calibration files are very likely gated behind commercial access.

## Recommended escalation path

If the package update and sensor override don't resolve the issue, these are the most productive next steps in priority order:

- **Post on the D-Robotics English forum** at `https://forum-en.d-robotics.cc/` with your exact error output, `i2cdetect` results, and package versions — as of this research, zero posts exist about this specific error, so you'd be the first to report it
- **Contact D-Robotics FAE** (Field Application Engineer) through the commercial SDK questionnaire at the link in the V4.0.2 release notes — they can provide the correct ISP calibration package or confirm whether your camera version requires commercial SDK support
- **Verify your camera is the GS130W (SC132GS)** rather than the SC230AI module — the GS130W has explicit S100 compatibility and its driver was recently added to the SDK, so it may have better out-of-box support
- **Try the dedicated stereo MIPI camera package**: `ros2 launch hobot_stereo_mipi_cam stereo_mipi_cam.launch.py` — this package handles stereo-specific initialization and may bypass the broken auto-detection path entirely

## Conclusion

The core problem is a **sensor misidentification bug**, not missing hardware support. Your SC230AI or SC132GS sensor at I2C address 0x30 is being incorrectly classified as OVX8B by the auto-detection system, which then fails when it can't find OVX8B ISP calibration data. The DIP switches should be set to LPWM + 3.3V on both channels. The software fix is to explicitly specify the sensor type via the `mipi_video_device` ROS2 launch parameter and use the V2.1 stereonet launch file that supports S100. If this doesn't work, the ISP calibration libraries for your sensor on S100 may require either a newer package update or commercial SDK access — contacting D-Robotics FAE support directly is the fastest path to resolution. Critically, confirm whether your module is the SC230AI version (color, 70mm, plastic) or the GS130W SC132GS version (mono, 80mm, metal) — the GS130W has better documented S100 support and is the camera D-Robotics officially recommends for the S100 platform.