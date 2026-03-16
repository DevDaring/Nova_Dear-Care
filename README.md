# Dear-Care — AI-Powered Healthcare Assistant

> **Amazon Nova Hackathon** | Team: DevDaring  
> Platform: D-Robotics RDK S100 V1P0 (Ubuntu 22.04, ARM64, 4GB RAM)

---

## Overview

**Dear-Care** is a portable, voice-activated AI healthcare assistant built for community health workers. Running on an edge AI device (RDK S100) with **Amazon Nova as the core intelligence layer**, it enables frontline health workers to:

- **Speak naturally** in English, Hindi, French, German, Italian, Spanish, and Portuguese
- **Consult interactively** — multi-turn health conversations powered by Amazon Nova Lite
- **Read prescriptions** via Amazon Textract + PaddleOCR
- **Measure vital signs** (SpO2, heart rate, temperature, pressure) with connected sensors
- **Get AI-powered clinical notes** via AWS Lambda + Amazon Nova Lite
- **Identify patients** through Aadhaar number collection and lookup
- **Send results to mobile app** via SNS push notifications to Fit-U companion app
- **Work fully offline** — every AWS service has a local fallback

---

## Amazon Nova Integration

| Nova Service | Usage in Dear-Care | Status |
|---|---|---|
| **Amazon Nova Lite** | Core reasoning engine — intent classification, prescription analysis, health consultation, clinical notes | Active |
| **Amazon Polly** (Neural) | Primary TTS engine (7 languages) | Active |
| **Amazon Transcribe** | Real-time streaming speech-to-text | Active |

### Voice Pipeline

```
User speaks → Jabra Mic → Amazon Transcribe (STT)
    → Nova Lite (intent + reasoning)
    → Amazon Polly Neural (TTS) / pyttsx3 (offline fallback)
    → Bose Bluetooth Speaker
```

### Consultation Mode

```
User speaks → Transcribe (STT) → Nova Lite (reason about patient context)
    → Polly (speak response) → repeat (up to 10 turns)
```

Amazon Nova Lite (`amazon.nova-lite-v1:0`) is the core reasoning engine for all
AI tasks: intent classification, Aadhaar extraction, prescription analysis, health
consultation, and clinical notes. Amazon Polly Neural provides TTS with fallback
to pyttsx3 offline. Amazon Transcribe Streaming handles real-time STT.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DEAR-CARE DEVICE                        │
│                      (RDK S100 ARM64)                        │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │ Voice I/O  │  │  Camera    │  │  Sensors               │ │
│  │ Jabra Mic  │  │  SC230AI   │  │  MAX30102 (SpO2/HR)    │ │
│  │ Bose BT    │  │  MIPI CSI  │  │  BMP280 (Temp/Humid)   │ │
│  └─────┬──────┘  └─────┬──────┘  └─────────┬──────────────┘ │
│        │               │                    │                │
│  ┌─────▼───────────────▼────────────────────▼──────────────┐ │
│  │              Python Application (17 modules)            │ │
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
│  │ Bedrock     │  │     S3      │  │     Lambda           │ │
│  │ Nova Lite   │  │ Encounters  │  │ Clinical Notes Gen   │ │
│  │ (Reasoning) │  │ + Results   │  │ Triage Review        │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │ Polly       │  │ Transcribe  │  │ API Gateway          │ │
│  │ Neural TTS  │  │ Streaming   │  │ Fit-U Mobile API     │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │ DynamoDB    │  │    SNS      │  │    Textract          │ │
│  │ Health Data │  │ Push Notify │  │ Prescription OCR     │ │
│  └─────────────┘  └─────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## AWS Services Used

| Service | Purpose | Fallback |
|---------|---------|----------|
| **Amazon Bedrock** (Nova Lite) | Core reasoning: intent, prescription analysis, health consultation, clinical notes | Keyword matching + rule-based triage |
| **Amazon Polly** (Neural) | Primary TTS for 7 languages | pyttsx3 offline |
| **Amazon Transcribe** Streaming | Real-time speech-to-text | SpeechRecognition offline |
| **Amazon Textract** | Prescription OCR | PaddleOCR 2.7.0 |
| **Amazon S3** | Encounter data + clinical notes storage | Local CSV + JSON |
| **AWS Lambda** | Cloud-based clinical notes generation | On-device triage only |
| **Amazon DynamoDB** | Fit-U health data + verdict storage | App continues without |
| **Amazon SNS** | Push notifications to Fit-U mobile app | App polls for verdicts |
| **API Gateway** | REST API for Fit-U Flutter app | App uses cached data |

> Every fallback event is logged with the reason for the switch.

---

## Healthcare Flow

```
Aadhaar Collection → Patient Lookup (CSV database)
    → Prescription Capture (optional, multi-document)
    → Pulse / SpO2 Sensor (MAX30102)
    → Environment Sensors (BMP280)
    → Save & Upload → AWS Lambda (clinical notes via Nova Lite)
    → Speak Lambda Results + Send to Mobile App (SNS)
    → Health Consultation (optional, Transcribe → Nova Lite → Polly)
    → Next Patient
```

---

## Hardware

| Component | Model | Interface |
|-----------|-------|-----------|
| Edge AI Board | D-Robotics RDK S100 V1P0 | ARM64, 4GB RAM |
| Camera | SC230AI | MIPI CSI |
| Microphone | Jabra EVOLVE 20 MS | USB (`plughw:1,0`) |
| Speaker | Bose SoundLink Micro | Bluetooth A2DP |
| Pulse Oximeter | MAX30102 | I2C Bus 5, 0x57 |
| Environment | BMP280 | I2C Bus 5, 0x76 |
| BT Dongle | TP-Link UB500 | USB |

---

## Fit-U Companion App (Flutter)

The **Fit-U** Flutter mobile app runs on the health worker's phone and syncs with Dear-Care:

- **Sends** step count, distance, speed, activity, GPS to DynamoDB via API Gateway
- **Receives** triage verdicts and health summaries from Dear-Care via DynamoDB polling + SNS push
- **Offline queue** with SQLite for areas with spotty connectivity
- **API Gateway URL**: Configured per-worker via `env_config.dart` (gitignored)

---

## Quick Start

```bash
git clone https://github.com/DevDaring/Nova_Dear-Care.git
cd Nova_Dear-Care

# Install Python dependencies
pip3 install -r Code/requirements.txt

# Configure AWS credentials
cd Code && cp env.template .env && nano .env

# Run Dear-Care
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
```

### Text-Only Mode (no mic/speaker)

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
```

---

## Project Structure

```
Nova_Dear-Care/
├── Code/
│   ├── main.py                  # Entry point + main loop
│   ├── guided_flow.py           # 9-stage guided healthcare flow
│   ├── encounter_manager.py     # Patient encounter lifecycle
│   ├── voice_handler.py         # TTS (Polly Neural) + STT (Transcribe)
│   ├── aws_handler.py           # Bedrock Nova Lite, S3, Lambda integration
│   ├── triage_engine.py         # On-device rule-based triage
│   ├── camera_handler.py        # SC230AI MIPI camera capture
│   ├── ocr_handler.py           # Textract + PaddleOCR
│   ├── sensor_handler.py        # MAX30102 + BMP280 I2C sensors
│   ├── intent_handler.py        # Bedrock + keyword intent classification
│   ├── language_handler.py      # 7 languages, Polly Neural voice mapping
│   ├── storage_manager.py       # Local CSV + JSON storage
│   ├── sync_manager.py          # S3 sync with Lambda trigger
│   ├── fitu_client.py           # Fit-U mobile app DynamoDB/SNS integration
│   ├── security.py              # PIN auth + AES-256 encryption
│   ├── config.py                # All configuration constants
│   ├── utils.py                 # Logging, memory management, helpers
│   ├── lambda/
│   │   └── handler.py           # Lambda: clinical notes via Bedrock
│   └── deploy_lambda.sh         # Lambda deployment script
├── flutter_app/                 # Fit-U companion Flutter app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── services/aws_sync_service.dart
│   │   ├── screens/settings_screen.dart
│   │   ├── env_config.dart      # Local secrets (gitignored)
│   │   └── env_config.template.dart
│   └── pubspec.yaml
├── .env                         # AWS credentials (gitignored)
└── README.md
```

---

## Environment Variables

Create `Code/.env` with:

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=dear-care-data-<account_id>
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
LAMBDA_FUNCTION_NAME=dear-care-clinical-notes
BOSE_SINK_NAME=bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
FITU_API_GATEWAY_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/fitu-health
FITU_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:account_id:dear-care-fitu-notifications
FITU_DYNAMODB_TABLE=dear-care-fitu-health
```

---

## Voice Interaction

Dear-Care uses a guided sequential flow. The assistant speaks prompts and the
health worker responds naturally. No wake word needed — each step is voice-guided:

| Step | Action |
|------|--------|
| 1 | Collect Aadhaar number (voice → Nova Lite extraction) |
| 2 | Patient lookup (existing record) or new registration |
| 3 | Prescription capture (optional, camera → Textract/PaddleOCR → Nova Lite analysis) |
| 4 | Pulse / SpO2 measurement (MAX30102 sensor) |
| 5 | Environment readings (BMP280 — temperature, pressure) |
| 6 | Save & upload → Lambda processes clinical notes → results spoken back + sent to mobile app |
| 7 | Health consultation (optional — Transcribe STT → Nova Lite reasoning → Polly TTS) |

---

## License

MIT License — DevDaring 2025

---

## Project Structure

```
AI_4_Bharat/
├── Code/                       # Main application
│   ├── main.py                 # Entry point + sequential healthcare flow
│   ├── guided_flow.py          # Guided encounter orchestrator
│   ├── aws_handler.py          # Bedrock Nova Lite, S3, Lambda, Textract
│   ├── intent_handler.py       # Bedrock LLM intent classifier
│   ├── voice_handler.py        # Polly Neural TTS + Transcribe STT
│   ├── ocr_handler.py          # Textract + PaddleOCR
│   ├── sensor_handler.py       # MAX30102 + BMP280 drivers
│   ├── camera_handler.py       # SC230AI MIPI capture
│   ├── encounter_manager.py    # Patient encounter state machine
│   ├── storage_manager.py      # CSV database + Aadhaar lookup
│   ├── language_handler.py     # 7 languages, Polly Neural voice mapping
│   ├── triage_engine.py        # Clinical triage engine
│   ├── config.py               # Configuration + prompts
│   ├── Sensor_Setup_Guide.md   # Hardware setup docs
│   └── Sensors_Test/           # Hardware test scripts
├── RDK_S100_Guide.md           # Board documentation
├── RDK_System_Info.md          # System specifications
└── Camera_Expansion_Guide.md   # Camera setup reference
```

---

## AWS Services Used

- **Amazon Bedrock** (Nova Lite v1:0) — Core reasoning: intent, Aadhaar extraction, health analysis, consultation, prescriptions
- **Amazon Polly** — Primary Neural TTS (7 languages)
- **Amazon Transcribe** — Real-time streaming STT
- **Amazon Textract** — Document OCR
- **Amazon S3** — Cloud storage for encounters
- **AWS Lambda** — Clinical notes generation via Nova Lite
- **AWS IAM** — Access control

---

## Team

**DevDaring** — AWS Hackathon: AI for Bharat

## License

Built for the **AWS "AI for Bharat" Hackathon**. All code is original work by Team DevDaring.
