#!/usr/bin/env python3
"""
sensor_handler.py - MAX30102 (SpO2/HR) and BME280 (Temp/Humidity) sensor handler
for Pocket ASHA on RDK S100.

Graceful failure: If a sensor is not connected, methods return None instead of crashing.
"""

import time
from typing import Optional, Dict
from utils import get_logger

_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


# ============================================================
# I2C helpers
# ============================================================

def _check_i2c_device(bus: int, addr: int) -> bool:
    """Check if an I2C device is present."""
    try:
        import smbus2
        b = smbus2.SMBus(bus)
        b.read_byte(addr)
        b.close()
        return True
    except Exception:
        return False


# ============================================================
# MAX30102 — SpO2 + Heart Rate
# ============================================================

# Register map
_MAX_INT_STATUS   = 0x00
_MAX_INT_ENABLE   = 0x02
_MAX_FIFO_WR_PTR  = 0x04
_MAX_OVF_COUNTER  = 0x05
_MAX_FIFO_RD_PTR  = 0x06
_MAX_FIFO_DATA    = 0x07
_MAX_FIFO_CONFIG  = 0x08
_MAX_MODE_CONFIG  = 0x09
_MAX_SPO2_CONFIG  = 0x0A
_MAX_LED1_PA      = 0x0C
_MAX_LED2_PA      = 0x0D
_MAX_PART_ID      = 0xFF


class MAX30102:
    """MAX30102 pulse oximeter / heart-rate sensor via I2C."""

    def __init__(self, bus: int = 1, addr: int = 0x57):
        self.bus_num = bus
        self.addr = addr
        self._bus = None
        self.available = False

    def connect(self) -> bool:
        try:
            import smbus2
            if not _check_i2c_device(self.bus_num, self.addr):
                _logger().warning("[SENSOR] MAX30102 not detected on I2C bus %d addr 0x%02X", self.bus_num, self.addr)
                return False
            self._bus = smbus2.SMBus(self.bus_num)
            part_id = self._bus.read_byte_data(self.addr, _MAX_PART_ID)
            if part_id != 0x15:
                _logger().warning("[SENSOR] Unexpected MAX30102 part ID: 0x%02X", part_id)
                return False
            self._setup()
            self.available = True
            _logger().info("[SENSOR] MAX30102 connected")
            return True
        except Exception as e:
            _logger().warning("[SENSOR] MAX30102 init failed: %s", e)
            return False

    def _setup(self):
        b = self._bus
        a = self.addr
        # Reset
        b.write_byte_data(a, _MAX_MODE_CONFIG, 0x40)
        time.sleep(0.1)
        # Interrupt enable: A_FULL + data ready
        b.write_byte_data(a, _MAX_INT_ENABLE, 0xC0)
        # FIFO config: sample avg=4, rollover=on
        b.write_byte_data(a, _MAX_FIFO_CONFIG, 0x4F)
        # Mode: SpO2 mode
        b.write_byte_data(a, _MAX_MODE_CONFIG, 0x03)
        # SpO2 config: ADC range=4096, sample rate=100, pulse width=411
        b.write_byte_data(a, _MAX_SPO2_CONFIG, 0x27)
        # LED currents
        b.write_byte_data(a, _MAX_LED1_PA, 0x24)
        b.write_byte_data(a, _MAX_LED2_PA, 0x24)
        # Clear FIFO pointers
        b.write_byte_data(a, _MAX_FIFO_WR_PTR, 0x00)
        b.write_byte_data(a, _MAX_OVF_COUNTER, 0x00)
        b.write_byte_data(a, _MAX_FIFO_RD_PTR, 0x00)

    def _read_fifo(self):
        """Read one sample (red + ir) from FIFO."""
        b = self._bus
        a = self.addr
        d = b.read_i2c_block_data(a, _MAX_FIFO_DATA, 6)
        red = ((d[0] << 16) | (d[1] << 8) | d[2]) & 0x03FFFF
        ir  = ((d[3] << 16) | (d[4] << 8) | d[5]) & 0x03FFFF
        return red, ir

    def read_vitals(self, duration: int = 15) -> Optional[Dict]:
        """
        Read SpO2 and heart rate over `duration` seconds.
        Returns dict with spo2, heart_rate, confidence or None.
        """
        if not self.available:
            _logger().warning("[SENSOR] MAX30102 not available, skipping vitals")
            return None
        try:
            red_samples = []
            ir_samples = []
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    red, ir = self._read_fifo()
                    if ir > 5000:  # finger is likely on the sensor
                        red_samples.append(red)
                        ir_samples.append(ir)
                except Exception:
                    pass
                time.sleep(0.02)

            if len(ir_samples) < 50:
                _logger().warning("[SENSOR] Insufficient samples (%d), ensure finger is on sensor", len(ir_samples))
                return None

            spo2 = self._calc_spo2(red_samples, ir_samples)
            hr = self._calc_hr(ir_samples)
            confidence = min(len(ir_samples) / 200, 1.0)

            return {
                "spo2": round(spo2, 1),
                "heart_rate": int(hr),
                "confidence": round(confidence, 2),
            }
        except Exception as e:
            _logger().error("[SENSOR] MAX30102 read error: %s", e)
            return None

    @staticmethod
    def _calc_spo2(red, ir):
        """Estimate SpO2 from red/IR ratio (simplified Beer-Lambert)."""
        import statistics
        avg_red = statistics.mean(red) if red else 1
        avg_ir = statistics.mean(ir) if ir else 1
        if avg_ir == 0:
            return 0.0
        ratio = avg_red / avg_ir
        # Empirical linear approximation
        spo2 = 110.0 - 25.0 * ratio
        return max(0.0, min(100.0, spo2))

    @staticmethod
    def _calc_hr(ir_samples):
        """Estimate heart rate from IR signal peaks."""
        if len(ir_samples) < 50:
            return 0
        import statistics
        mean_ir = statistics.mean(ir_samples)
        # Simple peak detection
        peaks = []
        for i in range(1, len(ir_samples) - 1):
            if ir_samples[i] > mean_ir and ir_samples[i] > ir_samples[i - 1] and ir_samples[i] > ir_samples[i + 1]:
                peaks.append(i)
        if len(peaks) < 2:
            return 0
        # Average interval between peaks (samples at ~50Hz)
        intervals = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
        avg_interval = statistics.mean(intervals)
        sample_rate = 50  # approximate
        hr = (sample_rate / avg_interval) * 60
        return max(30, min(200, hr))

    def close(self):
        if self._bus:
            try:
                self._bus.close()
            except Exception:
                pass


# ============================================================
# BME280 — Temperature / Humidity / Pressure
# ============================================================

class BME280:
    """BME280 environmental sensor via I2C."""

    def __init__(self, bus: int = 1, addr: int = 0x76):
        self.bus_num = bus
        self.addr = addr
        self.available = False
        self._bme = None

    def connect(self) -> bool:
        try:
            if not _check_i2c_device(self.bus_num, self.addr):
                _logger().warning("[SENSOR] BME280 not detected on I2C bus %d addr 0x%02X", self.bus_num, self.addr)
                return False
            # Try using smbus2 + bme280 library, fall back to raw I2C
            try:
                import smbus2
                import bme280 as bme280_lib
                self._bus_obj = smbus2.SMBus(self.bus_num)
                self._calib = bme280_lib.load_calibration_params(self._bus_obj, self.addr)
                self._bme = bme280_lib
                self.available = True
                _logger().info("[SENSOR] BME280 connected (bme280 library)")
                return True
            except ImportError:
                pass
            # Fallback: raw I2C reads
            import smbus2
            b = smbus2.SMBus(self.bus_num)
            chip_id = b.read_byte_data(self.addr, 0xD0)
            b.close()
            if chip_id in (0x58, 0x60):  # BMP280=0x58, BME280=0x60
                self.available = True
                _logger().info("[SENSOR] BME280 detected (raw mode, chip 0x%02X)", chip_id)
                return True
            _logger().warning("[SENSOR] Unexpected BME280 chip ID: 0x%02X", chip_id)
            return False
        except Exception as e:
            _logger().warning("[SENSOR] BME280 init failed: %s", e)
            return False

    def read(self) -> Optional[Dict]:
        """Read temperature, humidity, pressure. Returns dict or None."""
        if not self.available:
            _logger().warning("[SENSOR] BME280 not available, skipping")
            return None
        try:
            if self._bme:
                data = self._bme.sample(self._bus_obj, self.addr, self._calib)
                return {
                    "temperature": round(data.temperature, 1),
                    "humidity": round(data.humidity, 1),
                    "pressure": round(data.pressure, 1),
                }
            # Raw I2C fallback — trigger forced measurement and read raw registers
            return self._read_raw()
        except Exception as e:
            _logger().error("[SENSOR] BME280 read error: %s", e)
            return None

    def _read_raw(self) -> Optional[Dict]:
        """Read temperature from raw registers (minimal implementation)."""
        try:
            import smbus2
            b = smbus2.SMBus(self.bus_num)
            # Trigger forced measurement: osrs_t=1, osrs_p=1, mode=forced
            b.write_byte_data(self.addr, 0xF4, 0x25)
            time.sleep(0.05)
            # Read raw temp
            data = b.read_i2c_block_data(self.addr, 0xFA, 3)
            raw = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
            # Very rough approximation (actual calculation needs calibration)
            temp_c = raw / 5120.0
            b.close()
            return {"temperature": round(temp_c, 1), "humidity": None, "pressure": None}
        except Exception as e:
            _logger().error("[SENSOR] BME280 raw read error: %s", e)
            return None

    def close(self):
        if hasattr(self, "_bus_obj") and self._bus_obj:
            try:
                self._bus_obj.close()
            except Exception:
                pass


# ============================================================
# Unified Sensor Handler
# ============================================================

class SensorHandler:
    """Unified handler for all sensors with graceful failure."""

    def __init__(self):
        from config import MAX30102_I2C_BUS, MAX30102_I2C_ADDR, BME280_I2C_BUS, BME280_I2C_ADDR
        self.max30102 = MAX30102(MAX30102_I2C_BUS, MAX30102_I2C_ADDR)
        self.bme280 = BME280(BME280_I2C_BUS, BME280_I2C_ADDR)

    def detect_sensors(self) -> Dict:
        """Detect which sensors are connected. Never crashes."""
        status = {"max30102": False, "bme280": False}
        try:
            status["max30102"] = self.max30102.connect()
        except Exception:
            pass
        try:
            status["bme280"] = self.bme280.connect()
        except Exception:
            pass
        return status

    def read_vitals(self, duration: int = 15) -> Optional[Dict]:
        """Read SpO2 + HR from MAX30102. Returns None if sensor unavailable."""
        return self.max30102.read_vitals(duration)

    def read_environment(self) -> Optional[Dict]:
        """Read temp/humidity/pressure from BME280. Returns None if unavailable."""
        return self.bme280.read()

    def read_all(self, vitals_duration: int = 15) -> Dict:
        """Read all available sensors. Missing values are None."""
        result = {"spo2": None, "heart_rate": None, "temperature": None,
                  "humidity": None, "pressure": None, "confidence": None}
        vitals = self.read_vitals(vitals_duration)
        if vitals:
            result.update(vitals)
        env = self.read_environment()
        if env:
            result["temperature"] = env.get("temperature")
            result["humidity"] = env.get("humidity")
            result["pressure"] = env.get("pressure")
        return result

    def close(self):
        self.max30102.close()
        self.bme280.close()
