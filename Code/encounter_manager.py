#!/usr/bin/env python3
"""
encounter_manager.py - Patient encounter workflow state machine for Dear-Care.
Manages the complete encounter flow: demographics → photo → vitals → audio →
triage → recommendations → OCR → store → sync → education.
Integrates with Fit-U companion app for mobility data.
"""

import os
import json
from enum import Enum
from typing import Optional, Dict
from pathlib import Path

from config import (
    ENCOUNTER_DIR, ENCOUNTER_START, CONFIRM_CAPTURE,
    CSV_HEADERS,
)
from utils import get_logger, generate_encounter_id, generate_patient_id, get_timestamp

_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


class EncounterState(Enum):
    IDLE = "idle"
    DEMOGRAPHICS = "demographics"
    PHOTO = "photo"
    VITALS = "vitals"
    AUDIO = "audio"
    TRIAGE = "triage"
    OCR = "ocr"
    REVIEW = "review"
    COMPLETE = "complete"


# Valid transitions
_TRANSITIONS = {
    EncounterState.IDLE: [EncounterState.DEMOGRAPHICS],
    EncounterState.DEMOGRAPHICS: [EncounterState.PHOTO, EncounterState.VITALS, EncounterState.COMPLETE],
    EncounterState.PHOTO: [EncounterState.VITALS, EncounterState.OCR, EncounterState.COMPLETE],
    EncounterState.VITALS: [EncounterState.AUDIO, EncounterState.TRIAGE, EncounterState.COMPLETE],
    EncounterState.AUDIO: [EncounterState.TRIAGE, EncounterState.COMPLETE],
    EncounterState.TRIAGE: [EncounterState.OCR, EncounterState.REVIEW, EncounterState.COMPLETE],
    EncounterState.OCR: [EncounterState.REVIEW, EncounterState.COMPLETE],
    EncounterState.REVIEW: [EncounterState.COMPLETE],
    EncounterState.COMPLETE: [EncounterState.IDLE],
}


class EncounterManager:
    """Manages a single patient encounter through all steps."""

    def __init__(self):
        self.state = EncounterState.IDLE
        self.encounter_id: Optional[str] = None
        self.patient_id: Optional[str] = None
        self.data: Dict = {}
        self.folder: Optional[Path] = None
        self.fitu_client = None
        self.fitu_data = {}

    def init_fitu_client(self):
        """Initialize Fit-U client (lazy initialization)."""
        if self.fitu_client is None:
            try:
                from fitu_client import FituClient
                from config import Config
                self.fitu_client = FituClient(Config())
                _logger().info("[ENC] Fit-U client initialized")
            except Exception as e:
                _logger().warning("[ENC] Fit-U client init failed: %s", e)
        return self.fitu_client

    @property
    def active(self) -> bool:
        return self.state != EncounterState.IDLE

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _transition(self, new_state: EncounterState):
        if new_state in _TRANSITIONS.get(self.state, []):
            _logger().info("[ENC] %s → %s", self.state.value, new_state.value)
            self.state = new_state
        else:
            _logger().warning("[ENC] Invalid transition %s → %s", self.state.value, new_state.value)

    # ------------------------------------------------------------------
    # Start / End
    # ------------------------------------------------------------------

    def start(self) -> str:
        """Start a new encounter. Returns encounter ID."""
        self.encounter_id = generate_encounter_id()
        self.patient_id = generate_patient_id()
        self.data = {
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "timestamp": get_timestamp(),
            "aadhaar_number": "",
            "patient_name": "",
            "age": "",
            "gender": "",
            "spo2": "",
            "heart_rate": "",
            "temperature": "",
            "triage_level": "",
            "triage_confidence": "",
            "sync_status": "pending",
            "photo_count": 0,
            "audio_count": 0,
            "notes": "",
            "symptoms": "",
        }
        # Create encounter folder
        self.folder = ENCOUNTER_DIR / self.encounter_id
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / "photos").mkdir(exist_ok=True)
        (self.folder / "audio").mkdir(exist_ok=True)

        self._transition(EncounterState.DEMOGRAPHICS)

        # Save initial data
        self._save_encounter_json()

        from storage_manager import StorageManager
        sm = StorageManager()
        sm.create_encounter(self.encounter_id, **{k: v for k, v in self.data.items() if k != 'encounter_id'})

        _logger().info("[ENC] Started encounter %s", self.encounter_id)
        return self.encounter_id

    def end(self) -> Dict:
        """End current encounter and return summary."""
        if not self.active:
            return {}
        summary = self._build_summary()
        self.state = EncounterState.COMPLETE
        self._save_encounter_json()

        from storage_manager import StorageManager
        sm = StorageManager()
        sm.update_encounter(self.encounter_id, **{k: v for k, v in self.data.items() if k != 'encounter_id'})

        _logger().info("[ENC] Ended encounter %s", self.encounter_id)
        self._reset()
        return summary

    def cancel(self):
        """Cancel the current encounter without saving."""
        _logger().info("[ENC] Cancelled encounter %s", self.encounter_id)
        self._reset()

    def _reset(self):
        self.state = EncounterState.IDLE
        self.encounter_id = None
        self.patient_id = None
        self.data = {}
        self.folder = None

    # ------------------------------------------------------------------
    # Demographics
    # ------------------------------------------------------------------

    def set_demographics(self, name: str = "", age: str = "", gender: str = ""):
        self.data["patient_name"] = name
        self.data["age"] = age
        self.data["gender"] = gender
        _logger().info("[ENC] Demographics: %s, %s, %s", name, age, gender)

    def parse_demographics(self, text: str) -> Dict:
        """Try to extract name, age, gender from free-form text."""
        import re
        info = {"name": "", "age": "", "gender": ""}

        # Age patterns
        age_match = re.search(r'(\d{1,3})\s*(?:years?|yrs?|sal)\s*(?:old)?', text, re.IGNORECASE)
        if age_match:
            info["age"] = age_match.group(1)

        # Gender
        lower = text.lower()
        if any(w in lower for w in ["female", "woman", "girl", "mahila", "lady", "aurat"]):
            info["gender"] = "F"
        elif any(w in lower for w in ["male", "man", "boy", "aadmi"]):
            info["gender"] = "M"

        # Name — heuristic: first capitalized word(s) not matching other patterns
        words = text.split()
        name_words = []
        skip = {"years", "year", "old", "male", "female", "patient", "name", "age", "gender"}
        for w in words:
            clean = re.sub(r'[^a-zA-Z]', '', w)
            if clean and clean.lower() not in skip and not clean.isdigit():
                name_words.append(clean)
                if len(name_words) >= 3:
                    break
        info["name"] = " ".join(name_words)

        return info

    def advance_from_demographics(self):
        self._transition(EncounterState.PHOTO)

    # ------------------------------------------------------------------
    # Photo capture
    # ------------------------------------------------------------------

    def save_photo(self, image_path: str) -> Optional[str]:
        """Copy/move captured photo into encounter folder. Returns saved path."""
        import shutil
        if not self.folder:
            return None
        count = self.data.get("photo_count", 0) + 1
        dest = self.folder / "photos" / f"photo_{count}.jpg"
        try:
            shutil.copy2(image_path, str(dest))
            self.data["photo_count"] = count
            _logger().info("[ENC] Saved photo %d: %s", count, dest)
            return str(dest)
        except Exception as e:
            _logger().error("[ENC] Photo save error: %s", e)
            return None

    def advance_from_photo(self):
        self._transition(EncounterState.VITALS)

    # ------------------------------------------------------------------
    # Vitals
    # ------------------------------------------------------------------

    def set_vitals(self, spo2=None, heart_rate=None, temperature=None):
        if spo2 is not None:
            self.data["spo2"] = str(round(spo2, 1))
        if heart_rate is not None:
            self.data["heart_rate"] = str(round(heart_rate, 1))
        if temperature is not None:
            self.data["temperature"] = str(round(temperature, 1))

    def advance_from_vitals(self):
        self._transition(EncounterState.AUDIO)

    # ------------------------------------------------------------------
    # Audio recording
    # ------------------------------------------------------------------

    def save_audio(self, audio_path: str) -> Optional[str]:
        """Save audio recording into encounter folder."""
        import shutil
        if not self.folder:
            return None
        count = self.data.get("audio_count", 0) + 1
        dest = self.folder / "audio" / f"audio_{count}.wav"
        try:
            shutil.copy2(audio_path, str(dest))
            self.data["audio_count"] = count
            _logger().info("[ENC] Saved audio %d: %s", count, dest)
            return str(dest)
        except Exception as e:
            _logger().error("[ENC] Audio save error: %s", e)
            return None

    def advance_from_audio(self):
        self._transition(EncounterState.TRIAGE)

    # ------------------------------------------------------------------
    # Triage
    # ------------------------------------------------------------------

    def run_triage(self, symptoms: str = "") -> "TriageResult":
        """Run on-device triage using current vitals."""
        from triage_engine import assess
        spo2 = float(self.data["spo2"]) if self.data.get("spo2") else None
        hr = float(self.data["heart_rate"]) if self.data.get("heart_rate") else None
        temp = float(self.data["temperature"]) if self.data.get("temperature") else None
        self.data["symptoms"] = symptoms

        result = assess(spo2=spo2, heart_rate=hr, temperature=temp, symptoms=symptoms)
        self.data["triage_level"] = result.level.value
        self.data["triage_confidence"] = str(round(result.confidence, 2))
        if self.state != EncounterState.TRIAGE:
            self._transition(EncounterState.TRIAGE)
        return result

    def advance_from_triage(self):
        self._transition(EncounterState.OCR)

    # ------------------------------------------------------------------
    # Fit-U Integration
    # ------------------------------------------------------------------

    def fetch_fitu_data(self, worker_id: str) -> Dict:
        """
        Fetch latest Fit-U health data for the worker.
        Should be called before final AI analysis.

        Args:
            worker_id: The health worker ID

        Returns:
            Dict with Fit-U health data or empty dict if unavailable
        """
        if not worker_id:
            _logger().warning("[ENC] No worker_id provided for Fit-U fetch")
            return {}

        try:
            client = self.init_fitu_client()
            if client:
                self.fitu_data = client.fetch_latest_fitu_data(worker_id)
                if self.fitu_data:
                    _logger().info(
                        "[ENC] Fit-U data fetched: steps=%s, activity=%s",
                        self.fitu_data.get("steps", 0),
                        self.fitu_data.get("activity", "unknown")
                    )
                return self.fitu_data
        except Exception as e:
            _logger().warning("[ENC] Fit-U data fetch failed: %s", e)
        return {}

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    def run_ocr(self, image_path: str = None) -> str:
        """Run OCR on latest photo or given image. Returns extracted text."""
        if image_path is None:
            # Use latest photo
            count = self.data.get("photo_count", 0)
            if count > 0 and self.folder:
                image_path = str(self.folder / "photos" / f"photo_{count}.jpg")
            else:
                return ""
        from ocr_handler import extract_text
        text = extract_text(image_path)
        if text:
            self.data["notes"] = (self.data.get("notes", "") + " OCR: " + text[:200]).strip()
        self._transition(EncounterState.OCR)
        return text

    def advance_from_ocr(self):
        self._transition(EncounterState.REVIEW)

    # ------------------------------------------------------------------
    # Skip steps
    # ------------------------------------------------------------------

    def skip_to(self, target: EncounterState):
        """Skip forward to a target state, if reachable from current."""
        visited = set()
        queue = [self.state]
        while queue:
            s = queue.pop(0)
            if s == target:
                self._transition(target)
                return True
            if s in visited:
                continue
            visited.add(s)
            queue.extend(_TRANSITIONS.get(s, []))
        _logger().warning("[ENC] Cannot skip to %s from %s", target.value, self.state.value)
        return False

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_encounter_json(self):
        if not self.folder:
            return
        path = self.folder / "encounter.json"
        try:
            with open(path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            _logger().error("[ENC] JSON save error: %s", e)

    def _build_summary(self) -> Dict:
        return {
            "encounter_id": self.encounter_id,
            "patient_name": self.data.get("patient_name", ""),
            "aadhaar_number": self.data.get("aadhaar_number", ""),
            "age": self.data.get("age", ""),
            "gender": self.data.get("gender", ""),
            "spo2": self.data.get("spo2", ""),
            "heart_rate": self.data.get("heart_rate", ""),
            "temperature": self.data.get("temperature", ""),
            "triage_level": self.data.get("triage_level", ""),
            "photo_count": self.data.get("photo_count", 0),
            "audio_count": self.data.get("audio_count", 0),
            "notes": self.data.get("notes", ""),
            "sync_status": self.data.get("sync_status", "pending"),
        }

    def get_voice_summary(self) -> str:
        """Generate a voice-friendly summary of current encounter."""
        parts = []
        name = self.data.get("patient_name")
        if name:
            parts.append(f"Patient {name}")
        age = self.data.get("age")
        gender = self.data.get("gender")
        if age:
            parts.append(f"Age {age}")
        if gender:
            parts.append(f"Gender {'female' if gender == 'F' else 'male' if gender == 'M' else gender}")

        from triage_engine import format_vitals_report
        spo2 = float(self.data["spo2"]) if self.data.get("spo2") else None
        hr = float(self.data["heart_rate"]) if self.data.get("heart_rate") else None
        temp = float(self.data["temperature"]) if self.data.get("temperature") else None
        vitals = format_vitals_report(spo2, hr, temp)
        if vitals != "No vital signs were measured.":
            parts.append(vitals)

        triage = self.data.get("triage_level")
        if triage:
            parts.append(f"Triage level: {triage}")

        photos = self.data.get("photo_count", 0)
        audios = self.data.get("audio_count", 0)
        if photos:
            parts.append(f"{photos} photos captured")
        if audios:
            parts.append(f"{audios} audio recordings")

        return ". ".join(parts) + "." if parts else "No data collected yet."

    def get_next_prompt(self) -> str:
        """Get the next prompt based on current state."""
        prompts = {
            EncounterState.DEMOGRAPHICS: ENCOUNTER_START,
            EncounterState.PHOTO: CONFIRM_CAPTURE,
            EncounterState.VITALS: "Ready to measure vitals. Please attach the sensor.",
            EncounterState.AUDIO: "Would you like to record a cough or symptom audio?",
            EncounterState.TRIAGE: "Running health assessment now.",
            EncounterState.OCR: "Would you like to scan a prescription or document?",
            EncounterState.REVIEW: "Here is the encounter summary. Say confirm to save, or cancel.",
            EncounterState.COMPLETE: "Encounter saved. Say sync to upload when ready.",
        }
        return prompts.get(self.state, "")
