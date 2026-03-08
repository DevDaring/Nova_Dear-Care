"""
Lambda handler for Pocket ASHA clinical notes generation.
Receives encounter data from S3, generates clinical notes via Bedrock,
stores results back in S3.

Actions:
  - generate_notes: structured clinical notes from encounter data
  - triage_review: AI review of on-device triage decision
  - health_summary: consolidated health analysis with prescriptions & vitals
"""

import json
import os
import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
BUCKET = os.environ.get("S3_BUCKET_NAME", "pocket-asha-data-343104031497")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

s3 = boto3.client("s3", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def handler(event, context):
    """
    Lambda entry point.

    Expected event:
    {
        "encounter_id": "ENC-20250101-ABCD",
        "action": "generate_notes"  # or "triage_review" or "health_summary"
    }
    """
    encounter_id = event.get("encounter_id", "")
    action = event.get("action", "generate_notes")

    if not encounter_id:
        return {"statusCode": 400, "body": "Missing encounter_id"}

    try:
        # Load encounter data from S3
        key = f"encounters/{encounter_id}/encounter.json"
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        data = json.loads(obj["Body"].read().decode("utf-8"))

        if action == "generate_notes":
            result = _generate_clinical_notes(encounter_id, data)
        elif action == "triage_review":
            result = _review_triage(encounter_id, data)
        elif action == "health_summary":
            result = _generate_health_summary(encounter_id, data)
        else:
            return {"statusCode": 400, "body": f"Unknown action: {action}"}

        return {"statusCode": 200, "body": json.dumps(result)}

    except s3.exceptions.NoSuchKey:
        return {"statusCode": 404, "body": f"Encounter {encounter_id} not found"}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}


def _generate_clinical_notes(encounter_id: str, data: dict) -> dict:
    """Generate structured clinical notes from encounter data."""
    aadhaar = data.get("aadhaar_number", "")
    aadhaar_display = f"{aadhaar[:4]}****{aadhaar[-4:]}" if aadhaar and len(aadhaar) == 12 else "N/A"

    prompt = f"""Generate brief clinical notes for this patient encounter:
- Patient: {data.get('patient_name', 'Unknown')}, Age: {data.get('age', 'N/A')}, Gender: {data.get('gender', 'N/A')}
- Aadhaar (masked): {aadhaar_display}
- SpO2: {data.get('spo2', 'N/A')}%
- Heart Rate: {data.get('heart_rate', 'N/A')} bpm
- Temperature: {data.get('temperature', 'N/A')}°C
- Triage Level: {data.get('triage_level', 'N/A')}
- Notes: {data.get('notes', 'None')}
- Symptoms: {data.get('symptoms', 'None')}

Format as:
CLINICAL NOTES
Patient: [name/age/gender]
ID: [masked Aadhaar]
Vitals: [summary]
Assessment: [brief assessment]
Plan: [recommended next steps]
Keep it concise (under 200 words)."""

    response = _invoke_bedrock(prompt)

    # Store notes in S3
    notes_key = f"encounters/{encounter_id}/clinical_notes.txt"
    s3.put_object(Bucket=BUCKET, Key=notes_key, Body=response.encode("utf-8"))

    return {"encounter_id": encounter_id, "notes": response, "s3_key": notes_key}


def _review_triage(encounter_id: str, data: dict) -> dict:
    """AI review of on-device triage decision."""
    prompt = f"""Review this triage assessment by a community health worker:
- SpO2: {data.get('spo2', 'N/A')}%, HR: {data.get('heart_rate', 'N/A')} bpm, Temp: {data.get('temperature', 'N/A')}°C
- Device triage: {data.get('triage_level', 'N/A')}
- Symptoms: {data.get('symptoms', 'None')}

Do you agree with the triage level? If not, what should it be and why?
Keep response under 100 words."""

    response = _invoke_bedrock(prompt)

    review_key = f"encounters/{encounter_id}/triage_review.txt"
    s3.put_object(Bucket=BUCKET, Key=review_key, Body=response.encode("utf-8"))

    return {"encounter_id": encounter_id, "review": response, "s3_key": review_key}


def _generate_health_summary(encounter_id: str, data: dict) -> dict:
    """Consolidated health summary with prescriptions, vitals, and environment."""
    # Try to load prescription OCR text from S3
    prescriptions = _load_prescriptions(encounter_id)

    prompt = f"""Provide a consolidated health summary for this patient encounter:

Patient: {data.get('patient_name', 'Unknown')}, Age: {data.get('age', 'N/A')}, Gender: {data.get('gender', 'N/A')}

Vitals:
- SpO2: {data.get('spo2', 'N/A')}%
- Heart Rate: {data.get('heart_rate', 'N/A')} bpm
- Temperature: {data.get('temperature', 'N/A')}°C

Symptoms: {data.get('symptoms', 'None reported')}
Triage Level: {data.get('triage_level', 'N/A')}
Notes: {data.get('notes', 'None')}

Prescriptions/OCR Text:
{prescriptions if prescriptions else 'No prescriptions captured'}

Provide:
1. Overall assessment (1 sentence)
2. Key concerns (bullet points)
3. Prescription review (if any medications found, check for interactions)
4. Recommendation: URGENT referral or ROUTINE follow-up

Keep response under 300 words."""

    response = _invoke_bedrock(prompt)

    summary_key = f"encounters/{encounter_id}/health_summary.txt"
    s3.put_object(Bucket=BUCKET, Key=summary_key, Body=response.encode("utf-8"))

    return {"encounter_id": encounter_id, "summary": response, "s3_key": summary_key}


def _load_prescriptions(encounter_id: str) -> str:
    """Load any OCR/prescription text files from the encounter folder in S3."""
    try:
        prefix = f"encounters/{encounter_id}/"
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        texts = []
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".txt") and "prescription" in key.lower():
                body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode("utf-8")
                texts.append(body)
        # Also check the notes field for OCR text
        return "\n---\n".join(texts) if texts else ""
    except Exception:
        return ""


def _invoke_bedrock(prompt: str) -> str:
    """Call Bedrock with Nova Lite."""
    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "system": [{"text": "You are a medical AI assistant generating clinical documentation for rural healthcare."}],
        "inferenceConfig": {"maxTokens": 512, "temperature": 0.3},
    }
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    result = json.loads(resp["body"].read())
    return result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
