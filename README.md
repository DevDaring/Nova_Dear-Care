# Dear-Care — AI-Powered Healthcare Assistant

> **Amazon Nova Hackathon — AI for Bharat** | Team: DevDaring  
> Platform: D-Robotics RDK S100 V1P0 (Ubuntu 22.04.5, ARM64, 4GB RAM)

---

## Table of Contents

- [Overview](#overview)
- [Amazon Nova Integration](#amazon-nova-integration)
- [Architecture](#architecture)
- [Healthcare Flow](#healthcare-flow)
- [AWS Services Used](#aws-services-used)
- [Hardware](#hardware)
- [Supported Languages](#supported-languages)
- [Vital Sign Thresholds](#vital-sign-thresholds)
- [Fit-U Companion App](#fit-u-companion-app-flutter)
- [Lambda Functions](#lambda-functions)
- [Module Reference](#module-reference)
- [Configuration Reference](#configuration-reference)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Security](#security)
- [Team & License](#team--license)

---

## Overview

**Dear-Care** is a portable, voice-activated AI healthcare assistant built for community health workers in rural India. Running on an edge AI device (RDK S100) with **Amazon Nova as the core intelligence layer**, it enables frontline health workers to:

- **Speak naturally** in 7 languages — English, Hindi, French, German, Italian, Spanish, Portuguese
- **Identify patients** through Aadhaar number voice collection (Nova Lite extraction + regex fallback)
- **Scan prescriptions** via camera → Amazon Textract + PaddleOCR → Nova Lite analysis
- **Measure vital signs** — SpO2, heart rate (MAX30102), temperature, pressure (BMP280)
- **Get AI clinical decisions** — encounter data uploaded to Lambda → Nova Lite generates health summary, clinical notes, triage review → results spoken to health worker and sent to mobile app
- **Consult interactively** — multi-turn health conversations (Transcribe STT → Nova Lite reasoning → Polly TTS)
- **Send results to mobile** — Fit-U Flutter companion app receives verdicts via SNS push + DynamoDB polling
- **Work fully offline** — every AWS service has a local fallback; data syncs when connectivity returns

---

## Amazon Nova Integration

| Nova Service | Usage in Dear-Care |
|---|---|
| **Amazon Nova 2 Lite** (`amazon.nova-2-lite-v1:0`) | Core reasoning — intent classification, Aadhaar extraction, prescription analysis, health consultation, clinical notes generation, triage review, health summary |
| **Amazon Polly** (Neural) | Primary TTS engine — 7 languages with Neural voices |
| **Amazon Transcribe** Streaming | Real-time speech-to-text via WebSocket |

### Voice Pipeline

```
User speaks → Jabra EVOLVE 20 MS (USB mic)
    → Amazon Transcribe Streaming (STT)
    → Nova Lite (intent classification + reasoning)
    → Amazon Polly Neural (TTS)
    → Bose SoundLink Micro (Bluetooth speaker)
```

### Consultation Pipeline

```
User speaks → Transcribe (STT) → Nova Lite (reason with patient context: vitals, prescriptions, history)
    → Polly Neural (speak response) → repeat (up to 10 turns)
    → User says "stop" / "goodbye" to end
```

### Lambda Processing Pipeline

```
Encounter data → S3 upload → Lambda invoked
    → Lambda reads encounter from S3
    → Nova Lite generates: health_summary + clinical_notes + triage_review
    → Results stored in S3 + DynamoDB
    → SNS push notification to Fit-U mobile app
    → Health summary spoken to health worker on device
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DEAR-CARE DEVICE                        │
│                   RDK S100 V1P0 (ARM64)                      │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │ Voice I/O  │  │  Camera    │  │     Sensors            │ │
│  │ Jabra Mic  │  │  SC230AI   │  │  MAX30102 (SpO2/HR)    │ │
│  │ Bose BT    │  │  MIPI CSI  │  │  BMP280 (Temp/Press)   │ │
│  └─────┬──────┘  └─────┬──────┘  └─────────┬──────────────┘ │
│        │               │                    │                │
│  ┌─────▼───────────────▼────────────────────▼──────────────┐ │
│  │             Python Application (17 modules)             │ │
│  │  main.py │ guided_flow.py │ encounter_manager.py        │ │
│  │  voice_handler.py │ aws_handler.py │ triage_engine.py   │ │
│  │  camera_handler.py │ ocr_handler.py │ sensor_handler.py │ │
│  │  intent_handler.py │ language_handler.py │ config.py     │ │
│  │  storage_manager.py │ sync_manager.py │ security.py     │ │
│  │  fitu_client.py │ utils.py                              │ │
│  └─────────────────────┬───────────────────────────────────┘ │
└─────────────────────────┼────────────────────────────────────┘
                          │  HTTPS
┌─────────────────────────▼────────────────────────────────────┐
│                    AWS CLOUD SERVICES                         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │   Bedrock   │  │     S3      │  │       Lambda         │ │
│  │  Nova Lite  │  │ Encounters  │  │  health_summary      │ │
│  │ (Reasoning) │  │  + Results  │  │  generate_notes      │ │
│  │             │  │             │  │  triage_review       │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │    Polly    │  │ Transcribe  │  │    API Gateway       │ │
│  │ Neural TTS  │  │  Streaming  │  │  Fit-U Mobile API    │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │  DynamoDB   │  │     SNS     │  │     Textract         │ │
│  │ Health Data │  │ Push Notify │  │  Prescription OCR    │ │
│  │  + Verdicts │  │  to Mobile  │  │                      │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Healthcare Flow

The assistant "Kamal" guides the health worker through a sequential encounter:

```
Step 1: Collect Aadhaar (voice → Nova Lite extraction → masked confirmation)
    ↓
Step 2: Patient Lookup (CSV database) or New Registration (ask name)
    ↓
Step 3: Prescription Capture (optional, multi-document loop)
        Camera → Textract/PaddleOCR → Nova Lite analysis
    ↓
Step 4: Pulse / SpO2 Measurement (MAX30102 sensor, I2C)
    ↓
Step 5: Environment Readings (BMP280 — temperature, pressure)
    ↓
Step 6: Save & Upload to Cloud
        → S3 upload → Lambda processes 3 actions:
          • health_summary  — consolidated report with vitals, Rx, environment
          • generate_notes  — structured clinical notes
          • triage_review   — AI review of triage decision
        → Health summary spoken to health worker
        → SNS notification sent to Fit-U mobile app
    ↓
Step 7: Health Consultation (optional)
        Multi-turn: Transcribe STT → Nova Lite → Polly TTS
    ↓
Step 8: Next Patient (loop) or Shutdown
```

### Voice Interaction Details

| Step | Kamal Says | Health Worker Responds |
|------|-----------|----------------------|
| Aadhaar | "Please tell me the patient's 12 digit Aadhaar number" | Speaks the number |
| Confirm | "I heard Aadhaar number 1234 **** 9012. Is that correct?" | "Yes" / "No" |
| Prescription | "Do you have any prescriptions to scan?" | "Yes" / "No" |
| More Rx | "Do you have another prescription to scan?" | "Yes" / "No" |
| Consultation | "Would you like a health consultation?" | "Yes" / "No" |
| Next patient | "Would you like to check another patient?" | "Yes" / "No" |

**Yes/No Detection**: Whole-word matching with punctuation stripping. Supports English + Hindi affirmatives/negatives:
- **Yes words**: yes, yeah, haan, ha, ji, ok, okay, sure, yep
- **No words**: no, nahi, nah, nope, na (deny takes priority over yes)

---

## AWS Services Used

| Service | Purpose | Fallback |
|---------|---------|----------|
| **Amazon Bedrock** (Nova Lite) | Core reasoning: intent, Aadhaar extraction, prescription analysis, health consultation, clinical notes, triage review, health summary | Keyword matching + rule-based triage |
| **Amazon Polly** (Neural) | Primary TTS for 7 languages | pyttsx3 offline engine |
| **Amazon Transcribe** Streaming | Real-time speech-to-text via WebSocket | SpeechRecognition (Google API) |
| **Amazon Textract** | Prescription/document OCR | PaddleOCR 2.7.0 (on-device) |
| **Amazon S3** | Encounter data + clinical notes + photo storage | Local CSV + JSON files |
| **AWS Lambda** | Cloud-based clinical notes, health summary, triage review via Nova Lite | On-device triage only |
| **Amazon DynamoDB** | Fit-U health worker data + verdict storage for mobile polling | App continues without |
| **Amazon SNS** | Push notifications to Fit-U mobile app after each decision | Mobile app polls DynamoDB |
| **API Gateway** | REST API for Fit-U Flutter app | App uses cached data |

> Every fallback event is logged with the reason for the switch.

---

## Hardware

| Component | Model | Interface | Details |
|-----------|-------|-----------|---------|
| Edge AI Board | D-Robotics RDK S100 V1P0 | ARM64, 4GB RAM | Ubuntu 22.04.5 LTS |
| Camera | SC230AI | MIPI CSI | 1920×1080, 30fps, RAW10 Bayer |
| Microphone | Jabra EVOLVE 20 MS | USB (card 1, `plughw:1,0`) | 16kHz mono capture |
| Speaker | Bose SoundLink Micro | Bluetooth A2DP | Via TP-Link UB500 dongle |
| Pulse Oximeter | MAX30102 | I2C Bus 5, addr 0x57 | SpO2 + Heart Rate |
| Environment | BMP280 | I2C Bus 5, addr 0x76 | Temperature + Pressure |
| BT Dongle | TP-Link UB500 | USB | Bluetooth 5.0 |

### Camera Details

- Uses RDK S100 `get_vin_data` binary for RAW10 capture
- 10-bit bitpacked Bayer BGGR → demosaic → gamma correction → auto white balance
- Saved as JPEG for upload + OCR processing

### Sensor I2C Addresses

```
Bus 5 (0x57) — MAX30102 Pulse Oximeter
Bus 5 (0x76) — BMP280 Temperature/Pressure
```

---

## Supported Languages

| Code | Language | Polly Voice | Engine | Transcribe Code |
|------|----------|-------------|--------|-----------------|
| `en` | English | Matthew | Neural | `en-US` |
| `hi` | Hindi (हिन्दी) | Kajal | Neural | `hi-IN` |
| `fr` | French (Français) | Lea | Neural | `fr-FR` |
| `de` | German (Deutsch) | Vicki | Neural | `de-DE` |
| `it` | Italian (Italiano) | Bianca | Neural | `it-IT` |
| `es` | Spanish (Español) | Lucia | Neural | `es-ES` |
| `pt` | Portuguese (Português) | Camila | Neural | `pt-BR` |

Default: Hindi (`hi`) with Polly voice Kajal.  
Language can be changed at runtime via voice command.

---

## Vital Sign Thresholds

| Vital | Normal | Warning | Critical |
|-------|--------|---------|----------|
| **SpO2** | ≥ 94% | < 94% | < 90% |
| **Heart Rate** | 50–120 bpm | < 50 or > 120 bpm | < 40 or > 150 bpm |
| **Temperature** | 35.0–38.5°C | > 38.5°C or < 35.0°C | > 39.5°C |

The on-device `triage_engine.py` uses these thresholds for immediate URGENT/ROUTINE classification before cloud processing.

---

## Fit-U Companion App (Flutter)

The **Fit-U** Flutter mobile app runs on the health worker's phone and syncs with Dear-Care:

### Data Flow

```
Health Worker's Phone (Fit-U App)
    ├── SENDS to AWS:
    │   ├── Step count, distance, speed
    │   ├── Activity level, GPS coordinates
    │   └── Estimated heart rate
    │   (via API Gateway → DynamoDB: dear-care-fitu-health)
    │
    └── RECEIVES from AWS:
        ├── Triage verdicts and health summaries
        ├── Clinical notes and recommendations
        └── Push notifications per encounter
        (via SNS push + DynamoDB polling: dear-care-verdicts)
```

### SNS Notification Payload

```json
{
  "notification_type": "DEAR_CARE_VERDICT",
  "worker_id": "DC-001",
  "encounter_id": "ENC_20260316201958_879",
  "triage_level": "ROUTINE",
  "summary": "Patient presents with mild fever...",
  "timestamp": "2026-03-16T20:25:37Z",
  "s3_path": "encounters/ENC_.../verdict.json"
}
```

### Fit-U AWS Resources

| Resource | Name/ARN |
|----------|----------|
| DynamoDB Table | `dear-care-fitu-health` |
| DynamoDB Table | `dear-care-verdicts` |
| SNS Topic | `dear-care-fitu-notifications` |
| API Gateway | REST API for write operations |

---

## Lambda Functions

The Lambda function `dear-care-clinical-notes` supports three actions:

### `health_summary` (Primary)

Consolidated health analysis including vitals, prescriptions, environment, symptoms, and Fit-U mobility data. Returns assessment, key concerns, prescription review, and URGENT/ROUTINE recommendation.

### `generate_notes`

Structured clinical notes formatted as: Patient info, Vitals summary, Assessment, Plan. Stored as `clinical_notes.txt` in S3.

### `triage_review`

AI review of the on-device triage decision. Validates whether the URGENT/ROUTINE classification was appropriate.

### Lambda Environment Variables

| Variable | Default |
|----------|---------|
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET_NAME` | `dear-care-data` |
| `BEDROCK_MODEL_ID` | `amazon.nova-2-lite-v1:0` |
| `FITU_SNS_TOPIC_ARN` | (configured per deployment) |
| `FITU_DYNAMODB_TABLE` | `dear-care-fitu-health` |
| `VERDICTS_DYNAMODB_TABLE` | `dear-care-verdicts` |

### Lambda Flow

```
event: {encounter_id, action} →
    Read encounter.json from S3 →
    Fetch Fit-U worker data from DynamoDB (optional) →
    Call Bedrock Nova Lite with medical prompt →
    Store result in S3 →
    Store verdict in DynamoDB (for mobile polling) →
    Send SNS notification to Fit-U app →
    Return {statusCode: 200, body: {summary, s3_key}}
```

---

## Module Reference

### Core Application

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `main.py` | Entry point, DearCare class, sequential flow | `run()`, `_save_and_upload()`, `_health_consultation()`, `_collect_aadhaar()`, `_is_yes()` |
| `guided_flow.py` | Alternative 9-stage guided encounter flow | `run()` — Language → Wake → Aadhaar → Lookup → Inquiry → Rx → Pulse → Env → Analysis |
| `config.py` | All configuration constants, prompts, thresholds | 60+ constants, system prompts, intent keywords |

### AWS Integration

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `aws_handler.py` | Bedrock Nova Lite, S3, Lambda | `invoke_llm()`, `chat()`, `invoke_lambda()`, `extract_aadhaar_llm()`, `analyze_prescription()`, `analyze_health_summary()`, `upload_file()`, `test_connection()` |
| `fitu_client.py` | Fit-U mobile app DynamoDB/SNS | `fetch_latest_fitu_data()`, `notify_fitu_verdict_ready()`, `is_available()` |
| `sync_manager.py` | Background S3 sync + Lambda trigger | `start()`, `stop()`, `sync_now()`, background thread every 60s |
| `lambda/handler.py` | Cloud-side clinical notes generation | `handler()` — 3 actions: `health_summary`, `generate_notes`, `triage_review` |

### Voice & Language

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `voice_handler.py` | Polly TTS + Transcribe STT + audio I/O | `speak()`, `listen()`, `text_to_speech()`, `speech_to_text()`, `record_audio()`, `play_audio()`, `listen_for_wake_word()` |
| `language_handler.py` | 7-language support with Polly/Transcribe mapping | `set_language()`, `get_polly_voice()`, `get_transcribe_lang_code()`, `detect_language_from_text()` |
| `intent_handler.py` | Intent classification (Bedrock + keyword fallback) | `classify()` → returns `(Intent, confidence)` |

### Sensors & Camera

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `sensor_handler.py` | MAX30102 + BMP280 I2C drivers | `SensorHandler.detect_sensors()`, `read_vitals(duration)` |
| `camera_handler.py` | SC230AI MIPI camera capture | `check_camera_available()`, RAW10 decode, Bayer demosaic |
| `ocr_handler.py` | Document OCR (Textract + PaddleOCR) | `extract_text(image_path, prefer_online=True)` |

### Data Management

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `encounter_manager.py` | Encounter lifecycle + state machine | `start()`, `end()`, `set_demographics()`, `set_vitals()`, `run_triage()`, `save_photo()` |
| `storage_manager.py` | Local CSV database + Aadhaar lookup | `create_encounter()`, `update_encounter()`, `find_by_aadhaar()`, `get_pending_encounters()` |
| `triage_engine.py` | On-device rule-based triage | URGENT/ROUTINE classification from vitals |
| `security.py` | PIN authentication + AES-256 encryption | PIN hash verification, data encryption |
| `utils.py` | Logging, memory management, helpers | `check_internet()`, `free_memory()`, `setup_logging()`, `generate_encounter_id()` |

### Intent Types

The intent classifier recognizes 14 intents:

| Intent | Trigger Examples |
|--------|-----------------|
| `START_ENCOUNTER` | "start checkup", "new patient" |
| `CAPTURE_IMAGE` | "take picture", "scan prescription" |
| `MEASURE_VITALS` | "check pulse", "measure oxygen" |
| `RECORD_AUDIO` | "record cough", "audio note" |
| `CONFIRM` | "yes", "haan", "okay" |
| `DENY` | "no", "nahi", "cancel" |
| `HEALTH_QUESTION` | "what is diabetes", health queries |
| `SET_LANGUAGE` | "speak Hindi", "change language" |
| `SYNC_DATA` | "sync data", "upload" |
| `HELP` | "help", "what can you do" |
| `EXIT` | "goodbye", "stop" |
| `GREETING` | "hello", "namaste" |
| `THANKS` | "thank you", "dhanyavaad" |
| `UNKNOWN` | Unrecognized commands |

---

## Configuration Reference

### Bedrock LLM

| Constant | Value |
|----------|-------|
| `BEDROCK_MODEL_ID` | `amazon.nova-2-lite-v1:0` |
| `BEDROCK_MAX_TOKENS` | `512` |
| `BEDROCK_TEMPERATURE` | `0.7` |

### Audio

| Constant | Value |
|----------|-------|
| `AUDIO_SAMPLE_RATE` | `16000` Hz |
| `AUDIO_CHANNELS` | `1` (mono) |
| `AUDIO_FORMAT` | `S16_LE` |
| `DEFAULT_RECORD_DURATION` | `7` sec |
| `WAKE_WORD_LISTEN_DURATION` | `5` sec |

### Polly TTS

| Constant | Value |
|----------|-------|
| `POLLY_VOICE_ID` | `Kajal` (default Hindi) |
| `POLLY_ENGINE` | `neural` |
| `POLLY_OUTPUT_FORMAT` | `pcm` |
| `POLLY_SAMPLE_RATE` | `16000` |

### Camera

| Constant | Value |
|----------|-------|
| `CAMERA_SENSOR_INDEX` | `6` |
| `CAMERA_WIDTH × HEIGHT` | `1920 × 1080` |
| `CAMERA_FPS` | `30` |

### Wake Words

- Assistant name: **Kamal**
- Wake words: `kamal`, `dear care`, `dear-care`
- Wake phrases: `hello kamal`, `ok kamal`, `hey kamal`, `hi kamal` (+ variations)

### Data Retention

| Constant | Value |
|----------|-------|
| `DATA_RETENTION_DAYS` | `30` |
| `MAX_OFFLINE_ENCOUNTERS` | `100` |

### CSV Schema (encounters.csv)

```
encounter_id, timestamp, worker_id, patient_id, aadhaar_number, patient_name,
age, gender, spo2, heart_rate, temperature, triage_level, triage_confidence,
sync_status, photo_count, audio_count, notes
```

---

## Quick Start

### Prerequisites

- D-Robotics RDK S100 V1P0 (or any ARM64 Linux board)
- Python 3.12+
- AWS account with Bedrock, S3, Lambda, Polly, Transcribe access
- MAX30102 + BMP280 sensors on I2C Bus 5 (optional)
- USB microphone + Bluetooth speaker (optional — text mode available)

### Installation

```bash
git clone https://github.com/DevDaring/Nova_Dear-Care.git
cd Nova_Dear-Care

# Create virtual environment
python3 -m venv .venv312
source .venv312/bin/activate

# Install dependencies
pip install -r Code/requirements.txt

# Configure AWS credentials
cd Code && cp env.template .env && nano .env
```

### Run Dear-Care (Voice Mode)

```bash
cd Code
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
```

### Run Dear-Care (Text-Only Mode)

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
```

### Run Guided Encounter Flow

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --guided
```

### Test Full Pipeline (No Voice/Sensors Needed)

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 test_pipeline.py
```

This creates a dummy encounter with a test Aadhaar, uploads to S3, invokes all 3 Lambda actions, speaks the health summary, and sends an SNS notification to the mobile app.

---

## Environment Variables

Create `Code/.env` from `Code/env.template`:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# S3
S3_BUCKET_NAME=dear-care-data-<account_id>

# Bedrock
BEDROCK_MODEL_ID=amazon.nova-2-lite-v1:0

# Lambda
LAMBDA_FUNCTION_NAME=dear-care-clinical-notes

# Audio (Bluetooth speaker sink name)
BOSE_SINK_NAME=bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink

# Fit-U Mobile App Integration
FITU_API_GATEWAY_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/fitu-health
FITU_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:<account_id>:dear-care-fitu-notifications
FITU_DYNAMODB_TABLE=dear-care-fitu-health

# Security
DEARCARE_PIN_HASH=<bcrypt_hash>
```

---

## Project Structure

```
Nova_Dear-Care/
├── Code/
│   ├── main.py                  # Entry point + DearCare class + sequential flow
│   ├── guided_flow.py           # Alternative 9-stage guided encounter flow
│   ├── aws_handler.py           # Bedrock Nova Lite, S3, Lambda integration
│   ├── voice_handler.py         # Polly Neural TTS + Transcribe Streaming STT
│   ├── intent_handler.py        # Bedrock + keyword intent classification
│   ├── language_handler.py      # 7 languages, Polly Neural voice mapping
│   ├── encounter_manager.py     # Patient encounter lifecycle + state machine
│   ├── storage_manager.py       # Local CSV database + Aadhaar lookup
│   ├── sync_manager.py          # Background S3 sync + Lambda trigger
│   ├── fitu_client.py           # Fit-U mobile app DynamoDB/SNS integration
│   ├── triage_engine.py         # On-device rule-based triage engine
│   ├── sensor_handler.py        # MAX30102 + BMP280 I2C sensor drivers
│   ├── camera_handler.py        # SC230AI MIPI camera RAW10 capture
│   ├── ocr_handler.py           # Amazon Textract + PaddleOCR
│   ├── security.py              # PIN authentication + AES-256 encryption
│   ├── config.py                # All constants, prompts, thresholds
│   ├── utils.py                 # Logging, memory management, helpers
│   ├── test_pipeline.py         # End-to-end pipeline test script
│   ├── requirements.txt         # Python dependencies
│   ├── env.template             # Environment variable template
│   ├── deploy_lambda.sh         # Lambda deployment script
│   ├── Sensor_Setup_Guide.md    # Hardware setup documentation
│   ├── Sensors_Test/            # Hardware test scripts
│   ├── lambda/
│   │   └── handler.py           # Lambda: clinical notes via Nova Lite
│   ├── data/
│   │   └── encounters/          # Local encounter storage (CSV + JSON + photos)
│   ├── temp/                    # Temporary audio files
│   ├── logs/                    # Application logs
│   └── audio/                   # Audio recordings
├── flutter_app/                 # Fit-U companion Flutter app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── services/aws_sync_service.dart
│   │   ├── screens/settings_screen.dart
│   │   ├── env_config.dart      # Local secrets (gitignored)
│   │   └── env_config.template.dart
│   └── pubspec.yaml
├── System_Prompt.md             # System prompt documentation
├── README.md                    # This file
└── .env                         # AWS credentials (gitignored)
```

---

## Dependencies

### Python Packages (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `boto3` | ≥ 1.35.0 | AWS SDK (Bedrock, S3, Lambda, Polly, Transcribe, DynamoDB, SNS) |
| `amazon-transcribe` | ≥ 0.6.0 | Transcribe Streaming WebSocket SDK |
| `python-dotenv` | ≥ 1.0.0 | Environment variable loading |
| `numpy` | 1.26.4 | Numerical operations for sensor data + image processing |
| `opencv-python` | 4.6.0.66 | Camera capture + image processing |
| `paddlepaddle-xpu` | 2.6.1 | PaddleOCR inference engine (ARM64 XPU) |
| `paddleocr` | 2.7.0.3 | Offline OCR (Textract fallback) |
| `pyttsx3` | ≥ 2.90 | Offline TTS (Polly fallback) |
| `SpeechRecognition` | ≥ 3.10.0 | Offline STT (Transcribe fallback) |
| `PyAudio` | ≥ 0.2.14 | Audio I/O for SpeechRecognition |
| `cryptography` | ≥ 42.0.0 | AES-256 data encryption |
| `smbus2` | ≥ 0.4.0 | I2C sensor communication |
| `bme280` | ≥ 0.2.4 | BMP280 sensor driver |
| `Pillow` | ≥ 10.0.0 | Image processing |
| `requests` | ≥ 2.31.0 | HTTP requests |
| `Flask` | ≥ 3.0.0 | Local web interface (optional) |

### System Dependencies

- `arecord` / `parecord` — ALSA/PulseAudio audio recording
- `paplay` — PulseAudio audio playback
- `pulseaudio` — Audio routing (Bluetooth A2DP)
- `i2c-tools` — I2C device detection

---

## Security

- **PIN Authentication**: Optional PIN-based access control with bcrypt hash
- **AES-256 Encryption**: Patient data encrypted at rest
- **Aadhaar Masking**: Only first 4 and last 4 digits displayed (e.g., `1234 **** 9012`)
- **Data Retention**: Automatic cleanup after 30 days
- **Offline Limit**: Maximum 100 encounters stored locally before sync required
- **HTTPS Only**: All AWS communication over TLS
- **`.env` Gitignored**: Credentials never committed to repository

---

## Team & License

**Team DevDaring** — Built for the **AWS "AI for Bharat" Hackathon**

MIT License — All code is original work by Team DevDaring.
