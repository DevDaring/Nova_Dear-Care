# Pocket ASHA — AI-Powered Healthcare Assistant for Rural India

> **AWS Hackathon: AI for Bharat** | Team: DevDaring  
> Platform: D-Robotics RDK S100 (Ubuntu 22.04, ARM64)

---

## Problem Statement

India has over 1 million ASHA (Accredited Social Health Activist) workers serving rural communities with limited access to doctors, diagnostic tools, and connectivity. These frontline workers need a portable, intelligent assistant that:

- Works **offline-first** in areas with no internet
- Reads **prescriptions** in multiple Indian languages
- Measures **vital signs** (SpO2, heart rate, temperature)
- Performs **clinical triage** on-device
- Syncs data to the **cloud** when connectivity is available
- Supports **voice interaction** in local languages

**Pocket ASHA** solves this by running on an edge AI device (RDK S100) with AWS cloud services for enhanced capabilities when online.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      POCKET ASHA DEVICE                      │
│                     (RDK S100 Edge AI)                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐ │
│  │  Camera   │  │  Jabra   │  │ MAX30102  │  │  BME280    │ │
│  │  (MIPI)   │  │  Mic     │  │ SpO2/HR   │  │ Temp/Hum   │ │
│  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  └─────┬──────┘ │
│        │              │              │              │         │
│  ┌─────▼──────────────▼──────────────▼──────────────▼──────┐ │
│  │              Python Application Layer                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │ │
│  │  │  OCR     │ │  Intent  │ │  Triage  │ │  Encounter │ │ │
│  │  │PaddleOCR │ │ Handler  │ │  Engine  │ │  Manager   │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘ │ │
│  └──────────────────────┬──────────────────────────────────┘ │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │ (when online)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                      AWS CLOUD SERVICES                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Bedrock  │  │  Polly   │  │Transcribe│  │  Textract  │  │
│  │Nova Lite │  │  (TTS)   │  │  (STT)   │  │   (OCR)    │  │
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

### 1. Offline-First Healthcare Triage
- Rule-based clinical triage engine runs **entirely on-device** in under 10 seconds
- Classifies patients as **URGENT**, **FOLLOW_UP**, or **ROUTINE**
- Uses clinically validated thresholds (SpO2 < 94% → urgent, HR > 120 → urgent, Temp > 39.5°C → urgent)
- No internet required for life-saving assessments

### 2. Prescription & Document Reading (OCR)
- **Offline:** PaddleOCR (2.7.0) runs locally on the device
- **Online:** Amazon Textract for higher accuracy
- Auto-selects best available engine based on connectivity
- Extracts medicine names, dosages, and timing from prescriptions

### 3. Voice-First Interface
- Wake word activated: "Hello Asha", "Ok Asha", "Hey Asha"
- **Online TTS:** Amazon Polly (neural voice "Kajal" for Hindi/English)
- **Offline TTS:** pyttsx3 engine as fallback
- **Online STT:** Amazon Transcribe (en-IN)
- **Offline STT:** SpeechRecognition (Google free tier / CMU Sphinx)
- Supports **11 Indian languages**: English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi

### 4. Vital Signs Monitoring
- **MAX30102** pulse oximeter: SpO2 percentage and heart rate (BPM)
- **BME280** environmental sensor: Body temperature, humidity, pressure
- Graceful degradation — works without sensors, activates when connected
- 15-second measurement window with confidence scoring

### 5. AI-Powered Health Assistance
- Amazon Bedrock with **Nova Lite** model for health Q&A
- Prescription analysis and medicine extraction
- AI triage review via AWS Lambda
- Multi-turn conversational context with chat history

### 6. Patient Encounter Workflow
- Full state machine: Demographics → Photo → Vitals → Audio → Triage → OCR → Review → Complete
- Steps are **skippable** — flexible workflow for field conditions
- Per-encounter folders with photos, audio recordings, and clinical data
- CSV database + JSON encounter files for local storage

### 7. Cloud Sync & Clinical Notes
- Background sync thread (60-second intervals)
- Uploads complete encounter data to **Amazon S3**
- **AWS Lambda** generates structured clinical notes via Bedrock
- Handles intermittent connectivity gracefully

### 8. Security & Privacy
- PIN-based authentication (SHA-256 with salt)
- AES-256-GCM encryption for patient data files
- 30-day data retention policy with automatic cleanup
- Maximum 100 offline encounters limit
- All credentials in `.env` file (not in code)

---

## AWS Services Used

| Service | Purpose | Online/Offline |
|---------|---------|---------------|
| **Amazon Bedrock** (Nova Lite v1:0) | LLM for health Q&A, prescription analysis, triage assessment | Online only |
| **Amazon Polly** | Text-to-Speech in Indian languages (neural voice "Kajal") | Online (pyttsx3 offline fallback) |
| **Amazon Transcribe** | Speech-to-Text in Indian English (en-IN) | Online (SpeechRecognition offline fallback) |
| **Amazon Textract** | High-accuracy document OCR | Online (PaddleOCR offline fallback) |
| **Amazon S3** | Cloud storage for encounter data, photos, audio, clinical notes | Online (local CSV offline) |
| **AWS Lambda** | Serverless clinical notes generation and triage review | Online only |
| **AWS IAM** | Role-based access control for Lambda execution | Infrastructure |

---

## AI & ML Technologies

| Technology | Usage | Runs On |
|------------|-------|---------|
| **Amazon Nova Lite** (Bedrock) | Conversational health assistant, prescription analysis, medicine extraction, triage assessment | Cloud |
| **PaddleOCR 2.7.0** | Offline text extraction from prescriptions and medical documents | Device (CPU) |
| **PaddlePaddle XPU 2.6.1** | Deep learning inference engine for OCR models | Device |
| **Custom Triage Engine** | Rule-based clinical assessment using vital sign thresholds | Device |
| **Intent Classifier** | Keyword-based NLU with 14 intent categories | Device |
| **pyttsx3** | Offline text-to-speech synthesis | Device |
| **SpeechRecognition** | Offline/free speech-to-text | Device |

---

## Hardware Requirements

| Component | Model | Connection | Purpose |
|-----------|-------|-----------|---------|
| **Edge AI Board** | D-Robotics RDK S100 | — | Main compute (ARM64, 4GB+ RAM) |
| **Camera** | MIPI Stereo Camera | MIPI CSI | Prescription/document capture |
| **Microphone** | Jabra USB Speakerphone | USB (hw:1,0) | Voice input |
| **Speaker** | Bose Bluetooth Speaker | Bluetooth A2DP | Voice output |
| **Pulse Oximeter** | MAX30102 | I2C Bus 1, Addr 0x57 | SpO2 and heart rate |
| **Environment Sensor** | BME280 | I2C Bus 1, Addr 0x76 | Temperature, humidity, pressure |

> **Note:** The system works without sensors — they activate automatically when connected.

---

## Project Structure

```
Code/
├── main.py                 # Entry point — PocketAsha class, main loop
├── config.py               # Central configuration, .env loading, constants
├── utils.py                # Logging, connectivity check, memory management
├── security.py             # PIN authentication, AES-256 encryption
├── storage_manager.py      # CSV database, encounter folders, cleanup
├── sensor_handler.py       # MAX30102 + BME280 I2C sensor drivers
├── camera_handler.py       # MIPI stereo camera capture (hobot_vio)
├── language_handler.py     # 11 Indian language mappings for Polly/Transcribe
├── voice_handler.py        # Audio recording, Polly TTS, Transcribe STT
├── intent_handler.py       # 14-intent keyword classifier
├── ocr_handler.py          # PaddleOCR (offline) + Textract (online)
├── aws_handler.py          # Bedrock LLM, S3, Lambda integration
├── triage_engine.py        # Rule-based clinical triage (offline)
├── encounter_manager.py    # Patient encounter state machine
├── sync_manager.py         # Background S3 sync thread
├── requirements.txt        # Python dependencies
├── env.template            # .env file template
├── deploy_lambda.sh        # Lambda deployment script (AWS CLI)
├── .env                    # Credentials (not committed)
├── lambda/
│   └── handler.py          # AWS Lambda function for clinical notes
├── Sensors_Test/
│   └── test_all_sensors.py # Hardware diagnostic tool
├── data/
│   └── encounters/         # Local encounter storage (auto-created)
├── temp/                   # Temporary files (auto-created)
├── audio/                  # Audio recordings (auto-created)
└── logs/                   # Application logs (auto-created)
```

---

## Quick Start Guide

### Prerequisites
- RDK S100 board running Ubuntu 22.04 (ARM64)
- Python 3.10+
- AWS account with Bedrock, Polly, Transcribe, S3, Lambda access
- Jabra USB microphone connected
- Bose Bluetooth speaker paired

### Step 1: Clone the Repository

```bash
git clone https://github.com/DevDaring/AI_4_Bharat.git
cd AI_4_Bharat
```

### Step 2: Install Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y python3-pip python3-dev portaudio19-dev \
    libasound2-dev libpulse-dev i2c-tools fonts-freefont-ttf

# Python packages (system-wide, no venv)
pip3 install -r Code/requirements.txt

# Pin critical versions for ARM64 compatibility
pip3 install numpy==1.26.4 opencv-python==4.6.0.66
```

### Step 3: Configure AWS

```bash
# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)

# Create S3 bucket
aws s3 mb s3://pocket-asha-data-YOUR_ACCOUNT_ID --region us-east-1
```

### Step 4: Set Up Environment

```bash
cd Code
cp env.template .env
# Edit .env with your actual credentials:
nano .env
```

Fill in:
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`
- `S3_BUCKET_NAME` (e.g., `pocket-asha-data-123456789012`)
- `BOSE_SINK` — find with: `pactl list sinks short | grep bluez`

### Step 5: Deploy Lambda Function

```bash
bash deploy_lambda.sh
```

This automatically:
1. Creates IAM role with S3 + Bedrock + Lambda permissions
2. Packages and deploys the clinical notes Lambda function
3. Runs a test invocation

### Step 6: Test Hardware (Optional)

```bash
cd Code
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 Sensors_Test/test_all_sensors.py
```

This checks all sensors, camera, microphone, speaker, and AWS connectivity.

### Step 7: Run Pocket ASHA

```bash
cd ~/Documents/AI_4_Bharat/Code
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
```

> **Note:** The MIPI camera is accessed directly via `hobot_vio` (libsrcampy) — no separate camera launch step needed. Just ensure the MIPI cable is connected.

**Text-only mode** (no microphone/speaker needed):
```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
```

> **Important:** The `env -u LD_LIBRARY_PATH -u LD_PRELOAD` prefix is required on RDK S100 to avoid conflicts between Hobot system libraries and PaddlePaddle.

---

## Usage Guide

### Voice Commands

| Say This | What Happens |
|----------|-------------|
| "Hello Asha, start new patient" | Begins a patient encounter |
| "Hello Asha, take a picture" | Captures prescription/document photo |
| "Hello Asha, read my prescription" | Captures + OCR + AI analysis |
| "Hello Asha, check my vitals" | Measures SpO2, heart rate, temperature |
| "Hello Asha, record cough" | Records symptom audio |
| "Hello Asha, I have a headache" | AI health consultation |
| "Hello Asha, sync data" | Uploads pending encounters to cloud |
| "Hello Asha, change language to Hindi" | Switches voice language |
| "Hello Asha, help" | Lists available commands |
| "Hello Asha, goodbye" | Ends session |

### Patient Encounter Workflow

```
1. "Start new patient"
   └─→ Asha asks for name, age, gender

2. "Take a picture" (of prescription)
   └─→ Captures photo, runs OCR, analyzes medicines

3. "Check vitals"
   └─→ Reads SpO2, heart rate, temperature from sensors

4. "Record cough"
   └─→ Records 10-second audio sample

5. Automatic triage assessment
   └─→ URGENT / FOLLOW_UP / ROUTINE classification

6. "Yes" to confirm and save
   └─→ Encounter stored locally, queued for sync

7. "Sync data" (when internet available)
   └─→ Uploads to S3, Lambda generates clinical notes
```

### Text Input Mode

When running with `--text`, type commands directly at the prompt. All voice commands work as text input too. Text input always takes priority over voice when both are available.

---

## Offline vs Online Capabilities

| Feature | Offline | Online |
|---------|---------|--------|
| Wake word detection | Local keyword match | Same |
| Intent classification | Keyword scoring | Same |
| OCR (prescription reading) | PaddleOCR | Amazon Textract |
| Text-to-Speech | pyttsx3 | Amazon Polly (neural) |
| Speech-to-Text | SpeechRecognition | Amazon Transcribe |
| Clinical triage | Rule-based engine | Same + AI review |
| Health Q&A | Not available | Amazon Bedrock (Nova Lite) |
| Patient data storage | Local CSV + JSON | S3 cloud sync |
| Clinical notes | Not available | Lambda + Bedrock |
| Vital signs | Same (on-device) | Same |
| Camera capture | Same (on-device) | Same |

> All critical features (triage, vitals, OCR, recording) work **completely offline**. Cloud services enhance accuracy and add AI capabilities when available.

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
| Bengali | bn | Aditi | Standard | bn-IN |
| Tamil | ta | Aditi | Standard | ta-IN |
| Telugu | te | Aditi | Standard | te-IN |
| Marathi | mr | Aditi | Standard | mr-IN |
| Gujarati | gu | Aditi | Standard | gu-IN |
| Kannada | kn | Aditi | Standard | kn-IN |
| Malayalam | ml | Aditi | Standard | ml-IN |
| Odia | or | Aditi | Standard | or-IN |
| Punjabi | pa | Aditi | Standard | pa-IN |

---

## Security Measures

- **PIN Authentication:** SHA-256 hashed with random salt, stored in `.env`
- **Data Encryption:** AES-256-GCM via `cryptography` library for patient files
- **Credential Isolation:** All secrets in `.env` file, excluded from Git via `.gitignore`
- **Data Retention:** Automatic cleanup of encounters older than 30 days
- **Capacity Limits:** Maximum 100 offline encounters to prevent storage overflow
- **No Service Disruption:** All security features are additive — authentication failure does not crash any service or prevent emergency use
- **AWS IAM:** Least-privilege role for Lambda with only S3, Bedrock, and CloudWatch access
- **No Hardcoded Secrets:** All API keys, tokens, and passwords loaded from environment variables

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| PaddleOCR crashes with `SIGSEGV` | Use `env -u LD_LIBRARY_PATH -u LD_PRELOAD` prefix |
| "Jabra not found" | Check USB connection: `arecord -l` |
| "Bluetooth speaker not found" | Re-pair: `bluetoothctl connect XX:XX:XX:XX:XX:XX` |
| Camera not available | Check MIPI cable connection; run sensor diagnostic |
| "No internet" but WiFi connected | Check DNS: `ping s3.amazonaws.com` |
| Sensors not detected | Check I2C: `sudo i2cdetect -y 1` |
| NumPy version error | Re-pin: `pip3 install numpy==1.26.4` |
| Bedrock access denied | Enable Nova Lite model access in AWS Console → Bedrock → Model access |
| Lambda deployment fails | Check AWS CLI config: `aws sts get-caller-identity` |
| Out of memory | Close other apps; OCR auto-unloads after use |

---

## Development

### Adding a New Sensor

1. Create a class in `sensor_handler.py` with `connect()`, `read()`, `close()` methods
2. Add I2C address to `config.py`
3. Update `SensorHandler.detect_sensors()` and `read_all()`
4. Add test in `Sensors_Test/test_all_sensors.py`

### Adding a New Language

1. Add language entry to `LANGUAGES` dict in `language_handler.py`
2. Add keyword to `LANGUAGE_KEYWORDS` in `config.py`

### Adding a New Intent

1. Add value to `Intent` enum in `intent_handler.py`
2. Add keywords list to `config.py`
3. Add to `_KEYWORD_MAP` in `intent_handler.py`
4. Handle in `process_command()` in `main.py`

---

## API / Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS IAM secret key |
| `AWS_REGION` | Yes | AWS region (default: `us-east-1`) |
| `AWS_ACCOUNT_ID` | Yes | 12-digit AWS account number |
| `S3_BUCKET_NAME` | Yes | S3 bucket for data sync |
| `LAMBDA_FUNCTION_NAME` | No | Lambda function name (default: `pocket-asha-clinical-notes`) |
| `BOSE_SINK` | No | PulseAudio Bluetooth sink name |
| `ASHA_PIN_HASH` | No | Pre-set PIN hash for authentication |
| `AWS_BEARER_TOKEN_BEDROCK` | No | Bearer token for Bedrock access |

---

## Team

**DevDaring** — AWS Hackathon: AI for Bharat

---

## License

This project was built for the **AWS "AI for Bharat" Hackathon**. All code is original work by Team DevDaring.
