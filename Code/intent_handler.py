#!/usr/bin/env python3
"""
intent_handler.py - Wake word detection and intent classification for Pocket ASHA.
"""

from enum import Enum, auto
from typing import Tuple

from config import (
    CAPTURE_KEYWORDS, VITALS_KEYWORDS, RECORD_AUDIO_KEYWORDS,
    CONFIRM_KEYWORDS, DENY_KEYWORDS, HEALTH_KEYWORDS, EXIT_KEYWORDS,
    ENCOUNTER_KEYWORDS, SYNC_KEYWORDS, LANGUAGE_KEYWORDS, HELP_KEYWORDS,
)


class Intent(Enum):
    START_ENCOUNTER = auto()
    CAPTURE_IMAGE = auto()
    MEASURE_VITALS = auto()
    RECORD_AUDIO = auto()
    CONFIRM = auto()
    DENY = auto()
    HEALTH_QUESTION = auto()
    SET_LANGUAGE = auto()
    SYNC_DATA = auto()
    HELP = auto()
    EXIT = auto()
    GREETING = auto()
    THANKS = auto()
    UNKNOWN = auto()


# keyword → intent mapping (order matters: first match wins)
_KEYWORD_MAP = [
    (ENCOUNTER_KEYWORDS, Intent.START_ENCOUNTER),
    (CAPTURE_KEYWORDS, Intent.CAPTURE_IMAGE),
    (VITALS_KEYWORDS, Intent.MEASURE_VITALS),
    (RECORD_AUDIO_KEYWORDS, Intent.RECORD_AUDIO),
    (CONFIRM_KEYWORDS, Intent.CONFIRM),
    (DENY_KEYWORDS, Intent.DENY),
    (HEALTH_KEYWORDS, Intent.HEALTH_QUESTION),
    (LANGUAGE_KEYWORDS, Intent.SET_LANGUAGE),
    (SYNC_KEYWORDS, Intent.SYNC_DATA),
    (HELP_KEYWORDS, Intent.HELP),
    (EXIT_KEYWORDS, Intent.EXIT),
]

_GREETING_WORDS = ["hello", "hi", "namaste", "good morning", "good afternoon", "good evening"]
_THANKS_WORDS = ["thank", "thanks", "dhanyavaad", "shukriya"]


def classify(text: str) -> Tuple[Intent, float]:
    """
    Classify user intent from text.
    Returns (Intent, confidence 0-1).
    """
    if not text:
        return Intent.UNKNOWN, 0.0

    text_l = text.lower().strip()
    words = text_l.split()

    # Keyword matching — score by number of matching keywords (run first)
    best_intent = Intent.UNKNOWN
    best_score = 0.0

    for keywords, intent in _KEYWORD_MAP:
        matches = 0
        for kw in keywords:
            if len(kw) <= 3:
                # Short keywords: match whole words only
                if kw in words:
                    matches += 1
            else:
                if kw in text_l:
                    matches += 1
        if matches > 0:
            score = min(0.5 + matches * 0.15, 0.98)
            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score >= 0.65:
        return best_intent, best_score

    # Thanks — word-level match, only if no strong keyword match
    if any(w in words for w in ["thanks", "thank", "dhanyavaad", "shukriya"]):
        return Intent.THANKS, 0.85

    # Greeting — word-level match
    if any(w in words for w in ["hello", "hi", "namaste"]) or \
       any(g in text_l for g in ["good morning", "good afternoon", "good evening"]):
        return Intent.GREETING, 0.85

    if best_score > 0:
        return best_intent, best_score

    # Check for camera-related words as extra signal
    camera_words = ["picture", "photo", "image", "camera", "snap", "capture", "scan", "read"]
    if any(w in text_l for w in camera_words):
        return Intent.CAPTURE_IMAGE, 0.60

    # Check for health question patterns
    health_q = ["how", "what", "why", "should", "can i", "is it"]
    if any(q in text_l for q in health_q) and any(h in text_l for h in ["health", "pain", "sick", "feel"]):
        return Intent.HEALTH_QUESTION, 0.55

    return Intent.UNKNOWN, 0.0
