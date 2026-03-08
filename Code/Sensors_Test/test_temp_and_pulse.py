#!/usr/bin/env python3
"""
test_temp_and_pulse.py — Combined BME280 + MAX30102 Test

Tests both sensors connected on the same I2C bus (bus 5, J24 40-pin header):
  - BME280  at 0x76 → Temperature, Humidity, Pressure
  - MAX30102 at 0x57 → Pulse Oximeter (RED + IR LEDs)

Usage:
    cd ~/Documents/AI_4_Bharat/Code
    sudo python3 Sensors_Test/test_temp_and_pulse.py
"""

import sys
import time

# ==============================================================
# Constants
# ==============================================================
I2C_BUS         = 5
BME280_ADDR     = 0x76
MAX30102_ADDR   = 0x57

# MAX30102 registers
REG_FIFO_WR_PTR   = 0x04
REG_FIFO_OVF_CTR  = 0x05
REG_FIFO_RD_PTR   = 0x06
REG_FIFO_DATA     = 0x07
REG_FIFO_CONFIG   = 0x08
REG_MODE_CONFIG   = 0x09
REG_SPO2_CONFIG   = 0x0A
REG_LED1_PA       = 0x0C
REG_LED2_PA       = 0x0D
REG_TEMP_INT      = 0x1F
REG_TEMP_FRAC     = 0x20
REG_TEMP_CONFIG   = 0x21
REG_REVISION_ID   = 0xFE
REG_PART_ID       = 0xFF

# ==============================================================
# Helpers
# ==============================================================

def banner(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def result(label, passed, detail=""):
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {label}")
    if detail:
        print(f"         {detail}")

passed_count = 0
failed_count = 0

def track(ok):
    global passed_count, failed_count
    if ok:
        passed_count += 1
    else:
        failed_count += 1


# ==============================================================
# PART A — BME280 Tests
# ==============================================================

def test_bme280_connection(bus):
    """A1: Check BME280 responds on I2C."""
    banner("A1: BME280 — I2C Connection")
    try:
        bus.read_byte(BME280_ADDR)
        result(f"BME280 responds at 0x{BME280_ADDR:02X} on bus {I2C_BUS}", True)
        return True
    except OSError as e:
        result(f"BME280 at 0x{BME280_ADDR:02X} on bus {I2C_BUS}", False,
               f"Error: {e}. Check wiring: VIN→Pin1(3.3V), GND→Pin6, SDA→Pin3, SCL→Pin5")
        return False


def test_bme280_chip_id(bus):
    """A2: Verify BME280 chip ID."""
    banner("A2: BME280 — Chip ID Verification")
    chip_id = bus.read_byte_data(BME280_ADDR, 0xD0)
    names = {0x60: "BME280", 0x58: "BMP280"}
    name = names.get(chip_id)
    if name:
        result(f"Chip ID = 0x{chip_id:02X} ({name})", True)
        if chip_id == 0x58:
            print("         Note: BMP280 has no humidity sensor — only temp + pressure")
        return True
    else:
        result(f"Chip ID = 0x{chip_id:02X}", False,
               "Expected 0x60 (BME280) or 0x58 (BMP280)")
        return False


def test_bme280_reading(bus):
    """A3: Read calibrated temperature, humidity, pressure via bme280 library."""
    banner("A3: BME280 — Sensor Reading")
    try:
        import bme280
        calib = bme280.load_calibration_params(bus, BME280_ADDR)
        data = bme280.sample(bus, BME280_ADDR, calib)

        temp = data.temperature
        hum = data.humidity
        pres = data.pressure

        print(f"  Temperature : {temp:.2f} °C")
        print(f"  Humidity    : {hum:.2f} %")
        print(f"  Pressure    : {pres:.2f} hPa")

        # Sanity checks
        ok = True
        if not (-40 <= temp <= 85):
            result("Temperature range", False, f"{temp:.1f}°C is out of BME280 range (-40 to 85)")
            ok = False
        if not (0 <= pres <= 1200):
            result("Pressure range", False, f"{pres:.1f} hPa is out of range")
            ok = False

        if ok:
            result("BME280 readings valid", True,
                   f"T={temp:.1f}°C, H={hum:.1f}%, P={pres:.1f}hPa")
        return ok
    except ImportError:
        result("bme280 library", False, "Not installed. Run: sudo pip3 install RPi.bme280")
        return False
    except Exception as e:
        result("BME280 read", False, f"Error: {e}")
        return False


def test_bme280_continuous(bus, seconds=5):
    """A4: Continuous BME280 readings to check stability."""
    banner(f"A4: BME280 — Continuous Readings ({seconds}s)")
    try:
        import bme280
        calib = bme280.load_calibration_params(bus, BME280_ADDR)

        temps = []
        start = time.time()
        print(f"  Sampling for {seconds} seconds...")
        while time.time() - start < seconds:
            data = bme280.sample(bus, BME280_ADDR, calib)
            temps.append(data.temperature)
            elapsed = time.time() - start
            if len(temps) % 5 == 0:
                print(f"    [{elapsed:4.1f}s] T={data.temperature:.2f}°C  "
                      f"H={data.humidity:.1f}%  P={data.pressure:.1f}hPa")
            time.sleep(0.2)

        count = len(temps)
        t_min, t_max = min(temps), max(temps)
        drift = t_max - t_min

        print(f"\n  Samples: {count}, Temp range: {t_min:.2f} – {t_max:.2f}°C, Drift: {drift:.2f}°C")

        if drift < 3.0:
            result("Temperature stability", True, f"Drift {drift:.2f}°C over {seconds}s — stable")
            return True
        else:
            result("Temperature stability", False, f"Drift {drift:.2f}°C — unstable readings")
            return False
    except Exception as e:
        result("Continuous read", False, f"Error: {e}")
        return False


# ==============================================================
# PART B — MAX30102 Tests
# ==============================================================

def test_max30102_connection(bus):
    """B1: Check MAX30102 responds on I2C."""
    banner("B1: MAX30102 — I2C Connection")
    try:
        bus.read_byte(MAX30102_ADDR)
        result(f"MAX30102 responds at 0x{MAX30102_ADDR:02X} on bus {I2C_BUS}", True)
        return True
    except OSError as e:
        result(f"MAX30102 at 0x{MAX30102_ADDR:02X} on bus {I2C_BUS}", False,
               f"Error: {e}. Check wiring: VIN→Pin1(3.3V), GND→Pin6, SDA→Pin3, SCL→Pin5")
        return False


def test_max30102_part_id(bus):
    """B2: Verify MAX30102 Part ID."""
    banner("B2: MAX30102 — Part ID Verification")
    part_id = bus.read_byte_data(MAX30102_ADDR, REG_PART_ID)
    rev_id = bus.read_byte_data(MAX30102_ADDR, REG_REVISION_ID)
    if part_id == 0x15:
        result(f"Part ID = 0x{part_id:02X} (MAX30102)", True, f"Revision: 0x{rev_id:02X}")
        return True
    else:
        result(f"Part ID = 0x{part_id:02X}", False,
               f"Expected 0x15 (MAX30102). Got 0x{part_id:02X}")
        return False


def test_max30102_temperature(bus):
    """B3: Read MAX30102 on-die temperature."""
    banner("B3: MAX30102 — Die Temperature")
    try:
        bus.write_byte_data(MAX30102_ADDR, REG_TEMP_CONFIG, 0x01)
        time.sleep(0.1)

        temp_int = bus.read_byte_data(MAX30102_ADDR, REG_TEMP_INT)
        temp_frac = bus.read_byte_data(MAX30102_ADDR, REG_TEMP_FRAC)
        if temp_int > 127:
            temp_int -= 256
        temp_c = temp_int + (temp_frac * 0.0625)

        if -10 < temp_c < 60:
            result(f"Die temperature: {temp_c:.1f} °C", True)
            return True
        else:
            result(f"Die temperature: {temp_c:.1f} °C (out of range)", False)
            return False
    except Exception as e:
        result("Temperature read", False, f"Error: {e}")
        return False


def test_max30102_fifo(bus, duration=8):
    """B4: Configure SpO2 mode and read FIFO data."""
    banner(f"B4: MAX30102 — Live FIFO Data ({duration}s)")
    print("  Configuring SpO2 mode (RED + IR)...")

    try:
        a = MAX30102_ADDR

        # Reset
        bus.write_byte_data(a, REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)
        for _ in range(10):
            if not (bus.read_byte_data(a, REG_MODE_CONFIG) & 0x40):
                break
            time.sleep(0.05)

        # Configure
        bus.write_byte_data(a, REG_FIFO_CONFIG, 0x4F)   # avg=4, rollover
        bus.write_byte_data(a, REG_SPO2_CONFIG, 0x27)    # ADC 4096, 100sps, 18-bit
        bus.write_byte_data(a, REG_LED1_PA, 0x24)        # RED 6.4mA
        bus.write_byte_data(a, REG_LED2_PA, 0x24)        # IR 6.4mA

        # Clear FIFO
        bus.write_byte_data(a, REG_FIFO_WR_PTR, 0x00)
        bus.write_byte_data(a, REG_FIFO_OVF_CTR, 0x00)
        bus.write_byte_data(a, REG_FIFO_RD_PTR, 0x00)

        # SpO2 mode
        bus.write_byte_data(a, REG_MODE_CONFIG, 0x03)

        print(f"  Reading for {duration} seconds...")
        print("  (Place finger on sensor for pulse detection)\n")

        red_samples = []
        ir_samples = []
        start = time.time()

        while time.time() - start < duration:
            wr = bus.read_byte_data(a, REG_FIFO_WR_PTR)
            rd = bus.read_byte_data(a, REG_FIFO_RD_PTR)
            n = (wr - rd) & 0x1F
            if n == 0:
                time.sleep(0.01)
                continue
            for _ in range(n):
                raw = bus.read_i2c_block_data(a, REG_FIFO_DATA, 6)
                red = ((raw[0] & 0x03) << 16) | (raw[1] << 8) | raw[2]
                ir  = ((raw[3] & 0x03) << 16) | (raw[4] << 8) | raw[5]
                red_samples.append(red)
                ir_samples.append(ir)

            if len(red_samples) % 50 == 0 and red_samples:
                elapsed = time.time() - start
                print(f"    [{elapsed:5.1f}s] Samples: {len(red_samples):4d} | "
                      f"RED: {red_samples[-1]:6d} | IR: {ir_samples[-1]:6d}")

        # Shutdown
        bus.write_byte_data(a, REG_MODE_CONFIG, 0x80)

        total = len(red_samples)
        print(f"\n  Total samples: {total}")

        if total == 0:
            result("FIFO data", False, "No samples collected")
            return False

        red_avg = sum(red_samples) / total
        ir_avg = sum(ir_samples) / total
        red_range = max(red_samples) - min(red_samples)
        ir_range = max(ir_samples) - min(ir_samples)

        print(f"  RED — avg: {red_avg:.0f}, range: {red_range}")
        print(f"  IR  — avg: {ir_avg:.0f}, range: {ir_range}")

        if red_avg < 100 and ir_avg < 100:
            result("LED activity", False, "Both readings near zero — check VIN wiring")
            return False

        result("LED activity", True, f"RED avg={red_avg:.0f}, IR avg={ir_avg:.0f}")

        if red_range > 500 or ir_range > 500:
            result("Pulse signal detected", True,
                   "Finger on sensor — good signal variation")
        else:
            print("         (No finger detected — LEDs are working fine)")

        return True

    except Exception as e:
        result("FIFO read", False, f"Error: {e}")
        return False


# ==============================================================
# Main
# ==============================================================

def main():
    print("=" * 60)
    print("  Combined Sensor Test: BME280 + MAX30102")
    print("  I2C Bus 5 — J24 40-Pin Header")
    print("  BME280: 0x76 | MAX30102: 0x57")
    print("=" * 60)

    try:
        import smbus2
    except ImportError:
        print("\n  [FAIL] smbus2 not installed. Run: pip3 install smbus2")
        sys.exit(1)

    try:
        bus = smbus2.SMBus(I2C_BUS)
    except PermissionError:
        print(f"\n  [FAIL] Permission denied on /dev/i2c-{I2C_BUS}")
        print("         Run with: sudo python3 Sensors_Test/test_temp_and_pulse.py")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n  [FAIL] /dev/i2c-{I2C_BUS} not found")
        print("         Enable I2C5 via: sudo srpi-config")
        sys.exit(1)

    # ---- Part A: BME280 ----
    banner("PART A: BME280 (Temperature / Humidity / Pressure)")
    bme_tests = [
        test_bme280_connection,
        test_bme280_chip_id,
        test_bme280_reading,
        test_bme280_continuous,
    ]
    for t in bme_tests:
        try:
            track(t(bus))
        except Exception as e:
            result(t.__name__, False, f"Unexpected: {e}")
            track(False)

    # ---- Part B: MAX30102 ----
    banner("PART B: MAX30102 (Pulse Oximeter / Heart Rate)")
    max_tests = [
        test_max30102_connection,
        test_max30102_part_id,
        test_max30102_temperature,
        test_max30102_fifo,
    ]
    for t in max_tests:
        try:
            track(t(bus))
        except Exception as e:
            result(t.__name__, False, f"Unexpected: {e}")
            track(False)

    bus.close()

    # ---- Summary ----
    total = passed_count + failed_count
    print(f"\n{'='*60}")
    print(f"  SUMMARY: {passed_count} passed, {failed_count} failed out of {total} tests")
    print(f"{'='*60}")

    if failed_count == 0:
        print("  ✓ Both sensors fully working on I2C bus 5!")
    else:
        print("  ✗ Some tests failed — check output above.")

    print()
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
