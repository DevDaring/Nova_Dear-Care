#!/usr/bin/env python3
"""
triage_engine.py - On-device clinical triage for Dear-Care.
Rule-based assessment that works entirely offline. < 10s completion.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List

from config import (
    SPO2_LOW_THRESHOLD, SPO2_CRITICAL_THRESHOLD,
    HR_LOW_THRESHOLD, HR_HIGH_THRESHOLD, HR_CRITICAL_LOW, HR_CRITICAL_HIGH,
    TEMP_HIGH_THRESHOLD, TEMP_CRITICAL_THRESHOLD, TEMP_LOW_THRESHOLD,
)
from utils import get_logger

_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


class TriageLevel(Enum):
    URGENT = "URGENT"
    FOLLOW_UP = "FOLLOW_UP"
    ROUTINE = "ROUTINE"
    UNKNOWN = "UNKNOWN"


@dataclass
class TriageResult:
    level: TriageLevel = TriageLevel.UNKNOWN
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """One-line summary for voice output."""
        if self.level == TriageLevel.URGENT:
            return "URGENT: Patient needs immediate medical attention. " + "; ".join(self.reasons[:2])
        elif self.level == TriageLevel.FOLLOW_UP:
            return "FOLLOW-UP: Patient should see a doctor within 24 hours. " + "; ".join(self.reasons[:2])
        elif self.level == TriageLevel.ROUTINE:
            return "ROUTINE: Patient vitals are within normal range."
        return "Unable to assess triage level due to insufficient data."


# ============================================================
# Rule-based triage
# ============================================================

def assess(
    spo2: Optional[float] = None,
    heart_rate: Optional[float] = None,
    temperature: Optional[float] = None,
    symptoms: Optional[str] = None,
) -> TriageResult:
    """Assess patient condition. Returns TriageResult. Works entirely offline."""
    result = TriageResult()
    flags_urgent = []
    flags_follow = []
    flags_normal = []
    data_points = 0

    # ---- SpO2 ----
    if spo2 is not None:
        data_points += 1
        if spo2 < SPO2_CRITICAL_THRESHOLD:
            flags_urgent.append(f"SpO2 critically low at {spo2}%")
        elif spo2 < SPO2_LOW_THRESHOLD:
            flags_follow.append(f"SpO2 below normal at {spo2}%")
        else:
            flags_normal.append(f"SpO2 normal at {spo2}%")

    # ---- Heart Rate ----
    if heart_rate is not None:
        data_points += 1
        if heart_rate < HR_CRITICAL_LOW or heart_rate > HR_CRITICAL_HIGH:
            flags_urgent.append(f"Heart rate critical at {heart_rate} bpm")
        elif heart_rate < HR_LOW_THRESHOLD or heart_rate > HR_HIGH_THRESHOLD:
            flags_follow.append(f"Heart rate abnormal at {heart_rate} bpm")
        else:
            flags_normal.append(f"Heart rate normal at {heart_rate} bpm")

    # ---- Temperature ----
    if temperature is not None:
        data_points += 1
        if temperature >= TEMP_CRITICAL_THRESHOLD:
            flags_urgent.append(f"High fever at {temperature}°C")
        elif temperature >= TEMP_HIGH_THRESHOLD:
            flags_follow.append(f"Fever at {temperature}°C")
        elif temperature < TEMP_LOW_THRESHOLD:
            flags_follow.append(f"Low body temperature at {temperature}°C")
        else:
            flags_normal.append(f"Temperature normal at {temperature}°C")

    # ---- Symptom keywords ----
    if symptoms:
        data_points += 1
        lower = symptoms.lower()
        urgent_words = [
            "chest pain", "breathing difficulty", "unconscious",
            "seizure", "severe bleeding", "collapsed", "stroke",
            "not breathing", "unresponsive", "cyanosis",
        ]
        follow_words = [
            "headache", "dizziness", "vomiting", "diarrhoea", "diarrhea",
            "cough", "weakness", "pain", "swelling", "rash",
        ]
        for w in urgent_words:
            if w in lower:
                flags_urgent.append(f"Reported: {w}")
        for w in follow_words:
            if w in lower:
                flags_follow.append(f"Reported: {w}")
        if not flags_urgent and not flags_follow:
            flags_normal.append("No concerning symptoms detected")

    # ---- Determine level ----
    if flags_urgent:
        result.level = TriageLevel.URGENT
        result.reasons = flags_urgent + flags_follow
        result.recommendations = [
            "Refer patient to nearest health facility immediately.",
            "Monitor continuously until help arrives.",
        ]
        result.confidence = min(0.95, 0.6 + 0.1 * len(flags_urgent))
    elif flags_follow:
        result.level = TriageLevel.FOLLOW_UP
        result.reasons = flags_follow
        result.recommendations = [
            "Schedule follow-up within 24 hours.",
            "Monitor symptoms and recheck vitals.",
        ]
        result.confidence = min(0.85, 0.5 + 0.1 * len(flags_follow))
    elif data_points > 0:
        result.level = TriageLevel.ROUTINE
        result.reasons = flags_normal
        result.recommendations = ["Continue routine monitoring."]
        result.confidence = min(0.9, 0.5 + 0.15 * data_points)
    else:
        result.level = TriageLevel.UNKNOWN
        result.reasons = ["No vital signs or symptoms provided"]
        result.recommendations = ["Collect vital signs before assessment."]
        result.confidence = 0.0

    _logger().info("[TRIAGE] %s (conf=%.2f): %s", result.level.value, result.confidence, result.reasons)
    return result


def format_vitals_report(
    spo2: Optional[float] = None,
    heart_rate: Optional[float] = None,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
) -> str:
    """Human-readable vitals report for voice output."""
    parts = []
    if spo2 is not None:
        status = "normal" if spo2 >= SPO2_LOW_THRESHOLD else "low"
        parts.append(f"Oxygen level is {spo2:.0f} percent, which is {status}")
    if heart_rate is not None:
        if HR_LOW_THRESHOLD <= heart_rate <= HR_HIGH_THRESHOLD:
            status = "normal"
        else:
            status = "abnormal"
        parts.append(f"Heart rate is {heart_rate:.0f} beats per minute, which is {status}")
    if temperature is not None:
        if temperature >= TEMP_HIGH_THRESHOLD:
            status = "high, indicating fever"
        elif temperature < TEMP_LOW_THRESHOLD:
            status = "low"
        else:
            status = "normal"
        parts.append(f"Body temperature is {temperature:.1f} degrees Celsius, which is {status}")
    if humidity is not None:
        parts.append(f"Ambient humidity is {humidity:.0f} percent")

    if not parts:
        return "No vital signs were measured."
    return ". ".join(parts) + "."
