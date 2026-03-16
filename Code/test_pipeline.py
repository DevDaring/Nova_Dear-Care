#!/usr/bin/env python3
"""
Quick end-to-end pipeline test:
  1. Creates a dummy encounter with a 12-digit Aadhaar
  2. Saves it locally
  3. Uploads to S3
  4. Invokes Lambda (health_summary)
  5. Parses and prints the decision
  6. Sends notification to mobile app via Fit-U SNS
"""

import json
import os
import sys
import shutil
from datetime import datetime

# Ensure Code/ is on the path
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CODE_DIR)

from utils import setup_logging, check_internet

setup_logging()

# ---------- Step 1: Create dummy encounter ----------
enc_id = f"ENC_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}_999"
enc_dir = os.path.join(CODE_DIR, "data", "encounters", enc_id)
os.makedirs(enc_dir, exist_ok=True)

encounter = {
    "encounter_id": enc_id,
    "patient_id": "PAT_TEST_001",
    "timestamp": datetime.now().isoformat(),
    "aadhaar_number": "998877665544",
    "patient_name": "Test Patient",
    "age": "45",
    "gender": "M",
    "spo2": "94.2",
    "heart_rate": "82",
    "temperature": "37.1",
    "triage_level": "ROUTINE",
    "triage_confidence": "0.85",
    "sync_status": "pending",
    "photo_count": 0,
    "audio_count": 0,
    "notes": "Prescription: Paracetamol 500mg twice daily. Blood pressure 130/85.",
    "symptoms": "Mild fever, headache for 2 days",
    "env_pressure": "1013.2",
}

enc_path = os.path.join(enc_dir, "encounter.json")
with open(enc_path, "w") as f:
    json.dump(encounter, f, indent=2)
print(f"[1/6] Created encounter: {enc_id}")
print(f"      Aadhaar: 9988 **** 5544")
print(f"      Patient: Test Patient, 45/M")
print(f"      Vitals:  SpO2=94.2%, HR=82, Temp=37.1°C")
print(f"      Rx:      Paracetamol 500mg")
print()

# ---------- Step 2: Check connectivity ----------
if not check_internet():
    print("[ERROR] No internet connection. Cannot continue.")
    sys.exit(1)
print("[2/6] Internet: Online")
print()

# ---------- Step 3: Upload to S3 ----------
try:
    import boto3
    from config import AWS_REGION, S3_BUCKET_NAME

    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_key = f"encounters/{enc_id}/encounter.json"
    s3.upload_file(enc_path, S3_BUCKET_NAME, s3_key)
    print(f"[3/6] Uploaded to s3://{S3_BUCKET_NAME}/{s3_key}")
    print()
except Exception as e:
    print(f"[ERROR] S3 upload failed: {e}")
    sys.exit(1)

# ---------- Step 4: Invoke Lambda (health_summary) ----------
try:
    from aws_handler import invoke_lambda

    payload = {"encounter_id": enc_id, "action": "health_summary"}
    print(f"[4/6] Invoking Lambda with action=health_summary ...")
    resp = invoke_lambda(payload)

    if not resp:
        print("[ERROR] Lambda returned None")
        sys.exit(1)

    status = resp.get("statusCode", 0)
    print(f"      Status: {status}")

    if status == 200:
        body = resp.get("body", "")
        if isinstance(body, str):
            try:
                body_data = json.loads(body)
                decision = body_data.get("summary", body_data.get("message", body))
            except (json.JSONDecodeError, ValueError):
                decision = body
        elif isinstance(body, dict):
            decision = body.get("summary", body.get("message", str(body)))
        else:
            decision = str(body) if body else "(empty)"
        print()
        print("=" * 60)
        print("  CLOUD DECISION / HEALTH SUMMARY")
        print("=" * 60)
        print(decision)
        print("=" * 60)
        print()
    else:
        body = resp.get("body", "")
        print(f"[ERROR] Lambda returned status {status}: {body}")
        sys.exit(1)

except Exception as e:
    print(f"[ERROR] Lambda invocation failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# ---------- Step 5: Invoke Lambda (generate_notes + triage_review) ----------
for action in ["generate_notes", "triage_review"]:
    try:
        r = invoke_lambda({"encounter_id": enc_id, "action": action})
        s = r.get("statusCode", 0) if r else "None"
        print(f"[5/6] Lambda {action}: status={s}")
    except Exception as e:
        print(f"[5/6] Lambda {action}: FAILED ({e})")
print()

# ---------- Step 6: Send mobile notification ----------
try:
    from fitu_client import FituClient
    import config

    fitu = FituClient(config)
    if fitu.is_available():
        ok = fitu.notify_fitu_verdict_ready(
            worker_id="TEST_WORKER",
            encounter_id=enc_id,
            triage_level=encounter.get("triage_level", "ROUTINE"),
            summary=decision[:500] if decision else f"Test encounter {enc_id} processed."
        )
        print(f"[6/6] Mobile notification: {'SENT' if ok else 'FAILED'}")
    else:
        print(f"[6/6] Mobile notification: Fit-U not available (SNS not configured?)")
except Exception as e:
    print(f"[6/6] Mobile notification: FAILED ({e})")

# ---------- Cleanup test encounter from local disk ----------
try:
    shutil.rmtree(enc_dir)
    print(f"\n[CLEANUP] Removed local test encounter {enc_id}")
except Exception:
    pass

print("\n[DONE] Pipeline test complete.")
