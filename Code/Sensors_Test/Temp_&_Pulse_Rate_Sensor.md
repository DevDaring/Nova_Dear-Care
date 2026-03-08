You don’t need any kernel changes for BME280.  
You’ll just add one Python driver (bme280 + smbus2), point it to the **same I²C bus** you already use for MAX30102, and run a tiny script. [randomnerdtutorials](https://randomnerdtutorials.com/raspberry-pi-bme280-python/)


***

## 0. Assumptions

I’ll write steps assuming:

- MAX30102 is already working on some I²C bus number, call it **BUS_N** (for you it’s whatever bus showed `0x57` in `i2cdetect`). [kernel](https://www.kernel.org/doc/html/latest/i2c/dev-interface.html)
- BME280 (GY‑BME280) is wired:  
  - VCC → J24 pin 1 (3.3 V), GND → pin 6, SDA → pin 3, SCL → pin 5 (shared with MAX30102). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/48918449/671749dc-971a-4ad3-9cd5-613c3dd62e09/01_rdk_s100.md)
- SW6 “40 PIN” is already set so pins 3/5 are I2C5, not UART. [d-robotics.github](https://d-robotics.github.io/rdk_doc/en/Basic_Application/03_40pin_user_guide/40pin_define/)

Anywhere you see `BUS_N` below, replace it with **the same bus number you used for MAX30102** (e.g. 5).

***

## 1. Confirm that BME280 is visible on I²C

1. In a terminal:

   ```bash
   sudo i2cdetect -y BUS_N
   ```

2. In the grid you should now see:
   - `57` → MAX30102  
   - `76` **or** `77` → GY‑BME280 (its I²C address depends on SDO wiring / board default). [robu](https://robu.in/product/gy-bme280-3-3-precision-altimeter-atmospheric-pressure-sensor-module/)

If you see one of `0x76` or `0x77`, wiring is OK and you can proceed. [randomnerdtutorials](https://randomnerdtutorials.com/solved-could-not-find-a-valid-bme280-sensor/)

***

## 2. Install Python libraries for BME280

You already have Python and `python3-smbus` from MAX30102 setup, but these commands are safe to re‑run:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-smbus
sudo pip3 install smbus2 RPi.bme280
```

- `smbus2` gives improved I²C support in Python. [bme280.readthedocs](https://bme280.readthedocs.io)
- `RPi.bme280` is a wrapper that internally uses `bme280` and `smbus2`, used by many Raspberry Pi tutorials. [randomnerdtutorials](https://randomnerdtutorials.com/raspberry-pi-bme280-python/)

This stack is pure user‑space; no board‑specific magic, so any AI tool can safely work with it.

***

## 3. Create a reusable BME280 helper module

Make one small file that hides all low‑level details. Then future tools just call a single function.

1. Create a file:

   ```bash
   cd ~
   nano bme280_helper.py
   ```

2. Put this code inside, **editing BUS_N and ADDRESS as needed**:

   ```python
   # bme280_helper.py
   #
   # Minimal, dumb-proof wrapper around the BME280 sensor.
   # Edit ONLY BUS_N and ADDRESS for your board.

   import smbus2
   import bme280  # provided by RPi.bme280 dependency

   # CHANGE THESE TWO VALUES IF NEEDED:
   BUS_N = 5          # <-- set this to your I2C bus (same as MAX30102)
   ADDRESS = 0x76     # <-- change to 0x77 if your sensor shows that in i2cdetect

   # Create and cache the bus + calibration at import time
   _bus = smbus2.SMBus(BUS_N)
   _calib = bme280.load_calibration_params(_bus, ADDRESS)

   def read_bme280():
       """
       Take one reading from BME280 and return a dict with
       temperature_C, humidity_percent, pressure_hPa.
       Any caller (human or AI tool) can just use this function.
       """
       data = bme280.sample(_bus, ADDRESS, _calib)
       return {
           "temperature_C": float(data.temperature),
           "humidity_percent": float(data.humidity),
           "pressure_hPa": float(data.pressure),
       }
   ```

   This is straight from the canonical `smbus2 + bme280` pattern, just wrapped into a single `read_bme280()` function. [hackster](https://www.hackster.io/Shilleh/beginner-tutorial-how-to-connect-raspberry-pi-and-bme280-4fdbd5)

3. Save (`Ctrl+O`, Enter) and exit (`Ctrl+X`).

Now **any script** can get a reading with:

```python
from bme280_helper import read_bme280
reading = read_bme280()
```

No one has to know about bus numbers, addresses, or calibration parameters.

***

## 4. Simple one‑file test script

Create a script that just prints values every 2 seconds.

1. Create file:

   ```bash
   nano read_bme280_demo.py
   ```

2. Paste:

   ```python
   # read_bme280_demo.py
   import time
   from bme280_helper import read_bme280

   print("Starting BME280 demo...")

   try:
       while True:
           values = read_bme280()
           print(
               "T = {:.2f} °C,  RH = {:.2f} %,  P = {:.2f} hPa".format(
                   values["temperature_C"],
                   values["humidity_percent"],
                   values["pressure_hPa"],
               )
           )
           time.sleep(2)
   except KeyboardInterrupt:
       print("Stopped by user.")
   ```

3. Run it:

   ```bash
   python3 read_bme280_demo.py
   ```

If everything is correct, you’ll see temperature, humidity, and pressure values continuously printed. [bme280.readthedocs](https://bme280.readthedocs.io)

***

## 5. Making it “AI‑friendly” (how other tools should use this)

You now have **one clear contract** for any future code or AI agent:

- **Do not touch hardware / I²C setup.** (Already done via `srpi-config`, I²C tools, etc.) [docs.kernel](https://docs.kernel.org/i2c/dev-interface.html)
- **Only change these parts if needed:**
  - `BUS_N` constant in `bme280_helper.py` (I²C bus number).  
  - `ADDRESS` constant in `bme280_helper.py` (0x76 vs 0x77).  
- **To read sensor data:**

  ```python
  from bme280_helper import read_bme280
  env = read_bme280()
  print(env["temperature_C"], env["humidity_percent"], env["pressure_hPa"])
  ```

- Higher‑level apps (logging, dashboards, ML, etc.) should **only depend on that function**, not on smbus2 or register details.

This pattern mirrors well‑documented Raspberry Pi BME280 tutorials, just adapted so your RDK S100’s bus number is configurable. [hackster](https://www.hackster.io/Shilleh/beginner-tutorial-how-to-connect-raspberry-pi-and-bme280-4fdbd5)

***

If you paste your actual `i2cdetect -y BUS_N` output, I can tell you exactly what to set for `BUS_N` and `ADDRESS` so you don’t have to guess.