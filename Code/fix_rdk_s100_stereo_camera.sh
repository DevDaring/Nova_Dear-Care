#!/bin/bash
###############################################################################
#  FIX: D-Robotics RDK Stereo Camera Module (SC230AI) on RDK S100
#
#  Problem : Camera auto-detected as "ovx8bstd" → missing ISP calibration
#            libraries → hbn_camera_create() fails with error -65666
#  Root cause: The SC230AI stereo camera (designed for RDK X5) is being
#              misidentified as OVX8B on the RDK S100 platform
#  Solution : Update packages, install correct ROS2 stereo nodes, and
#             launch with the proper stereo pipeline for S100
#
#  Hardware : RDK S100 V1P0 + Camera Expansion Board + RDK Stereo Camera
#  Date     : 2026-03-08
#  Author   : Generated for Pocket ASHA — AI for Bharat Hackathon
###############################################################################
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_step()  { echo -e "\n${GREEN}[STEP $1]${NC} $2"; }
log_warn()  { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=================================================================="
echo "  RDK S100 + SC230AI Stereo Camera — Fix Script"
echo "=================================================================="
echo ""
echo "This script will:"
echo "  1. Verify hardware connections"
echo "  2. Check and fix DIP switch guidance"
echo "  3. Update all system packages"
echo "  4. Install correct stereo camera ROS2 packages"
echo "  5. Remove broken OVX8B stub (if present)"
echo "  6. Test camera with the correct RDK S100 stereo pipeline"
echo ""

###############################################################################
# STEP 0: PRE-FLIGHT CHECKS
###############################################################################
log_step "0" "Pre-flight checks"

# Check if running on RDK S100
if [ -f /etc/version ]; then
    RDKOS_VER=$(cat /etc/version 2>/dev/null || echo "unknown")
    log_info "RDK OS version: $RDKOS_VER"
fi

if command -v rdkos_info &>/dev/null; then
    rdkos_info 2>/dev/null || true
fi

ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    log_error "This script must run on the RDK S100 (aarch64). Current arch: $ARCH"
    exit 1
fi

log_info "Architecture: $ARCH ✓"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    log_warn "Not running as root. Will use sudo for privileged commands."
    SUDO="sudo"
else
    SUDO=""
fi

###############################################################################
# STEP 1: VERIFY HARDWARE — I2C SENSOR DETECTION
###############################################################################
log_step "1" "Verifying hardware connections (I2C sensor detection)"

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│  DIP SWITCH SETTINGS — Camera Expansion Board                  │"
echo "│                                                                 │"
echo "│  SW2200 (Function Switch): Both → LPWM position               │"
echo "│  SW2201 (Voltage Switch):  Both → 3.3V position               │"
echo "│                                                                 │"
echo "│  IMPORTANT: Power OFF the board before changing DIP switches!  │"
echo "└─────────────────────────────────────────────────────────────────┘"
echo ""

# Scan I2C buses for camera sensors
log_info "Scanning I2C bus 1 (MIPI RX PHY 0 — left sensor)..."
if command -v i2cdetect &>/dev/null; then
    $SUDO i2cdetect -r -y 1 2>/dev/null || log_warn "i2cdetect failed on bus 1"
    echo ""

    log_info "Scanning I2C bus 2 (MIPI RX PHY 1 — right sensor)..."
    $SUDO i2cdetect -r -y 2 2>/dev/null || log_warn "i2cdetect failed on bus 2"
    echo ""

    # Check for expected addresses
    BUS1_30=$($SUDO i2cdetect -r -y 1 2>/dev/null | grep -c "30" || true)
    BUS2_32=$($SUDO i2cdetect -r -y 2 2>/dev/null | grep -c "32" || true)

    if [ "$BUS1_30" -gt 0 ] && [ "$BUS2_32" -gt 0 ]; then
        log_info "Both stereo sensors detected: Bus1:0x30 ✓  Bus2:0x32 ✓"
    else
        log_warn "One or both sensors not detected. Check cable connections."
        log_warn "Expected: Bus 1 → 0x30 (left), Bus 2 → 0x32 (right)"
    fi
else
    log_warn "i2cdetect not found. Installing i2c-tools..."
    $SUDO apt install -y i2c-tools
    $SUDO i2cdetect -r -y 1
    $SUDO i2cdetect -r -y 2
fi

###############################################################################
# STEP 2: CHECK CURRENT SENSOR DRIVER STATE
###############################################################################
log_step "2" "Checking current sensor driver state"

log_info "Listing installed camera sensor drivers..."
ls -la /usr/hobot/lib/sensor/lib*.so* 2>/dev/null || log_warn "No sensor drivers found at /usr/hobot/lib/sensor/"

echo ""
log_info "Checking for SC230AI driver..."
SC230_DRIVER=$(find / -name "libsc230*" 2>/dev/null | head -5)
if [ -n "$SC230_DRIVER" ]; then
    log_info "SC230AI driver found: $SC230_DRIVER ✓"
else
    log_warn "SC230AI driver NOT found. Will be installed with package update."
fi

echo ""
log_info "Checking for OVX8B stub (the problematic file)..."
OVX8B_STUB=$(find /usr/hobot/lib/sensor/ -name "lib_CL_OX8GB*" -o -name "lib_CW_OX8GB*" 2>/dev/null | head -5)
if [ -n "$OVX8B_STUB" ]; then
    log_warn "Found OVX8B calibration stub(s) — these will be removed:"
    echo "$OVX8B_STUB"
fi

###############################################################################
# STEP 3: UPDATE SYSTEM PACKAGES
###############################################################################
log_step "3" "Updating system packages (this may take several minutes)"

log_info "Running apt update..."
$SUDO apt update 2>&1 || {
    log_warn "apt update failed. Trying to fix sources..."
    # Try alternate source if default fails
    log_info "Check network connectivity and apt sources."
}

log_info "Upgrading all packages..."
$SUDO apt upgrade -y 2>&1 || log_warn "apt upgrade had issues, continuing..."

log_info "Upgrading hobot-camera specifically..."
$SUDO apt install -y --reinstall hobot-camera 2>/dev/null || log_warn "hobot-camera reinstall skipped"

###############################################################################
# STEP 4: REMOVE OVX8B STUBS (IF ANY WERE MANUALLY CREATED)
###############################################################################
log_step "4" "Removing any manually created OVX8B calibration stubs"

# These are the stubs from previous troubleshooting attempts
STUBS=(
    "/usr/hobot/lib/sensor/lib_CL_OX8GB_L121_067_L.so"
    "/usr/hobot/lib/sensor/lib_CW_OX8GB_A120_065_L.so"
    "/usr/hobot/lib/sensor/lib_CW_OX8GB_A030_017_L.so"
    "/usr/hobot/lib/sensor/lib_CO_OX8GB_A121_055_L.so"
    "/usr/hobot/lib/sensor/lib_CH_OX8GB_A120_065_L.so"
    "/usr/hobot/lib/sensor/lib_CH_OX8GB_A030_017_L.so"
    "/usr/hobot/lib/sensor/lib_CL_OX8GB_L030_017_L.so"
)

for stub in "${STUBS[@]}"; do
    if [ -f "$stub" ]; then
        SIZE=$(stat -c%s "$stub" 2>/dev/null || echo "0")
        # Only remove if it's a small stub (<50KB), not a real calibration file
        if [ "$SIZE" -lt 51200 ]; then
            log_info "Removing stub: $stub (${SIZE} bytes)"
            $SUDO rm -f "$stub"
        else
            log_warn "Keeping $stub (${SIZE} bytes — may be legitimate)"
        fi
    fi
done

###############################################################################
# STEP 5: INSTALL TOGETHEROS.BOT (tros) STEREO CAMERA PACKAGES
###############################################################################
log_step "5" "Installing TogetheROS.Bot stereo camera packages for RDK S100"

# Remove old/broken stereonet model package if present
log_info "Removing old stereonet model package (if present)..."
$SUDO apt-get remove -y tros-humble-stereonet-model 2>/dev/null || true
$SUDO dpkg --remove --force-all tros-humble-stereonet-model 2>/dev/null || true

# Install the correct packages
log_info "Installing tros-humble-hobot-stereonet (stereo depth algorithm)..."
$SUDO apt install -y tros-humble-hobot-stereonet 2>&1 || {
    log_warn "tros-humble-hobot-stereonet install failed. Trying alternatives..."
    $SUDO apt install -y tros-humble-hobot-stereonet-utils 2>/dev/null || true
}

log_info "Installing tros-humble-mipi-cam (MIPI camera ROS2 node)..."
$SUDO apt install -y tros-humble-mipi-cam 2>&1 || log_warn "mipi-cam already installed or unavailable"

log_info "Installing tros-humble-hobot-stereo-mipi-cam (stereo MIPI camera node)..."
$SUDO apt install -y tros-humble-hobot-stereo-mipi-cam 2>&1 || log_warn "stereo-mipi-cam unavailable — will try alternative approach"

log_info "Installing additional dependencies..."
$SUDO apt install -y tros-humble-hobot-codec 2>/dev/null || true
$SUDO apt install -y tros-humble-websocket 2>/dev/null || true

###############################################################################
# STEP 6: VERIFY INSTALLATIONS
###############################################################################
log_step "6" "Verifying package installations"

echo ""
log_info "Installed hobot packages:"
dpkg -l | grep hobot | awk '{printf "  %-45s %s\n", $2, $3}' || true

echo ""
log_info "Installed tros packages:"
dpkg -l | grep tros | awk '{printf "  %-45s %s\n", $2, $3}' || true

echo ""
log_info "Checking for stereonet launch files..."
find /opt/tros/ -name "*stereonet*v2.1*" -type f 2>/dev/null || \
    log_warn "No v2.1 stereonet launch files found"

echo ""
log_info "Checking for stereo MIPI cam launch files..."
find /opt/tros/ -name "*stereo_mipi_cam*" -type f 2>/dev/null || \
    log_warn "No stereo MIPI cam launch files found"

###############################################################################
# STEP 7: CREATE TEST SCRIPTS
###############################################################################
log_step "7" "Creating test scripts in /home/sunrise/ (or /root/)"

WORKDIR="/home/sunrise"
[ -d "$WORKDIR" ] || WORKDIR="/root"
[ -d "$WORKDIR" ] || WORKDIR="$HOME"

# --- Test Script A: Stereo Depth Pipeline (OFFICIAL RDK S100 command) ---
cat > "$WORKDIR/test_stereo_depth_s100.sh" << 'SCRIPT_A'
#!/bin/bash
###############################################################################
#  TEST A: RDK S100 Stereo Depth Pipeline (Official command from D-Robotics)
#  Source: https://developer.d-robotics.cc/rdk_doc/en/Robot_development/boxs/spatial/hobot_stereonet/
###############################################################################
echo "Starting RDK S100 Stereo Depth Pipeline (v2.1)..."
echo "View output at: http://<RDK_IP>:8000"
echo ""

source /opt/tros/humble/setup.bash

# RDK S100 specific launch — uses v2.1 which is the S100-compatible version
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
SCRIPT_A
chmod +x "$WORKDIR/test_stereo_depth_s100.sh"

# --- Test Script B: Stereo MIPI Camera Node (lower-level test) ---
cat > "$WORKDIR/test_stereo_mipi_cam.sh" << 'SCRIPT_B'
#!/bin/bash
###############################################################################
#  TEST B: Stereo MIPI Camera Node (lower-level test without depth algorithm)
#  This tests if the stereo camera itself can initialize and stream
###############################################################################
echo "Starting Stereo MIPI Camera node..."
echo ""

source /opt/tros/humble/setup.bash

ros2 launch hobot_stereo_mipi_cam stereo_mipi_cam.launch.py
SCRIPT_B
chmod +x "$WORKDIR/test_stereo_mipi_cam.sh"

# --- Test Script C: Single MIPI Camera Test (fallback) ---
cat > "$WORKDIR/test_single_mipi_cam.sh" << 'SCRIPT_C'
#!/bin/bash
###############################################################################
#  TEST C: Single MIPI Camera Test (tests one sensor at a time)
#  Use this if stereo tests fail — it isolates the problem
###############################################################################
echo "Starting single MIPI camera test..."
echo "View output at: http://<RDK_IP>:8000"
echo ""

source /opt/tros/humble/setup.bash

# Try with explicit sc230ai sensor type to bypass auto-detection
ros2 launch mipi_cam mipi_cam.launch.py \
    mipi_video_device:=sc230ai
SCRIPT_C
chmod +x "$WORKDIR/test_single_mipi_cam.sh"

# --- Test Script D: Python direct camera test (lowest level) ---
cat > "$WORKDIR/test_python_camera.py" << 'SCRIPT_D'
#!/usr/bin/env python3
"""
TEST D: Direct Python camera test using hobot_vio libsrcampy
Tests if the camera can open at the lowest API level.

If this fails with -65666, the ISP calibration issue is at the
system library level and requires a package update from D-Robotics.
"""
import sys

try:
    from hobot_vio import libsrcampy
except ImportError:
    print("ERROR: hobot_vio not installed. Run: sudo apt install hobot-spdev")
    sys.exit(1)

print("=" * 60)
print("  Direct Camera Test — hobot_vio libsrcampy")
print("=" * 60)

# Test camera 0 (left sensor, I2C bus 1, addr 0x30)
print("\n[1] Testing Camera 0 (left sensor)...")
cam0 = libsrcampy.Camera()
ret = cam0.open_cam(0, -1, 30, 1920, 1080)
if ret == 0:
    print("    ✓ Camera 0 opened successfully!")
    img = cam0.get_img(2, 1920, 1080)
    if img is not None:
        print(f"    ✓ Got image: {len(img)} bytes")
    else:
        print("    ✗ get_img returned None")
    cam0.close_cam()
else:
    print(f"    ✗ Camera 0 open failed with error: {ret}")
    print("    → If error is -65666: ISP calibration still missing")
    print("    → Try the ROS2 stereo pipeline instead (test_stereo_depth_s100.sh)")

# Test camera 1 (right sensor, I2C bus 2, addr 0x32)
print("\n[2] Testing Camera 1 (right sensor)...")
cam1 = libsrcampy.Camera()
ret = cam1.open_cam(1, -1, 30, 1920, 1080)
if ret == 0:
    print("    ✓ Camera 1 opened successfully!")
    cam1.close_cam()
else:
    print(f"    ✗ Camera 1 open failed with error: {ret}")

print("\n" + "=" * 60)
print("Test complete.")
SCRIPT_D
chmod +x "$WORKDIR/test_python_camera.py"

log_info "Test scripts created in: $WORKDIR/"
echo "  - test_stereo_depth_s100.sh   (PRIMARY — full stereo depth pipeline)"
echo "  - test_stereo_mipi_cam.sh     (stereo camera node only)"
echo "  - test_single_mipi_cam.sh     (single camera with sc230ai override)"
echo "  - test_python_camera.py       (lowest-level Python API test)"

###############################################################################
# STEP 8: RUN DIAGNOSTIC SUMMARY
###############################################################################
log_step "8" "Diagnostic summary"

echo ""
echo "=================================================================="
echo "  DIAGNOSTIC SUMMARY"
echo "=================================================================="
echo ""

# Check kernel
echo "Kernel: $(uname -r)"
echo "Board:  $(cat /proc/device-tree/model 2>/dev/null || echo 'unknown')"
echo ""

# Check MIPI host status
echo "MIPI Host Status:"
for i in 0 1 4; do
    CFG=$(cat /sys/class/vps/mipi_host${i}/status/cfg 2>/dev/null || echo "N/A")
    echo "  mipi_host${i}: $CFG"
done
echo ""

# Check VIN devices
echo "VIN devices:"
ls /dev/vin*_src 2>/dev/null | head -6 || echo "  No VIN devices found"
echo ""

###############################################################################
# FINAL INSTRUCTIONS
###############################################################################
echo ""
echo "=================================================================="
echo "  WHAT TO DO NEXT"
echo "=================================================================="
echo ""
echo "  1. REBOOT the board first:"
echo "     sudo reboot"
echo ""
echo "  2. After reboot, try the tests IN THIS ORDER:"
echo ""
echo "     a) PRIMARY — Full Stereo Depth on S100:"
echo "        cd $WORKDIR && ./test_stereo_depth_s100.sh"
echo "        → Open http://<RDK_IP>:8000 in browser to see depth map"
echo ""
echo "     b) If (a) fails — Try stereo camera node only:"
echo "        cd $WORKDIR && ./test_stereo_mipi_cam.sh"
echo ""
echo "     c) If (b) fails — Try single camera with sensor override:"
echo "        cd $WORKDIR && ./test_single_mipi_cam.sh"
echo ""
echo "     d) If all fail — Run Python diagnostic:"
echo "        cd $WORKDIR && python3 test_python_camera.py"
echo ""
echo "  3. If Python test still gives -65666 error:"
echo "     → The hobot-camera package needs an update from D-Robotics"
echo "     → Post on: https://developer.d-robotics.cc/en (English forum)"
echo "     → Include your rdkos_info output and this error"
echo ""
echo "  4. HARDWARE CHECKLIST:"
echo "     □ Camera Expansion Board LED D2000 is GREEN"
echo "     □ SW2200 = LPWM (both switches)"
echo "     □ SW2201 = 3.3V (both switches)"
echo "     □ FPC cables: blue side up, fully seated, latches closed"
echo "     □ Board was powered OFF during cable connections"
echo ""
echo "=================================================================="
echo "  Script complete. Reboot and run tests."
echo "=================================================================="
