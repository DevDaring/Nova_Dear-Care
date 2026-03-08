# Probable Issues — Pocket ASHA on RDK S100

Issues that **can break the project at runtime** during demo. Ordered by severity.

---

## 1. CRITICAL: `.env` File Missing — App Will Crash or AWS Will Fail

**File:** `Code/config.py` (line 16)  
**Problem:** `config.py` does `load_dotenv(ENV_PATH)` where `ENV_PATH = Path(__file__).parent / ".env"`. There is only `env.template` in the repo — no actual `.env` file. Without it:
- All `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME` will be empty strings
- Every Bedrock, Polly, Transcribe, S3, Lambda call will fail with `NoCredentialsError` or `InvalidIdentityToken`
- Sync will silently fail every 60 seconds (background thread catches the error but does nothing)

**Fix:** Before running, copy and fill the template:
```bash
cp ~/Documents/AI_4_Bharat/Code/env.template ~/Documents/AI_4_Bharat/Code/.env
# Edit .env with actual AWS credentials
```

---

## 2. CRITICAL: `LD_LIBRARY_PATH` / `LD_PRELOAD` Not Unset — PaddleOCR Segfaults

**File:** `Code/ocr_handler.py`, `Code/main.py` (header comment)  
**Problem:** RDK S100 ships with Hobot multimedia libraries set in `LD_LIBRARY_PATH` and `LD_PRELOAD` system-wide. These conflict with PaddleOCR's internal libraries, causing **instant segfault** when PaddleOCR loads.  
If you run `python3 main.py` instead of `env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py`, the first OCR attempt will crash the entire process.

**Fix:** Always launch with:
```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
```

---

## 3. CRITICAL: `amazon-transcribe-streaming-sdk` Not in `requirements.txt`

**File:** `Code/voice_handler.py` (line ~283-285)  
**Problem:** STT uses `from amazon_transcribe.client import TranscribeStreamingClient` — this is the `amazon-transcribe-streaming-sdk` package. It is **not listed** in `requirements.txt`. If not installed, every voice-to-text attempt will fail since Transcribe Streaming is the primary STT engine.  
The fallback (`SpeechRecognition` with Google free tier) requires internet and may also fail due to API rate limits.

**Fix:** Add to requirements.txt and install:
```bash
pip3 install amazon-transcribe-streaming-sdk
```

---

## 4. CRITICAL: `get_vin_data` Binary Might Not Exist at Hardcoded Path

**File:** `Code/camera_handler.py` (line 33)  
**Problem:** Camera capture depends on a C binary at the hardcoded path:
```python
_GET_VIN_DATA = "/app/multimedia_samples/sample_vin/get_vin_data/get_vin_data"
```
If the RDK S100 firmware was updated or the multimedia samples were not deployed to `/app/`, this binary won't exist and **every camera capture will silently return `None`** — no photo, no OCR, no prescription reading.

**How to check:**
```bash
ls -la /app/multimedia_samples/sample_vin/get_vin_data/get_vin_data
```

---

## 5. HIGH: Camera Test in `test_all_sensors.py` Tests Wrong Method

**File:** `Code/Sensors_Test/test_all_sensors.py` (line ~225-280)  
**Problem:** The test script uses `hobot_vio.libsrcampy` (open_cam / get_img) to test the camera. But the actual app uses `get_vin_data` C binary for capture (see `camera_handler.py` docstring: "libsrcampy does NOT include SC230AI in its compiled sensor list"). This means:
- `test_all_sensors.py` will always **FAIL** for camera test (showing "NOT WORKING") even when the camera actually works fine with `get_vin_data`
- This can cause **false alarm during demo** — you'll think camera is broken when it isn't

**Workaround:** Ignore the camera test result from `test_all_sensors.py`. Test camera separately:
```bash
sudo /app/multimedia_samples/sample_vin/get_vin_data/get_vin_data -s 6
# Then press 'g' to grab, 'q' to quit — check if .raw file is created
```

---

## 6. HIGH: Camera Capture Requires `sudo` — Permission Denied Without It

**File:** `Code/camera_handler.py` (line ~170)  
**Problem:** `capture_image()` runs:
```python
proc = subprocess.Popen(["sudo", _GET_VIN_DATA, "-s", str(_SENSOR_INDEX)], ...)
```
If the `sunrise` user doesn't have **passwordless sudo** for this binary, the process will hang waiting for a password (stdin is being used for `g`/`q` commands), eventually timeout after 15 seconds, and return `None`.

**How to check:**
```bash
sudo -n /app/multimedia_samples/sample_vin/get_vin_data/get_vin_data --help
# If it asks for password, you need to fix sudoers
```

**Fix:** Add to `/etc/sudoers.d/asha`:
```
sunrise ALL=(ALL) NOPASSWD: /app/multimedia_samples/sample_vin/get_vin_data/get_vin_data
```

---

## 7. HIGH: `CSV_HEADERS` Missing `symptoms` Field — Data Silently Dropped

**File:** `Code/config.py` (line 299-303) vs `Code/encounter_manager.py` (line ~275, ~97)  
**Problem:** `encounter_manager.py` sets `self.data["symptoms"] = symptoms` and passes it to `StorageManager.update_encounter()`. But `CSV_HEADERS` in config.py is:
```python
CSV_HEADERS = [
    "encounter_id", "timestamp", "asha_worker_id", "patient_id",
    "aadhaar_number", "patient_name", "age", "gender", "spo2", "heart_rate",
    "temperature", "triage_level", "triage_confidence",
    "sync_status", "photo_count", "audio_count", "notes",
]
```
**`symptoms` is NOT in the list.** The `update_encounter()` method filters: `{k: str(v) for k, v in kwargs.items() if k in CSV_HEADERS}` — so symptoms are silently ignored and **never saved to CSV**. The triage engine still works (uses in-memory data), but symptoms won't persist across restarts or appear in synced data.

---

## 8. HIGH: Polly TTS Will Crash for Non-Hindi/English Languages

**File:** `Code/language_handler.py` (lines 28-100) and `Code/voice_handler.py` (line ~175)  
**Problem:** Languages like Bengali, Tamil, Telugu, Marathi, etc. have `"polly_voice": None` in the config. When TTS runs, it does:
```python
voice = info.get("polly_voice") or "Kajal"
```
This falls back to `"Kajal"`, but the `lang_code` is set to e.g. `"bn-IN"` (Bengali). **Polly's Kajal voice does not support Bengali** — it only supports `en-IN` and `hi-IN`. This will throw:
```
botocore.exceptions.ClientError: InvalidParameterValue: Voice Kajal is not available for language code bn-IN
```
The app will then fall back to `pyttsx3` offline TTS, which may also fail on aarch64 if `espeak` is not installed.

**Fix before demo:** Either stick to English/Hindi languages, or install espeak:
```bash
sudo apt install espeak
```

---

## 9. HIGH: Bluetooth Speaker Not Paired — Voice Output Completely Silent

**File:** `Code/config.py` (line 62), `Code/voice_handler.py`  
**Problem:** `BOSE_SINK` is hardcoded to `"bluez_sink.78_2B_64_DD_68_CF.a2dp_sink"` and also read from `.env`. If the Bose speaker:
- Is not powered on
- Is not paired & connected via Bluetooth
- Has a different MAC address than the hardcoded one
- The `hobot-bluetooth.service` is crashing (documented in `RDK_System_Info.md`)

Then `paplay` will fail for every TTS output. The fallback tries a discovered `bluez_sink`, then default sink — but if no sink exists, **all voice output is silently lost**.

**How to check:**
```bash
pactl list sinks short | grep bluez
# Must show the Bose sink as RUNNING or IDLE
```

---

## 10. HIGH: Jabra Mic at Wrong ALSA Device Index

**File:** `Code/config.py` (line 59): `JABRA_CAPTURE_DEV = "plughw:1,0"`  
**Problem:** The Jabra mic is hardcoded to ALSA card 1. If another USB device is plugged in first, or after a reboot, the Jabra may appear as `hw:0,0` or `hw:2,0`. The recording will fail with "No such device" and fallback to `parecord` (PulseAudio), which has its own issues.  
`voice_handler.py` has `_discover_mic()` but it's **never called** — `record_audio()` uses `JABRA_CAPTURE_DEV` from config directly.

**How to check before demo:**
```bash
arecord -l
# Note the actual card number for Jabra, update .env or config.py if needed
```

---

## 11. MEDIUM: `select.select()` on stdin Hangs in Voice Mode

**File:** `Code/main.py` (line 183-186), `Code/guided_flow.py` (line ~86)  
**Problem:** `get_input()` uses `select.select([sys.stdin], [], [], 0.1)` to check for text input. On Linux, when running from an SSH session or through `nohup`, stdin may not behave as expected:
- If stdin is closed or redirected, `select.select` may raise an exception or return immediately
- The 0.1s timeout runs on every loop iteration, adding latency

This won't crash (it's in a try/except), but it may cause **unexpected behavior** when running via SSH.

---

## 12. MEDIUM: First PaddleOCR Load Takes 10-15 Seconds (Demo Stall)

**File:** `Code/ocr_handler.py` (line ~35)  
**Problem:** PaddleOCR is lazy-loaded on first use. The first `_get_ocr()` call downloads/loads the recognition model, detection model, and classification model into memory. On RDK S100, this takes **10-15 seconds**.  
During a live demo, when you say "read prescription" for the first time, there will be an awkward silence while the model loads.

**Mitigation:** Pre-warm PaddleOCR before the demo by running one OCR command, or add a warmup call during initialization.

---

## 13. MEDIUM: Transcribe Streaming `BrokenPipeError` on Repeated Calls

**File:** `Code/voice_handler.py` (lines ~300-330)  
**Problem:** The Transcribe Streaming SDK creates a new `asyncio` event loop per call (`asyncio.new_event_loop()`). On successive voice inputs, the previous loop's resources may not be fully cleaned up, causing `BrokenPipeError` on the next call. The code catches this but returns empty text, making the voice recognition **silently fail** — the user thinks the mic isn't working but it's actually a Transcribe connection issue.

**Symptoms:** Voice recognition works the first time, then becomes unresponsive.

---

## 14. MEDIUM: `guided_flow.py` — `_wait_for_wake` Can Block for 2.5 Minutes

**File:** `Code/guided_flow.py` (line ~212)  
**Problem:** In guided mode (`--guided`), `_wait_for_wake()` loops 30 times waiting for wake word detection. Each iteration records + transcribes audio (~7 seconds). If the venue is noisy and wake word is never detected, the flow **blocks for ~3.5 minutes** before continuing with "Starting the checkup now."

During a demo, this can be frustrating. In text mode, it's mitigated since you can type "hello asha".

---

## 15. MEDIUM: S3 Bucket May Not Exist — Sync Fails Silently

**File:** `Code/aws_handler.py`, `Code/sync_manager.py`  
**Problem:** `ensure_bucket()` exists in `aws_handler.py` but is **never called** during app startup or sync. If the S3 bucket (`pocket-asha-data` or the one in `.env`) doesn't exist in your AWS account, every sync upload will fail silently (caught by exception handler in sync loop).

**Fix before demo:**
```bash
aws s3 mb s3://pocket-asha-data  # or your bucket name
```

---

## 16. MEDIUM: Lambda Function May Not Be Deployed

**File:** `Code/deploy_lambda.sh`, `Code/lambda/handler.py`  
**Problem:** The Lambda function `pocket-asha-clinical-notes` must be deployed to AWS separately using `deploy_lambda.sh`. If not deployed, every `invoke_lambda()` call after sync will fail. This won't crash the app, but clinical notes won't be generated — reducing the demo impact.

**Fix:**
```bash
cd ~/Documents/AI_4_Bharat/Code
bash deploy_lambda.sh
```

---

## 17. LOW: `SensorHandler` Re-instantiated Every Vitals Call — I2C Resource Leak

**File:** `Code/main.py` (line ~340)  
**Problem:** `_measure_vitals()` creates a **new** `SensorHandler()` on every call:
```python
sh = SensorHandler()
sh.detect_sensors()
readings = sh.read_all()
sh.close()
```
Each `SensorHandler()` opens new `smbus2.SMBus` connections. While `close()` is called, rapid repeated calls could hit "Resource temporarily unavailable" errors on I2C bus 5 if the previous bus handle wasn't fully released.

---

## 18. LOW: `encounter_manager.py` — `run_triage()` Called Without Checking State

**File:** `Code/encounter_manager.py` (line ~272)  
**Problem:** `run_triage()` does:
```python
if self.state != EncounterState.TRIAGE:
    self._transition(EncounterState.TRIAGE)
```
But `_TRANSITIONS` only allows TRIAGE from `AUDIO` or `VITALS`. If triage is triggered at an unexpected state (e.g., directly from DEMOGRAPHICS), the transition is logged as invalid but the method still runs and writes triage data. This can cause state machine inconsistency.

---

## 19. LOW: `_confirm()` in `guided_flow.py` Defaults to Yes on Empty Input

**File:** `Code/guided_flow.py` (line ~123)  
**Problem:** `_confirm()` returns `True` if the response is non-empty and doesn't contain explicit denial words. In a noisy environment, any background noise transcribed as random text (e.g., "umm", "ah") will be treated as **confirmation**. This could lead to:
- Wrong Aadhaar confirmed
- Unwanted photo captures confirmed
- Unintended encounter completions

---

## Quick Pre-Demo Checklist

```
[ ] .env file created from env.template with real AWS credentials
[ ] Run with: env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
[ ] amazon-transcribe-streaming-sdk installed
[ ] get_vin_data binary exists at /app/multimedia_samples/...
[ ] sudo works without password for get_vin_data
[ ] Bose Bluetooth speaker paired and connected
[ ] Jabra mic at correct ALSA card number (check arecord -l)
[ ] S3 bucket exists in AWS account
[ ] Lambda function deployed (bash deploy_lambda.sh)
[ ] espeak installed (sudo apt install espeak) for offline TTS
[ ] PaddleOCR pre-warmed (run one OCR call before demo)
[ ] Stick to English or Hindi for Polly TTS
[ ] i2cdetect -y 5 shows 0x57 and 0x76
[ ] Camera DIP switch SW2200 set to MCLK (DOWN)
```
