#!/usr/bin/env python3
"""
config.py - Configuration and Constants for Dear-Care System

Target Platform: RDK S100 (Ubuntu 22.04, ARM64, 4GB RAM)
Hackathon: Amazon Nova Devpost | Voice AI Track
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

# ============================================================
# AWS CREDENTIALS
# ============================================================
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
AWS_BEARER_TOKEN = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "dear-care-data")
LAMBDA_FUNCTION_NAME = os.getenv("LAMBDA_FUNCTION_NAME", "dear-care-clinical-notes")

# ============================================================
# FIT-U COMPANION APP INTEGRATION
# ============================================================
FITU_API_GATEWAY_URL = os.getenv("FITU_API_GATEWAY_URL", "")
FITU_SNS_TOPIC_ARN = os.getenv("FITU_SNS_TOPIC_ARN", "")
FITU_DATA_S3_PREFIX = os.getenv("FITU_DATA_S3_PREFIX", "fitu-companion/")
FITU_DYNAMODB_TABLE = os.getenv("FITU_DYNAMODB_TABLE", "dear-care-fitu-health")
WORKER_ID = os.getenv("WORKER_ID", "DC-KOUSHIK-001")
DEVICE_AADHAAR = os.getenv("DEVICE_AADHAAR", "123456789012")
VERDICT_SERVER_PORT = int(os.getenv("VERDICT_SERVER_PORT", "8080"))

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ENCOUNTER_DIR = DATA_DIR / "encounters"
TEMP_DIR = BASE_DIR / "temp"
AUDIO_DIR = BASE_DIR / "audio"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
for d in [DATA_DIR, ENCOUNTER_DIR, TEMP_DIR, AUDIO_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# CSV database
ENCOUNTERS_CSV = ENCOUNTER_DIR / "encounters.csv"

# ============================================================
# AUDIO CONFIGURATION
# ============================================================
JABRA_CAPTURE_DEV = "plughw:1,0"
JABRA_PLAYBACK_DEV = "plughw:1,0"
BOSE_SINK = os.getenv("BOSE_SINK", "bluez_sink.78_2B_64_DD_68_CF.a2dp_sink")

AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "S16_LE"
DEFAULT_RECORD_DURATION = 7
WAKE_WORD_LISTEN_DURATION = 5

TEMP_AUDIO_INPUT = TEMP_DIR / "voice_input.wav"
TEMP_AUDIO_OUTPUT = TEMP_DIR / "voice_output.wav"

# ============================================================
# WAKE WORD CONFIGURATION
# ============================================================
WAKE_WORDS = ["kamal", "dear care", "dear-care"]
WAKE_WORD_VARIATIONS = [
    "kamal", "kamaal", "kamal", "kaml",
    "dear care", "dear-care", "dearcare",
]
ASSISTANT_NAME = "Kamal"
WAKE_PHRASES = [
    "hello kamal", "ok kamal", "okay kamal", "hey kamal", "hi kamal",
    "dear care", "dear-care",
]

# ============================================================
# CAMERA CONFIGURATION (SC230AI via get_vin_data — RDK S100 MIPI)
# ============================================================
CAMERA_SENSOR_INDEX = 6   # SC230AI in get_vin_data sensor list
CAMERA_FPS = 30
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_TIMEOUT_SEC = 15.0
SNAPSHOT_PREFIX = "patient_"

# ============================================================
# SENSOR CONFIGURATION
# ============================================================
MAX30102_I2C_BUS = 5
MAX30102_I2C_ADDR = 0x57
BME280_I2C_BUS = 5
BME280_I2C_ADDR = 0x76

# Vital sign thresholds
SPO2_LOW_THRESHOLD = 94.0
SPO2_CRITICAL_THRESHOLD = 90.0
HR_LOW_THRESHOLD = 50
HR_HIGH_THRESHOLD = 120
HR_CRITICAL_LOW = 40
HR_CRITICAL_HIGH = 150
TEMP_HIGH_THRESHOLD = 38.5
TEMP_CRITICAL_THRESHOLD = 39.5
TEMP_LOW_THRESHOLD = 35.0

# ============================================================
# OCR CONFIGURATION
# ============================================================
OCR_LANG = "en"
OCR_USE_ANGLE_CLS = False
OCR_FONT_PATH = str(BASE_DIR / "doc" / "fonts" / "simfang.ttf")

# ============================================================
# BEDROCK MODEL CONFIGURATION
# ============================================================
BEDROCK_MODEL_ID = "amazon.nova-2-lite-v1:0"
BEDROCK_MAX_TOKENS = 512
BEDROCK_TEMPERATURE = 0.7

# ============================================================
# POLLY TTS CONFIGURATION
# ============================================================
POLLY_VOICE_ID = "Kajal"
POLLY_ENGINE = "neural"
POLLY_OUTPUT_FORMAT = "pcm"
POLLY_SAMPLE_RATE = "16000"

# ============================================================
# TRANSCRIBE STT CONFIGURATION
# ============================================================
TRANSCRIBE_LANGUAGE = "en-IN"
TRANSCRIBE_SAMPLE_RATE = 16000

# ============================================================
# SECURITY
# ============================================================
DEARCARE_PIN_HASH = os.getenv("DEARCARE_PIN_HASH", "")
DATA_RETENTION_DAYS = 30
MAX_OFFLINE_ENCOUNTERS = 100

# ============================================================
# INTENT KEYWORDS
# ============================================================
CAPTURE_KEYWORDS = [
    "take picture", "take image", "take photo", "capture",
    "take a picture", "take an image", "take a photo",
    "take snap", "take a snap", "prescription snap", "snap prescription",
    "click photo", "click picture", "snap", "photograph",
    "look at the prescription", "look at prescription",
    "look at the report", "look at report",
    "look at this", "look at that", "see this", "see that",
    "read prescription", "read my prescription", "scan prescription",
    "show prescription", "see prescription", "check prescription",
    "read this", "read that", "scan this", "scan it",
    "read document", "read paper", "scan document",
    "read report", "scan report", "medical document",
    "open camera", "use camera", "camera please",
    "prescription", "medicine paper", "medical report",
]

VITALS_KEYWORDS = [
    "check vitals", "measure vitals", "vital signs", "vitals",
    "check pulse", "pulse", "heart rate", "heartbeat",
    "oxygen", "spo2", "saturation", "oxygen level",
    "temperature", "fever", "temp", "body temperature",
    "blood pressure", "bp",
    "check health", "health check",
]

RECORD_AUDIO_KEYWORDS = [
    "record cough", "cough sample", "record audio", "record sound",
    "listen to cough", "cough test", "record symptoms",
    "symptom recording", "voice note", "audio note",
]

CONFIRM_KEYWORDS = [
    "yes", "yeah", "yep", "sure", "ok", "okay", "confirm",
    "do it", "go ahead", "please", "haan", "ji", "ha",
]

DENY_KEYWORDS = [
    "no", "nope", "nah", "don't", "cancel", "stop",
    "negative", "nahi", "na", "skip",
]

HEALTH_KEYWORDS = [
    "health", "feeling", "pain", "ache", "symptom", "sick",
    "unwell", "condition", "problem", "dard", "bukhar",
]

EXIT_KEYWORDS = ["exit", "quit", "bye", "goodbye", "stop", "end", "close", "shutdown"]

ENCOUNTER_KEYWORDS = [
    "start patient", "new patient", "start encounter",
    "new encounter", "begin patient", "register patient",
    "patient visit", "new visit",
]

SYNC_KEYWORDS = ["sync", "upload", "synchronize", "send data", "push data"]

LANGUAGE_KEYWORDS = [
    "change language", "set language", "speak hindi",
    "speak english", "speak tamil", "speak bengali",
    "language", "bhasha",
]

HELP_KEYWORDS = ["help", "assist", "what can you do", "how do i", "guide"]

# ============================================================
# CONVERSATION PROMPTS
# ============================================================
GREETING_MESSAGE = (
    "Namaste! I am Kamal, your healthcare assistant. "
    "I can help you with patient checkups, prescriptions, and health assessments. "
    "Say Hello Kamal followed by your command."
)

FAREWELL_MESSAGE = (
    "Take care! Remember to sync your data when you have internet. "
    "Stay healthy and goodbye!"
)

WAKE_WORD_HINT = "Say Hello Kamal or Ok Kamal to talk to me."

CONFIRM_CAPTURE = "Ready to capture. Say yes to proceed or no to cancel."

ENCOUNTER_START = (
    "Starting new patient encounter. "
    "Please tell me the patient's name, age, and gender."
)

# ============================================================
# BEDROCK SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are Kamal, an AI healthcare assistant for rural Indian community health workers.
You help with patient triage, prescription reading, and health education.
You run on a Dear-Care device with a MIPI camera, pulse oximeter sensor, and environment sensor.
You CAN capture images, measure pulse/SpO2, and read temperature/pressure.

RULES:
1. Keep ALL responses BRIEF - maximum 2-3 sentences.
2. Use simple language that community health workers understand.
3. For prescriptions, clearly state medicine names, dosages, and timing.
4. For vitals, explain what the numbers mean in simple terms.
5. Always recommend consulting a doctor for serious conditions.
6. Be warm, caring, and culturally sensitive.
7. If unsure about medical advice, say so clearly.
8. You run on a device with limited memory - be concise."""

OCR_ANALYSIS_PROMPT = """Based on this text from a medical document, provide a brief summary:
- Medicine names and dosages
- Key medical findings
- Important instructions

Keep response to 2-3 sentences, easy for a health worker to understand.

Text: {ocr_text}"""

MEDICINE_EXTRACTION_PROMPT = """From this prescription text, extract medicine names and timings.
Return ONLY a JSON array: [{{"medicine": "name", "timing": "time"}}]
If none found, return [].

Text: {ocr_text}"""

TRIAGE_PROMPT = """Given these patient vitals and symptoms, provide a brief triage assessment:
- SpO2: {spo2}%
- Heart Rate: {heart_rate} bpm
- Temperature: {temperature}°C
- Symptoms: {symptoms}

Classify as URGENT or ROUTINE. Give 1-2 sentence recommendation."""

INTENT_CLASSIFICATION_PROMPT = """Classify the following user utterance into exactly one intent.
Return ONLY a JSON object: {{"intent": "<INTENT>", "confidence": <0.0-1.0>}}

Valid intents: START_ENCOUNTER, CAPTURE_IMAGE, MEASURE_VITALS, RECORD_AUDIO,
CONFIRM, DENY, HEALTH_QUESTION, SET_LANGUAGE, SYNC_DATA, HELP, EXIT,
GREETING, THANKS, UNKNOWN

Utterance: {text}"""

AADHAAR_EXTRACTION_PROMPT = """Extract the 12-digit Aadhaar number from the following text.
Return ONLY a JSON object: {{"aadhaar": "<12-digit number or null>"}}
If no valid 12-digit Aadhaar number is found, return {{"aadhaar": null}}

Text: {text}"""

HEALTH_SUMMARY_PROMPT = """You are a healthcare assistant. Provide a brief, actionable health summary.

Patient data:
- Symptoms: {symptoms}
- Prescriptions: {prescriptions}
- SpO2: {spo2}%
- Heart Rate: {heart_rate} bpm
- Temperature: {temperature}°C
- Ambient Pressure: {pressure} hPa
- On-device triage: {triage}

Historical records (previous visits):
{history}

Provide:
1. Overall assessment (1-2 sentences, consider historical context if available)
2. Key concerns (bullet points)
3. Recommendation: URGENT referral or ROUTINE follow-up
4. If historical data available, note any trends or changes from previous visits

Keep response under 8 sentences."""

# ============================================================
# CSV SCHEMA
# ============================================================
CSV_HEADERS = [
    "encounter_id", "timestamp", "worker_id", "patient_id",
    "aadhaar_number", "patient_name", "age", "gender", "spo2", "heart_rate",
    "temperature", "triage_level", "triage_confidence",
    "sync_status", "photo_count", "audio_count", "notes",
]
