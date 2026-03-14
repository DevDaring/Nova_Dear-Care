# Pocket ASHA — AI-Powered Healthcare Assistant for Rural India

> **AWS Hackathon: AI for Bharat** | Team: DevDaring  
> Platform: D-Robotics RDK S100 V1P0 (Ubuntu 22.04.5, ARM64, 4GB RAM)

---

## Problem Statement

India has over 1 million ASHA (Accredited Social Health Activist) workers serving rural communities with limited access to doctors, diagnostic tools, and connectivity. These frontline workers need a portable, intelligent assistant that:

- Reads **prescriptions** in multiple Indian languages
- Measures **vital signs** (SpO2, heart rate, temperature)
- Performs **clinical triage** using AI
- Supports **voice interaction** in local languages (English, Hindi, Bengali)
- Uses **Aadhaar-based** patient identification for continuity of care
- Syncs data to the **cloud** when connectivity is available
- Falls back to **offline** operation when internet is unavailable

**Pocket ASHA** solves this by running on an edge AI device (RDK S100) with **AWS services as the primary intelligence layer** and offline fallbacks for every capability.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      POCKET ASHA DEVICE                      │
│              RDK S100 V1P0 (ARM64, Ubuntu 22.04)             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐ │
│  │ SC230AI  │  │  Jabra   │  │ MAX30102  │  │  BMP280    │ │
│  │  Camera  │  │EVOLVE 20 │  │ SpO2/HR   │  │ Temp/Press │ │
│  │  (MIPI)  │  │ (USB)    │  │ (I2C:5)   │  │ (I2C:5)    │ │
│  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  └─────┬──────┘ │
│        │              │              │              │         │
│  ┌─────▼──────────────▼──────────────▼──────────────▼──────┐ │
│  │             Guided Flow Orchestrator                     │ │
│  │                                                          │ │
│  │  Language → Wake Word → Aadhaar → Health Inquiry →      │ │
│  │  Prescription Loop → Pulse Sensor → Environment →       │ │
│  │  AI Analysis → Save & Next Patient                      │ │
│  │                                                          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │ │
│  │  │  OCR     │ │  Intent  │ │  Triage  │ │  Encounter │ │ │
│  │  │Textract+ │ │ Bedrock+ │ │  Engine  │ │  Manager   │ │ │
│  │  │PaddleOCR │ │ Keywords │ │          │ │ (Aadhaar)  │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘ │ │
│  └──────────────────────┬──────────────────────────────────┘ │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │ AWS Primary (offline fallback)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   AWS CLOUD SERVICES                         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Bedrock  │  │  Polly   │  │Transcribe│  │  Textract  │  │
│  │Nova Lite │  │  Kajal   │  │  (STT)   │  │   (OCR)    │  │
│  │ (LLM)   │  │  Neural  │  │  en/hi/bn│  │            │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                 │
│  │    S3    │  │  Lambda  │                                  │
│  │ Storage  │  │  Notes   │                                  │
│  └──────────┘  └──────────┘                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. AWS-First Intelligence Layer
- **Amazon Bedrock Nova Lite** powers ALL AI tasks: intent classification, Aadhaar extraction from speech, health analysis, prescription analysis, patient triage
- Every AWS call has an **offline fallback** (keyword matching, regex, PaddleOCR, pyttsx3, SpeechRecognition)
- Every fallback event is **logged** with the reason (e.g., `[INTENT] FALLBACK: keyword matching — Bedrock unavailable: no internet`)

### 2. Guided Healthcare Flow
- **Structured encounter** — not freeform commands  
- Flow: **Language Selection** → **Wake Word** → **Aadhaar Collection** → **Patient Lookup** → **Health Inquiry** → **Prescription Capture Loop** → **Pulse Reading** → **Environment Sensors** → **Final AI Analysis** → **Save & Next Patient**
- Aadhaar-based patient registry using CSV database for continuity of care

### 3. Prescription & Document Reading (OCR)
- **Primary:** Amazon Textract — high-accuracy cloud OCR
- **Fallback:** PaddleOCR 2.7.0 — runs locally on device
- Bedrock Nova Lite analyzes extracted text: medicine names, dosages, timing, key findings
- Prescription capture loop — scan multiple pages until patient says "no more"

### 4. Voice-First Interface
- Wake word activated: **"Hello Asha"**, **"Ok Asha"**, **"Hey Asha"**, or just **"Asha"**
- **Primary TTS:** Amazon Polly (neural voice "Kajal" — supports English & Hindi)
- **Fallback TTS:** pyttsx3 offline engine
- **Primary STT:** Amazon Transcribe (en-IN, hi-IN, bn-IN)
- **Fallback STT:** SpeechRecognition (Google free tier)
- Supports **English**, **Hindi**, and **Bengali** for the guided flow

### 5. Vital Signs Monitoring
- **MAX30102** pulse oximeter on I2C Bus 5, Addr 0x57: SpO2 % and heart rate (BPM)
- **BMP280** environmental sensor on I2C Bus 5, Addr 0x76: ambient temperature and barometric pressure
- 3-attempt retry for pulse sensor with voice prompts ("Place your finger on the sensor")
- 15-second measurement window with confidence scoring

### 6. AI Health Analysis
- **Final consolidated analysis** via Bedrock Nova Lite combining: symptoms, prescription data, vital signs, and environmental data
- Per-encounter AI triage assessment: URGENT / FOLLOW_UP / ROUTINE
- Medicine extraction returned as structured JSON
- Conversational health Q&A with chat history

### 7. Patient Encounter Workflow
- Aadhaar-based patient identification (12-digit Verhoeff validation)
- CSV database with per-encounter folders for photos, audio, and clinical data
- State machine: IDLE → DEMOGRAPHICS → PHOTO → VITALS → AUDIO → TRIAGE → OCR → REVIEW → COMPLETE
- Steps are **skippable** for flexible field conditions

### 8. Cloud Sync & Clinical Notes
- Background sync thread (60-second intervals)
- Uploads complete encounter data to **Amazon S3**
- **AWS Lambda** generates structured clinical notes via Bedrock
- Handles intermittent connectivity gracefully

### 9. Security & Privacy
- PIN-based authentication (SHA-256 with salt)
- AES-256-GCM encryption for patient data files
- 30-day data retention policy with automatic cleanup
- Maximum 100 offline encounters limit
- All credentials in `.env` file (not in code)

---

## AWS Services Used

| Service | Purpose | Fallback |
|---------|---------|----------|
| **Amazon Bedrock** (Nova Lite v1:0) | Intent classification, Aadhaar extraction, health Q&A, prescription analysis, triage, final analysis | Keyword matching (intent), regex (Aadhaar) |
| **Amazon Polly** (Kajal neural) | Text-to-Speech in English (en-IN) and Hindi (hi-IN) | pyttsx3 offline engine |
| **Amazon Transcribe** | Speech-to-Text in en-IN, hi-IN, bn-IN | SpeechRecognition (Google free tier) |
| **Amazon Textract** | High-accuracy document/prescription OCR | PaddleOCR 2.7.0 (on-device) |
| **Amazon S3** | Cloud storage for encounters, photos, audio, clinical notes | Local CSV + JSON files |
| **AWS Lambda** | Serverless clinical notes generation | Not applicable (online only) |
| **AWS IAM** | Role-based access control for all services | Not applicable |

> **Design Principle:** AWS is **always tried first**. If it fails, the fallback is used and the event is logged.

---

## AI & ML Technologies

| Technology | Usage | Runs On | Role |
|------------|-------|---------|------|
| **Amazon Nova Lite** (Bedrock) | Intent classification, Aadhaar extraction, health Q&A, prescription analysis, consolidated health analysis | Cloud | **Primary** |
| **Amazon Textract** | Prescription and document OCR | Cloud | **Primary** |
| **PaddleOCR 2.7.0** | Offline text extraction from prescriptions | Device (CPU) | **Fallback** |
| **PaddlePaddle XPU 2.6.1** | Deep learning inference engine for OCR | Device | **Fallback** |
| **Custom Triage Engine** | Rule-based clinical assessment using vital sign thresholds | Device | Offline safety net |
| **pyttsx3** | Offline text-to-speech synthesis | Device | **Fallback** |
| **SpeechRecognition** | Offline/free speech-to-text | Device | **Fallback** |

---

## Hardware

| Component | Model | Connection | Purpose |
|-----------|-------|-----------|---------|
| **Edge AI Board** | D-Robotics RDK S100 V1P0 | — | Main compute (ARM64, 4GB RAM, Ubuntu 22.04) |
| **Camera** | SC230AI MIPI Camera | MIPI CSI (sensor index 6) | Prescription/document capture |
| **Headset** | Jabra EVOLVE 20 MS | USB (ALSA card 1, `plughw:1,0`) | Microphone + Speaker (bidirectional audio) |
| **Pulse Oximeter** | MAX30102 | I2C Bus 5, Addr 0x57 | SpO2 and heart rate measurement |
| **Environment Sensor** | BMP280 (chip ID 0x58) | I2C Bus 5, Addr 0x76 | Ambient temperature and barometric pressure |

> **Note:** The system works without sensors — they activate automatically when connected.  
> **Note:** BMP280 is used (not BME280) — humidity reads 0% and is excluded from measurements.

---

## Project Structure

```
AI_4_Bharat/
├── Code/
│   ├── main.py                 # Entry point — PocketAsha class, GuidedFlow launcher
│   ├── guided_flow.py          # Guided healthcare encounter orchestrator
│   ├── config.py               # Central config, prompts, CSV schema, .env loading
│   ├── utils.py                # Logging, connectivity check, memory management
│   ├── security.py             # PIN authentication, AES-256 encryption
│   ├── storage_manager.py      # CSV database, encounter folders, Aadhaar lookup
│   ├── sensor_handler.py       # MAX30102 + BMP280 I2C sensor drivers (Bus 5)
│   ├── camera_handler.py       # SC230AI MIPI camera capture (get_vin_data)
│   ├── language_handler.py     # Language mappings for Polly/Transcribe
│   ├── voice_handler.py        # Audio recording (Jabra), Polly TTS, Transcribe STT
│   ├── intent_handler.py       # Bedrock LLM intent classifier (keyword fallback)
│   ├── ocr_handler.py          # Textract (primary) + PaddleOCR (fallback)
│   ├── aws_handler.py          # Bedrock LLM, S3, Lambda, Textract integration
│   ├── triage_engine.py        # Rule-based clinical triage (offline)
│   ├── encounter_manager.py    # Patient encounter state machine (with Aadhaar)
│   ├── sync_manager.py         # Background S3 sync thread
│   ├── requirements.txt        # Python dependencies
│   ├── env.template            # .env file template
│   ├── deploy_lambda.sh        # Lambda deployment script (AWS CLI)
│   ├── .env                    # AWS credentials (not committed)
│   ├── Sensor_Setup_Guide.md   # Detailed hardware setup documentation
│   ├── lambda/
│   │   └── handler.py          # AWS Lambda function for clinical notes
│   ├── Sensors_Test/
│   │   ├── test_all_sensors.py     # Full hardware diagnostic
│   │   ├── test_pulse_sensor.py    # MAX30102 standalone test
│   │   └── test_temp_and_pulse.py  # Combined BMP280 + MAX30102 test
│   ├── data/
│   │   └── encounters/         # Local encounter storage + encounters.csv
│   ├── temp/                   # Temporary audio/image files (auto-created)
│   ├── audio/                  # Audio recordings (auto-created)
│   └── logs/                   # Application logs (auto-created)
├── RDK_S100_Guide.md           # Board documentation
├── RDK_System_Info.md          # System specifications
├── Camera_Expansion_Guide.md   # Camera setup reference
└── doc.md                      # UI flowchart (Mermaid)
```

---

## Guided Healthcare Flow

```
┌─────────────────────────────────────────────────────────┐
│                    POCKET ASHA FLOW                      │
│                                                         │
│  1. LANGUAGE SELECTION                                  │
│     "Press 1 for English, 2 for Hindi, 3 for Bengali"  │
│                       ▼                                 │
│  2. WAKE WORD DETECTION                                 │
│     Say "Hello Asha" / "Ok Asha" / "Hey Asha"          │
│                       ▼                                 │
│  3. AADHAAR COLLECTION                                  │
│     "Please tell me your 12-digit Aadhaar number"       │
│     → Bedrock extracts digits from speech               │
│     → Read back for confirmation                        │
│     → Verhoeff checksum validation                      │
│                       ▼                                 │
│  4. PATIENT LOOKUP                                      │
│     CSV search by Aadhaar → welcome back / new patient  │
│     New: collect name, age, gender                      │
│                       ▼                                 │
│  5. HEALTH INQUIRY                                      │
│     "What health problem are you facing today?"         │
│     → Store symptoms in encounter                       │
│                       ▼                                 │
│  6. PRESCRIPTION CAPTURE LOOP                           │
│     "Do you have a prescription to show?"               │
│     → Yes: Camera capture → Textract OCR → Bedrock      │
│       analysis → "Any more prescriptions?"              │
│     → No: proceed to sensors                            │
│                       ▼                                 │
│  7. PULSE READING (MAX30102)                            │
│     "Place your finger on the sensor"                   │
│     → 3 attempts max, 15s each                          │
│     → SpO2 % + Heart Rate BPM                          │
│                       ▼                                 │
│  8. ENVIRONMENT (BMP280)                                │
│     → Ambient temperature + barometric pressure         │
│                       ▼                                 │
│  9. FINAL AI ANALYSIS (Bedrock Nova Lite)               │
│     → Consolidated assessment: symptoms + vitals +      │
│       prescriptions + environment data                  │
│     → Triage classification + recommendations           │
│                       ▼                                 │
│  10. SAVE & NEXT PATIENT                                │
│      → Save encounter (CSV + JSON + media files)        │
│      → Speak summary → return to Step 2 (wake word)     │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- RDK S100 V1P0 board running Ubuntu 22.04 (ARM64)
- Python 3.10+
- AWS account with Bedrock (Nova Lite enabled), Polly, Transcribe, Textract, S3, Lambda access
- Jabra EVOLVE 20 MS USB headset connected

### Step 1: Clone & Install

```bash
git clone https://github.com/DevDaring/AI_4_Bharat.git
cd AI_4_Bharat

# System packages
sudo apt update
sudo apt install -y python3-pip python3-dev portaudio19-dev \
    libasound2-dev libpulse-dev i2c-tools fonts-freefont-ttf

# Python packages
pip3 install -r Code/requirements.txt
pip3 install numpy==1.26.4 opencv-python==4.6.0.66
```

### Step 2: Configure AWS

```bash
cd Code
cp env.template .env
nano .env
```

Fill in:
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (default: `us-east-1`)
- `AWS_ACCOUNT_ID`
- `S3_BUCKET_NAME` (e.g., `dear-care-data-your_account_id`)

### Step 3: Deploy Lambda (Optional)

```bash
bash deploy_lambda.sh
```

### Step 4: Verify Hardware (Optional)

```bash
# Check I2C sensors on Bus 5
sudo i2cdetect -y -r 5
# Expected: 0x57 (MAX30102) and 0x76 (BMP280)

# Check Jabra headset
arecord -l
# Expected: card 1: Jabra EVOLVE 20 MS

# Run full diagnostic
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Sensors_Test/test_temp_and_pulse.py
```

### Step 5: Run Pocket ASHA

```bash
cd ~/Documents/AI_4_Bharat/Code
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
```

**Text-only mode** (no headset needed):
```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
```

> **Important:** The `env -u LD_LIBRARY_PATH -u LD_PRELOAD` prefix is required on RDK S100 to avoid conflicts between Hobot system libraries and PaddlePaddle.

---

## Offline vs Online Capabilities

| Feature | Online (AWS Primary) | Offline (Fallback) |
|---------|---------------------|-------------------|
| Intent classification | **Amazon Bedrock** Nova Lite | Keyword scoring |
| Aadhaar extraction | **Amazon Bedrock** Nova Lite | Regex pattern matching |
| OCR (prescriptions) | **Amazon Textract** | PaddleOCR (on-device) |
| Text-to-Speech | **Amazon Polly** (Kajal neural) | pyttsx3 |
| Speech-to-Text | **Amazon Transcribe** | SpeechRecognition |
| Health Q&A | **Amazon Bedrock** Nova Lite | Not available |
| Prescription analysis | **Amazon Bedrock** Nova Lite | OCR text only |
| Final health analysis | **Amazon Bedrock** Nova Lite | Rule-based triage |
| Clinical triage | **Amazon Bedrock** + rule engine | Rule-based engine |
| Patient data storage | **Amazon S3** cloud sync | Local CSV + JSON |
| Clinical notes | **AWS Lambda** + Bedrock | Not available |
| Vital signs | Same (on-device sensors) | Same |
| Camera capture | Same (on-device MIPI) | Same |

> **Design:** AWS is **always tried first**. Every fallback is **logged** with the failure reason.

---

## Clinical Triage Thresholds

| Vital Sign | Normal | Follow-Up | Urgent |
|-----------|--------|-----------|--------|
| SpO2 | ≥ 94% | 90–94% | < 90% |
| Heart Rate | 50–120 bpm | 40–50 or 120–150 | < 40 or > 150 |
| Temperature | 35–38.5°C | 38.5–39.5°C | ≥ 39.5°C or < 35°C |

Urgent symptom keywords: chest pain, breathing difficulty, unconscious, seizure, severe bleeding, collapsed, stroke

---

## Supported Languages

| Language | Code | Polly Voice | Engine | Transcribe |
|----------|------|-------------|--------|------------|
| English | en | Kajal | Neural | en-IN |
| Hindi | hi | Kajal | Neural | hi-IN |
| Bengali | bn | — (pyttsx3 fallback) | — | bn-IN |

---

## Security Measures

- **PIN Authentication:** SHA-256 hashed with random salt, stored in `.env`
- **Data Encryption:** AES-256-GCM via `cryptography` library for patient files
- **Credential Isolation:** All secrets in `.env` file, excluded from Git via `.gitignore`
- **Data Retention:** Automatic cleanup of encounters older than 30 days
- **Capacity Limits:** Maximum 100 offline encounters to prevent storage overflow
- **AWS IAM:** Least-privilege role for Lambda with only S3, Bedrock, and CloudWatch access
- **No Hardcoded Secrets:** All API keys, tokens, and passwords loaded from environment variables

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| PaddleOCR crashes with `SIGSEGV` | Use `env -u LD_LIBRARY_PATH -u LD_PRELOAD` prefix |
| "Jabra not found" | Check USB connection: `arecord -l` |
| Camera not available | Check MIPI cable; verify with `get_vin_data -s 6` |
| "No internet" but WiFi connected | Check DNS: `ping s3.amazonaws.com` |
| Sensors not detected | Check I2C Bus 5: `sudo i2cdetect -y -r 5` |
| NumPy version error | Re-pin: `pip3 install numpy==1.26.4` |
| Bedrock access denied | Enable Nova Lite model in AWS Console → Bedrock → Model access |
| Lambda deployment fails | Check AWS CLI: `aws sts get-caller-identity` |
| Out of memory | Close other apps; OCR auto-unloads after use |
| BMP280 humidity reads 0% | Expected — BMP280 has no humidity sensor (only temp+pressure) |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS IAM secret key |
| `AWS_REGION` | Yes | AWS region (default: `us-east-1`) |
| `AWS_ACCOUNT_ID` | Yes | 12-digit AWS account number |
| `S3_BUCKET_NAME` | Yes | S3 bucket for data sync |
| `LAMBDA_FUNCTION_NAME` | No | Lambda function name (default: `pocket-asha-clinical-notes`) |
| `ASHA_PIN_HASH` | No | Pre-set PIN hash for authentication |
| `AWS_BEARER_TOKEN_BEDROCK` | No | Bearer token for Bedrock access |

---

## Team

**DevDaring** — AWS Hackathon: AI for Bharat

---

## License

This project was built for the **AWS "AI for Bharat" Hackathon**. All code is original work by Team DevDaring.
