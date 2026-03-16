# Dear-Care — Code Directory

> See the [project README](../README.md) for full documentation, architecture, and setup instructions.

## Quick Reference

```bash
# Run Dear-Care (voice mode)
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py

# Run Dear-Care (text-only mode)
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
```

## Module Overview

| Module | Purpose |
|--------|---------|
| `main.py` | Entry point, main event loop, command processing |
| `guided_flow.py` | 9-stage guided healthcare encounter flow |
| `encounter_manager.py` | Patient encounter lifecycle and data management |
| `voice_handler.py` | TTS (Nova Sonic → Polly → pyttsx3) and STT (Transcribe → SpeechRecognition) |
| `aws_handler.py` | Bedrock (Nova Lite + Nova Sonic), S3, Lambda integration |
| `triage_engine.py` | On-device rule-based clinical triage (works offline) |
| `camera_handler.py` | SC230AI MIPI camera capture via `get_vin_data` |
| `ocr_handler.py` | Prescription OCR — Textract (online) + PaddleOCR (offline) |
| `sensor_handler.py` | MAX30102 (SpO2/HR) + BMP280 (Temp/Humidity) I2C sensors |
| `intent_handler.py` | Bedrock LLM intent classification + keyword fallback |
| `language_handler.py` | 6 Indian languages with Polly voice and Transcribe mappings |
| `storage_manager.py` | Local CSV database + encounter file management |
| `sync_manager.py` | Background S3 sync with Lambda trigger |
| `fitu_client.py` | Fit-U mobile app integration (DynamoDB + SNS) |
| `security.py` | PIN authentication + AES-256 data encryption |
| `config.py` | All configuration constants, prompts, and hardware settings |
| `utils.py` | Logging, memory management, signal handlers |

## Lambda

The `lambda/handler.py` runs on AWS Lambda and generates clinical notes, triage reviews, and health summaries using Amazon Bedrock Nova Lite.

Deploy with:
```bash
bash deploy_lambda.sh
```
