# Pocket ASHA — AI-Powered Healthcare Assistant for Rural India

> **AWS Hackathon: AI for Bharat** | Team: DevDaring  
> Platform: D-Robotics RDK S100 V1P0 (Ubuntu 22.04.5, ARM64, 4GB RAM)

---

## What is Pocket ASHA?

**Pocket ASHA** is a portable, voice-activated AI healthcare assistant built for India's 1 million+ ASHA (Accredited Social Health Activist) workers. Running on an edge AI device with **AWS services as the primary intelligence layer**, it enables frontline health workers to:

- **Read prescriptions** using Amazon Textract + PaddleOCR
- **Measure vital signs** (SpO2, heart rate, temperature) via connected sensors
- **Identify patients** through Aadhaar number collection and lookup
- **Get AI health analysis** powered by Amazon Bedrock Nova Lite
- **Interact by voice** in English, Hindi, and Bengali via Amazon Polly & Transcribe
- **Work offline** with automatic fallbacks for every AWS service — all logged

---

## AWS-First Architecture

Every AI capability uses **AWS as primary**, with offline fallbacks:

| Capability | AWS Primary | Offline Fallback |
|------------|-------------|-----------------|
| Intent Classification | **Amazon Bedrock** Nova Lite | Keyword matching |
| Aadhaar Extraction | **Amazon Bedrock** Nova Lite | Regex patterns |
| Prescription OCR | **Amazon Textract** | PaddleOCR 2.7.0 |
| Text-to-Speech | **Amazon Polly** (Kajal neural) | pyttsx3 |
| Speech-to-Text | **Amazon Transcribe** | SpeechRecognition |
| Health Analysis | **Amazon Bedrock** Nova Lite | Rule-based triage |
| Data Storage | **Amazon S3** | Local CSV + JSON |
| Clinical Notes | **AWS Lambda** + Bedrock | Not available |

> **Every fallback event is logged** with the reason for the switch.

---

## Guided Healthcare Flow

```
Language Selection → Wake Word ("Hello Asha") → Aadhaar Collection
    → Patient Lookup → Health Inquiry → Prescription Capture Loop
    → Pulse Sensor (3 attempts) → Environment Sensors
    → Final AI Analysis (Bedrock) → Save & Next Patient
```

---

## Hardware

| Component | Model | Interface |
|-----------|-------|-----------|
| Edge AI Board | RDK S100 V1P0 | ARM64, 4GB RAM |
| Camera | SC230AI | MIPI CSI |
| Audio | Jabra EVOLVE 20 MS | USB (`plughw:1,0`) |
| Pulse Oximeter | MAX30102 | I2C Bus 5, 0x57 |
| Environment | BMP280 | I2C Bus 5, 0x76 |

---

## Quick Start

```bash
git clone https://github.com/DevDaring/AI_4_Bharat.git
cd AI_4_Bharat

# Install dependencies
pip3 install -r Code/requirements.txt

# Configure AWS credentials
cd Code && cp env.template .env && nano .env

# Run Pocket ASHA
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py
```

See [Code/README.md](Code/README.md) for detailed setup, architecture diagrams, and usage guide.

---

## Project Structure

```
AI_4_Bharat/
├── Code/                       # Main application
│   ├── main.py                 # Entry point
│   ├── guided_flow.py          # Guided encounter orchestrator
│   ├── aws_handler.py          # Bedrock, S3, Lambda, Textract
│   ├── intent_handler.py       # Bedrock LLM intent classifier
│   ├── voice_handler.py        # Polly TTS + Transcribe STT
│   ├── ocr_handler.py          # Textract + PaddleOCR
│   ├── sensor_handler.py       # MAX30102 + BMP280 drivers
│   ├── camera_handler.py       # SC230AI MIPI capture
│   ├── encounter_manager.py    # Patient encounter state machine
│   ├── storage_manager.py      # CSV database + Aadhaar lookup
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

- **Amazon Bedrock** (Nova Lite v1:0) — LLM for intent, Aadhaar, health analysis, prescriptions
- **Amazon Polly** — Neural TTS (Kajal voice, en-IN / hi-IN)
- **Amazon Transcribe** — STT (en-IN, hi-IN, bn-IN)
- **Amazon Textract** — Document OCR
- **Amazon S3** — Cloud storage for encounters
- **AWS Lambda** — Clinical notes generation
- **AWS IAM** — Access control

---

## Team

**DevDaring** — AWS Hackathon: AI for Bharat

## License

Built for the **AWS "AI for Bharat" Hackathon**. All code is original work by Team DevDaring.
