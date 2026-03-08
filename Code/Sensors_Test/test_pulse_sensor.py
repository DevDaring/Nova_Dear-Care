#!/usr/bin/env python3
"""
test_pulse_sensor.py — MAX30102 Pulse Oximeter / Heart Rate Sensor Test

Tests the MAX30102 sensor connected to the RDK S100 via I2C:
  - Bus 5, Address 0x57 (pins: SDA→J24 Pin3, SCL→J24 Pin5, VIN→Pin1, GND→Pin6)

This script:
  1. Detects the sensor on I2C bus 5
  2. Verifies Part ID (0x15 = MAX30102) and Revision ID
  3. Configures the sensor for SpO2 mode (RED + IR LEDs)
  4. Reads live FIFO data for ~10 seconds
  5. Reports whether a pulse signal is detected

Usage:
    cd ~/Documents/AI_4_Bharat/Code
    sudo python3 Sensors_Test/test_pulse_sensor.py

    Or without sudo (if user is in i2c group):
    python3 Sensors_Test/test_pulse_sensor.py
"""

import sys
import time

# ==============================================================
# MAX30102 Register Map
# ==============================================================
I2C_BUS     = 5
I2C_ADDR    = 0x57

# Status registers
REG_INT_STATUS_1   = 0x00
REG_INT_STATUS_2   = 0x01
REG_INT_ENABLE_1   = 0x02
REG_INT_ENABLE_2   = 0x03

# FIFO registers
REG_FIFO_WR_PTR    = 0x04
REG_FIFO_OVF_CTR   = 0x05
REG_FIFO_RD_PTR    = 0x06
REG_FIFO_DATA      = 0x07

# Configuration registers
REG_FIFO_CONFIG    = 0x08
REG_MODE_CONFIG    = 0x09
REG_SPO2_CONFIG    = 0x0A
REG_LED1_PA        = 0x0C  # RED LED current
REG_LED2_PA        = 0x0D  # IR LED current
REG_MULTI_LED_1    = 0x11
REG_MULTI_LED_2    = 0x12

# Temperature registers
REG_TEMP_INT       = 0x1F
REG_TEMP_FRAC      = 0x20
REG_TEMP_CONFIG    = 0x21

# ID registers
REG_REVISION_ID    = 0xFE
REG_PART_ID        = 0xFF

# Expected values
EXPECTED_PART_ID   = 0x15  # MAX30102

# ==============================================================
# Helpers
# ==============================================================

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def print_result(label, passed, detail=""):
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {label}")
    if detail:
        print(f"         {detail}")


# ==============================================================
# Test Functions
# ==============================================================

def test_connection(bus):
    """Test 1: Check if MAX30102 responds on I2C."""
    print_header("Test 1: I2C Connection")
    try:
        bus.read_byte(I2C_ADDR)
        print_result("I2C device responds at 0x57 on bus 5", True)
        return True
    except OSError as e:
        print_result("I2C device responds at 0x57 on bus 5", False,
                     f"Error: {e}. Check wiring: SDA→Pin3, SCL→Pin5, VIN→Pin1(3.3V), GND→Pin6")
        return False


def test_part_id(bus):
    """Test 2: Verify Part ID = 0x15 (MAX30102)."""
    print_header("Test 2: Part ID Verification")
    part_id = bus.read_byte_data(I2C_ADDR, REG_PART_ID)
    rev_id = bus.read_byte_data(I2C_ADDR, REG_REVISION_ID)
    if part_id == EXPECTED_PART_ID:
        print_result(f"Part ID = 0x{part_id:02X} (MAX30102)", True,
                     f"Revision: 0x{rev_id:02X}")
        return True
    else:
        print_result(f"Part ID = 0x{part_id:02X}", False,
                     f"Expected 0x{EXPECTED_PART_ID:02X} (MAX30102). "
                     f"Got 0x{part_id:02X} — may be MAX30100 (0x11) or different sensor")
        return False


def test_temperature(bus):
    """Test 3: Read on-die temperature (verifies register read/write)."""
    print_header("Test 3: Temperature Register Read")
    try:
        # Trigger a temperature measurement
        bus.write_byte_data(I2C_ADDR, REG_TEMP_CONFIG, 0x01)
        time.sleep(0.1)

        temp_int = bus.read_byte_data(I2C_ADDR, REG_TEMP_INT)
        temp_frac = bus.read_byte_data(I2C_ADDR, REG_TEMP_FRAC)

        # temp_int is signed 8-bit
        if temp_int > 127:
            temp_int -= 256
        temp_c = temp_int + (temp_frac * 0.0625)

        if -10 < temp_c < 60:
            print_result(f"Die temperature: {temp_c:.1f} °C", True,
                         "Register read/write working correctly")
            return True
        else:
            print_result(f"Die temperature: {temp_c:.1f} °C (out of range)", False,
                         "Unexpected value — sensor may be malfunctioning")
            return False
    except Exception as e:
        print_result("Temperature read", False, f"Error: {e}")
        return False


def test_fifo_data(bus, duration_sec=10):
    """Test 4: Configure SpO2 mode and read live FIFO data."""
    print_header(f"Test 4: Live Pulse Data ({duration_sec}s)")
    print("  Configuring sensor for SpO2 mode (RED + IR LEDs)...")

    try:
        # Reset the sensor
        bus.write_byte_data(I2C_ADDR, REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)

        # Wait for reset to complete
        for _ in range(10):
            mode = bus.read_byte_data(I2C_ADDR, REG_MODE_CONFIG)
            if not (mode & 0x40):
                break
            time.sleep(0.05)

        # FIFO config: sample averaging = 4, FIFO rollover enabled
        bus.write_byte_data(I2C_ADDR, REG_FIFO_CONFIG, 0x4F)

        # SpO2 config: ADC range 4096nA, 100 samples/sec, 18-bit pulse width
        bus.write_byte_data(I2C_ADDR, REG_SPO2_CONFIG, 0x27)

        # LED currents: moderate brightness (6.4 mA)
        bus.write_byte_data(I2C_ADDR, REG_LED1_PA, 0x24)  # RED
        bus.write_byte_data(I2C_ADDR, REG_LED2_PA, 0x24)  # IR

        # Clear FIFO pointers
        bus.write_byte_data(I2C_ADDR, REG_FIFO_WR_PTR, 0x00)
        bus.write_byte_data(I2C_ADDR, REG_FIFO_OVF_CTR, 0x00)
        bus.write_byte_data(I2C_ADDR, REG_FIFO_RD_PTR, 0x00)

        # Enable SpO2 mode (RED + IR)
        bus.write_byte_data(I2C_ADDR, REG_MODE_CONFIG, 0x03)

        print(f"  Reading FIFO for {duration_sec} seconds...")
        print("  (Place your finger on the sensor for best results)\n")

        red_samples = []
        ir_samples = []
        start = time.time()

        while time.time() - start < duration_sec:
            # Check how many samples are available
            wr_ptr = bus.read_byte_data(I2C_ADDR, REG_FIFO_WR_PTR)
            rd_ptr = bus.read_byte_data(I2C_ADDR, REG_FIFO_RD_PTR)

            num_samples = (wr_ptr - rd_ptr) & 0x1F  # 5-bit pointers
            if num_samples == 0:
                time.sleep(0.01)
                continue

            for _ in range(num_samples):
                # Each sample = 6 bytes (3 for RED, 3 for IR) in 18-bit mode
                raw = bus.read_i2c_block_data(I2C_ADDR, REG_FIFO_DATA, 6)
                red = ((raw[0] & 0x03) << 16) | (raw[1] << 8) | raw[2]
                ir  = ((raw[3] & 0x03) << 16) | (raw[4] << 8) | raw[5]
                red_samples.append(red)
                ir_samples.append(ir)

            # Print progress every ~2 seconds
            elapsed = time.time() - start
            if len(red_samples) % 50 == 0 and red_samples:
                last_red = red_samples[-1]
                last_ir = ir_samples[-1]
                print(f"    [{elapsed:5.1f}s] Samples: {len(red_samples):4d} | "
                      f"RED: {last_red:6d} | IR: {last_ir:6d}")

        # Shut down sensor
        bus.write_byte_data(I2C_ADDR, REG_MODE_CONFIG, 0x80)  # Shutdown mode

        # Analyze results
        total = len(red_samples)
        print(f"\n  Total samples collected: {total}")

        if total == 0:
            print_result("FIFO data read", False,
                         "No samples collected — sensor may not be initialized properly")
            return False

        # Basic statistics
        red_min = min(red_samples)
        red_max = max(red_samples)
        red_avg = sum(red_samples) / total
        ir_min = min(ir_samples)
        ir_max = max(ir_samples)
        ir_avg = sum(ir_samples) / total
        red_range = red_max - red_min
        ir_range = ir_max - ir_min

        print(f"  RED LED — min: {red_min}, max: {red_max}, avg: {red_avg:.0f}, range: {red_range}")
        print(f"  IR  LED — min: {ir_min}, max: {ir_max}, avg: {ir_avg:.0f}, range: {ir_range}")

        # Check if LEDs are active (non-zero readings)
        if red_avg < 100 and ir_avg < 100:
            print_result("LED activity", False,
                         "Both RED and IR readings near zero — LEDs may not be firing. "
                         "Check sensor VIN is connected to 3.3V")
            return False

        print_result("LED activity", True,
                     f"RED avg={red_avg:.0f}, IR avg={ir_avg:.0f}")

        # Check for signal variation (indicates finger presence / pulse)
        has_signal = red_range > 500 or ir_range > 500
        if has_signal:
            print_result("Pulse signal detected", True,
                         f"Good signal variation (RED range={red_range}, IR range={ir_range}). "
                         "Finger detected on sensor!")

            # Simple peak detection for approximate heart rate
            if total >= 50:
                hr_estimate = _estimate_heart_rate(ir_samples)
                if hr_estimate:
                    print_result(f"Estimated heart rate: ~{hr_estimate} BPM", True,
                                 "(Rough estimate — use HeartRateMonitor for accurate readings)")
        else:
            print_result("Pulse signal", False,
                         f"Low signal variation (RED range={red_range}, IR range={ir_range}). "
                         "No finger detected — place finger firmly on sensor and re-run")

        return True

    except Exception as e:
        print_result("FIFO data read", False, f"Error: {e}")
        return False


def _estimate_heart_rate(ir_samples):
    """Very rough heart rate estimation via zero-crossing of AC component."""
    if len(ir_samples) < 50:
        return None

    # Remove DC component (simple moving average subtraction)
    window = min(25, len(ir_samples) // 4)
    if window < 3:
        return None

    avg = sum(ir_samples) / len(ir_samples)
    ac = [s - avg for s in ir_samples]

    # Count zero crossings (positive direction)
    crossings = 0
    for i in range(1, len(ac)):
        if ac[i - 1] < 0 and ac[i] >= 0:
            crossings += 1

    if crossings < 2:
        return None

    # Each positive zero crossing ≈ one heartbeat
    # Sample rate with averaging=4 at 100sps → ~25 effective sps
    sample_rate = 25  # approximate with sample_avg=4
    duration = len(ir_samples) / sample_rate
    bpm = int((crossings / duration) * 60)

    if 40 <= bpm <= 200:
        return bpm
    return None


# ==============================================================
# Main
# ==============================================================

def main():
    print("=" * 60)
    print("  MAX30102 Pulse Rate / SpO2 Sensor Test")
    print("  RDK S100 — I2C Bus 5, Address 0x57")
    print("  Connection: SDA→Pin3, SCL→Pin5, VIN→Pin1(3.3V), GND→Pin6")
    print("=" * 60)

    try:
        import smbus2
    except ImportError:
        print("\n  [FAIL] smbus2 not installed. Run: pip3 install smbus2")
        sys.exit(1)

    # Open I2C bus
    try:
        bus = smbus2.SMBus(I2C_BUS)
    except PermissionError:
        print(f"\n  [FAIL] Permission denied on /dev/i2c-{I2C_BUS}")
        print("         Run with: sudo python3 Sensors_Test/test_pulse_sensor.py")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n  [FAIL] /dev/i2c-{I2C_BUS} not found")
        print("         Enable I2C5 via: sudo srpi-config → Interface Options → I2C5")
        sys.exit(1)

    passed = 0
    failed = 0

    # Run tests
    for test_fn in [test_connection, test_part_id, test_temperature, test_fifo_data]:
        try:
            if test_fn(bus):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_result(test_fn.__name__, False, f"Unexpected error: {e}")
            failed += 1

    bus.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY: {passed} passed, {failed} failed out of {passed + failed} tests")
    print(f"{'='*60}")

    if failed == 0:
        print("  ✓ MAX30102 sensor is fully working!")
        print("    Ready for Pocket ASHA pulse/SpO2 measurements.")
    else:
        print("  ✗ Some tests failed. Check the output above for details.")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
