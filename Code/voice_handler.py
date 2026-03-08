#!/usr/bin/env python3
"""
voice_handler.py - Audio recording, TTS (Polly/pyttsx3), STT (Transcribe/SpeechRecognition)
for Pocket ASHA on RDK S100.

Audio flow:
 INPUT:  Jabra USB Microphone (hw:1,0) via arecord
 OUTPUT: Bose Bluetooth Speaker via PulseAudio paplay
"""

import math
import os
import re
import struct
import subprocess
import time
import wave
from pathlib import Path
from typing import Optional, Tuple

from utils import get_logger

_log = None
_pyttsx_engine = None
_beep_path = None


def _generate_beep(path: str, freq: int = 880, duration: float = 0.25) -> str:
    """Generate a short beep WAV file. Returns path on success."""
    sample_rate = 16000
    n_samples = int(sample_rate * duration)
    samples = [int(16000 * math.sin(2 * math.pi * freq * t / sample_rate))
               for t in range(n_samples)]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return path


def _play_beep():
    """Play the cached beep sound to signal recording is about to start."""
    global _beep_path
    if _beep_path is None:
        from config import TEMP_DIR
        _beep_path = str(TEMP_DIR / "beep.wav")
        _generate_beep(_beep_path)
    try:
        subprocess.run(["paplay", _beep_path], capture_output=True, timeout=3)
    except Exception:
        pass


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


# ============================================================
# Recording — from Jabra USB Microphone
# ============================================================

def _release_audio_device():
    try:
        subprocess.run(["pkill", "-9", "arecord"], capture_output=True, timeout=2)
        time.sleep(0.2)
    except Exception:
        pass


def _discover_mic() -> str:
    """Auto-discover Jabra or USB mic ALSA device."""
    default = "plughw:1,0"
    try:
        res = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
        for line in res.stdout.split("\n"):
            ll = line.lower()
            if "jabra" in ll:
                m = re.search(r"card\s+(\d+)", line)
                if m:
                    return f"plughw:{m.group(1)},0"
            if "usb" in ll and "card" in ll:
                m = re.search(r"card\s+(\d+)", line)
                if m:
                    return f"plughw:{m.group(1)},0"
    except Exception:
        pass
    return default


def record_audio(output_path: str, duration: int = 7, device: str = None) -> bool:
    """Record WAV from Jabra mic. Returns True on success."""
    from config import JABRA_CAPTURE_DEV, AUDIO_SAMPLE_RATE, AUDIO_CHANNELS
    device = device or JABRA_CAPTURE_DEV
    if device.startswith("hw:"):
        device = "plug" + device
    _play_beep()
    _release_audio_device()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(2):
        cmd = ["arecord", "-D", device, "-f", "S16_LE",
               "-r", str(AUDIO_SAMPLE_RATE), "-c", str(AUDIO_CHANNELS),
               "-d", str(duration), output_path]
        _logger().info("[VOICE] Recording %ds (attempt %d)…", duration, attempt + 1)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                _logger().info("[VOICE] Recorded %s (%d bytes)", output_path, os.path.getsize(output_path))
                return True
            if "busy" in res.stderr.lower():
                _release_audio_device()
                time.sleep(0.5)
                continue
        except subprocess.TimeoutExpired:
            pass
        break

    # Fallback: parecord
    return _record_pulseaudio(output_path, duration)


def _record_pulseaudio(output_path: str, duration: int) -> bool:
    from config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS
    try:
        cmd = ["parecord", "--channels", str(AUDIO_CHANNELS), "--rate", str(AUDIO_SAMPLE_RATE),
               "--format", "s16le", "--file-format", "wav", output_path]
        subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 1)
    except subprocess.TimeoutExpired:
        pass
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return True
    return False


# ============================================================
# Playback — Bose Bluetooth Speaker
# ============================================================

def _discover_bt_sink() -> Optional[str]:
    try:
        res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True, timeout=5)
        for line in res.stdout.split("\n"):
            if "bluez_sink" in line:
                return line.split()[1]
    except Exception:
        pass
    return None


def play_audio(audio_path: str) -> bool:
    """Play WAV/PCM file via Bluetooth speaker, fallback to default sink."""
    from config import BOSE_SINK
    if not os.path.exists(audio_path):
        return False
    # Try Bose sink
    for sink in [BOSE_SINK, _discover_bt_sink(), None]:
        cmd = ["paplay"]
        if sink:
            cmd += ["-d", sink]
        cmd.append(audio_path)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                return True
        except Exception:
            continue
    return False


# ============================================================
# TTS — Amazon Polly (online) → pyttsx3 (offline)
# ============================================================

def text_to_speech(text: str, output_path: str) -> bool:
    """Convert text to WAV. Tries Polly first, then pyttsx3 offline."""
    if _try_polly_tts(text, output_path):
        return True
    _logger().info("[TTS] Polly unavailable, using pyttsx3 offline")
    return _try_pyttsx3(text, output_path)


def _try_polly_tts(text: str, output_path: str) -> bool:
    try:
        import boto3
        from config import AWS_REGION
        from language_handler import get_polly_voice, get_polly_lang_code, get_language_info

        info = get_language_info()
        voice = info.get("polly_voice") or "Kajal"
        engine = info.get("polly_engine", "neural")
        lang_code = info.get("polly_lang", "en-IN")

        client = boto3.client("polly", region_name=AWS_REGION)
        kwargs = dict(
            Text=text, OutputFormat="pcm", VoiceId=voice,
            SampleRate="16000", LanguageCode=lang_code,
        )
        # neural engine only for voices that support it
        if engine == "neural":
            kwargs["Engine"] = "neural"
        resp = client.synthesize_speech(**kwargs)

        pcm = resp["AudioStream"].read()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        # Wrap raw PCM in a WAV header
        _pcm_to_wav(pcm, output_path)
        _logger().info("[TTS] Polly generated: %s", output_path)
        return True
    except Exception as e:
        _logger().warning("[TTS] Polly error: %s", e)
        return False


def _pcm_to_wav(pcm_data: bytes, wav_path: str, rate: int = 16000, channels: int = 1, width: int = 2):
    """Wrap raw PCM bytes in a WAV file."""
    import struct
    data_len = len(pcm_data)
    with open(wav_path, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_len))
        f.write(b"WAVE")
        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<HHIIHH", 1, channels, rate, rate * channels * width, channels * width, width * 8))
        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", data_len))
        f.write(pcm_data)


def _try_pyttsx3(text: str, output_path: str) -> bool:
    global _pyttsx_engine
    try:
        import pyttsx3
        if _pyttsx_engine is None:
            _pyttsx_engine = pyttsx3.init()
            _pyttsx_engine.setProperty("rate", 150)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        _pyttsx_engine.save_to_file(text, output_path)
        _pyttsx_engine.runAndWait()
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            _logger().info("[TTS] pyttsx3 generated: %s", output_path)
            return True
        return False
    except Exception as e:
        _logger().warning("[TTS] pyttsx3 error: %s", e)
        return False


# ============================================================
# STT — Amazon Transcribe (online) → SpeechRecognition (offline/free)
# ============================================================

def speech_to_text(audio_path: str) -> Tuple[str, float]:
    """Transcribe audio. Returns (text, confidence). Tries Transcribe Streaming then free fallback."""
    print("  [Processing speech...]", flush=True)
    t0 = time.time()
    text, conf = _try_transcribe_stt(audio_path)
    if text:
        _logger().info("[STT] Completed in %.1fs", time.time() - t0)
        return text, conf
    text, conf = _try_speech_recognition(audio_path)
    _logger().info("[STT] Completed in %.1fs", time.time() - t0)
    return text, conf


def _try_transcribe_stt(audio_path: str) -> Tuple[str, float]:
    """Use AWS Transcribe Streaming SDK for real-time STT."""
    try:
        import asyncio
        from amazon_transcribe.client import TranscribeStreamingClient
        from amazon_transcribe.handlers import TranscriptResultStreamHandler
        from amazon_transcribe.model import TranscriptEvent
        from config import AWS_REGION
        from language_handler import get_transcribe_lang_code

        lang = get_transcribe_lang_code()
        if not lang:
            return "", 0.0

        # Read the WAV file (skip 44-byte header)
        with open(audio_path, "rb") as f:
            f.read(44)  # skip WAV header
            audio_data = f.read()

        if not audio_data:
            return "", 0.0

        final_transcript = []

        class Handler(TranscriptResultStreamHandler):
            async def handle_transcript_event(self, transcript_event: TranscriptEvent):
                results = transcript_event.transcript.results
                for result in results:
                    if not result.is_partial:
                        for alt in result.alternatives:
                            final_transcript.append(alt.transcript)

        async def _stream():
            client = TranscribeStreamingClient(region=AWS_REGION)
            stream = await client.start_stream_transcription(
                language_code=lang,
                media_sample_rate_hz=16000,
                media_encoding="pcm",
            )
            handler = Handler(stream.output_stream)

            # Stream audio chunks (8KB each)
            chunk_size = 8192
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await stream.input_stream.end_stream()

            await handler.handle_events()

        asyncio.run(_stream())

        text = " ".join(final_transcript).strip()
        if text:
            _logger().info("[STT] Transcribe Streaming: '%s'", text[:80])
            return text, 0.92
        return "", 0.0

    except Exception as e:
        _logger().warning("[STT] Transcribe Streaming error: %s", e)
        return "", 0.0


def _try_speech_recognition(audio_path: str) -> Tuple[str, float]:
    """Fallback STT using free SpeechRecognition library."""
    try:
        import speech_recognition as sr
        rec = sr.Recognizer()
        with sr.AudioFile(audio_path) as src:
            audio = rec.record(src)
        text = rec.recognize_google(audio)
        _logger().info("[STT] SpeechRecognition: '%s'", text[:80])
        return text, 0.80
    except Exception as e:
        _logger().warning("[STT] SpeechRecognition error: %s", e)
        return "", 0.0


# ============================================================
# High-level helpers
# ============================================================

def speak(text: str) -> bool:
    """Generate TTS and play through speaker."""
    from config import TEMP_AUDIO_OUTPUT
    out = str(TEMP_AUDIO_OUTPUT)
    if text_to_speech(text, out):
        return play_audio(out)
    return False


def listen(duration: int = 7) -> str:
    """Record and transcribe (no wake word check). Retries once on empty result."""
    from config import TEMP_AUDIO_INPUT
    inp = str(TEMP_AUDIO_INPUT)
    for attempt in range(2):
        if record_audio(inp, duration):
            text, _ = speech_to_text(inp)
            if text:
                return text
            if attempt == 0:
                _logger().info("[VOICE] STT returned empty, retrying recording...")
        else:
            break
    return ""


def listen_for_wake_word(duration: int = 7) -> Tuple[bool, str]:
    """Record, transcribe, check for wake word. Returns (detected, command)."""
    from config import TEMP_AUDIO_INPUT, WAKE_WORDS, WAKE_WORD_VARIATIONS, WAKE_PHRASES
    inp = str(TEMP_AUDIO_INPUT)
    if not record_audio(inp, duration):
        return False, ""
    text, _ = speech_to_text(inp)
    if not text:
        return False, ""
    return detect_wake_word(text)


def detect_wake_word(text: str) -> Tuple[bool, str]:
    """Check if text contains wake word 'asha' and extract command."""
    if not text:
        return False, ""
    text_l = text.lower().strip()
    from config import WAKE_WORD_VARIATIONS
    words = text_l.split()
    # Check first two words for any wake word variation
    first_two = " ".join(words[:2]) if len(words) >= 2 else text_l
    for var in WAKE_WORD_VARIATIONS:
        if var in first_two:
            # Extract command after the wake word
            idx = text_l.find(var)
            cmd = text_l[idx + len(var):].strip()
            cmd = re.sub(r"^[,.\s]+", "", cmd)
            cmd = re.sub(r"^(and|please|can you|could you)\s+", "", cmd, flags=re.IGNORECASE)
            return True, cmd.strip()
    return False, ""


def check_audio_devices() -> dict:
    """Check availability of audio input/output devices."""
    status = {"mic": False, "speaker": False, "speaker_name": None}
    try:
        res = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
        if "card" in res.stdout.lower():
            status["mic"] = True
    except Exception:
        pass
    try:
        res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True, timeout=5)
        for line in res.stdout.split("\n"):
            if "bluez_sink" in line:
                status["speaker"] = True
                status["speaker_name"] = line.split()[1] if len(line.split()) >= 2 else None
                break
        if not status["speaker"] and res.stdout.strip():
            status["speaker"] = True  # at least default sink exists
    except Exception:
        pass
    return status
