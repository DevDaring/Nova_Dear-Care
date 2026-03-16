#!/usr/bin/env python3
"""
aws_handler.py - AWS Bedrock (LLM), S3, Lambda, and Nova Sonic integration for Dear-Care.
Uses Amazon Nova Lite (amazon.nova-lite-v1:0) via Bedrock for text.
Uses Amazon Nova 2 Sonic (amazon.nova-2-sonic-v1:0) via Bedrock for voice (requires aws-sdk-bedrock-runtime).
"""

import json
from typing import Optional, Dict, List, Tuple

from utils import get_logger, check_internet

_log = None
_bedrock_client = None
_bedrock_runtime_streaming = None
_s3_client = None
_lambda_client = None
_chat_history: List[Dict] = []

# Nova 2 Sonic Model ID
NOVA_SONIC_MODEL_ID = "amazon.nova-2-sonic-v1:0"


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


def _get_bedrock():
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        from config import AWS_REGION
        _bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _bedrock_client


def _get_bedrock_streaming():
    """Get or create Bedrock runtime streaming client for Nova 2 Sonic."""
    global _bedrock_runtime_streaming
    if _bedrock_runtime_streaming is None:
        import boto3
        from config import AWS_REGION
        _bedrock_runtime_streaming = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _bedrock_runtime_streaming


def _get_s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        from config import AWS_REGION
        _s3_client = boto3.client("s3", region_name=AWS_REGION)
    return _s3_client


def _get_lambda():
    global _lambda_client
    if _lambda_client is None:
        import boto3
        from config import AWS_REGION
        _lambda_client = boto3.client("lambda", region_name=AWS_REGION)
    return _lambda_client


# ============================================================
# Bedrock LLM
# ============================================================

def invoke_llm(prompt: str, system_prompt: str = None, max_tokens: int = None) -> str:
    """Invoke Amazon Nova Lite via Bedrock. Returns response text or empty string."""
    if not check_internet():
        _logger().warning("[AWS] No internet — cannot invoke Bedrock")
        return ""
    try:
        from config import BEDROCK_MODEL_ID, BEDROCK_MAX_TOKENS, BEDROCK_TEMPERATURE, SYSTEM_PROMPT

        client = _get_bedrock()
        sys_prompt = system_prompt or SYSTEM_PROMPT
        tokens = max_tokens or BEDROCK_MAX_TOKENS

        body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {
                "maxTokens": tokens,
                "temperature": BEDROCK_TEMPERATURE,
            },
        }
        if sys_prompt:
            body["system"] = [{"text": sys_prompt}]

        resp = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        result = json.loads(resp["body"].read())
        text = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
        _logger().info("[AWS] Bedrock response: %s…", text[:80])
        return text.strip()
    except Exception as e:
        _logger().error("[AWS] Bedrock error: %s", e)
        return ""


def chat(user_message: str) -> str:
    """Conversational chat with context history."""
    if not check_internet():
        return ""
    try:
        from config import BEDROCK_MODEL_ID, BEDROCK_MAX_TOKENS, BEDROCK_TEMPERATURE, SYSTEM_PROMPT
        global _chat_history

        _chat_history.append({"role": "user", "content": [{"text": user_message}]})
        # Keep history manageable (last 10 turns)
        if len(_chat_history) > 20:
            _chat_history = _chat_history[-20:]

        client = _get_bedrock()
        body = {
            "messages": _chat_history,
            "system": [{"text": SYSTEM_PROMPT}],
            "inferenceConfig": {"maxTokens": BEDROCK_MAX_TOKENS, "temperature": BEDROCK_TEMPERATURE},
        }
        resp = client.invoke_model(
            modelId=BEDROCK_MODEL_ID, contentType="application/json",
            accept="application/json", body=json.dumps(body),
        )
        result = json.loads(resp["body"].read())
        text = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
        _chat_history.append({"role": "assistant", "content": [{"text": text}]})
        return text.strip()
    except Exception as e:
        _logger().error("[AWS] Chat error: %s", e)
        return ""


def analyze_prescription(ocr_text: str) -> str:
    """Analyze prescription text via Bedrock."""
    from config import OCR_ANALYSIS_PROMPT
    prompt = OCR_ANALYSIS_PROMPT.format(ocr_text=ocr_text)
    return invoke_llm(prompt)


def extract_medicines(ocr_text: str) -> list:
    """Extract medicine list from prescription text. Returns list of dicts."""
    from config import MEDICINE_EXTRACTION_PROMPT
    prompt = MEDICINE_EXTRACTION_PROMPT.format(ocr_text=ocr_text)
    resp = invoke_llm(prompt, max_tokens=256)
    try:
        # Parse JSON from response
        start = resp.find("[")
        end = resp.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(resp[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return []


def get_triage_assessment(spo2, heart_rate, temperature, symptoms: str = "") -> str:
    """Get AI triage assessment from Bedrock."""
    from config import TRIAGE_PROMPT
    prompt = TRIAGE_PROMPT.format(
        spo2=spo2 or "N/A", heart_rate=heart_rate or "N/A",
        temperature=temperature or "N/A", symptoms=symptoms or "None reported",
    )
    return invoke_llm(prompt)


def clear_chat():
    global _chat_history
    _chat_history.clear()


def classify_intent_llm(text: str) -> dict:
    """Classify user intent via Bedrock. Returns {"intent": str, "confidence": float} or empty dict."""
    from config import INTENT_CLASSIFICATION_PROMPT
    prompt = INTENT_CLASSIFICATION_PROMPT.format(text=text)
    resp = invoke_llm(prompt, system_prompt="You are an intent classifier. Return only valid JSON.", max_tokens=64)
    if not resp:
        return {}
    try:
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(resp[start:end])
            return {"intent": data.get("intent", "UNKNOWN"), "confidence": float(data.get("confidence", 0.0))}
    except (json.JSONDecodeError, ValueError, TypeError):
        _logger().warning("[AWS] Failed to parse intent response: %s", resp[:100])
    return {}


def extract_aadhaar_llm(text: str) -> str:
    """Extract 12-digit Aadhaar number from speech text via Bedrock. Returns number string or empty."""
    from config import AADHAAR_EXTRACTION_PROMPT
    prompt = AADHAAR_EXTRACTION_PROMPT.format(text=text)
    resp = invoke_llm(prompt, system_prompt="You extract Aadhaar numbers. Return only valid JSON.", max_tokens=64)
    if not resp:
        return ""
    try:
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(resp[start:end])
            aadhaar = data.get("aadhaar")
            if aadhaar and len(str(aadhaar).replace(" ", "")) == 12:
                return str(aadhaar).replace(" ", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        _logger().warning("[AWS] Failed to parse Aadhaar response: %s", resp[:100])
    return ""


def analyze_health_summary(symptoms: str, prescriptions: str, vitals: dict, env_data: dict,
                           triage: str = "", history: str = "", fitu_data: dict = None) -> str:
    """Generate consolidated health summary via Bedrock, including triage, historical data, and Fit-U mobility data."""
    from config import HEALTH_SUMMARY_PROMPT

    # Build Fit-U mobility section if data available
    fitu_section = ""
    if fitu_data:
        fitu_section = f"""
MOBILITY DATA (from Fit-U companion app):
- Steps today: {fitu_data.get('steps', 'N/A')}
- Distance walked: {fitu_data.get('distance_km', 'N/A')} km
- Current activity: {fitu_data.get('activity', 'N/A')}
- Estimated speed: {fitu_data.get('speed_kmh', 'N/A')} km/h
- Location: {fitu_data.get('latitude', 'N/A')}, {fitu_data.get('longitude', 'N/A')}
"""

    # Update prompt to include Fit-U data
    prompt_template = HEALTH_SUMMARY_PROMPT
    if fitu_section:
        # Insert Fit-U section before the historical records
        prompt_template = prompt_template.replace(
            "Historical records (previous visits):",
            fitu_section + "\nHistorical records (previous visits):"
        )

    prompt = prompt_template.format(
        symptoms=symptoms or "None reported",
        prescriptions=prescriptions or "None captured",
        spo2=vitals.get("spo2", "N/A"),
        heart_rate=vitals.get("heart_rate", "N/A"),
        temperature=vitals.get("temperature", "N/A"),
        pressure=env_data.get("pressure", "N/A"),
        triage=triage or "Not assessed",
        history=history or "No previous visits found.",
    )
    return invoke_llm(prompt)


def invoke_nova_sonic_voice(text_prompt: str, language_code: str = "en-IN") -> Optional[bytes]:
    """
    Invoke Amazon Nova 2 Sonic for real-time voice response.
    Uses the bidirectional streaming API via aws-sdk-bedrock-runtime (requires Python 3.12+).
    Returns raw PCM audio bytes (24 kHz, 16-bit, mono) to be played through the speaker.
    Falls back to None if Nova Sonic SDK is unavailable (caller should use Polly).
    """
    try:
        from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient
        from aws_sdk_bedrock_runtime.config import Config
        from aws_sdk_bedrock_runtime.models import (
            InvokeModelWithBidirectionalStreamOperationInput,
            InvokeModelWithBidirectionalStreamInputChunk,
            BidirectionalInputPayloadPart,
        )
        import asyncio
        import base64
        import uuid
        import configparser
        import os
        from config import AWS_REGION

        # Ensure AWS env vars are set (EnvironmentCredentialsResolver needs them)
        if "AWS_ACCESS_KEY_ID" not in os.environ:
            _creds = configparser.ConfigParser()
            _creds.read(os.path.expanduser("~/.aws/credentials"))
            if _creds.has_section("default"):
                os.environ.setdefault("AWS_ACCESS_KEY_ID", _creds.get("default", "aws_access_key_id", fallback=""))
                os.environ.setdefault("AWS_SECRET_ACCESS_KEY", _creds.get("default", "aws_secret_access_key", fallback=""))

        from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

        async def _run_nova_sonic():
            prompt_name = str(uuid.uuid4())
            content_name = str(uuid.uuid4())
            audio_content_name = str(uuid.uuid4())

            # Initialize client
            config = Config(
                endpoint_uri=f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com",
                region=AWS_REGION,
                aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
            )
            client = BedrockRuntimeClient(config=config)

            # Open bidirectional stream
            stream = await client.invoke_model_with_bidirectional_stream(
                InvokeModelWithBidirectionalStreamOperationInput(model_id=NOVA_SONIC_MODEL_ID)
            )

            audio_chunks = []
            got_completion = asyncio.Event()

            # --- helper to send one JSON event ---
            async def _send(evt_dict):
                await stream.input_stream.send(
                    InvokeModelWithBidirectionalStreamInputChunk(
                        value=BidirectionalInputPayloadPart(
                            bytes_=json.dumps(evt_dict).encode("utf-8")
                        )
                    )
                )

            # 1. Session start
            await _send({
                "event": {
                    "sessionStart": {
                        "inferenceConfiguration": {
                            "maxTokens": 1024,
                            "topP": 0.9,
                            "temperature": 0.7,
                        }
                    }
                }
            })

            # 2. Prompt start (with male voice "matthew", 24 kHz output)
            await _send({
                "event": {
                    "promptStart": {
                        "promptName": prompt_name,
                        "textOutputConfiguration": {"mediaType": "text/plain"},
                        "audioOutputConfiguration": {
                            "mediaType": "audio/lpcm",
                            "sampleRateHertz": 24000,
                            "sampleSizeBits": 16,
                            "channelCount": 1,
                            "voiceId": "matthew",
                            "encoding": "base64",
                            "audioType": "SPEECH",
                        },
                    }
                }
            })

            # 3. System prompt
            sys_content_name = str(uuid.uuid4())
            await _send({"event": {"contentStart": {"promptName": prompt_name, "contentName": sys_content_name, "role": "SYSTEM", "type": "TEXT", "interactive": False, "textInputConfiguration": {"mediaType": "text/plain"}}}})
            await _send({"event": {"textInput": {"promptName": prompt_name, "contentName": sys_content_name, "content": "You are Kamal, a warm and helpful male healthcare assistant. Speak the given text naturally, clearly, and with empathy. Keep your response exactly as the text provided."}}})
            await _send({"event": {"contentEnd": {"promptName": prompt_name, "contentName": sys_content_name}}})

            # 4. Audio content start (required even for text-only — send silence)
            await _send({"event": {"contentStart": {"promptName": prompt_name, "contentName": audio_content_name, "type": "AUDIO", "interactive": True, "role": "USER", "audioInputConfiguration": {"mediaType": "audio/lpcm", "sampleRateHertz": 16000, "sampleSizeBits": 16, "channelCount": 1, "audioType": "SPEECH", "encoding": "base64"}}}})

            # 5. Response reader task
            last_audio_time = [0.0]  # mutable for closure
            import time as _time

            async def _read_responses():
                try:
                    while True:
                        try:
                            output = await stream.await_output()
                            result = await output[1].receive()
                            if result is None:
                                break
                            if result.value and result.value.bytes_:
                                resp = json.loads(result.value.bytes_.decode("utf-8"))
                                event_data = resp.get("event", {})
                                if "audioOutput" in event_data:
                                    audio_b64 = event_data["audioOutput"]["content"]
                                    audio_chunks.append(base64.b64decode(audio_b64))
                                    last_audio_time[0] = _time.monotonic()
                                elif "completionEnd" in event_data or "promptEnd" in event_data:
                                    got_completion.set()
                                    break
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    _logger().warning("[AWS] NovaSonic reader error: %s", e)
                got_completion.set()

            # Watchdog: if we got audio and no new audio for 3s, consider done
            async def _watchdog():
                while not got_completion.is_set():
                    await asyncio.sleep(0.5)
                    if audio_chunks and last_audio_time[0] > 0:
                        idle = _time.monotonic() - last_audio_time[0]
                        if idle > 3.0:
                            got_completion.set()
                            break

            reader_task = asyncio.create_task(_read_responses())
            watchdog_task = asyncio.create_task(_watchdog())

            # 6. Send a few silent audio chunks to keep the connection alive
            silent_chunk = base64.b64encode(b"\x00" * 2048).decode("utf-8")
            for _ in range(5):
                await _send({"event": {"audioInput": {"promptName": prompt_name, "contentName": audio_content_name, "content": silent_chunk}}})
                await asyncio.sleep(0.01)

            # 7. Send the text input
            text_content_name = str(uuid.uuid4())
            await _send({"event": {"contentStart": {"promptName": prompt_name, "contentName": text_content_name, "role": "USER", "type": "TEXT", "interactive": True, "textInputConfiguration": {"mediaType": "text/plain"}}}})
            await _send({"event": {"textInput": {"promptName": prompt_name, "contentName": text_content_name, "content": text_prompt}}})
            await _send({"event": {"contentEnd": {"promptName": prompt_name, "contentName": text_content_name}}})

            # 8. Keep sending silent audio while waiting for response
            async def _send_silence():
                try:
                    while not got_completion.is_set():
                        await _send({"event": {"audioInput": {"promptName": prompt_name, "contentName": audio_content_name, "content": silent_chunk}}})
                        await asyncio.sleep(0.01)
                except Exception:
                    pass

            silence_task = asyncio.create_task(_send_silence())

            # 9. Wait for completion with timeout
            try:
                await asyncio.wait_for(got_completion.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                _logger().warning("[AWS] NovaSonic: Timeout waiting for response")

            silence_task.cancel()
            try:
                await silence_task
            except asyncio.CancelledError:
                pass

            watchdog_task.cancel()
            try:
                await watchdog_task
            except asyncio.CancelledError:
                pass

            # 10. Cleanup — send end events and close gracefully
            try:
                await _send({"event": {"contentEnd": {"promptName": prompt_name, "contentName": audio_content_name}}})
                await _send({"event": {"promptEnd": {"promptName": prompt_name}}})
                await _send({"event": {"sessionEnd": {}}})
            except Exception:
                pass

            # Give CRT time to drain pending HTTP callbacks before closing
            await asyncio.sleep(0.2)

            # Let reader finish naturally before closing the stream
            try:
                await asyncio.wait_for(reader_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                reader_task.cancel()
                try:
                    await reader_task
                except (asyncio.CancelledError, Exception):
                    pass

            try:
                await stream.input_stream.close()
            except Exception:
                pass

            # Brief pause to let CRT finish HTTP teardown
            await asyncio.sleep(0.1)

            return b"".join(audio_chunks) if audio_chunks else None

        result = asyncio.run(_run_nova_sonic())
        if result:
            _logger().info("[AWS] NovaSonic: Generated %d bytes of audio (24kHz)", len(result))
            return result
        else:
            _logger().warning("[AWS] NovaSonic: No audio data received")
            return None

    except ImportError:
        _logger().info("[AWS] NovaSonic SDK not available (requires Python 3.12+) — using Polly fallback")
        return None
    except Exception as e:
        _logger().warning("[AWS] NovaSonic fallback: %s", e)
        return None


# ============================================================
# S3
# ============================================================

def ensure_bucket():
    """Create S3 bucket if it doesn't exist."""
    try:
        from config import S3_BUCKET_NAME, AWS_REGION
        s3 = _get_s3()
        try:
            s3.head_bucket(Bucket=S3_BUCKET_NAME)
        except Exception:
            kwargs = {"Bucket": S3_BUCKET_NAME}
            if AWS_REGION != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": AWS_REGION}
            s3.create_bucket(**kwargs)
            _logger().info("[AWS] Created S3 bucket: %s", S3_BUCKET_NAME)
    except Exception as e:
        _logger().error("[AWS] S3 bucket error: %s", e)


def upload_file(local_path: str, s3_key: str) -> bool:
    try:
        from config import S3_BUCKET_NAME
        _get_s3().upload_file(local_path, S3_BUCKET_NAME, s3_key)
        _logger().info("[AWS] Uploaded %s → s3://%s/%s", local_path, S3_BUCKET_NAME, s3_key)
        return True
    except Exception as e:
        _logger().error("[AWS] Upload error: %s", e)
        return False


def upload_encounter(encounter_id: str, folder_path: str) -> bool:
    """Upload entire encounter folder to S3."""
    import os
    from config import S3_BUCKET_NAME
    success = True
    for root, _, files in os.walk(folder_path):
        for fname in files:
            local = os.path.join(root, fname)
            rel = os.path.relpath(local, folder_path)
            key = f"encounters/{encounter_id}/{rel}"
            if not upload_file(local, key):
                success = False
    return success


# ============================================================
# Lambda
# ============================================================

def invoke_lambda(payload: dict) -> Optional[dict]:
    """Invoke the clinical notes Lambda function."""
    try:
        from config import LAMBDA_FUNCTION_NAME
        resp = _get_lambda().invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        result = json.loads(resp["Payload"].read())
        _logger().info("[AWS] Lambda response received")
        return result
    except Exception as e:
        _logger().error("[AWS] Lambda error: %s", e)
        return None


# ============================================================
# Connection test
# ============================================================

def test_connection() -> Dict:
    """Test AWS connectivity. Returns dict of service statuses."""
    results = {"bedrock": False, "s3": False, "polly": False, "transcribe": False}
    try:
        # Bedrock
        resp = invoke_llm("Say hello in one word.")
        results["bedrock"] = bool(resp)
    except Exception:
        pass
    try:
        from config import S3_BUCKET_NAME
        _get_s3().head_bucket(Bucket=S3_BUCKET_NAME)
        results["s3"] = True
    except Exception:
        pass
    try:
        import boto3
        from config import AWS_REGION
        polly = boto3.client("polly", region_name=AWS_REGION)
        polly.describe_voices(LanguageCode="en-IN")
        results["polly"] = True
    except Exception:
        pass
    try:
        import boto3
        from config import AWS_REGION
        tc = boto3.client("transcribe", region_name=AWS_REGION)
        tc.list_transcription_jobs(MaxResults=1)
        results["transcribe"] = True
    except Exception:
        pass
    return results
